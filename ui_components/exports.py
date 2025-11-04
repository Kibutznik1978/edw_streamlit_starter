"""Reusable export and download components."""

from pathlib import Path
from typing import Optional

import pandas as pd
import streamlit as st


def render_csv_download(
    df: pd.DataFrame,
    filename: str,
    button_label: str = "📊 Download CSV",
    key: str = "download_csv",
    help_text: Optional[str] = None,
) -> None:
    """Render a CSV download button.

    Args:
        df: DataFrame to export
        filename: Name for the downloaded file
        button_label: Label for the download button
        key: Unique key for the button widget
        help_text: Optional help text for the button
    """
    csv = df.to_csv(index=False)
    st.download_button(
        button_label, data=csv, file_name=filename, mime="text/csv", key=key, help=help_text
    )


def render_pdf_download(
    pdf_bytes: bytes,
    filename: str,
    button_label: str = "📄 Download PDF Report",
    key: str = "download_pdf",
    help_text: Optional[str] = None,
) -> None:
    """Render a PDF download button.

    Args:
        pdf_bytes: PDF file content as bytes
        filename: Name for the downloaded file
        button_label: Label for the download button
        key: Unique key for the button widget
        help_text: Optional help text for the button
    """
    st.download_button(
        button_label,
        data=pdf_bytes,
        file_name=filename,
        mime="application/pdf",
        key=key,
        help=help_text,
    )


def render_excel_download(
    file_path: Path,
    button_label: str = "📊 Download Excel Workbook",
    key: str = "download_excel",
    help_text: Optional[str] = None,
) -> None:
    """Render an Excel file download button.

    Args:
        file_path: Path to the Excel file
        button_label: Label for the download button
        key: Unique key for the button widget
        help_text: Optional help text for the button
    """
    st.download_button(
        button_label,
        data=file_path.read_bytes(),
        file_name=file_path.name,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key=key,
        help=help_text,
    )


def generate_edw_filename(
    domicile: str, aircraft: str, bid_period: str, file_type: str = "xlsx"
) -> str:
    """Generate consistent filename for EDW reports.

    Args:
        domicile: Domicile code (e.g., "ONT")
        aircraft: Aircraft type (e.g., "757")
        bid_period: Bid period (e.g., "2507")
        file_type: File extension without dot (e.g., "xlsx", "pdf")

    Returns:
        Formatted filename
    """
    if file_type == "xlsx":
        return f"{domicile}_{aircraft}_Bid{bid_period}_EDW_Report_Data.xlsx"
    elif file_type == "pdf":
        return f"{domicile}_{aircraft}_Bid{bid_period}_EDW_Report.pdf"
    else:
        return f"{domicile}_{aircraft}_Bid{bid_period}_EDW_Report.{file_type}"


def generate_bid_line_filename(file_type: str = "csv") -> str:
    """Generate consistent filename for bid line reports.

    Args:
        file_type: File extension without dot (e.g., "csv", "pdf")

    Returns:
        Formatted filename
    """
    if file_type == "csv":
        return "bid_lines_filtered.csv"
    elif file_type == "pdf":
        return "Bid_Lines_Analysis_Report.pdf"
    else:
        return f"bid_lines_report.{file_type}"


def render_download_section(title: str = "⬇️ Downloads") -> None:
    """Render a divider and header for the download section.

    Args:
        title: Section title
    """
    st.divider()
    st.header(title)


def render_two_column_downloads(left_widget_fn, right_widget_fn) -> None:
    """Render two download buttons side by side.

    Args:
        left_widget_fn: Callable that renders the left column widget
        right_widget_fn: Callable that renders the right column widget
    """
    col1, col2 = st.columns(2)

    with col1:
        left_widget_fn()

    with col2:
        right_widget_fn()


def handle_pdf_generation_error(error: Exception, show_traceback: bool = True) -> None:
    """Display error message for PDF generation failures.

    Args:
        error: The exception that was raised
        show_traceback: Whether to show full traceback in expander
    """
    st.error(f"Error generating PDF: {error}")

    if show_traceback:
        import traceback

        with st.expander("📋 Error Details"):
            st.code(traceback.format_exc())
