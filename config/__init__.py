"""
Configuration package for EDW Streamlit application.

This package centralizes all configuration, constants, and business rules
for better maintainability and single source of truth.

Modules:
- constants: Core business logic constants (EDW times, thresholds, etc.)
- branding: Brand identity and styling configuration
- validation: Validation rules and thresholds for data editing
"""

from .constants import (
    # EDW Time Detection
    EDW_START_HOUR,
    EDW_START_MINUTE,
    EDW_END_HOUR,
    EDW_END_MINUTE,
    EDW_TIME_RANGE_DESCRIPTION,

    # Buy-Up Analysis
    BUYUP_THRESHOLD_HOURS,

    # Chart Configuration
    CT_BT_BUCKET_SIZE_HOURS,
    CHART_HEIGHT_PX,
    CHART_LABEL_ANGLE,

    # Reserve Line Keywords
    RESERVE_DAY_KEYWORDS,
    SHIFTABLE_RESERVE_KEYWORD,
    VTO_KEYWORDS,

    # Hot Standby Detection
    HOT_STANDBY_MAX_SEGMENTS,
)

from .branding import (
    BrandColors,
    DEFAULT_BRAND,
    LOGO_PATH,
    DEFAULT_REPORT_TITLE,
)

from .validation import (
    # Credit Time / Block Time Validation
    CT_WARNING_THRESHOLD_HOURS,
    BT_WARNING_THRESHOLD_HOURS,
    CT_MIN_HOURS,
    CT_MAX_HOURS,
    BT_MIN_HOURS,
    BT_MAX_HOURS,

    # Days Off / Duty Days Validation
    DO_WARNING_THRESHOLD_DAYS,
    DD_WARNING_THRESHOLD_DAYS,
    DO_MIN_DAYS,
    DO_MAX_DAYS,
    DD_MIN_DAYS,
    DD_MAX_DAYS,

    # Combined Validation
    DO_PLUS_DD_MAX_DAYS,

    # Data Editor Configuration
    EDITABLE_COLUMNS,
    READONLY_COLUMNS,
)

__all__ = [
    # Constants
    'EDW_START_HOUR',
    'EDW_START_MINUTE',
    'EDW_END_HOUR',
    'EDW_END_MINUTE',
    'EDW_TIME_RANGE_DESCRIPTION',
    'BUYUP_THRESHOLD_HOURS',
    'CT_BT_BUCKET_SIZE_HOURS',
    'CHART_HEIGHT_PX',
    'CHART_LABEL_ANGLE',
    'RESERVE_DAY_KEYWORDS',
    'SHIFTABLE_RESERVE_KEYWORD',
    'VTO_KEYWORDS',
    'HOT_STANDBY_MAX_SEGMENTS',

    # Branding
    'BrandColors',
    'DEFAULT_BRAND',
    'LOGO_PATH',
    'DEFAULT_REPORT_TITLE',

    # Validation
    'CT_WARNING_THRESHOLD_HOURS',
    'BT_WARNING_THRESHOLD_HOURS',
    'CT_MIN_HOURS',
    'CT_MAX_HOURS',
    'BT_MIN_HOURS',
    'BT_MAX_HOURS',
    'DO_WARNING_THRESHOLD_DAYS',
    'DD_WARNING_THRESHOLD_DAYS',
    'DO_MIN_DAYS',
    'DO_MAX_DAYS',
    'DD_MIN_DAYS',
    'DD_MAX_DAYS',
    'DO_PLUS_DD_MAX_DAYS',
    'EDITABLE_COLUMNS',
    'READONLY_COLUMNS',
]
