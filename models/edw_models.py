"""
Data models for EDW pairing analysis.

Contains dataclasses representing individual trips and
aggregated EDW statistics from pairing analysis.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class TripData:
    """
    Individual trip/pairing record.

    Represents a single pairing with EDW classification and metrics.
    """

    trip_id: str
    is_edw: bool
    tafb_hours: Optional[float] = None  # Time Away From Base
    duty_days: Optional[int] = None
    credit_time_hours: Optional[float] = None
    is_hot_standby: bool = False
    edw_reason: Optional[str] = None  # Which duty day triggered EDW flag

    def trip_type(self) -> str:
        """
        Get human-readable trip type.

        Returns:
            String describing the trip classification
        """
        if self.is_hot_standby:
            return "Hot Standby"
        elif self.is_edw:
            return "EDW"
        else:
            return "Non-EDW"


@dataclass
class EDWStatistics:
    """
    Aggregated EDW statistics for a bid period.

    Contains summary metrics calculated from all trips in a pairing analysis.
    """

    total_trips: int
    edw_trips: int
    non_edw_trips: int
    trip_weighted_pct: float  # EDW trips / total trips * 100

    # Optional weighted percentages
    tafb_weighted_pct: Optional[float] = None  # EDW TAFB / total TAFB * 100
    duty_day_weighted_pct: Optional[float] = None  # EDW duty days / total duty days * 100

    # Optional raw values
    total_tafb_hours: Optional[float] = None
    edw_tafb_hours: Optional[float] = None
    total_duty_days: Optional[int] = None
    edw_duty_days: Optional[int] = None

    @property
    def edw_percentage(self) -> float:
        """Alias for trip_weighted_pct for backward compatibility."""
        return self.trip_weighted_pct

    def has_tafb_weighted(self) -> bool:
        """Check if TAFB-weighted percentage is available."""
        return self.tafb_weighted_pct is not None

    def has_duty_day_weighted(self) -> bool:
        """Check if duty-day-weighted percentage is available."""
        return self.duty_day_weighted_pct is not None
