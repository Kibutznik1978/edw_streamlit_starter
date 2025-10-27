"""
EDW Analysis Module

This module provides comprehensive pairing analysis functionality including:
- PDF parsing and text extraction
- EDW (Early/Day/Window) detection
- Statistical analysis and reporting
- Excel and PDF export

Main entry point: run_edw_report()
"""

# Main orchestration function
from .reporter import run_edw_report

# Parser functions (for UI use)
from .parser import (
    extract_pdf_header_info,
    parse_trip_for_table,
    format_trip_details,
    clean_text,
)

# Analyzer functions (for UI use)
from .analyzer import is_edw_trip, is_hot_standby

# Excel export (if needed separately)
from .excel_export import save_edw_excel, build_edw_dataframes

__all__ = [
    # Main function
    'run_edw_report',

    # Parser utilities
    'extract_pdf_header_info',
    'parse_trip_for_table',
    'format_trip_details',
    'clean_text',

    # Analysis functions
    'is_edw_trip',
    'is_hot_standby',

    # Excel utilities
    'save_edw_excel',
    'build_edw_dataframes',
]
