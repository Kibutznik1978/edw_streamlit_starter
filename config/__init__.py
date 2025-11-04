"""
Configuration package for EDW Streamlit application.

This package centralizes all configuration, constants, and business rules
for better maintainability and single source of truth.

Modules:
- constants: Core business logic constants (EDW times, thresholds, etc.)
- branding: Brand identity and styling configuration
- validation: Validation rules and thresholds for data editing
"""

from .branding import (
    DEFAULT_BRAND,
    DEFAULT_REPORT_TITLE,
    LOGO_PATH,
    BrandColors,
)
from .constants import (  # EDW Time Detection; Buy-Up Analysis; Chart Configuration; Reserve Line Keywords; Hot Standby Detection
    BUYUP_THRESHOLD_HOURS,
    CHART_HEIGHT_PX,
    CHART_LABEL_ANGLE,
    CT_BT_BUCKET_SIZE_HOURS,
    EDW_END_HOUR,
    EDW_END_MINUTE,
    EDW_START_HOUR,
    EDW_START_MINUTE,
    EDW_TIME_RANGE_DESCRIPTION,
    HOT_STANDBY_MAX_SEGMENTS,
    RESERVE_DAY_KEYWORDS,
    SHIFTABLE_RESERVE_KEYWORD,
    VTO_KEYWORDS,
)
from .validation import (  # Credit Time / Block Time Validation; Days Off / Duty Days Validation; Combined Validation; Data Editor Configuration
    BT_MAX_HOURS,
    BT_MIN_HOURS,
    BT_WARNING_THRESHOLD_HOURS,
    CT_MAX_HOURS,
    CT_MIN_HOURS,
    CT_WARNING_THRESHOLD_HOURS,
    DD_MAX_DAYS,
    DD_MIN_DAYS,
    DD_WARNING_THRESHOLD_DAYS,
    DO_MAX_DAYS,
    DO_MIN_DAYS,
    DO_PLUS_DD_MAX_DAYS,
    DO_WARNING_THRESHOLD_DAYS,
    EDITABLE_COLUMNS,
    READONLY_COLUMNS,
)

__all__ = [
    # Constants
    "EDW_START_HOUR",
    "EDW_START_MINUTE",
    "EDW_END_HOUR",
    "EDW_END_MINUTE",
    "EDW_TIME_RANGE_DESCRIPTION",
    "BUYUP_THRESHOLD_HOURS",
    "CT_BT_BUCKET_SIZE_HOURS",
    "CHART_HEIGHT_PX",
    "CHART_LABEL_ANGLE",
    "RESERVE_DAY_KEYWORDS",
    "SHIFTABLE_RESERVE_KEYWORD",
    "VTO_KEYWORDS",
    "HOT_STANDBY_MAX_SEGMENTS",
    # Branding
    "BrandColors",
    "DEFAULT_BRAND",
    "LOGO_PATH",
    "DEFAULT_REPORT_TITLE",
    # Validation
    "CT_WARNING_THRESHOLD_HOURS",
    "BT_WARNING_THRESHOLD_HOURS",
    "CT_MIN_HOURS",
    "CT_MAX_HOURS",
    "BT_MIN_HOURS",
    "BT_MAX_HOURS",
    "DO_WARNING_THRESHOLD_DAYS",
    "DD_WARNING_THRESHOLD_DAYS",
    "DO_MIN_DAYS",
    "DO_MAX_DAYS",
    "DD_MIN_DAYS",
    "DD_MAX_DAYS",
    "DO_PLUS_DD_MAX_DAYS",
    "EDITABLE_COLUMNS",
    "READONLY_COLUMNS",
]
