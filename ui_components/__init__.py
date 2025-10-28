"""Reusable UI components for Streamlit pages.

This package provides modular, reusable UI components for building consistent
Streamlit interfaces across different analyzer pages.

Modules:
    filters: Range sliders and filter logic
    data_editor: Data editor with validation and change tracking
    exports: Download buttons and file generation
    statistics: Metrics display and pay period analysis
    trip_viewer: Trip details viewer for EDW analysis
"""

# Import from filters module
from .filters import (
    create_metric_range_filter,
    create_bid_line_filters,
    apply_dataframe_filters,
    is_filter_active,
    render_filter_summary,
    render_filter_reset_button,
)

# Import from data_editor module
from .data_editor import (
    create_bid_line_editor,
    detect_changes,
    validate_bid_line_edits,
    render_change_summary,
    render_reset_button,
    render_editor_header,
    render_filter_status_message,
)

# Import from exports module
from .exports import (
    render_csv_download,
    render_pdf_download,
    render_excel_download,
    generate_edw_filename,
    generate_bid_line_filename,
    render_download_section,
    render_two_column_downloads,
    handle_pdf_generation_error,
)

# Import from statistics module
from .statistics import (
    extract_reserve_line_numbers,
    filter_by_reserve_lines,
    calculate_metric_stats,
    render_basic_statistics,
    render_pay_period_analysis,
    render_reserve_summary,
)

# Import from trip_viewer module
from .trip_viewer import (
    render_trip_details_viewer,
)

__all__ = [
    # Filters
    "create_metric_range_filter",
    "create_bid_line_filters",
    "apply_dataframe_filters",
    "is_filter_active",
    "render_filter_summary",
    "render_filter_reset_button",
    # Data Editor
    "create_bid_line_editor",
    "detect_changes",
    "validate_bid_line_edits",
    "render_change_summary",
    "render_reset_button",
    "render_editor_header",
    "render_filter_status_message",
    # Exports
    "render_csv_download",
    "render_pdf_download",
    "render_excel_download",
    "generate_edw_filename",
    "generate_bid_line_filename",
    "render_download_section",
    "render_two_column_downloads",
    "handle_pdf_generation_error",
    # Statistics
    "extract_reserve_line_numbers",
    "filter_by_reserve_lines",
    "calculate_metric_stats",
    "render_basic_statistics",
    "render_pay_period_analysis",
    "render_reserve_summary",
    # Trip Viewer
    "render_trip_details_viewer",
]

__version__ = "1.0.0"
__author__ = "Claude Code"
__description__ = "Reusable UI components for Streamlit analyzer pages"
