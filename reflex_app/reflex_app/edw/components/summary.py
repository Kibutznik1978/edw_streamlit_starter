"""EDW Analyzer Summary Statistics Component.

This module provides the summary statistics display component showing
trip counts and weighted EDW metrics.
"""

import reflex as rx
from ..edw_state import EDWState


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
        suffix: Optional suffix to append to value (e.g., "%")

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
                    f"{value_var}{suffix}",
                    value_var,
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
    )


def percentage_card(
    label: str,
    value_var,
    icon: str = "percent",
    color: str = "blue",
) -> rx.Component:
    """Create a percentage statistics card.

    Args:
        label: Display label for the percentage
        value_var: State variable containing the percentage value (without % sign)
        icon: Icon name from Reflex icon set
        color: Color theme

    Returns:
        rx.Component: Styled percentage card
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
            # Percentage value with larger display
            rx.hstack(
                rx.text(
                    rx.cond(
                        value_var > 0,
                        f"{value_var:.1f}",
                        "0.0",
                    ),
                    size="7",
                    weight="bold",
                    color=rx.color(color, 11),
                ),
                rx.text(
                    "%",
                    size="5",
                    weight="medium",
                    color=rx.color("gray", 10),
                ),
                spacing="1",
                align="baseline",
            ),
            spacing="2",
            align="start",
        ),
        padding="4",
        border_radius="8px",
        border=f"1px solid {rx.color(color, 6)}",
        background=rx.color(color, 2),
        min_width="160px",
        flex="1",
    )


def duty_day_statistics_component() -> rx.Component:
    """Duty day statistics display component.

    Shows average metrics for duty days broken down by All/EDW/Non-EDW.
    Only shown when results are available.

    Returns:
        rx.Component: Duty day statistics section
    """
    return rx.cond(
        EDWState.has_results,
        rx.vstack(
            # Section header
            rx.hstack(
                rx.icon("activity", size=24, color=rx.color("teal", 9)),
                rx.heading(
                    "Duty Day Averages",
                    size="5",
                    weight="bold",
                ),
                spacing="3",
                align="center",
            ),
            # Statistics table
            rx.box(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Metric"),
                            rx.table.column_header_cell("All Trips"),
                            rx.table.column_header_cell("EDW Trips"),
                            rx.table.column_header_cell("Non-EDW Trips"),
                        ),
                    ),
                    rx.table.body(
                        # Build table rows from duty_day_stats (list of records)
                        rx.foreach(
                            EDWState.duty_day_stats,
                            lambda row: rx.table.row(
                                rx.table.cell(row["Metric"], weight="medium"),
                                rx.table.cell(row["All"]),
                                rx.table.cell(
                                    row["EDW"],
                                    color=rx.color("indigo", 11),
                                ),
                                rx.table.cell(
                                    row["Non-EDW"],
                                    color=rx.color("amber", 11),
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
            # Distribution preview note
            rx.box(
                rx.text(
                    "Detailed duty day distribution charts will be available in the Charts section below.",
                    size="2",
                    color=rx.color("gray", 10),
                ),
                padding="3",
                border_radius="6px",
                background=rx.color("gray", 3),
                width="100%",
            ),
            # Divider before next section
            rx.divider(),
            spacing="4",
            width="100%",
        ),
    )


def summary_component() -> rx.Component:
    """Summary statistics display component.

    Displays trip counts, weighted EDW metrics, and duty day statistics
    after PDF analysis. Only shown when results are available.

    Returns:
        rx.Component: Complete summary statistics section
    """
    return rx.cond(
        EDWState.has_results,
        rx.vstack(
            # Trip Summary Section
            rx.vstack(
                # Section header
                rx.hstack(
                    rx.icon("bar-chart-2", size=24, color=rx.color("blue", 9)),
                    rx.heading(
                        "Trip Summary",
                        size="5",
                        weight="bold",
                    ),
                    spacing="3",
                    align="center",
                ),
                # Trip count cards
                rx.flex(
                    stat_card(
                        "Unique Pairings",
                        EDWState.unique_pairings,
                        icon="hash",
                        color="purple",
                    ),
                    stat_card(
                        "Total Trips",
                        EDWState.total_trips,
                        icon="package",
                        color="blue",
                    ),
                    stat_card(
                        "EDW Trips",
                        EDWState.edw_trips,
                        icon="moon",
                        color="indigo",
                    ),
                    stat_card(
                        "Day Trips",
                        EDWState.day_trips,
                        icon="sun",
                        color="amber",
                    ),
                    stat_card(
                        "Hot Standby",
                        EDWState.hot_standby_trips,
                        icon="zap",
                        color="red",
                    ),
                    direction="row",
                    wrap="wrap",
                    spacing="4",
                    width="100%",
                ),
                spacing="4",
                width="100%",
            ),
            # Weighted Metrics Section
            rx.vstack(
                # Section header
                rx.hstack(
                    rx.icon("percent", size=24, color=rx.color("green", 9)),
                    rx.heading(
                        "Weighted EDW Metrics",
                        size="5",
                        weight="bold",
                    ),
                    spacing="3",
                    align="center",
                ),
                # Percentage cards
                rx.flex(
                    percentage_card(
                        "Trip-Weighted",
                        EDWState.trip_weighted_pct,
                        icon="package",
                        color="blue",
                    ),
                    percentage_card(
                        "TAFB-Weighted",
                        EDWState.tafb_weighted_pct,
                        icon="clock",
                        color="green",
                    ),
                    percentage_card(
                        "Duty Day-Weighted",
                        EDWState.duty_day_weighted_pct,
                        icon="calendar-days",
                        color="purple",
                    ),
                    direction="row",
                    wrap="wrap",
                    spacing="4",
                    width="100%",
                ),
                # Metrics explanation
                rx.box(
                    rx.text(
                        "Weighted metrics show EDW trip percentage calculated by different methods: ",
                        "trip count (simple ratio), TAFB hours (time away from base), ",
                        "and duty days (calendar days with duty).",
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
            # Duty Day Statistics Section
            duty_day_statistics_component(),
            spacing="6",
            width="100%",
        ),
    )
