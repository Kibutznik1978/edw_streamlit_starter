"""Duty Day Distribution Charts Component.

This module provides interactive Recharts bar charts for visualizing
duty day distribution data in the EDW Pairing Analyzer.
"""

import reflex as rx

from ..edw_state import EDWState
from reflex_app.theme import Colors


def charts_component() -> rx.Component:
    """Duty day distribution charts component.

    Displays two interactive bar charts:
    1. Duty day count distribution
    2. Duty day percentage distribution

    Includes toggle to exclude 1-day trips from visualization.
    Only shown when results are available.

    Returns:
        Reflex component
    """
    return rx.cond(
        EDWState.has_results,
        rx.card(
            rx.vstack(
                # Section header
                rx.heading(
                    "Duty Day Distribution",
                    size="6",
                    weight="bold",
                    margin_bottom="4",
                ),

                # Exclude 1-day trips toggle
                rx.hstack(
                rx.switch(
                    checked=EDWState.exclude_turns,
                    on_change=EDWState.set_exclude_turns,
                ),
                rx.text(
                    "Exclude 1-day trips",
                    size="2",
                    weight="medium",
                ),
                spacing="2",
                align="center",
                margin_bottom="4",
            ),

            # Charts grid (side-by-side, fully responsive)
            rx.flex(
                # Count chart
                rx.box(
                    rx.heading("Duty Day Count Distribution", size="5", margin_bottom="3"),
                    rx.recharts.bar_chart(
                        rx.recharts.bar(
                            data_key="Trips",
                            fill=Colors.sky_500,
                            stroke=Colors.navy_700,
                            stroke_width=1,
                            label={"position": "top", "fill": Colors.gray_700, "fontSize": 12},
                        ),
                        rx.recharts.x_axis(data_key="Duty Days"),
                        rx.recharts.y_axis(),
                        rx.recharts.cartesian_grid(stroke_dasharray="3 3"),
                        rx.recharts.graphing_tooltip(
                            cursor={"fill": "rgba(0, 0, 0, 0.1)"},
                        ),
                        data=EDWState.duty_dist_display,
                        width="100%",
                        height=400,
                    ),
                    flex="1",
                    min_width="0",
                ),

                # Percentage chart
                rx.box(
                    rx.heading("Duty Day Percentage Distribution", size="5", margin_bottom="3"),
                    rx.recharts.bar_chart(
                        rx.recharts.bar(
                            data_key="Percent",
                            fill=Colors.teal_600,
                            stroke=Colors.navy_700,
                            stroke_width=1,
                            label={"position": "top", "fill": Colors.gray_700, "fontSize": 12},
                        ),
                        rx.recharts.x_axis(data_key="Duty Days"),
                        rx.recharts.y_axis(),
                        rx.recharts.cartesian_grid(stroke_dasharray="3 3"),
                        rx.recharts.graphing_tooltip(
                            cursor={"fill": "rgba(0, 0, 0, 0.1)"},
                        ),
                        data=EDWState.duty_dist_display,
                        width="100%",
                        height=400,
                    ),
                    flex="1",
                    min_width="0",
                ),

                direction="row",
                wrap="wrap",
                spacing="4",
                width="100%",
            ),

                # Info callout
                rx.callout.root(
                    rx.callout.text(
                        "Interactive charts powered by Recharts. Hover over bars for details.",
                    ),
                    size="1",
                    color="gray",
                    margin_top="4",
                ),

                width="100%",
                spacing="4",
            ),
            size="4",
            width="100%",
        )
    )
