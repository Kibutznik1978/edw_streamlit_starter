"""
Data models for bid line analysis.

Contains dataclasses representing individual bid lines and
reserve line information parsed from bid line PDFs.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class BidLineData:
    """
    Individual bid line record.

    Represents a single bid line with all metrics and classification flags.
    """

    line_number: int
    credit_time: float  # hours
    block_time: float  # hours
    days_off: int
    duty_days: int
    is_reserve: bool = False
    is_hsby: bool = False  # Hot Standby reserve
    vto_type: Optional[str] = None  # "VTO", "VTOR", "VOR"
    vto_period: Optional[int] = None  # 1 or 2 (which pay period is VTO)

    def is_buy_up(self, threshold: float = 75.0) -> bool:
        """
        Check if this line qualifies as a buy-up line.

        Args:
            threshold: Credit time threshold (default 75.0 hours)

        Returns:
            True if credit time is below threshold
        """
        return self.credit_time < threshold

    def is_split_vto(self) -> bool:
        """
        Check if this is a split VTO line (one period regular, one VTO).

        Returns:
            True if vto_type and vto_period are both set
        """
        return self.vto_type is not None and self.vto_period is not None


@dataclass
class ReserveLineInfo:
    """
    Reserve line slot information.

    Contains counts and line numbers for reserve and hot standby lines
    parsed from crew composition sections.
    """

    captain_slots: int = 0
    first_officer_slots: int = 0
    reserve_line_numbers: List[int] = field(default_factory=list)
    hsby_line_numbers: List[int] = field(default_factory=list)

    @property
    def total_slots(self) -> int:
        """Total reserve slots (Captain + First Officer)."""
        return self.captain_slots + self.first_officer_slots

    def has_reserve_lines(self) -> bool:
        """Check if any reserve lines exist."""
        return len(self.reserve_line_numbers) > 0 or len(self.hsby_line_numbers) > 0
