"""Distribution Charts Component for Bid Line Analyzer.

This module provides interactive Recharts visualizations for bid line data:
- Credit Time (CT) distribution
- Block Time (BT) distribution
- Days Off (DO) distribution
- Duty Days (DD) distribution
- Pay period comparison charts (conditional)
"""

from typing import Optional, Tuple

import reflex as rx

from ..bid_line_state import BidLineState
from reflex_app.theme import Colors


def distribution_chart(
    title: str,
    data_var,
    x_axis_key: str,
    y_axis_key: str,
    bar_color: str,
    bar_stroke: str,
    *,
    y_domain: Optional[Tuple[int, int]] = None,
) -> rx.Component:
    """Create a distribution bar chart."""
    return rx.box(
        rx.heading(title, size="4", margin_bottom="3", weight="bold"),
        rx.recharts.bar_chart(
            rx.recharts.bar(
                data_key=y_axis_key,
                fill=bar_color,
                stroke=bar_stroke,
                stroke_width=1,
                label={"position": "top", "fill": Colors.gray_700, "fontSize": 12},
            ),
            rx.recharts.x_axis(
                data_key=x_axis_key,
                angle=-45,
                text_anchor="end",
                height=80,
            ),
            rx.recharts.y_axis(domain=y_domain),
            rx.recharts.cartesian_grid(stroke_dasharray="3 3"),
            rx.recharts.graphing_tooltip(cursor={"fill": "rgba(0, 0, 0, 0.1)"}),
            data=data_var,
            width="100%",
            height=350,
        ),
        flex="1",
        min_width="300px",
    )


def _period_distribution_chart(
    title: str,
    data_var,
    x_axis_key: str,
    bar_color: str,
    bar_stroke: str,
    *,
    y_domain: Optional[Tuple[int, int]] = None,
) -> rx.Component:
    """Render a distribution chart for a specific pay period with fallback messaging."""
    return rx.cond(
        data_var.length() > 0,
        distribution_chart(
            title,
            data_var,
            x_axis_key,
            "Count",
            bar_color,
            bar_stroke,
            y_domain=y_domain,
        ),
        rx.box(
            rx.heading(title, size="4", margin_bottom="3", weight="bold"),
            rx.text(
                "No data available for this pay period.",
                size="2",
                color=Colors.gray_700,
            ),
            border=f"1px dashed {Colors.gray_400}",
            border_radius="8px",
            padding="4",
            flex="1",
            min_width="300px",
        ),
    )


def pay_period_comparison_charts() -> rx.Component:
    """Pay period comparison charts (conditional).

    Shows bar charts comparing CT, BT, DO, DD between pay periods.
    Only displayed when pay period data is available.

    Returns:
        rx.Component: Pay period comparison charts section
    """
    return rx.cond(
        BidLineState.has_pay_periods,
        rx.vstack(
            # Divider before comparison section
            rx.divider(margin_top="6", margin_bottom="4"),

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
                margin_bottom="4",
            ),

            # Comparison bars (side-by-side for each metric)
            rx.flex(
                # CT comparison
                rx.box(
                    rx.heading("Credit Time (CT)", size="4", margin_bottom="3", weight="bold"),
                    rx.recharts.bar_chart(
                        rx.recharts.bar(
                            data_key="PP1",
                            fill=rx.color("blue", 7),
                            stroke=Colors.navy_700,
                            stroke_width=1,
                            name="Pay Period 1",
                        ),
                        rx.recharts.bar(
                            data_key="PP2",
                            fill=rx.color("blue", 9),
                            stroke=Colors.navy_700,
                            stroke_width=1,
                            name="Pay Period 2",
                        ),
                        rx.recharts.x_axis(data_key="Metric"),
                        rx.recharts.y_axis(),
                        rx.recharts.cartesian_grid(stroke_dasharray="3 3"),
                        rx.recharts.legend(),
                        rx.recharts.graphing_tooltip(),
                        data=[{
                            "Metric": "CT (hrs)",
                            "PP1": BidLineState.pp1_ct_mean,
                            "PP2": BidLineState.pp2_ct_mean,
                        }],
                        width="100%",
                        height=250,
                    ),
                    flex="1",
                    min_width="250px",
                    max_width="420px",
                ),

                # BT comparison
                rx.box(
                    rx.heading("Block Time (BT)", size="4", margin_bottom="3", weight="bold"),
                    rx.recharts.bar_chart(
                        rx.recharts.bar(
                            data_key="PP1",
                            fill=rx.color("cyan", 7),
                            stroke=Colors.navy_700,
                            stroke_width=1,
                            name="Pay Period 1",
                        ),
                        rx.recharts.bar(
                            data_key="PP2",
                            fill=rx.color("cyan", 9),
                            stroke=Colors.navy_700,
                            stroke_width=1,
                            name="Pay Period 2",
                        ),
                        rx.recharts.x_axis(data_key="Metric"),
                        rx.recharts.y_axis(),
                        rx.recharts.cartesian_grid(stroke_dasharray="3 3"),
                        rx.recharts.legend(),
                        rx.recharts.graphing_tooltip(),
                        data=[{
                            "Metric": "BT (hrs)",
                            "PP1": BidLineState.pp1_bt_mean,
                            "PP2": BidLineState.pp2_bt_mean,
                        }],
                        width="100%",
                        height=250,
                    ),
                    flex="1",
                    min_width="250px",
                    max_width="420px",
                ),

                # DO comparison
                rx.box(
                    rx.heading("Days Off (DO)", size="4", margin_bottom="3", weight="bold"),
                    rx.recharts.bar_chart(
                        rx.recharts.bar(
                            data_key="PP1",
                            fill=rx.color("green", 7),
                            stroke=Colors.navy_700,
                            stroke_width=1,
                            name="Pay Period 1",
                        ),
                        rx.recharts.bar(
                            data_key="PP2",
                            fill=rx.color("green", 9),
                            stroke=Colors.navy_700,
                            stroke_width=1,
                            name="Pay Period 2",
                        ),
                        rx.recharts.x_axis(data_key="Metric"),
                        rx.recharts.y_axis(),
                        rx.recharts.cartesian_grid(stroke_dasharray="3 3"),
                        rx.recharts.legend(),
                        rx.recharts.graphing_tooltip(),
                        data=[{
                            "Metric": "DO (days)",
                            "PP1": BidLineState.pp1_do_mean,
                            "PP2": BidLineState.pp2_do_mean,
                        }],
                        width="100%",
                        height=250,
                    ),
                    flex="1",
                    min_width="250px",
                    max_width="420px",
                ),

                # DD comparison
                rx.box(
                    rx.heading("Duty Days (DD)", size="4", margin_bottom="3", weight="bold"),
                    rx.recharts.bar_chart(
                        rx.recharts.bar(
                            data_key="PP1",
                            fill=rx.color("orange", 7),
                            stroke=Colors.navy_700,
                            stroke_width=1,
                            name="Pay Period 1",
                        ),
                        rx.recharts.bar(
                            data_key="PP2",
                            fill=rx.color("orange", 9),
                            stroke=Colors.navy_700,
                            stroke_width=1,
                            name="Pay Period 2",
                        ),
                        rx.recharts.x_axis(data_key="Metric"),
                        rx.recharts.y_axis(),
                        rx.recharts.cartesian_grid(stroke_dasharray="3 3"),
                        rx.recharts.legend(),
                        rx.recharts.graphing_tooltip(),
                        data=[{
                            "Metric": "DD (days)",
                            "PP1": BidLineState.pp1_dd_mean,
                            "PP2": BidLineState.pp2_dd_mean,
                        }],
                        width="100%",
                        height=250,
                    ),
                    flex="1",
                    min_width="250px",
                    max_width="420px",
                ),

                direction="row",
                wrap="wrap",
                spacing="4",
                width="100%",
            ),

            # Explanation note
            rx.callout.root(
                rx.callout.text(
                    "Pay period comparison shows average values for each metric across two pay periods. "
                    "Hover over bars for exact values.",
                ),
                size="1",
                color="gray",
                margin_top="3",
            ),

            spacing="4",
            width="100%",
        ),
    )


def pay_period_distribution_comparison() -> rx.Component:
    """Pay period distribution comparison section."""

    def distribution_pair(
        metric_label: str,
        data_pp1,
        data_pp2,
        x_axis_key: str,
        color_light: str,
        color_dark: str,
        y_domain,
    ) -> rx.Component:
        return rx.flex(
            _period_distribution_chart(
                f"{metric_label} – Pay Period 1",
                data_pp1,
                x_axis_key,
                color_light,
                Colors.navy_700,
                y_domain=y_domain,
            ),
            rx.cond(
                BidLineState.has_dual_pay_periods,
                _period_distribution_chart(
                    f"{metric_label} – Pay Period 2",
                    data_pp2,
                    x_axis_key,
                    color_dark,
                    Colors.navy_700,
                    y_domain=y_domain,
                ),
                rx.box(
                    rx.heading(f"{metric_label} – Pay Period 2", size="4", margin_bottom="3", weight="bold"),
                    rx.text(
                        "This bid period only provides a single pay period.",
                        size="2",
                        color=Colors.gray_700,
                    ),
                    border=f"1px dashed {Colors.gray_400}",
                    border_radius="8px",
                    padding="4",
                    flex="1",
                    min_width="300px",
                ),
            ),
            direction="row",
            wrap="wrap",
            spacing="4",
            width="100%",
        )

    return rx.cond(
        BidLineState.has_pay_periods,
        rx.vstack(
            rx.divider(margin_top="4", margin_bottom="4"),
            rx.hstack(
                rx.icon("bar-chart-big", size=24, color=rx.color("purple", 9)),
                rx.heading(
                    "Pay Period Distribution Comparisons",
                    size="5",
                    weight="bold",
                ),
                spacing="3",
                align="center",
            ),
            rx.text(
                "Side-by-side charts compare distributions for each pay period. "
                "Charts automatically hide when a pay period is unavailable.",
                size="2",
                color=Colors.gray_700,
            ),
            distribution_pair(
                "Credit Time (CT)",
                BidLineState.ct_distribution_pp1,
                BidLineState.ct_distribution_pp2,
                "Range",
                rx.color("blue", 7),
                rx.color("blue", 9),
                BidLineState.ct_distribution_y_domain,
            ),
            distribution_pair(
                "Block Time (BT)",
                BidLineState.bt_distribution_pp1,
                BidLineState.bt_distribution_pp2,
                "Range",
                rx.color("cyan", 7),
                rx.color("cyan", 9),
                BidLineState.bt_distribution_y_domain,
            ),
            distribution_pair(
                "Days Off (DO)",
                BidLineState.do_distribution_pp1,
                BidLineState.do_distribution_pp2,
                "Days",
                rx.color("green", 7),
                rx.color("green", 9),
                BidLineState.do_distribution_y_domain,
            ),
            distribution_pair(
                "Duty Days (DD)",
                BidLineState.dd_distribution_pp1,
                BidLineState.dd_distribution_pp2,
                "Days",
                rx.color("orange", 7),
                rx.color("orange", 9),
                BidLineState.dd_distribution_y_domain,
            ),
            spacing="5",
            width="100%",
        ),
        rx.fragment(),
    )


def charts_component() -> rx.Component:
    """Distribution charts component.

    Displays interactive bar charts showing the distribution of:
    - Credit Time (CT) in 10-hour bins
    - Block Time (BT) in 10-hour bins
    - Days Off (DO) by discrete values
    - Duty Days (DD) by discrete values

    Optionally includes pay period comparison charts when pay period data is available.
    Only shown when results are available.

    Returns:
        rx.Component: Complete charts section
    """
    return rx.cond(
        BidLineState.has_results,
        rx.card(
            rx.vstack(
                # Main section header
                rx.hstack(
                    rx.icon("bar-chart-2", size=24, color=rx.color("blue", 9)),
                    rx.heading(
                        "Distribution Charts",
                        size="6",
                        weight="bold",
                    ),
                    spacing="3",
                    align="center",
                ),

                # Distribution charts grid (2x2 responsive layout)
                rx.flex(
                    # CT distribution
                    distribution_chart(
                        "Credit Time (CT) Distribution",
                        BidLineState.ct_distribution_data,
                        "Range",
                        "Count",
                        rx.color("blue", 7),
                        Colors.navy_700,
                    ),

                    # BT distribution
                    distribution_chart(
                        "Block Time (BT) Distribution",
                        BidLineState.bt_distribution_data,
                        "Range",
                        "Count",
                        rx.color("cyan", 7),
                        Colors.navy_700,
                    ),

                    # DO distribution
                    distribution_chart(
                        "Days Off (DO) Distribution",
                        BidLineState.do_distribution_data,
                        "Days",
                        "Count",
                        rx.color("green", 7),
                        Colors.navy_700,
                    ),

                    # DD distribution
                    distribution_chart(
                        "Duty Days (DD) Distribution",
                        BidLineState.dd_distribution_data,
                        "Days",
                        "Count",
                        rx.color("orange", 7),
                        Colors.navy_700,
                    ),

                    direction="row",
                    wrap="wrap",
                    spacing="4",
                    width="100%",
                ),

                # Info callout
                rx.callout.root(
                    rx.callout.text(
                        "Interactive charts show the distribution of bid line metrics. "
                        "CT and BT are grouped in 10-hour ranges. DO and DD show exact day counts. "
                        "Hover over bars for details.",
                    ),
                    size="1",
                    color="gray",
                    margin_top="3",
                ),

                # Pay period comparison (conditional)
                pay_period_comparison_charts(),
                pay_period_distribution_comparison(),

                spacing="6",
                width="100%",
            ),
            size="4",
            width="100%",
        ),
    )
