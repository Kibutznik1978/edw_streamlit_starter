"""
pdf_generation package

Professional PDF report generation for airline bid packet analysis.

Modules:
    base: Shared base components (branding, colors, headers, footers, KPI badges)
    charts: Chart generation functions (generic, EDW, bid line)
    edw_pdf: EDW pairing analysis PDF reports
    bid_line_pdf: Bid line analysis PDF reports

Main Functions:
    - create_edw_pdf_report(): Generate EDW pairing analysis PDF
    - create_bid_line_pdf_report(): Generate bid line analysis PDF

Usage:
    from pdf_generation import create_edw_pdf_report, create_bid_line_pdf_report

    # EDW report
    create_edw_pdf_report(data, output_path, branding)

    # Bid line report
    pdf_bytes = create_bid_line_pdf_report(df, metadata, pay_periods, reserve_lines, branding)
"""

# Import base components for advanced usage
from .base import (
    DEFAULT_BRANDING,
    KPIBadge,
    draw_footer,
    draw_header,
    hex_to_reportlab_color,
    make_kpi_row,
    make_styled_table,
)
from .bid_line_pdf import ReportMetadata, create_bid_line_pdf_report

# Import chart functions for custom reports
from .charts import (  # Generic charts; EDW-specific charts
    save_bar_chart,
    save_duty_day_grouped_bar_chart,
    save_duty_day_radar_chart,
    save_edw_percentages_comparison_chart,
    save_edw_pie_chart,
    save_percentage_bar_chart,
    save_pie_chart,
    save_trip_length_bar_chart,
    save_trip_length_percentage_bar_chart,
    save_weighted_method_pie_chart,
)

# Import main report generation functions
from .edw_pdf import create_edw_pdf_report

# Define public API
__all__ = [
    # Main report functions
    "create_edw_pdf_report",
    "create_bid_line_pdf_report",
    "ReportMetadata",
    # Base components
    "DEFAULT_BRANDING",
    "hex_to_reportlab_color",
    "draw_header",
    "draw_footer",
    "KPIBadge",
    "make_kpi_row",
    "make_styled_table",
    # Chart functions
    "save_bar_chart",
    "save_percentage_bar_chart",
    "save_pie_chart",
    "save_edw_pie_chart",
    "save_trip_length_bar_chart",
    "save_trip_length_percentage_bar_chart",
    "save_edw_percentages_comparison_chart",
    "save_weighted_method_pie_chart",
    "save_duty_day_grouped_bar_chart",
    "save_duty_day_radar_chart",
]


# Package metadata
__version__ = "1.0.0"
__author__ = "Aero Crew Data"
__description__ = "Professional PDF report generation for airline bid packet analysis"
