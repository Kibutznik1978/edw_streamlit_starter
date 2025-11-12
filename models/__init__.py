"""
Data models package for EDW Streamlit application.

This package contains dataclasses and type definitions used throughout
the application for type safety and structured data handling.

Modules:
- pdf_models: PDF report metadata and header information
- bid_models: Bid line data structures and reserve line information
- edw_models: EDW analysis trip data and statistics
"""

from .bid_models import (
    BidLineData,
    ReserveLineInfo,
)
from .edw_models import (
    EDWStatistics,
    TripData,
)
from .pdf_models import (
    HeaderInfo,
    ReportMetadata,
)

__all__ = [
    # PDF Models
    "ReportMetadata",
    "HeaderInfo",
    # Bid Line Models
    "BidLineData",
    "ReserveLineInfo",
    # EDW Models
    "TripData",
    "EDWStatistics",
]
