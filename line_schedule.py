"""Helpers for working with parsed bid line day assignments."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence

import pandas as pd

# Known comment token classifications (duplicated from bid_parser for downstream use)
TRIP_TOKEN_RE = r"^\d{3,4}[A-Z]?$"
NUMERIC_TOKEN_RE = r"^\d+$"


@dataclass(frozen=True)
class LineDayAssignment:
    """Represents a single day entry parsed from a bid line comment grid."""

    line_id: int
    pay_period: int
    day_index: int
    value: str
    value_type: str
    pay_period_code: Optional[str] = None

    def is_trip(self) -> bool:
        return self.value_type == "trip"

    def normalized_trip_id(self) -> Optional[int]:
        if not self.is_trip():
            return None
        token = self.value.strip().upper()
        if not token:
            return None
        if token.endswith("A") or token.endswith("B"):
            token = token[:-1]
        try:
            return int(token)
        except ValueError:
            return None


def line_day_records_to_df(records: Sequence[dict]) -> pd.DataFrame:
    """Convert raw comment day records into a typed DataFrame."""

    if not records:
        return pd.DataFrame(
            columns=["Line", "PayPeriod", "PayPeriodCode", "DayIndex", "Value", "ValueType"]
        )

    frame = pd.DataFrame.from_records(records)

    expected_columns = {
        "Line": int,
        "PayPeriod": int,
        "PayPeriodCode": object,
        "DayIndex": int,
        "Value": object,
        "ValueType": object,
    }
    missing = [col for col in expected_columns if col not in frame.columns]
    if missing:
        raise ValueError(f"Missing columns in line day records: {missing}")

    typed = frame.astype({col: dtype for col, dtype in expected_columns.items() if col in frame.columns})
    typed["Value"] = typed["Value"].fillna("")
    typed["ValueType"] = typed["ValueType"].fillna("unknown")
    return typed.sort_values(["Line", "PayPeriod", "DayIndex"]).reset_index(drop=True)


def map_line_to_trip_tokens(day_df: pd.DataFrame) -> Dict[int, List[str]]:
    """Group trip tokens by line ID preserving chronological order."""

    if day_df.empty:
        return {}

    trip_rows = day_df[day_df["ValueType"] == "trip"].copy()
    if trip_rows.empty:
        return {}

    trip_rows = trip_rows.sort_values(["Line", "PayPeriod", "DayIndex"])  # ensure chronological order

    grouped: Dict[int, List[str]] = {}
    for line_id, group in trip_rows.groupby("Line"):
        grouped[line_id] = group["Value"].astype(str).tolist()
    return grouped


def normalize_trip_token(token: str) -> Optional[int]:
    """Convert a trip token into an integer Trip ID when possible."""

    if not token:
        return None
    token = token.strip().upper()
    if token.endswith("A") or token.endswith("B"):
        token = token[:-1]
    if not token:
        return None
    try:
        return int(token)
    except ValueError:
        return None


def expand_line_day_assignments(day_df: pd.DataFrame) -> List[LineDayAssignment]:
    """Convert a DataFrame of day assignments into LineDayAssignment objects."""

    if day_df.empty:
        return []

    assignments: List[LineDayAssignment] = []
    for record in day_df.to_dict(orient="records"):
        assignments.append(
            LineDayAssignment(
                line_id=int(record["Line"]),
                pay_period=int(record["PayPeriod"]),
                day_index=int(record["DayIndex"]),
                value=str(record["Value"]),
                value_type=str(record["ValueType"]),
                pay_period_code=record.get("PayPeriodCode"),
            )
        )
    return assignments


def summarize_day_types(day_df: pd.DataFrame) -> pd.DataFrame:
    """Return a pivot table counting each ValueType per line."""

    if day_df.empty:
        return pd.DataFrame(columns=["Line", "ValueType", "Count"])

    counts = day_df.groupby(["Line", "ValueType"])  # type: ignore[arg-type]
    summary = counts.size().reset_index(name="Count")
    return summary.sort_values(["Line", "ValueType"]).reset_index(drop=True)

