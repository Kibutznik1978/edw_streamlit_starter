"""Statistics Display Component for Bid Line Analyzer.

This module provides comprehensive statistics display for bid line data:
- Basic statistics (CT, BT, DO, DD) with min/max/mean/median
- Pay period comparison (conditional on pay period data availability)
- Reserve line statistics (conditional on reserve data availability)
"""

import reflex as rx

from ..bid_line_state import BidLineState


def stat_card(
    label: str,
    value_var,
    icon: str = "bar-chart",
    color: str = "blue",
    suffix: str = "",
) -> rx.Component:
    """Create a statistics card with label, value, and icon.

    Args:
        label: Display label for the statistic
        value_var: State variable containing the value
        icon: Icon name from Reflex icon set
        color: Color theme (blue, green, purple, etc.)
        suffix: Optional suffix to append to value (e.g., "hrs", "days")

    Returns:
        rx.Component: Styled statistics card
    """
    return rx.box(
        rx.vstack(
            # Icon and label row
            rx.hstack(
                rx.icon(icon, size=20, color=rx.color(color, 9)),
                rx.text(
                    label,
                    size="2",
                    weight="medium",
                    color=rx.color("gray", 11),
                ),
                spacing="2",
                align="center",
            ),
            # Value display
            rx.text(
                rx.cond(
                    suffix != "",
                    value_var.to(str) + " " + suffix,
                    value_var.to(str),
                ),
                size="6",
                weight="bold",
                color=rx.color("gray", 12),
            ),
            spacing="2",
            align="start",
        ),
        padding="4",
        border_radius="8px",
        border=f"1px solid {rx.color('gray', 6)}",
        background=rx.color("gray", 2),
        min_width="140px",
        flex="1",
        transition="all 200ms ease",
        _hover={
            "box_shadow": "0 4px 12px rgba(0, 0, 0, 0.1)",
            "transform": "translateY(-2px)",
            "border_color": rx.color('gray', 7),
        },
    )


def metric_group(
    metric_name: str,
    icon: str,
    color: str,
    min_val,
    max_val,
    mean_val,
    median_val,
    suffix: str = "",
) -> rx.Component:
    """Create a group of statistics cards for a single metric.

    Args:
        metric_name: Name of the metric (e.g., "Credit Time (CT)")
        icon: Icon name
        color: Color theme
        min_val: Minimum value state variable
        max_val: Maximum value state variable
        mean_val: Mean value state variable
        median_val: Median value state variable
        suffix: Unit suffix (e.g., "hrs", "days")

    Returns:
        rx.Component: Group of 4 stat cards (min/max/mean/median)
    """
    return rx.vstack(
        # Metric name header
        rx.hstack(
            rx.icon(icon, size=20, color=rx.color(color, 9)),
            rx.text(
                metric_name,
                size="3",
                weight="bold",
                color=rx.color("gray", 12),
            ),
            spacing="2",
            align="center",
        ),
        # Statistics cards
        rx.flex(
            stat_card("Min", min_val, icon="arrow-down", color=color, suffix=suffix),
            stat_card("Max", max_val, icon="arrow-up", color=color, suffix=suffix),
            stat_card("Mean", mean_val, icon="trending-up", color=color, suffix=suffix),
            stat_card("Median", median_val, icon="minus", color=color, suffix=suffix),
            direction="row",
            wrap="wrap",
            spacing="3",
            width="100%",
        ),
        spacing="3",
        width="100%",
    )


def pay_period_comparison() -> rx.Component:
    """Pay period comparison section (conditional).

    Shows CT, BT, DO, DD averages for each pay period side-by-side.
    Only displayed when pay period data is available.

    Returns:
        rx.Component: Pay period comparison section
    """
    return rx.cond(
        BidLineState.has_pay_periods,
        rx.vstack(
            # Section header
            rx.hstack(
                rx.icon("calendar-range", size=24, color=rx.color("purple", 9)),
                rx.heading(
                    "Pay Period Comparison",
                    size="5",
                    weight="bold",
                ),
                spacing="3",
                align="center",
            ),
            # Comparison table
            rx.box(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Metric"),
                            rx.table.column_header_cell("Pay Period 1"),
                            rx.table.column_header_cell("Pay Period 2"),
                            rx.table.column_header_cell("Difference"),
                        ),
                    ),
                    rx.table.body(
                        # CT row
                        rx.table.row(
                            rx.table.cell("Credit Time (CT)", weight="medium"),
                            rx.table.cell(
                                BidLineState.pp1_ct_mean.to(str) + " hrs",
                                color=rx.color("blue", 11),
                            ),
                            rx.table.cell(
                                BidLineState.pp2_ct_mean.to(str) + " hrs",
                                color=rx.color("blue", 11),
                            ),
                            rx.table.cell(
                                rx.cond(
                                    BidLineState.pp2_ct_mean > BidLineState.pp1_ct_mean,
                                    "+" + (BidLineState.pp2_ct_mean - BidLineState.pp1_ct_mean).to(str) + " hrs",
                                    (BidLineState.pp2_ct_mean - BidLineState.pp1_ct_mean).to(str) + " hrs",
                                ),
                                color=rx.cond(
                                    BidLineState.pp2_ct_mean > BidLineState.pp1_ct_mean,
                                    rx.color("green", 11),
                                    rx.color("red", 11),
                                ),
                            ),
                        ),
                        # BT row
                        rx.table.row(
                            rx.table.cell("Block Time (BT)", weight="medium"),
                            rx.table.cell(
                                BidLineState.pp1_bt_mean.to(str) + " hrs",
                                color=rx.color("cyan", 11),
                            ),
                            rx.table.cell(
                                BidLineState.pp2_bt_mean.to(str) + " hrs",
                                color=rx.color("cyan", 11),
                            ),
                            rx.table.cell(
                                rx.cond(
                                    BidLineState.pp2_bt_mean > BidLineState.pp1_bt_mean,
                                    "+" + (BidLineState.pp2_bt_mean - BidLineState.pp1_bt_mean).to(str) + " hrs",
                                    (BidLineState.pp2_bt_mean - BidLineState.pp1_bt_mean).to(str) + " hrs",
                                ),
                                color=rx.cond(
                                    BidLineState.pp2_bt_mean > BidLineState.pp1_bt_mean,
                                    rx.color("green", 11),
                                    rx.color("red", 11),
                                ),
                            ),
                        ),
                        # DO row
                        rx.table.row(
                            rx.table.cell("Days Off (DO)", weight="medium"),
                            rx.table.cell(
                                BidLineState.pp1_do_mean.to(str) + " days",
                                color=rx.color("green", 11),
                            ),
                            rx.table.cell(
                                BidLineState.pp2_do_mean.to(str) + " days",
                                color=rx.color("green", 11),
                            ),
                            rx.table.cell(
                                rx.cond(
                                    BidLineState.pp2_do_mean > BidLineState.pp1_do_mean,
                                    "+" + (BidLineState.pp2_do_mean - BidLineState.pp1_do_mean).to(str) + " days",
                                    (BidLineState.pp2_do_mean - BidLineState.pp1_do_mean).to(str) + " days",
                                ),
                                color=rx.cond(
                                    BidLineState.pp2_do_mean > BidLineState.pp1_do_mean,
                                    rx.color("green", 11),
                                    rx.color("red", 11),
                                ),
                            ),
                        ),
                        # DD row
                        rx.table.row(
                            rx.table.cell("Duty Days (DD)", weight="medium"),
                            rx.table.cell(
                                BidLineState.pp1_dd_mean.to(str) + " days",
                                color=rx.color("orange", 11),
                            ),
                            rx.table.cell(
                                BidLineState.pp2_dd_mean.to(str) + " days",
                                color=rx.color("orange", 11),
                            ),
                            rx.table.cell(
                                rx.cond(
                                    BidLineState.pp2_dd_mean > BidLineState.pp1_dd_mean,
                                    "+" + (BidLineState.pp2_dd_mean - BidLineState.pp1_dd_mean).to(str) + " days",
                                    (BidLineState.pp2_dd_mean - BidLineState.pp1_dd_mean).to(str) + " days",
                                ),
                                color=rx.cond(
                                    BidLineState.pp2_dd_mean > BidLineState.pp1_dd_mean,
                                    rx.color("green", 11),
                                    rx.color("red", 11),
                                ),
                            ),
                        ),
                    ),
                    variant="surface",
                    size="2",
                    width="100%",
                ),
                border_radius="8px",
                border=f"1px solid {rx.color('gray', 6)}",
                overflow="hidden",
            ),
            # Explanation note
            rx.box(
                rx.text(
                    "Positive difference (green) indicates higher values in Pay Period 2 compared to Pay Period 1.",
                    size="2",
                    color=rx.color("gray", 10),
                ),
                padding="3",
                border_radius="6px",
                background=rx.color("gray", 3),
                width="100%",
            ),
            spacing="4",
            width="100%",
        ),
    )


def reserve_statistics() -> rx.Component:
    """Reserve line statistics section (conditional).

    Shows reserve and hot standby slots for Captain and F/O positions.
    Only displayed when reserve data is available.

    Returns:
        rx.Component: Reserve statistics section
    """
    return rx.cond(
        (BidLineState.reserve_captain_slots > 0) | (BidLineState.reserve_fo_slots > 0) |
        (BidLineState.hot_standby_captain_slots > 0) | (BidLineState.hot_standby_fo_slots > 0),
        rx.vstack(
            # Section header
            rx.hstack(
                rx.icon("users", size=24, color=rx.color("amber", 9)),
                rx.heading(
                    "Reserve Line Statistics",
                    size="5",
                    weight="bold",
                ),
                spacing="3",
                align="center",
            ),
            # Reserve slots cards
            rx.flex(
                stat_card(
                    "Reserve Captain",
                    BidLineState.reserve_captain_slots,
                    icon="user-check",
                    color="blue",
                    suffix="slots",
                ),
                stat_card(
                    "Reserve F/O",
                    BidLineState.reserve_fo_slots,
                    icon="user-check",
                    color="cyan",
                    suffix="slots",
                ),
                stat_card(
                    "Hot Standby Captain",
                    BidLineState.hot_standby_captain_slots,
                    icon="zap",
                    color="red",
                    suffix="slots",
                ),
                stat_card(
                    "Hot Standby F/O",
                    BidLineState.hot_standby_fo_slots,
                    icon="zap",
                    color="orange",
                    suffix="slots",
                ),
                direction="row",
                wrap="wrap",
                spacing="4",
                width="100%",
            ),
            spacing="4",
            width="100%",
        ),
    )


def statistics_component() -> rx.Component:
    """Statistics display component.

    Displays comprehensive statistics for bid line data including:
    - Basic metrics (CT, BT, DO, DD) with min/max/mean/median
    - Pay period comparison (conditional)
    - Reserve line statistics (conditional)

    Only shown when results are available.

    Returns:
        rx.Component: Complete statistics section
    """
    return rx.cond(
        BidLineState.has_results,
        rx.card(
            rx.vstack(
                # Main statistics header
                rx.hstack(
                    rx.icon("bar-chart-2", size=24, color=rx.color("blue", 9)),
                    rx.heading(
                        "Bid Line Statistics",
                        size="6",
                        weight="bold",
                    ),
                    spacing="3",
                    align="center",
                ),

                # Basic Statistics Section
                rx.vstack(
                    # CT statistics
                    metric_group(
                        "Credit Time (CT)",
                        "clock",
                        "blue",
                        BidLineState.ct_min,
                        BidLineState.ct_max,
                        BidLineState.ct_mean,
                        BidLineState.ct_median,
                        "hrs",
                    ),

                    # BT statistics
                    metric_group(
                        "Block Time (BT)",
                        "timer",
                        "cyan",
                        BidLineState.bt_min,
                        BidLineState.bt_max,
                        BidLineState.bt_mean,
                        BidLineState.bt_median,
                        "hrs",
                    ),

                    # DO statistics
                    metric_group(
                        "Days Off (DO)",
                        "calendar-off",
                        "green",
                        BidLineState.do_min,
                        BidLineState.do_max,
                        BidLineState.do_mean,
                        BidLineState.do_median,
                        "days",
                    ),

                    # DD statistics
                    metric_group(
                        "Duty Days (DD)",
                        "calendar-check",
                        "orange",
                        BidLineState.dd_min,
                        BidLineState.dd_max,
                        BidLineState.dd_mean,
                        BidLineState.dd_median,
                        "days",
                    ),

                    spacing="6",
                    width="100%",
                ),

                # Divider before conditional sections
                rx.cond(
                    BidLineState.has_pay_periods,
                    rx.divider(),
                ),

                # Pay Period Comparison (conditional)
                pay_period_comparison(),

                # Divider before reserve stats (conditional)
                rx.cond(
                    (BidLineState.reserve_captain_slots > 0) | (BidLineState.reserve_fo_slots > 0) |
                    (BidLineState.hot_standby_captain_slots > 0) | (BidLineState.hot_standby_fo_slots > 0),
                    rx.divider(),
                ),

                # Reserve Statistics (conditional)
                reserve_statistics(),

                spacing="6",
                width="100%",
            ),
            size="4",
            width="100%",
        ),
    )
