"""Core merger utilities that link bid-line day assignments with pairing trip data."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

import pandas as pd

from line_schedule import line_day_records_to_df, normalize_trip_token
from trip_catalog import compute_trip_time_bands


@dataclass
class LineTripLink:
    line: int
    pay_period: int
    day_index: int
    trip_token: str
    trip_id: Optional[int]
    match_found: bool


def build_line_trip_links(
    line_day_records: Iterable[dict],
    trip_catalog: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Return per-day trip matches and per-line summary metrics.

    Args:
        line_day_records: Raw records emitted by the bid-line parser diagnostics.
        trip_catalog: DataFrame of parsed pairing trips with a `Trip ID` column.

    Returns:
        tuple(per_day_links, line_summary)
    """

    day_df = line_day_records_to_df(list(line_day_records))
    if day_df.empty:
        empty_links = pd.DataFrame(
            columns=["Line", "PayPeriod", "DayIndex", "Value", "TripID", "Match"]
        )
        summary = pd.DataFrame(
            columns=["Line", "ScheduledTrips", "UniqueTrips", "UnmatchedTokens"]
        )
        return empty_links, summary

    trip_rows = day_df[day_df["ValueType"] == "trip"].copy()
    if trip_rows.empty:
        empty_links = pd.DataFrame(
            columns=["Line", "PayPeriod", "DayIndex", "Value", "TripID", "Match"]
        )
        summary = pd.DataFrame(
            columns=["Line", "ScheduledTrips", "UniqueTrips", "UnmatchedTokens"]
        )
        return empty_links, summary

    trip_rows["TripID"] = trip_rows["Value"].apply(normalize_trip_token)

    catalog_ids = set(trip_catalog["Trip ID"].tolist()) if not trip_catalog.empty else set()
    trip_rows["Match"] = trip_rows["TripID"].apply(lambda value: value in catalog_ids if value is not None else False)

    per_day_links = trip_rows[["Line", "PayPeriod", "DayIndex", "Value", "TripID", "Match"]].copy()

    # Summaries per line
    grouped = per_day_links.groupby("Line")
    summary = grouped.agg(
        ScheduledTrips=("Value", "count"),
        UniqueTrips=("TripID", pd.Series.nunique),
        UnmatchedTokens=("Match", lambda matches: (~matches).sum()),
    ).reset_index()

    return per_day_links, summary


def unmatched_trip_tokens(per_day_links: pd.DataFrame) -> Dict[int, List[str]]:
    """Collect unmatched trip tokens by line for diagnostics."""

    if per_day_links.empty:
        return {}

    missing = per_day_links[~per_day_links["Match"]]
    if missing.empty:
        return {}

    result: Dict[int, List[str]] = {}
    for line_id, group in missing.groupby("Line"):
        result[line_id] = group["Value"].astype(str).tolist()
    return result


def summarize_line_trip_metrics(
    per_day_links: pd.DataFrame,
    trip_catalog: pd.DataFrame,
    day_start: int,
    day_end: int,
) -> pd.DataFrame:
    """Aggregate trip-level attributes for each line."""

    metric_columns = [
        "Line",
        "MatchedTripOccurrences",
        "MatchedUniqueTrips",
        "EDWTrips",
        "HotStandbyTrips",
        "TotalTAFBHours",
        "TotalDutyDays",
        "DayBlockHours",
        "NightBlockHours",
        "TripIDs",
    ]

    if per_day_links is None or per_day_links.empty:
        return pd.DataFrame(columns=metric_columns)

    if trip_catalog is None or trip_catalog.empty or "Trip ID" not in trip_catalog.columns:
        return pd.DataFrame(columns=metric_columns)

    matched = per_day_links[
        per_day_links["Match"] & per_day_links["TripID"].notna()
    ].copy()
    if matched.empty:
        return pd.DataFrame(columns=metric_columns)

    unique_pairs = matched.drop_duplicates(["Line", "TripID"])

    trip_subset_cols = [
        col
        for col in ["Trip ID", "EDW", "Hot Standby", "TAFB Hours", "Duty Days"]
        if col in trip_catalog.columns
    ]
    if "Trip ID" not in trip_subset_cols:
        trip_subset_cols.append("Trip ID")

    trip_subset = trip_catalog[trip_subset_cols].drop_duplicates("Trip ID")

    merged = unique_pairs.merge(
        trip_subset,
        left_on="TripID",
        right_on="Trip ID",
        how="left",
    )

    grouped = merged.groupby("Line", dropna=False)

    def _bool_sum(series: pd.Series) -> int:
        if series is None:
            return 0
        return int(series.fillna(False).astype(bool).sum())

    trip_time_bands = compute_trip_time_bands(trip_catalog, day_start, day_end)

    def _sum_band(series: pd.Series, index: int) -> float:
        total = 0.0
        for value in series:
            if pd.isna(value):
                continue
            try:
                trip_id = int(value)
            except (TypeError, ValueError):
                continue
            day_hours, night_hours = trip_time_bands.get(trip_id, (0.0, 0.0))
            total += day_hours if index == 0 else night_hours
        return round(total, 2)

    summary = pd.DataFrame(
        {
            "Line": grouped.size().index,
            "MatchedTripOccurrences": grouped["TripID"].count().values,
            "MatchedUniqueTrips": grouped["TripID"].nunique().values,
            "EDWTrips": (
                grouped["EDW"].apply(_bool_sum).values
                if "EDW" in merged.columns
                else [0] * grouped.ngroups
            ),
            "HotStandbyTrips": (
                grouped["Hot Standby"].apply(_bool_sum).values
                if "Hot Standby" in merged.columns
                else [0] * grouped.ngroups
            ),
            "TotalTAFBHours": (
                grouped["TAFB Hours"].sum(min_count=1).fillna(0).values
                if "TAFB Hours" in merged.columns
                else [0.0] * grouped.ngroups
            ),
            "TotalDutyDays": (
                grouped["Duty Days"].sum(min_count=1).fillna(0).values
                if "Duty Days" in merged.columns
                else [0.0] * grouped.ngroups
            ),
            "DayBlockHours": grouped["TripID"].apply(lambda s: _sum_band(s, 0)).values,
            "NightBlockHours": grouped["TripID"].apply(lambda s: _sum_band(s, 1)).values,
            "TripIDs": grouped["TripID"].apply(
                lambda series: sorted(
                    {int(value) for value in series if pd.notna(value)}
                )
            ).values,
        }
    )

    return summary
