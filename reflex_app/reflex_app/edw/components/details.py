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
            rx.callout(
                rx.text("Error parsing trip data: "),
                rx.text(EDWState.selected_trip_data["error"]),
                icon="triangle-alert",
                color_scheme="red",
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

                # Duty day table
                rx.box(
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("Day", padding="0.5rem"),
                                rx.table.column_header_cell("Flight", padding="0.5rem"),
                                rx.table.column_header_cell("Dep-Arr", padding="0.5rem"),
                                rx.table.column_header_cell("Depart (L) Z", padding="0.5rem"),
                                rx.table.column_header_cell("Arrive (L) Z", padding="0.5rem"),
                                rx.table.column_header_cell("Blk", padding="0.5rem"),
                                rx.table.column_header_cell("Cxn", padding="0.5rem"),
                                rx.table.column_header_cell("Duty", padding="0.5rem"),
                                rx.table.column_header_cell("Cr", padding="0.5rem"),
                                rx.table.column_header_cell("L/O", padding="0.5rem"),
                            )
                        ),
                        rx.table.body(
                            # Render all duty days
                            rx.foreach(
                                EDWState.selected_trip_data.get("duty_days", []),
                                lambda duty, idx: _render_duty_day(duty, idx),
                            )
                        ),
                        variant="surface",
                        size="1",
                    ),
                    overflow_x="auto",
                    width="100%",
                ),

                # Trip summary
                rx.cond(
                    EDWState.selected_trip_data.contains("trip_summary"),
                    _render_trip_summary(EDWState.selected_trip_data["trip_summary"]),
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


def _render_duty_day(duty: Dict[str, Any], duty_idx: int) -> rx.Component:
    """Render all rows for a single duty day.

    Args:
        duty: Duty day data dict (Var)
        duty_idx: Index of this duty day (0-based from foreach)

    Returns:
        Fragment containing all table rows for this duty day
    """
    return rx.fragment(
        # Duty start row (Briefing)
        rx.cond(
            duty.contains("duty_start"),
            rx.table.row(
                rx.table.cell(
                    rx.text("Briefing", font_style="italic"),
                    colspan=3,
                    padding="0.5rem",
                    background_color=rx.color("gray", 2),
                ),
                rx.table.cell(duty["duty_start"], padding="0.5rem", background_color=rx.color("gray", 2)),
                rx.table.cell("", padding="0.5rem", background_color=rx.color("gray", 2)),
                rx.table.cell("", colspan=5, padding="0.5rem", background_color=rx.color("gray", 2)),
            ),
            rx.fragment(),
        ),

        # Flight rows
        rx.foreach(
            duty.get("flights", []),
            lambda flight, flight_idx: _render_flight_row(flight, flight_idx),
        ),

        # Duty end row (Debriefing)
        rx.cond(
            duty.contains("duty_end"),
            rx.table.row(
                rx.table.cell(
                    rx.text("Debriefing", font_style="italic"),
                    colspan=3,
                    padding="0.5rem",
                    background_color=rx.color("gray", 2),
                ),
                rx.table.cell("", padding="0.5rem", background_color=rx.color("gray", 2)),
                rx.table.cell(duty["duty_end"], padding="0.5rem", background_color=rx.color("gray", 2)),
                rx.table.cell("", colspan=5, padding="0.5rem", background_color=rx.color("gray", 2)),
            ),
            rx.fragment(),
        ),

        # Subtotal row
        rx.table.row(
            rx.table.cell(
                "Duty Day Subtotal:",
                colspan=5,
                text_align="right",
                padding="0.5rem",
                font_weight="bold",
                background_color=rx.color("gray", 3),
            ),
            rx.table.cell(
                duty.get("block_total", ""),
                padding="0.5rem",
                font_weight="bold",
                background_color=rx.color("gray", 3),
            ),
            rx.table.cell(
                "",
                padding="0.5rem",
                background_color=rx.color("gray", 3),
            ),
            rx.table.cell(
                duty.get("duty_time", ""),
                padding="0.5rem",
                font_weight="bold",
                background_color=rx.color("gray", 3),
            ),
            rx.table.cell(
                duty.get("credit", ""),
                padding="0.5rem",
                font_weight="bold",
                background_color=rx.color("gray", 3),
            ),
            rx.table.cell(
                duty.get("rest", ""),
                padding="0.5rem",
                font_weight="bold",
                background_color=rx.color("gray", 3),
            ),
        ),
    )


def _render_flight_row(flight: Dict[str, Any], flight_idx: int) -> rx.Component:
    """Render a single flight row in the duty day table.

    Args:
        flight: Flight data dict (Var)
        flight_idx: Index of this flight in the duty day (0-based from foreach)

    Returns:
        Table row component
    """
    return rx.table.row(
        rx.table.cell(flight.get("day", ""), padding="0.5rem"),
        rx.table.cell(flight.get("flight", ""), padding="0.5rem"),
        rx.table.cell(flight.get("route", ""), padding="0.5rem"),
        rx.table.cell(flight.get("depart", ""), padding="0.5rem"),
        rx.table.cell(flight.get("arrive", ""), padding="0.5rem"),
        rx.table.cell(flight.get("block", ""), padding="0.5rem"),
        rx.table.cell(flight.get("connection", ""), padding="0.5rem"),
        # Duty, Cr, L/O columns are handled by rowspan in original -
        # for now, leave empty (Reflex tables don't support rowspan well)
        rx.table.cell("", padding="0.5rem"),
        rx.table.cell("", padding="0.5rem"),
        rx.table.cell("", padding="0.5rem"),
    )


def _render_trip_summary(summary: Dict[str, Any]) -> rx.Component:
    """Render trip summary section.

    Args:
        summary: Trip summary data dict (Var)

    Returns:
        Component displaying trip summary
    """
    # Define the fields we want to display
    row1_fields = ["Credit", "Blk", "Duty Time", "TAFB", "Duty Days"]
    row2_fields = ["Prem", "PDiem", "LDGS", "Crew", "Domicile"]

    return rx.vstack(
        rx.heading("Trip Summary", size="4", weight="bold", margin_top="1rem"),
        rx.divider(),
        rx.vstack(
            # Row 1
            rx.hstack(
                rx.foreach(
                    row1_fields,
                    lambda field: rx.cond(
                        summary.contains(field),
                        rx.hstack(
                            rx.text(f"{field}:", weight="bold", size="2"),
                            rx.text(summary[field], size="2"),
                            spacing="1",
                        ),
                        rx.fragment(),
                    ),
                ),
                spacing="4",
                wrap="wrap",
            ),
            # Row 2
            rx.hstack(
                rx.foreach(
                    row2_fields,
                    lambda field: rx.cond(
                        summary.contains(field),
                        rx.hstack(
                            rx.text(f"{field}:", weight="bold", size="2"),
                            # Add $ prefix for Prem and PDiem if needed
                            rx.cond(
                                (field == "Prem") | (field == "PDiem"),
                                rx.cond(
                                    summary[field].startswith("$"),
                                    rx.text(summary[field], size="2"),
                                    rx.text(f"${summary[field]}", size="2"),
                                ),
                                rx.text(summary[field], size="2"),
                            ),
                            spacing="1",
                        ),
                        rx.fragment(),
                    ),
                ),
                spacing="4",
                wrap="wrap",
            ),
            spacing="2",
            padding="1rem",
            background_color=rx.color("blue", 2),
            border_radius="0.5rem",
        ),
        width="100%",
        spacing="2",
    )
