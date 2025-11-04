"""Shared UI components used across multiple pages."""

from typing import Any, Dict

import streamlit as st


def display_header_info(header_info: Dict[str, Any]) -> None:
    """Display extracted PDF header information in an info box.

    Args:
        header_info: Dictionary with keys: bid_period, domicile, fleet_type, etc.
    """
    if not header_info:
        return

    st.info(
        f"**Extracted from PDF:**\n\n"
        f"📅 Bid Period: **{header_info.get('bid_period', 'N/A')}**\n\n"
        f"🏠 Domicile: **{header_info.get('domicile', 'N/A')}**\n\n"
        f"✈️ Fleet Type: **{header_info.get('fleet_type', 'N/A')}**\n\n"
        f"📆 Date Range: **{header_info.get('date_range') or header_info.get('bid_period_date_range', 'N/A')}**"
    )


def show_parsing_warnings(warnings: list, max_display: int = 20) -> None:
    """Display parsing warnings in an expander.

    Args:
        warnings: List of warning messages
        max_display: Maximum number of warnings to display
    """
    if not warnings:
        return

    with st.expander("⚠️ Parsing Warnings", expanded=False):
        for warning in warnings[:max_display]:
            st.warning(warning)
        if len(warnings) > max_display:
            st.caption(f"...and {len(warnings) - max_display} more warnings")


def show_error_details(error: Exception) -> None:
    """Display error details in an expander.

    Args:
        error: Exception that was raised
    """
    import traceback

    st.error(f"Error: {str(error)}")
    with st.expander("📋 Error Details"):
        st.code(traceback.format_exc())


def progress_bar_callback(
    current: int, total: int, progress_bar, status_text, message_prefix: str = "Processing"
) -> None:
    """Standard progress bar update callback.

    Args:
        current: Current progress value
        total: Total progress value
        progress_bar: Streamlit progress bar object
        status_text: Streamlit text element for status updates
        message_prefix: Prefix for status message
    """
    progress_bar.progress(current / total)
    status_text.text(f"{message_prefix} {current} of {total}...")
