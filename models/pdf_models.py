"""
Data models for PDF report generation.

Contains dataclasses for report metadata and header information
shared across EDW and Bid Line PDF generation.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Iterable


@dataclass
class ReportMetadata:
    """
    Metadata for analysis reports (EDW and Bid Line).

    Used to configure PDF report generation with titles, subtitles,
    and filter information.
    """

    title: str = "Analysis Report"
    subtitle: Optional[str] = None
    filters: Optional[Dict[str, Iterable]] = None

    def has_filters(self) -> bool:
        """
        Check if any filters are applied.

        Returns:
            True if filters dictionary exists and is non-empty
        """
        return self.filters is not None and len(self.filters) > 0


@dataclass
class HeaderInfo:
    """
    Parsed PDF header information.

    Contains metadata extracted from bid packet PDF headers including
    domicile, aircraft type, bid period, and date ranges.
    """

    domicile: Optional[str] = None
    aircraft: Optional[str] = None
    bid_period: Optional[str] = None
    date_range: Optional[str] = None
    source_page: int = 1  # Which page the header was found on

    def is_complete(self) -> bool:
        """
        Check if all required fields are present.

        Returns:
            True if domicile, aircraft, and bid_period are all populated
        """
        return all([self.domicile, self.aircraft, self.bid_period])

    def __str__(self) -> str:
        """
        Format header information for display.

        Returns:
            Human-readable string with all populated fields
        """
        parts = []
        if self.domicile:
            parts.append(f"Domicile: {self.domicile}")
        if self.aircraft:
            parts.append(f"Aircraft: {self.aircraft}")
        if self.bid_period:
            parts.append(f"Bid Period: {self.bid_period}")
        if self.date_range:
            parts.append(f"Date Range: {self.date_range}")
        return " | ".join(parts)
