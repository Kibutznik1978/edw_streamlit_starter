"""Trip Details Viewer Component.

This module provides detailed trip information display for the EDW Pairing Analyzer,
including trip selection, formatted trip text, duty day breakdown, and trip summary.
"""

import reflex as rx
from typing import Dict, Any

from ..edw_state import EDWState


def details_component() -> rx.Component:
    """Trip details viewer component.

    Displays trip selector dropdown and detailed trip information including
    duty days, flights, and trip summary.

    Only shown when results are available.

    Returns:
        Reflex component
    """
    return rx.cond(
        EDWState.has_results,
        rx.vstack(
            # Header
            rx.heading("Trip Details Viewer", size="6", weight="bold"),

            # Trip selector
            rx.cond(
                EDWState.available_trip_ids.length() > 0,
                rx.vstack(
                    rx.text(
                        "Select a trip ID to view full pairing details:",
                        size="2",
                        weight="medium",
                    ),
                    rx.select.root(
                        rx.select.trigger(
                            placeholder="Choose a trip...",
                        ),
                        rx.select.content(
                            rx.foreach(
                                EDWState.available_trip_ids,
                                lambda trip_id: rx.select.item(
                                    f"Trip {trip_id}",
                                    value=trip_id,
                                ),
                            )
                        ),
                        value=EDWState.selected_trip_id,
                        on_change=EDWState.set_selected_trip_id,
                        size="3",
                    ),
                    spacing="2",
                    width="100%",
                ),
                rx.text(
                    "No trips available to display.",
                    color="gray",
                    size="2",
                ),
            ),

            # Trip details display
            rx.cond(
                EDWState.selected_trip_id != "",
                rx.box(
                    _render_trip_details(),
                    padding="1rem",
                    border_radius="0.5rem",
                    border=f"1px solid {rx.color('gray', 4)}",
                    background_color=rx.color("gray", 1),
                    margin_top="1rem",
                ),
                rx.fragment(),
            ),

            spacing="4",
            width="100%",
            padding="1rem",
        ),
        rx.fragment(),
    )


def _render_trip_details() -> rx.Component:
    """Render trip details when a trip is selected.

    Uses EDWState.selected_trip_data computed var for reactive parsing.

    Returns:
        Component displaying selected trip details
    """
    return rx.cond(
        # Check if trip data is available
        EDWState.selected_trip_data.length() > 0,
        rx.cond(
            # Check if there was a parsing error
            EDWState.selected_trip_data.contains("error"),
            # Show error message
            rx.callout.root(
                rx.vstack(
                    rx.text("Error parsing trip data: "),
                    rx.text(EDWState.selected_trip_data["error"]),
                    spacing="1",
                ),
                icon="triangle-alert",
                color="red",
            ),
            # Show trip details
            rx.vstack(
                # Date/frequency line
                rx.cond(
                    EDWState.selected_trip_data.contains("date_freq"),
                    rx.text(
                        EDWState.selected_trip_data["date_freq"],
                        size="2",
                        color="gray",
                    ),
                    rx.fragment(),
                ),

                # Duty day table (using flattened rows - no nested foreach)
                # Styled to match Streamlit version with monospace font and borders
                rx.box(
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell(
                                    "Day",
                                    padding="6px 4px",
                                    background_color="#e0e0e0",
                                    border="1px solid #999",
                                    font_weight="bold",
                                    font_size="10px",
                                    white_space="nowrap",
                                ),
                                rx.table.column_header_cell(
                                    "Flight",
                                    padding="6px 4px",
                                    background_color="#e0e0e0",
                                    border="1px solid #999",
                                    font_weight="bold",
                                    font_size="10px",
                                    white_space="nowrap",
                                ),
                                rx.table.column_header_cell(
                                    "Dep-Arr",
                                    padding="6px 4px",
                                    background_color="#e0e0e0",
                                    border="1px solid #999",
                                    font_weight="bold",
                                    font_size="10px",
                                    white_space="nowrap",
                                ),
                                rx.table.column_header_cell(
                                    "Depart (L) Z",
                                    padding="6px 4px",
                                    background_color="#e0e0e0",
                                    border="1px solid #999",
                                    font_weight="bold",
                                    font_size="10px",
                                    white_space="nowrap",
                                ),
                                rx.table.column_header_cell(
                                    "Arrive (L) Z",
                                    padding="6px 4px",
                                    background_color="#e0e0e0",
                                    border="1px solid #999",
                                    font_weight="bold",
                                    font_size="10px",
                                    white_space="nowrap",
                                ),
                                rx.table.column_header_cell(
                                    "Blk",
                                    padding="6px 4px",
                                    background_color="#e0e0e0",
                                    border="1px solid #999",
                                    font_weight="bold",
                                    font_size="10px",
                                    white_space="nowrap",
                                ),
                                rx.table.column_header_cell(
                                    "Cxn",
                                    padding="6px 4px",
                                    background_color="#e0e0e0",
                                    border="1px solid #999",
                                    font_weight="bold",
                                    font_size="10px",
                                    white_space="nowrap",
                                ),
                                rx.table.column_header_cell(
                                    "Duty",
                                    padding="6px 4px",
                                    background_color="#e0e0e0",
                                    border="1px solid #999",
                                    font_weight="bold",
                                    font_size="10px",
                                    white_space="nowrap",
                                ),
                                rx.table.column_header_cell(
                                    "Cr",
                                    padding="6px 4px",
                                    background_color="#e0e0e0",
                                    border="1px solid #999",
                                    font_weight="bold",
                                    font_size="10px",
                                    white_space="nowrap",
                                ),
                                rx.table.column_header_cell(
                                    "L/O",
                                    padding="6px 4px",
                                    background_color="#e0e0e0",
                                    border="1px solid #999",
                                    font_weight="bold",
                                    font_size="10px",
                                    white_space="nowrap",
                                ),
                            )
                        ),
                        rx.table.body(
                            # Single foreach over flattened table rows
                            rx.foreach(
                                EDWState.selected_trip_table_rows,
                                lambda row: _render_table_row(row),
                            )
                        ),
                        variant="surface",
                        size="1",
                        width="100%",
                        min_width="650px",
                        border_collapse="collapse",
                        font_family="'Courier New', monospace",
                        font_size="11px",
                    ),
                    overflow_x="auto",
                    width="100%",
                    max_width="60%",
                    margin="0 auto",
                    # Responsive: 100% on mobile, 60% on desktop
                    css={
                        "@media (max-width: 768px)": {
                            "max-width": "100%",
                        }
                    },
                ),

                # Trip summary
                rx.cond(
                    EDWState.selected_trip_summary.length() > 0,
                    _render_trip_summary(EDWState.selected_trip_summary),
                    rx.fragment(),
                ),

                spacing="3",
                width="100%",
            ),
        ),
        # No trip data - show placeholder
        rx.box(
            rx.text(
                "Select a trip from the dropdown above to view details.",
                color="gray",
                size="2",
            ),
            padding="2rem",
            text_align="center",
        ),
    )


def _render_table_row(row: Dict[str, Any]) -> rx.Component:
    """Render a single table row based on its type.

    Uses rx.match to switch between different row types (briefing, flight, debriefing, subtotal).
    This avoids nested foreach issues in Reflex 0.8.18.

    Styled to match Streamlit version with borders and proper backgrounds.

    Args:
        row: Flattened row data dict with 'row_type' field

    Returns:
        Table row component
    """
    return rx.match(
        row["row_type"],
        # Briefing row
        ("briefing", rx.table.row(
            rx.table.cell(
                rx.text("Briefing", font_style="italic"),
                colspan=3,
                padding="4px",
                background_color="#f9f9f9",
                border="1px solid #ccc",
                font_size="11px",
            ),
            rx.table.cell(
                row["duty_start"],
                padding="4px",
                background_color="#f9f9f9",
                border="1px solid #ccc",
                font_size="11px",
            ),
            rx.table.cell(
                "",
                padding="4px",
                background_color="#f9f9f9",
                border="1px solid #ccc",
                font_size="11px",
            ),
            rx.table.cell(
                "",
                colspan=5,
                padding="4px",
                background_color="#f9f9f9",
                border="1px solid #ccc",
                font_size="11px",
            ),
        )),
        # Flight row
        ("flight", rx.table.row(
            rx.table.cell(row.get("day", ""), padding="4px", border="1px solid #ccc", font_size="11px"),
            rx.table.cell(row.get("flight", ""), padding="4px", border="1px solid #ccc", font_size="11px"),
            rx.table.cell(row.get("route", ""), padding="4px", border="1px solid #ccc", font_size="11px"),
            rx.table.cell(row.get("depart", ""), padding="4px", border="1px solid #ccc", font_size="11px"),
            rx.table.cell(row.get("arrive", ""), padding="4px", border="1px solid #ccc", font_size="11px"),
            rx.table.cell(row.get("block", ""), padding="4px", border="1px solid #ccc", font_size="11px"),
            rx.table.cell(row.get("connection", ""), padding="4px", border="1px solid #ccc", font_size="11px"),
            # Duty, Cr, L/O columns left empty (rowspan not well-supported)
            rx.table.cell("", padding="4px", border="1px solid #ccc", font_size="11px"),
            rx.table.cell("", padding="4px", border="1px solid #ccc", font_size="11px"),
            rx.table.cell("", padding="4px", border="1px solid #ccc", font_size="11px"),
        )),
        # Debriefing row
        ("debriefing", rx.table.row(
            rx.table.cell(
                rx.text("Debriefing", font_style="italic"),
                colspan=3,
                padding="4px",
                background_color="#f9f9f9",
                border="1px solid #ccc",
                font_size="11px",
            ),
            rx.table.cell(
                "",
                padding="4px",
                background_color="#f9f9f9",
                border="1px solid #ccc",
                font_size="11px",
            ),
            rx.table.cell(
                row["duty_end"],
                padding="4px",
                background_color="#f9f9f9",
                border="1px solid #ccc",
                font_size="11px",
            ),
            rx.table.cell(
                "",
                colspan=5,
                padding="4px",
                background_color="#f9f9f9",
                border="1px solid #ccc",
                font_size="11px",
            ),
        )),
        # Subtotal row
        ("subtotal", rx.table.row(
            rx.table.cell(
                "Duty Day Subtotal:",
                colspan=5,
                text_align="right",
                padding="4px",
                font_weight="bold",
                background_color="#f5f5f5",
                border="2px solid #666",
                border_top="2px solid #666",
                font_size="11px",
            ),
            rx.table.cell(
                row.get("block_total", ""),
                padding="4px",
                font_weight="bold",
                background_color="#f5f5f5",
                border="1px solid #ccc",
                border_top="2px solid #666",
                font_size="11px",
            ),
            rx.table.cell(
                "",
                padding="4px",
                background_color="#f5f5f5",
                border="1px solid #ccc",
                border_top="2px solid #666",
                font_size="11px",
            ),
            rx.table.cell(
                row.get("duty_time", ""),
                padding="4px",
                font_weight="bold",
                background_color="#f5f5f5",
                border="1px solid #ccc",
                border_top="2px solid #666",
                font_size="11px",
            ),
            rx.table.cell(
                row.get("credit", ""),
                padding="4px",
                font_weight="bold",
                background_color="#f5f5f5",
                border="1px solid #ccc",
                border_top="2px solid #666",
                font_size="11px",
            ),
            rx.table.cell(
                row.get("rest", ""),
                padding="4px",
                font_weight="bold",
                background_color="#f5f5f5",
                border="1px solid #ccc",
                border_top="2px solid #666",
                font_size="11px",
            ),
        )),
        # Default/fallback
        rx.fragment(),
    )


def _render_trip_summary(summary: Dict[str, Any]) -> rx.Component:
    """Render trip summary section.

    Styled to match Streamlit version with monospace font and blue background.

    Args:
        summary: Trip summary data dict (Var)

    Returns:
        Component displaying trip summary
    """
    # Render as a table-like layout matching Streamlit styling
    return rx.box(
        rx.vstack(
            # Header row
            rx.box(
                rx.text(
                    "TRIP SUMMARY",
                    weight="bold",
                    size="3",
                    text_align="center",
                ),
                padding="6px",
                background_color="#d6eaf8",
                border="3px solid #333",
                border_bottom="none",
                width="100%",
            ),
            # Content box
            rx.box(
                rx.vstack(
                    # Row 1 - hardcoded fields (using get with defaults to avoid missing key errors)
                    rx.hstack(
                        rx.text("Credit: ", weight="bold", font_family="'Courier New', monospace", font_size="11px", white_space="nowrap"),
                        rx.text(summary.get("Credit", ""), font_family="'Courier New', monospace", font_size="11px"),
                        rx.text("Blk: ", weight="bold", font_family="'Courier New', monospace", font_size="11px", white_space="nowrap", margin_left="1rem"),
                        rx.text(summary.get("Blk", ""), font_family="'Courier New', monospace", font_size="11px"),
                        rx.text("Duty Time: ", weight="bold", font_family="'Courier New', monospace", font_size="11px", white_space="nowrap", margin_left="1rem"),
                        rx.text(summary.get("Duty Time", ""), font_family="'Courier New', monospace", font_size="11px"),
                        rx.text("TAFB: ", weight="bold", font_family="'Courier New', monospace", font_size="11px", white_space="nowrap", margin_left="1rem"),
                        rx.text(summary.get("TAFB", ""), font_family="'Courier New', monospace", font_size="11px"),
                        rx.text("Duty Days: ", weight="bold", font_family="'Courier New', monospace", font_size="11px", white_space="nowrap", margin_left="1rem"),
                        rx.text(summary.get("Duty Days", ""), font_family="'Courier New', monospace", font_size="11px"),
                        spacing="1",
                        wrap="wrap",
                    ),
                    # Row 2 - hardcoded fields
                    rx.hstack(
                        rx.text("Prem: ", weight="bold", font_family="'Courier New', monospace", font_size="11px", white_space="nowrap"),
                        rx.text(summary.get("Prem", ""), font_family="'Courier New', monospace", font_size="11px"),
                        rx.text("PDiem: ", weight="bold", font_family="'Courier New', monospace", font_size="11px", white_space="nowrap", margin_left="1rem"),
                        rx.text(summary.get("PDiem", ""), font_family="'Courier New', monospace", font_size="11px"),
                        rx.text("LDGS: ", weight="bold", font_family="'Courier New', monospace", font_size="11px", white_space="nowrap", margin_left="1rem"),
                        rx.text(summary.get("LDGS", ""), font_family="'Courier New', monospace", font_size="11px"),
                        rx.text("Crew: ", weight="bold", font_family="'Courier New', monospace", font_size="11px", white_space="nowrap", margin_left="1rem"),
                        rx.text(summary.get("Crew", ""), font_family="'Courier New', monospace", font_size="11px"),
                        rx.text("Domicile: ", weight="bold", font_family="'Courier New', monospace", font_size="11px", white_space="nowrap", margin_left="1rem"),
                        rx.text(summary.get("Domicile", ""), font_family="'Courier New', monospace", font_size="11px"),
                        spacing="1",
                        wrap="wrap",
                    ),
                    spacing="3",
                ),
                padding="10px",
                background_color="#f0f8ff",
                border="1px solid #ccc",
                border_top="none",
                width="100%",
            ),
            spacing="0",
            width="100%",
        ),
        margin_top="0",
        width="100%",
    )
