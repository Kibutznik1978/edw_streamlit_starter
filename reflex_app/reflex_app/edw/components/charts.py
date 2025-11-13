"""Duty Day Distribution Charts Component.

This module provides interactive Plotly charts for visualizing
duty day distribution data in the EDW Pairing Analyzer.
"""

import reflex as rx

from ..edw_state import EDWState


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

            # Charts grid (side-by-side on desktop, stacked on mobile)
            rx.flex(
                # Count chart
                rx.box(
                    rx.plotly(
                        data=EDWState.duty_day_count_chart,
                        layout={},
                        config={
                            "displayModeBar": True,
                            "displaylogo": False,
                            "modeBarButtonsToRemove": [
                                "pan2d",
                                "select2d",
                                "lasso2d",
                                "autoScale2d",
                            ],
                        },
                    ),
                    width="100%",
                    min_width="400px",
                    flex="1",
                ),

                # Percentage chart
                rx.box(
                    rx.plotly(
                        data=EDWState.duty_day_percent_chart,
                        layout={},
                        config={
                            "displayModeBar": True,
                            "displaylogo": False,
                            "modeBarButtonsToRemove": [
                                "pan2d",
                                "select2d",
                                "lasso2d",
                                "autoScale2d",
                            ],
                        },
                    ),
                    width="100%",
                    min_width="400px",
                    flex="1",
                ),

                direction="row",
                wrap="wrap",
                spacing="4",
                width="100%",
            ),

                # Info callout
                rx.callout.root(
                    rx.callout.text(
                        "Interactive charts powered by Plotly. Hover over bars for details, use toolbar to zoom/pan.",
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
