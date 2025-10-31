"""
EDW detection logic for pairing analysis.

This module contains the core business logic for identifying Early/Day/Window (EDW)
trips and hot standby pairings.
"""

import re

from config import (
    EDW_END_HOUR,
    EDW_END_MINUTE,
    EDW_START_HOUR,
    EDW_START_MINUTE,
    HOT_STANDBY_MAX_SEGMENTS,
)

from .parser import extract_local_times


def is_edw_trip(trip_text):
    """
    Determine if a trip qualifies as EDW (Early/Day/Window).

    A trip is EDW if any duty day touches 02:30-05:00 local time (inclusive).
    Local time is extracted from pattern (HH)MM:SS where HH is local hour.

    Args:
        trip_text: Raw trip text or duty day text

    Returns:
        Boolean: True if trip/duty day is EDW, False otherwise

    EDW Time Range:
        - 02:30 to 05:00 local time (inclusive)
        - Includes: 02:30, 03:00, 04:00, 05:00
        - Excludes: 02:29, 05:01
    """
    times = extract_local_times(trip_text)
    for t in times:
        hh, mm = map(int, t.split(":"))
        # Check if time falls within EDW range using config constants
        if (
            (hh == EDW_START_HOUR and mm >= EDW_START_MINUTE)
            or (hh > EDW_START_HOUR and hh < EDW_END_HOUR)
            or (hh == EDW_END_HOUR and mm == EDW_END_MINUTE)
        ):
            return True
    return False


def is_hot_standby(trip_text):
    """
    Identify Hot Standby pairings.

    These are single-segment pairings where departure and arrival are the same (e.g., ONT-ONT).
    Pairings with positioning legs (e.g., ONT-DFW, DFW-DFW, DFW-ONT) are NOT hot standby.

    Logic: Only mark as Hot Standby if there's exactly ONE flight segment and it's XXX-XXX
    (same departure and arrival airport).

    Args:
        trip_text: Raw trip text

    Returns:
        Boolean: True if hot standby, False otherwise

    Example:
        - ONT-ONT (1 segment) → Hot Standby
        - SDF-SDF (1 segment) → Hot Standby
        - ONT-DFW, DFW-DFW, DFW-ONT (3 segments) → NOT Hot Standby
    """
    # Look for airport pair patterns like "ONT-ONT", "SDF-SDF", etc.
    # Format is typically: FLIGHT_NUMBER\nDEPT-ARVL
    pattern = re.compile(r"\b([A-Z]{3})-([A-Z]{3})\b")
    matches = pattern.findall(trip_text)

    # Only mark as Hot Standby if:
    # 1. Exactly one route segment found (using config constant)
    # 2. That segment has same departure and arrival
    if len(matches) == HOT_STANDBY_MAX_SEGMENTS:
        dept, arvl = matches[0]
        if dept == arvl:
            return True

    return False
