"""Header Information Display Component for EDW Analyzer.

This component displays extracted PDF header information including:
- Domicile
- Aircraft/Fleet Type
- Bid Period
- Date Range
- Report Date

The component uses a responsive card layout and only displays when data is available.
"""

import reflex as rx
from ..edw_state import EDWState


def info_card(label: str, value_var, icon: str = "info") -> rx.Component:
    """Create an info card for displaying a single piece of header information.

    Args:
        label: The label text (e.g., "Domicile")
        value_var: The EDWState variable to display (e.g., EDWState.domicile)
        icon: Icon name from Reflex icon set

    Returns:
        rx.Component: A styled card component
    """
    return rx.box(
        rx.vstack(
            # Icon and label row
            rx.hstack(
                rx.icon(icon, size=20, color=rx.color("blue", 9)),
                rx.text(
                    label,
                    size="2",
                    weight="medium",
                    color=rx.color("gray", 11),
                ),
                spacing="2",
                align="center",
            ),
            # Value
            rx.text(
                value_var,
                size="4",
                weight="bold",
                color=rx.color("gray", 12),
            ),
            spacing="2",
            align="start",
            width="100%",
        ),
        padding="4",
        border_radius="8px",
        border=f"1px solid {rx.color('gray', 6)}",
        background=rx.color("gray", 2),
        width="100%",
        min_width="150px",
    )


def header_component() -> rx.Component:
    """Header information display component.

    Displays extracted PDF header information in a responsive card layout.
    Only shown when header data is available (after successful upload).

    Returns:
        rx.Component: The complete header display component
    """
    return rx.cond(
        EDWState.domicile != "",  # Only show if we have header data
        rx.vstack(
            # Section heading
            rx.hstack(
                rx.icon("file-text", size=24, color=rx.color("blue", 9)),
                rx.heading(
                    "Pairing Information",
                    size="6",
                    color=rx.color("gray", 12),
                ),
                spacing="2",
                align="center",
            ),

            # Info cards grid - responsive layout
            rx.box(
                rx.flex(
                    # Row 1: Domicile, Aircraft, Bid Period
                    info_card(
                        "Domicile",
                        EDWState.domicile,
                        "map-pin"
                    ),
                    info_card(
                        "Aircraft",
                        EDWState.aircraft,
                        "plane"
                    ),
                    info_card(
                        "Bid Period",
                        EDWState.bid_period,
                        "calendar"
                    ),

                    # Row 2: Date Range, Report Date
                    info_card(
                        "Date Range",
                        EDWState.date_range,
                        "calendar-range"
                    ),
                    info_card(
                        "Report Date",
                        EDWState.report_date,
                        "calendar-check"
                    ),

                    # Responsive layout configuration
                    direction="row",
                    wrap="wrap",
                    spacing="4",
                    width="100%",
                ),
                width="100%",
            ),

            # Divider below header
            rx.divider(),

            spacing="4",
            width="100%",
        ),
    )
