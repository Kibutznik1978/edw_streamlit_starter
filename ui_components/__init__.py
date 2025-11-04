"""Reusable UI components for Streamlit pages.

This package provides modular, reusable UI components for building consistent
Streamlit interfaces across different analyzer pages.

Modules:
    branding: Branded headers and styling components
    empty_states: Branded empty state messages
    filters: Range sliders and filter logic
    data_editor: Data editor with validation and change tracking
    exports: Download buttons and file generation
    statistics: Metrics display and pay period analysis
    trip_viewer: Trip details viewer for EDW analysis
"""

# Import from branding module
from .branding import (
    apply_brand_styling,
    render_app_header,
    render_section_header,
)

# Import from empty_states module
from .empty_states import (
    render_empty_state,
    render_no_upload_state,
    render_no_results_state,
    render_no_data_state,
    render_error_state,
    render_loading_state,
)

# Import from data_editor module
from .data_editor import (
    create_bid_line_editor,
    detect_changes,
    render_change_summary,
    render_editor_header,
    render_filter_status_message,
    render_reset_button,
    validate_bid_line_edits,
)

# Import from exports module
from .exports import (
    generate_bid_line_filename,
    generate_edw_filename,
    handle_pdf_generation_error,
    render_csv_download,
    render_download_section,
    render_excel_download,
    render_pdf_download,
    render_two_column_downloads,
)

# Import from filters module
from .filters import (
    apply_dataframe_filters,
    create_bid_line_filters,
    create_metric_range_filter,
    is_filter_active,
    render_filter_reset_button,
    render_filter_summary,
)

# Import from statistics module
from .statistics import (
    calculate_metric_stats,
    extract_reserve_line_numbers,
    filter_by_reserve_lines,
    render_basic_statistics,
    render_pay_period_analysis,
    render_reserve_summary,
)

# Import from trip_viewer module
from .trip_viewer import (
    render_trip_details_viewer,
)

__all__ = [
    # Branding
    "render_app_header",
    "render_section_header",
    "apply_brand_styling",
    # Empty States
    "render_empty_state",
    "render_no_upload_state",
    "render_no_results_state",
    "render_no_data_state",
    "render_error_state",
    "render_loading_state",
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
