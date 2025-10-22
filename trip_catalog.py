"""Utility helpers for building a pairing trip catalog used by the bid sorter."""

from __future__ import annotations

import re

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

import pandas as pd

from edw_reporter import (
    is_edw_trip,
    is_hot_standby,
    parse_duty_day_details,
    parse_duty_days,
    parse_max_duty_day_length,
    parse_max_legs_per_duty_day,
    parse_tafb,
    parse_trip_for_table,
    parse_trip_frequency,
    parse_trip_id,
)


@dataclass
class TripDutyDay:
    """Flattened representation of a duty day extracted from trip text."""

    trip_id: int
    duty_index: int
    is_edw: bool
    num_legs: int
    block_hours: float
    credit_hours: float
    duty_hours: float
    first_depart_local: Optional[str] = None
    last_arrive_local: Optional[str] = None
    layover: Optional[str] = None


def build_trip_catalog(trip_texts: Iterable[str]) -> pd.DataFrame:
    """Generate a catalog DataFrame with key metrics for each trip."""

    records: List[dict] = []
    for trip_text in trip_texts:
        trip_id = parse_trip_id(trip_text)
        if trip_id is None:
            continue

        frequency = parse_trip_frequency(trip_text)
        tafb_hours = parse_tafb(trip_text)
        duty_days = parse_duty_days(trip_text)
        max_duty_length = parse_max_duty_day_length(trip_text)
        max_legs = parse_max_legs_per_duty_day(trip_text)
        duty_day_details = parse_duty_day_details(trip_text)
        edw = is_edw_trip(trip_text)
        hot_standby = is_hot_standby(trip_text)
        parsed_trip = parse_trip_for_table(trip_text)

        records.append(
            {
                "Trip ID": trip_id,
                "Frequency": frequency,
                "Duty Days": duty_days,
                "TAFB Hours": round(tafb_hours, 2) if tafb_hours else 0.0,
                "Max Duty Length": round(max_duty_length, 2) if max_duty_length else 0.0,
                "Max Legs": max_legs,
                "EDW": edw,
                "Hot Standby": hot_standby,
                "Duty Day Details": duty_day_details,
                "Trip Parsed": parsed_trip,
            }
        )

    return pd.DataFrame.from_records(records)


def extract_trip_duty_days(trip_catalog: pd.DataFrame) -> List[TripDutyDay]:
    """Expand the catalog into individual duty day entries."""

    duty_days: List[TripDutyDay] = []
    if trip_catalog.empty:
        return duty_days

    for _, row in trip_catalog.iterrows():
        trip_id = int(row["Trip ID"])
        details = row.get("Duty Day Details") or []
        for idx, duty in enumerate(details, start=1):
            duty_days.append(
                TripDutyDay(
                    trip_id=trip_id,
                    duty_index=idx,
                    is_edw=bool(duty.get("is_edw")),
                    num_legs=int(duty.get("num_legs", 0) or 0),
                    block_hours=float(duty.get("block_hours", 0.0) or 0.0),
                    credit_hours=float(duty.get("credit_hours", 0.0) or 0.0),
                    duty_hours=float(duty.get("duration_hours", 0.0) or 0.0),
                    first_depart_local=duty.get("first_depart_local"),
                    last_arrive_local=duty.get("last_arrive_local"),
                    layover=duty.get("layover"),
                )
            )

    return duty_days


def _parse_local_hour(time_str: str) -> Optional[int]:
    if not time_str:
        return None
    match = re.search(r"\((\d{1,2})\)", str(time_str))
    if not match:
        return None
    try:
        hour = int(match.group(1)) % 24
    except ValueError:
        return None
    return hour


def _parse_duration_to_hours(duration: str) -> float:
    if not duration:
        return 0.0
    match = re.match(r"^(\d+)h(\d+)$", str(duration).strip())
    if not match:
        return 0.0
    hours = int(match.group(1))
    minutes = int(match.group(2))
    return round(hours + minutes / 60.0, 2)


def _is_day_hour(hour: int, day_start: int, day_end: int) -> bool:
    day_start %= 24
    day_end %= 24
    hour %= 24

    if day_start == day_end:
        return True
    if day_start < day_end:
        return day_start <= hour < day_end
    return hour >= day_start or hour < day_end


def compute_trip_time_bands(
    trip_catalog: pd.DataFrame,
    day_start: int,
    day_end: int,
) -> Dict[int, Tuple[float, float]]:
    """Map Trip ID to (day_block_hours, night_block_hours)."""

    if trip_catalog is None or trip_catalog.empty or "Trip ID" not in trip_catalog.columns:
        return {}

    results: Dict[int, Tuple[float, float]] = {}

    for _, row in trip_catalog.iterrows():
        trip_id = row.get("Trip ID")
        if pd.isna(trip_id):
            continue
        try:
            trip_id_int = int(trip_id)
        except (TypeError, ValueError):
            continue

        parsed_trip = row.get("Trip Parsed")
        if not isinstance(parsed_trip, dict):
            results[trip_id_int] = (0.0, 0.0)
            continue

        day_hours = 0.0
        night_hours = 0.0

        duty_days = parsed_trip.get("duty_days") or []
        for duty in duty_days:
            flights = duty.get("flights") if isinstance(duty, dict) else None
            if not flights:
                continue
            for flight in flights:
                if not isinstance(flight, dict):
                    continue
                depart = flight.get("depart")
                block = flight.get("block")
                block_hours = _parse_duration_to_hours(block)
                if block_hours <= 0:
                    continue
                hour = _parse_local_hour(depart)
                if hour is None:
                    continue
                if _is_day_hour(hour, day_start, day_end):
                    day_hours += block_hours
                else:
                    night_hours += block_hours

        results[trip_id_int] = (round(day_hours, 2), round(night_hours, 2))

    return results
