"""
Validation thresholds and rules for bid line data editing.

This module defines all validation constraints used in the data editor
and throughout the application for bid line metrics.
"""

from typing import List

# =============================================================================
# Credit Time (CT) Validation
# =============================================================================

# Warn if CT exceeds this threshold (unusually high)
CT_WARNING_THRESHOLD_HOURS = 150.0

# Valid range for CT values in data editor
CT_MIN_HOURS = 0.0
CT_MAX_HOURS = 200.0


# =============================================================================
# Block Time (BT) Validation
# =============================================================================

# Warn if BT exceeds this threshold (unusually high)
BT_WARNING_THRESHOLD_HOURS = 150.0

# Valid range for BT values in data editor
BT_MIN_HOURS = 0.0
BT_MAX_HOURS = 200.0


# =============================================================================
# Days Off (DO) Validation
# =============================================================================

# Warn if DO exceeds this threshold (unusually high)
DO_WARNING_THRESHOLD_DAYS = 20

# Valid range for DO values in data editor
DO_MIN_DAYS = 0
DO_MAX_DAYS = 31


# =============================================================================
# Duty Days (DD) Validation
# =============================================================================

# Warn if DD exceeds this threshold (unusually high)
DD_WARNING_THRESHOLD_DAYS = 20

# Valid range for DD values in data editor
DD_MIN_DAYS = 0
DD_MAX_DAYS = 31


# =============================================================================
# Combined Validation Rules
# =============================================================================

# Days Off + Duty Days should not exceed month length
DO_PLUS_DD_MAX_DAYS = 31


# =============================================================================
# Data Editor Configuration
# =============================================================================

# Columns that can be edited in the data editor
EDITABLE_COLUMNS: List[str] = ["CT", "BT", "DO", "DD"]

# Columns that are read-only (display only)
READONLY_COLUMNS: List[str] = ["Line"]


# =============================================================================
# Validation Functions
# =============================================================================

def is_valid_ct_bt_relationship(ct: float, bt: float) -> bool:
    """
    Check if CT/BT relationship is valid.

    Block time should not exceed credit time.

    Args:
        ct: Credit time in hours
        bt: Block time in hours

    Returns:
        True if valid, False if BT > CT
    """
    return bt <= ct


def is_valid_do_dd_total(do: int, dd: int) -> bool:
    """
    Check if DO + DD total is valid.

    Days off plus duty days should not exceed a month.

    Args:
        do: Days off
        dd: Duty days

    Returns:
        True if valid, False if total exceeds 31
    """
    return (do + dd) <= DO_PLUS_DD_MAX_DAYS


def get_ct_warnings(ct: float) -> List[str]:
    """
    Get validation warnings for credit time value.

    Args:
        ct: Credit time in hours

    Returns:
        List of warning messages (empty if no warnings)
    """
    warnings = []
    if ct > CT_WARNING_THRESHOLD_HOURS:
        warnings.append(f"CT exceeds {CT_WARNING_THRESHOLD_HOURS} hours")
    return warnings


def get_bt_warnings(bt: float) -> List[str]:
    """
    Get validation warnings for block time value.

    Args:
        bt: Block time in hours

    Returns:
        List of warning messages (empty if no warnings)
    """
    warnings = []
    if bt > BT_WARNING_THRESHOLD_HOURS:
        warnings.append(f"BT exceeds {BT_WARNING_THRESHOLD_HOURS} hours")
    return warnings


def get_do_warnings(do: int) -> List[str]:
    """
    Get validation warnings for days off value.

    Args:
        do: Days off

    Returns:
        List of warning messages (empty if no warnings)
    """
    warnings = []
    if do > DO_WARNING_THRESHOLD_DAYS:
        warnings.append(f"DO exceeds {DO_WARNING_THRESHOLD_DAYS} days")
    return warnings


def get_dd_warnings(dd: int) -> List[str]:
    """
    Get validation warnings for duty days value.

    Args:
        dd: Duty days

    Returns:
        List of warning messages (empty if no warnings)
    """
    warnings = []
    if dd > DD_WARNING_THRESHOLD_DAYS:
        warnings.append(f"DD exceeds {DD_WARNING_THRESHOLD_DAYS} days")
    return warnings
