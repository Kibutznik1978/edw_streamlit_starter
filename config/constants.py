"""
Core business logic constants for EDW and bid line analysis.

This module contains all hard-coded constants used throughout the application
for trip analysis, reserve line detection, and chart configuration.
"""

# =============================================================================
# EDW (Early/Day/Window) Time Detection
# =============================================================================

# EDW time range: 02:30 to 05:00 local time (inclusive)
EDW_START_HOUR = 2
EDW_START_MINUTE = 30
EDW_END_HOUR = 5
EDW_END_MINUTE = 0

# Human-readable description for documentation/UI
EDW_TIME_RANGE_DESCRIPTION = "02:30-05:00 local time (inclusive)"

# EDW Detection Logic:
# A trip is EDW if any duty day touches 02:30-05:00 local time.
# Includes: 02:30, 03:00, 04:00, 05:00
# Excludes: 02:29, 05:01
#
# Implementation: (hh == 2 and mm >= 30) or (hh in [3, 4]) or (hh == 5 and mm == 0)


# =============================================================================
# Buy-Up Analysis
# =============================================================================

# Credit time threshold for buy-up classification
# Lines with CT < 75 hours are considered "buy-up" lines
BUYUP_THRESHOLD_HOURS = 75.0


# =============================================================================
# Chart Configuration
# =============================================================================

# Bucket size for Credit Time (CT) and Block Time (BT) distribution histograms
# Creates bins: 70-75, 75-80, 80-85, etc.
CT_BT_BUCKET_SIZE_HOURS = 5.0

# Default chart height in pixels
CHART_HEIGHT_PX = 400

# X-axis label rotation angle (negative = counterclockwise)
CHART_LABEL_ANGLE = -45  # degrees


# =============================================================================
# Reserve Line Detection Keywords
# =============================================================================

# Reserve day codes found in bid line PDFs
# RA = Reserve AM, SA = Standby AM, RB = Reserve split, etc.
RESERVE_DAY_KEYWORDS = ["RA", "SA", "RB", "SB", "RC", "SC", "RD", "SD"]

# Keyword for shiftable reserve lines (found in comments section)
SHIFTABLE_RESERVE_KEYWORD = "SHIFTABLE RESERVE"

# VTO (Voluntary Time Off) line type keywords
# VTO = Voluntary Time Off
# VTOR = VTO with Reserve option
# VOR = Vacation on Reserve
VTO_KEYWORDS = ["VTO", "VTOR", "VOR"]


# =============================================================================
# Hot Standby Detection
# =============================================================================

# Maximum number of flight segments for hot standby classification
# Hot standby = single segment pairing where departure == arrival (e.g., ONT-ONT)
# Pairings with positioning legs are NOT hot standby (e.g., ONT-DFW, DFW-DFW, DFW-ONT = 3 segments)
HOT_STANDBY_MAX_SEGMENTS = 1
