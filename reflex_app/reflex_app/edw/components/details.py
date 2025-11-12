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

                # Duty day table and trip summary (single integrated container)
                # Styled to match Streamlit version with monospace font and borders
                rx.box(
                    rx.vstack(
                        # Main table
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
                            border_collapse="collapse",
                            font_family="'Courier New', monospace",
                            font_size="11px",
                        ),

                        # Trip summary (attached directly below table with no gap)
                        rx.cond(
                            EDWState.selected_trip_summary.length() > 0,
                            _render_trip_summary(EDWState.selected_trip_summary),
                            rx.fragment(),
                        ),

                        spacing="0",  # No gap between table and summary
                        width="100%",
                    ),
                    overflow_x="auto",
                    width="100%",
                    max_width="100%",  # Full width to prevent text wrapping
                    margin="0 auto",
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
        # Briefing row - 10 individual cells to match headers
        ("briefing", rx.table.row(
            # Column 1: Day - "Briefing" text
            rx.table.cell(
                rx.text("Briefing", font_style="italic"),
                padding="4px",
                background_color="#f9f9f9",
                border="1px solid #ccc",
                font_size="11px",
                white_space="nowrap",
            ),
            # Column 2: Flight - empty
            rx.table.cell(
                "",
                padding="4px",
                background_color="#f9f9f9",
                border="1px solid #ccc",
                font_size="11px",
                white_space="nowrap",
            ),
            # Column 3: Dep-Arr - empty
            rx.table.cell(
                "",
                padding="4px",
                background_color="#f9f9f9",
                border="1px solid #ccc",
                font_size="11px",
                white_space="nowrap",
            ),
            # Column 4: Depart (L) Z - briefing time
            rx.table.cell(
                row["duty_start"],
                padding="4px",
                background_color="#f9f9f9",
                border="1px solid #ccc",
                font_size="11px",
                white_space="nowrap",
            ),
            # Columns 5-10: Rest - empty
            rx.table.cell("", padding="4px", background_color="#f9f9f9", border="1px solid #ccc", font_size="11px", white_space="nowrap"),
            rx.table.cell("", padding="4px", background_color="#f9f9f9", border="1px solid #ccc", font_size="11px", white_space="nowrap"),
            rx.table.cell("", padding="4px", background_color="#f9f9f9", border="1px solid #ccc", font_size="11px", white_space="nowrap"),
            rx.table.cell("", padding="4px", background_color="#f9f9f9", border="1px solid #ccc", font_size="11px", white_space="nowrap"),
            rx.table.cell("", padding="4px", background_color="#f9f9f9", border="1px solid #ccc", font_size="11px", white_space="nowrap"),
            rx.table.cell("", padding="4px", background_color="#f9f9f9", border="1px solid #ccc", font_size="11px", white_space="nowrap"),
        )),
        # Flight row
        ("flight", rx.table.row(
            rx.table.cell(row.get("day", ""), padding="4px", border="1px solid #ccc", font_size="11px", white_space="nowrap"),
            rx.table.cell(row.get("flight", ""), padding="4px", border="1px solid #ccc", font_size="11px", white_space="nowrap"),
            rx.table.cell(row.get("route", ""), padding="4px", border="1px solid #ccc", font_size="11px", white_space="nowrap"),
            rx.table.cell(row.get("depart", ""), padding="4px", border="1px solid #ccc", font_size="11px", white_space="nowrap"),
            rx.table.cell(row.get("arrive", ""), padding="4px", border="1px solid #ccc", font_size="11px", white_space="nowrap"),
            rx.table.cell(row.get("block", ""), padding="4px", border="1px solid #ccc", font_size="11px", white_space="nowrap"),
            rx.table.cell(row.get("connection", ""), padding="4px", border="1px solid #ccc", font_size="11px", white_space="nowrap"),
            # Duty, Cr, L/O columns left empty (rowspan not well-supported)
            rx.table.cell("", padding="4px", border="1px solid #ccc", font_size="11px", white_space="nowrap"),
            rx.table.cell("", padding="4px", border="1px solid #ccc", font_size="11px", white_space="nowrap"),
            rx.table.cell("", padding="4px", border="1px solid #ccc", font_size="11px", white_space="nowrap"),
        )),
        # Debriefing row - 10 individual cells to match headers
        ("debriefing", rx.table.row(
            # Column 1: Day - "Debriefing" text
            rx.table.cell(
                rx.text("Debriefing", font_style="italic"),
                padding="4px",
                background_color="#f9f9f9",
                border="1px solid #ccc",
                font_size="11px",
                white_space="nowrap",
            ),
            # Column 2: Flight - empty
            rx.table.cell(
                "",
                padding="4px",
                background_color="#f9f9f9",
                border="1px solid #ccc",
                font_size="11px",
                white_space="nowrap",
            ),
            # Column 3: Dep-Arr - empty
            rx.table.cell(
                "",
                padding="4px",
                background_color="#f9f9f9",
                border="1px solid #ccc",
                font_size="11px",
                white_space="nowrap",
            ),
            # Column 4: Depart (L) Z - empty
            rx.table.cell(
                "",
                padding="4px",
                background_color="#f9f9f9",
                border="1px solid #ccc",
                font_size="11px",
                white_space="nowrap",
            ),
            # Column 5: Arrive (L) Z - debriefing time
            rx.table.cell(
                row["duty_end"],
                padding="4px",
                background_color="#f9f9f9",
                border="1px solid #ccc",
                font_size="11px",
                white_space="nowrap",
            ),
            # Columns 6-10: Rest - empty
            rx.table.cell("", padding="4px", background_color="#f9f9f9", border="1px solid #ccc", font_size="11px", white_space="nowrap"),
            rx.table.cell("", padding="4px", background_color="#f9f9f9", border="1px solid #ccc", font_size="11px", white_space="nowrap"),
            rx.table.cell("", padding="4px", background_color="#f9f9f9", border="1px solid #ccc", font_size="11px", white_space="nowrap"),
            rx.table.cell("", padding="4px", background_color="#f9f9f9", border="1px solid #ccc", font_size="11px", white_space="nowrap"),
            rx.table.cell("", padding="4px", background_color="#f9f9f9", border="1px solid #ccc", font_size="11px", white_space="nowrap"),
        )),
        # Subtotal row - 10 individual cells, label in column 5 (Arrive)
        ("subtotal", rx.table.row(
            # Empty cells for Day, Flight, Dep-Arr, Depart (columns 1-4)
            rx.table.cell(
                "",
                padding="4px",
                background_color="#f5f5f5",
                border="1px solid #ccc",
                border_top="2px solid #666",
                font_size="11px",
                white_space="nowrap",
            ),
            rx.table.cell(
                "",
                padding="4px",
                background_color="#f5f5f5",
                border="1px solid #ccc",
                border_top="2px solid #666",
                font_size="11px",
                white_space="nowrap",
            ),
            rx.table.cell(
                "",
                padding="4px",
                background_color="#f5f5f5",
                border="1px solid #ccc",
                border_top="2px solid #666",
                font_size="11px",
                white_space="nowrap",
            ),
            rx.table.cell(
                "",
                padding="4px",
                background_color="#f5f5f5",
                border="1px solid #ccc",
                border_top="2px solid #666",
                font_size="11px",
                white_space="nowrap",
            ),
            # Label in Arrive column (column 5)
            rx.table.cell(
                "Duty Day Subtotal:",
                text_align="right",
                padding="4px",
                font_weight="bold",
                background_color="#f5f5f5",
                border="1px solid #ccc",
                border_top="2px solid #666",
                font_size="11px",
                white_space="nowrap",
            ),
            # Block total in Blk column (column 6)
            rx.table.cell(
                row.get("block_total", ""),
                padding="4px",
                font_weight="bold",
                background_color="#f5f5f5",
                border="1px solid #ccc",
                border_top="2px solid #666",
                font_size="11px",
                white_space="nowrap",
            ),
            # Empty Cxn column (column 7)
            rx.table.cell(
                "",
                padding="4px",
                background_color="#f5f5f5",
                border="1px solid #ccc",
                border_top="2px solid #666",
                font_size="11px",
                white_space="nowrap",
            ),
            # Duty time in Duty column (column 8)
            rx.table.cell(
                row.get("duty_time", ""),
                padding="4px",
                font_weight="bold",
                background_color="#f5f5f5",
                border="1px solid #ccc",
                border_top="2px solid #666",
                font_size="11px",
                white_space="nowrap",
            ),
            # Credit in Cr column (column 9)
            rx.table.cell(
                row.get("credit", ""),
                padding="4px",
                font_weight="bold",
                background_color="#f5f5f5",
                border="1px solid #ccc",
                border_top="2px solid #666",
                font_size="11px",
                white_space="nowrap",
            ),
            # Rest in L/O column (column 10)
            rx.table.cell(
                row.get("rest", ""),
                padding="4px",
                font_weight="bold",
                background_color="#f5f5f5",
                border="1px solid #ccc",
                border_top="2px solid #666",
                font_size="11px",
                white_space="nowrap",
            ),
        )),
        # Default/fallback
        rx.fragment(),
    )


def _render_trip_summary(summary: Dict[str, Any]) -> rx.Component:
    """Render trip summary section.

    Styled to match Streamlit version exactly - box-based table layout with grid borders.

    Args:
        summary: Trip summary data dict (Var)

    Returns:
        Component displaying trip summary with table-like grid
    """
    # Render using divs with CSS grid to match Streamlit exactly
    return rx.box(
        # Header row
        rx.box(
            rx.text("TRIP SUMMARY", weight="bold", text_align="center"),
            padding="6px",
            background_color="#d6eaf8",
            border="1px solid #333",
            border_top="2px solid #666",
            font_family="'Courier New', monospace",
            font_size="11px",
            width="100%",
        ),
        # Row 1: Credit through Duty Days
        rx.box(
            rx.box(
                rx.text("Credit: ", as_="span", weight="bold"),
                rx.text(summary.get("Credit", ""), as_="span"),
                padding="6px",
                background_color="#f0f8ff",
                border="1px solid #ccc",
                border_top="none",
                font_family="'Courier New', monospace",
                font_size="11px",
                white_space="nowrap",
                flex="1",
            ),
            rx.box(
                rx.text("Blk: ", as_="span", weight="bold"),
                rx.text(summary.get("Blk", ""), as_="span"),
                padding="6px",
                background_color="#f0f8ff",
                border="1px solid #ccc",
                border_top="none",
                border_left="none",
                font_family="'Courier New', monospace",
                font_size="11px",
                white_space="nowrap",
                flex="1",
            ),
            rx.box(
                rx.text("Duty Time: ", as_="span", weight="bold"),
                rx.text(summary.get("Duty Time", ""), as_="span"),
                padding="6px",
                background_color="#f0f8ff",
                border="1px solid #ccc",
                border_top="none",
                border_left="none",
                font_family="'Courier New', monospace",
                font_size="11px",
                white_space="nowrap",
                flex="1.5",
            ),
            rx.box(
                rx.text("TAFB: ", as_="span", weight="bold"),
                rx.text(summary.get("TAFB", ""), as_="span"),
                padding="6px",
                background_color="#f0f8ff",
                border="1px solid #ccc",
                border_top="none",
                border_left="none",
                font_family="'Courier New', monospace",
                font_size="11px",
                white_space="nowrap",
                flex="1",
            ),
            rx.box(
                rx.text("Duty Days: ", as_="span", weight="bold"),
                rx.text(summary.get("Duty Days", ""), as_="span"),
                padding="6px",
                background_color="#f0f8ff",
                border="1px solid #ccc",
                border_top="none",
                border_left="none",
                font_family="'Courier New', monospace",
                font_size="11px",
                white_space="nowrap",
                flex="1",
            ),
            display="flex",
            width="100%",
        ),
        # Row 2: Prem through Domicile
        rx.box(
            rx.box(
                rx.text("Prem: ", as_="span", weight="bold"),
                rx.text(summary.get("Prem", ""), as_="span"),
                padding="6px",
                background_color="#f0f8ff",
                border="1px solid #ccc",
                border_top="none",
                font_family="'Courier New', monospace",
                font_size="11px",
                white_space="nowrap",
                flex="1",
            ),
            rx.box(
                rx.text("PDiem: ", as_="span", weight="bold"),
                rx.text(summary.get("PDiem", ""), as_="span"),
                padding="6px",
                background_color="#f0f8ff",
                border="1px solid #ccc",
                border_top="none",
                border_left="none",
                font_family="'Courier New', monospace",
                font_size="11px",
                white_space="nowrap",
                flex="1",
            ),
            rx.box(
                rx.text("LDGS: ", as_="span", weight="bold"),
                rx.text(summary.get("LDGS", ""), as_="span"),
                padding="6px",
                background_color="#f0f8ff",
                border="1px solid #ccc",
                border_top="none",
                border_left="none",
                font_family="'Courier New', monospace",
                font_size="11px",
                white_space="nowrap",
                flex="1",
            ),
            rx.box(
                rx.text("Crew: ", as_="span", weight="bold"),
                rx.text(summary.get("Crew", ""), as_="span"),
                padding="6px",
                background_color="#f0f8ff",
                border="1px solid #ccc",
                border_top="none",
                border_left="none",
                font_family="'Courier New', monospace",
                font_size="11px",
                white_space="nowrap",
                flex="1",
            ),
            rx.box(
                rx.text("Domicile: ", as_="span", weight="bold"),
                rx.text(summary.get("Domicile", ""), as_="span"),
                padding="6px",
                background_color="#f0f8ff",
                border="1px solid #ccc",
                border_top="none",
                border_left="none",
                font_family="'Courier New', monospace",
                font_size="11px",
                white_space="nowrap",
                flex="1",
            ),
            display="flex",
            width="100%",
        ),
        width="100%",
    )
