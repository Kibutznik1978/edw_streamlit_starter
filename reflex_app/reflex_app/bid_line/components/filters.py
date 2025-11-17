"""Filter Controls Component for Bid Line Analyzer.

This module provides filtering controls for bid line data:
- Credit Time (CT) range filter
- Block Time (BT) range filter
- Days Off (DO) range filter
- Duty Days (DD) range filter
- Active filter indicators
- Reset functionality
"""

import reflex as rx

from ..bid_line_state import BidLineState


def filters_component() -> rx.Component:
    """Filter controls component.

    Displays collapsible filter panel with range sliders for CT, BT, DO, DD.
    Only shown when results are available.

    Returns:
        Reflex component
    """
    return rx.cond(
        BidLineState.has_results,
        rx.card(
            rx.vstack(
                # Header with filter count indicator
                rx.hstack(
                    rx.heading(
                        "Filters",
                        size="6",
                        weight="bold",
                    ),
                    rx.hstack(
                        # Active filter indicator badge
                        rx.cond(
                            BidLineState.filters_active,
                            rx.badge(
                                rx.icon("filter", size=14),
                                "Active",
                                color_scheme="blue",
                                size="2",
                            ),
                        ),
                        # Line count badge
                        rx.badge(
                            rx.cond(
                                BidLineState.filtered_lines_count == BidLineState.total_lines,
                                BidLineState.filtered_lines_count.to(str) + " lines (all)",
                                BidLineState.filtered_lines_count.to(str) + " of " + BidLineState.total_lines.to(str) + " lines",
                            ),
                            color_scheme="gray",
                            size="2",
                        ),
                        spacing="2",
                    ),
                    spacing="3",
                    align="center",
                    width="100%",
                    justify="between",
                ),

                # Filter controls in accordion
                rx.accordion.root(
                    # Credit Time (CT) Filter
                    rx.accordion.item(
                        rx.accordion.trigger(
                            rx.hstack(
                                rx.icon("clock", size=18),
                                rx.text("Credit Time (CT)", weight="medium"),
                                spacing="2",
                            ),
                        ),
                        rx.accordion.content(
                            rx.vstack(
                                # CT Min slider
                                rx.vstack(
                                    rx.hstack(
                                        rx.text(
                                            "Minimum CT",
                                            size="2",
                                            weight="medium",
                                        ),
                                        rx.text(
                                            BidLineState.filter_ct_min.to(str) + " hrs",
                                            size="2",
                                            color="gray",
                                        ),
                                        spacing="2",
                                        align="center",
                                        width="100%",
                                        justify="between",
                                    ),
                                    rx.slider(
                                        default_value=[BidLineState.filter_ct_min],
                                        on_value_commit=lambda value: BidLineState.set_filter_ct_min(value[0]),
                                        min=0,
                                        max=200,
                                        step=1,
                                        width="100%",
                                    ),
                                    spacing="1",
                                    width="100%",
                                ),

                                # CT Max slider
                                rx.vstack(
                                    rx.hstack(
                                        rx.text(
                                            "Maximum CT",
                                            size="2",
                                            weight="medium",
                                        ),
                                        rx.text(
                                            BidLineState.filter_ct_max.to(str) + " hrs",
                                            size="2",
                                            color="gray",
                                        ),
                                        spacing="2",
                                        align="center",
                                        width="100%",
                                        justify="between",
                                    ),
                                    rx.slider(
                                        default_value=[BidLineState.filter_ct_max],
                                        on_value_commit=lambda value: BidLineState.set_filter_ct_max(value[0]),
                                        min=0,
                                        max=200,
                                        step=1,
                                        width="100%",
                                    ),
                                    spacing="1",
                                    width="100%",
                                ),

                                rx.text(
                                    "Show lines with CT in this range",
                                    size="1",
                                    color="gray",
                                ),

                                spacing="3",
                                width="100%",
                                padding="2",
                            ),
                        ),
                        value="ct",
                    ),

                    # Block Time (BT) Filter
                    rx.accordion.item(
                        rx.accordion.trigger(
                            rx.hstack(
                                rx.icon("timer", size=18),
                                rx.text("Block Time (BT)", weight="medium"),
                                spacing="2",
                            ),
                        ),
                        rx.accordion.content(
                            rx.vstack(
                                # BT Min slider
                                rx.vstack(
                                    rx.hstack(
                                        rx.text(
                                            "Minimum BT",
                                            size="2",
                                            weight="medium",
                                        ),
                                        rx.text(
                                            BidLineState.filter_bt_min.to(str) + " hrs",
                                            size="2",
                                            color="gray",
                                        ),
                                        spacing="2",
                                        align="center",
                                        width="100%",
                                        justify="between",
                                    ),
                                    rx.slider(
                                        default_value=[BidLineState.filter_bt_min],
                                        on_value_commit=lambda value: BidLineState.set_filter_bt_min(value[0]),
                                        min=0,
                                        max=200,
                                        step=1,
                                        width="100%",
                                    ),
                                    spacing="1",
                                    width="100%",
                                ),

                                # BT Max slider
                                rx.vstack(
                                    rx.hstack(
                                        rx.text(
                                            "Maximum BT",
                                            size="2",
                                            weight="medium",
                                        ),
                                        rx.text(
                                            BidLineState.filter_bt_max.to(str) + " hrs",
                                            size="2",
                                            color="gray",
                                        ),
                                        spacing="2",
                                        align="center",
                                        width="100%",
                                        justify="between",
                                    ),
                                    rx.slider(
                                        default_value=[BidLineState.filter_bt_max],
                                        on_value_commit=lambda value: BidLineState.set_filter_bt_max(value[0]),
                                        min=0,
                                        max=200,
                                        step=1,
                                        width="100%",
                                    ),
                                    spacing="1",
                                    width="100%",
                                ),

                                rx.text(
                                    "Show lines with BT in this range",
                                    size="1",
                                    color="gray",
                                ),

                                spacing="3",
                                width="100%",
                                padding="2",
                            ),
                        ),
                        value="bt",
                    ),

                    # Days Off (DO) Filter
                    rx.accordion.item(
                        rx.accordion.trigger(
                            rx.hstack(
                                rx.icon("calendar-off", size=18),
                                rx.text("Days Off (DO)", weight="medium"),
                                spacing="2",
                            ),
                        ),
                        rx.accordion.content(
                            rx.vstack(
                                # DO Min slider
                                rx.vstack(
                                    rx.hstack(
                                        rx.text(
                                            "Minimum DO",
                                            size="2",
                                            weight="medium",
                                        ),
                                        rx.text(
                                            BidLineState.filter_do_min.to(str) + " days",
                                            size="2",
                                            color="gray",
                                        ),
                                        spacing="2",
                                        align="center",
                                        width="100%",
                                        justify="between",
                                    ),
                                    rx.slider(
                                        default_value=[BidLineState.filter_do_min],
                                        on_value_commit=lambda value: BidLineState.set_filter_do_min(value[0]),
                                        min=0,
                                        max=31,
                                        step=1,
                                        width="100%",
                                    ),
                                    spacing="1",
                                    width="100%",
                                ),

                                # DO Max slider
                                rx.vstack(
                                    rx.hstack(
                                        rx.text(
                                            "Maximum DO",
                                            size="2",
                                            weight="medium",
                                        ),
                                        rx.text(
                                            BidLineState.filter_do_max.to(str) + " days",
                                            size="2",
                                            color="gray",
                                        ),
                                        spacing="2",
                                        align="center",
                                        width="100%",
                                        justify="between",
                                    ),
                                    rx.slider(
                                        default_value=[BidLineState.filter_do_max],
                                        on_value_commit=lambda value: BidLineState.set_filter_do_max(value[0]),
                                        min=0,
                                        max=31,
                                        step=1,
                                        width="100%",
                                    ),
                                    spacing="1",
                                    width="100%",
                                ),

                                rx.text(
                                    "Show lines with DO in this range",
                                    size="1",
                                    color="gray",
                                ),

                                spacing="3",
                                width="100%",
                                padding="2",
                            ),
                        ),
                        value="do",
                    ),

                    # Duty Days (DD) Filter
                    rx.accordion.item(
                        rx.accordion.trigger(
                            rx.hstack(
                                rx.icon("calendar-check", size=18),
                                rx.text("Duty Days (DD)", weight="medium"),
                                spacing="2",
                            ),
                        ),
                        rx.accordion.content(
                            rx.vstack(
                                # DD Min slider
                                rx.vstack(
                                    rx.hstack(
                                        rx.text(
                                            "Minimum DD",
                                            size="2",
                                            weight="medium",
                                        ),
                                        rx.text(
                                            BidLineState.filter_dd_min.to(str) + " days",
                                            size="2",
                                            color="gray",
                                        ),
                                        spacing="2",
                                        align="center",
                                        width="100%",
                                        justify="between",
                                    ),
                                    rx.slider(
                                        default_value=[BidLineState.filter_dd_min],
                                        on_value_commit=lambda value: BidLineState.set_filter_dd_min(value[0]),
                                        min=0,
                                        max=31,
                                        step=1,
                                        width="100%",
                                    ),
                                    spacing="1",
                                    width="100%",
                                ),

                                # DD Max slider
                                rx.vstack(
                                    rx.hstack(
                                        rx.text(
                                            "Maximum DD",
                                            size="2",
                                            weight="medium",
                                        ),
                                        rx.text(
                                            BidLineState.filter_dd_max.to(str) + " days",
                                            size="2",
                                            color="gray",
                                        ),
                                        spacing="2",
                                        align="center",
                                        width="100%",
                                        justify="between",
                                    ),
                                    rx.slider(
                                        default_value=[BidLineState.filter_dd_max],
                                        on_value_commit=lambda value: BidLineState.set_filter_dd_max(value[0]),
                                        min=0,
                                        max=31,
                                        step=1,
                                        width="100%",
                                    ),
                                    spacing="1",
                                    width="100%",
                                ),

                                rx.text(
                                    "Show lines with DD in this range",
                                    size="1",
                                    color="gray",
                                ),

                                spacing="3",
                                width="100%",
                                padding="2",
                            ),
                        ),
                        value="dd",
                    ),

                    type="multiple",  # Allow multiple sections open
                    width="100%",
                    variant="soft",
                ),

                # Reset button
                rx.button(
                    rx.icon("rotate-ccw", size=16),
                    "Reset All Filters",
                    on_click=BidLineState.reset_filters,
                    variant="soft",
                    color_scheme="gray",
                    width="100%",
                    cursor="pointer",
                ),

                width="100%",
                spacing="4",
            ),
            size="4",
            width="100%",
        )
    )
