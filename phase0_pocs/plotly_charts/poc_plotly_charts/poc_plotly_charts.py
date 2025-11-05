"""POC: Plotly Charts in Reflex.

This POC tests Plotly chart embedding and interactivity in Reflex.

Critical Requirements:
1. Render bar, pie, and radar charts (used heavily in app)
2. Interactive hover/zoom functionality
3. Responsive sizing for mobile
4. Export as images for PDF reports

Success Criteria:
✅ Plotly charts render correctly
✅ Hover tooltips work
✅ Zoom/pan interactions work
✅ Charts resize responsively
✅ Can export to static images

Risk: 🟢 LOW - Plotly is officially supported in Reflex
"""

import reflex as rx
import plotly.graph_objects as go
import plotly.express as px


class PlotlyChartsState(rx.State):
    """State for Plotly charts POC."""
    pass


# Sample data (static, not in state)
DUTY_DAY_DATA = {
    "0-5 hours": 45,
    "5-10 hours": 78,
    "10-15 hours": 92,
    "15-20 hours": 35,
    "20+ hours": 12,
}

EDW_DATA = {"EDW Trips": 85, "Non-EDW Trips": 115}

WEIGHTED_METRICS = {
    "Trip-weighted": 42.5,
    "TAFB-weighted": 38.7,
    "Duty-day-weighted": 45.2,
}


def create_bar_chart() -> go.Figure:
    """Create duty day distribution bar chart."""
    categories = list(DUTY_DAY_DATA.keys())
    values = list(DUTY_DAY_DATA.values())

    fig = go.Figure(
        data=[
            go.Bar(
                x=categories,
                y=values,
                marker=dict(color="#1f77b4"),
                text=values,
                textposition="outside",
            )
        ]
    )

    fig.update_layout(
        title="Duty Day Length Distribution",
        xaxis_title="Duty Day Length",
        yaxis_title="Count",
        height=400,
        template="plotly_white",
    )

    return fig


def create_pie_chart() -> go.Figure:
    """Create EDW vs Non-EDW pie chart."""
    labels = list(EDW_DATA.keys())
    values = list(EDW_DATA.values())

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                marker=dict(colors=["#ff7f0e", "#2ca02c"]),
                textinfo="label+percent",
                hovertemplate="<b>%{label}</b><br>%{value} trips<br>%{percent}<extra></extra>",
            )
        ]
    )

    fig.update_layout(
        title="EDW Trip Distribution",
        height=400,
    )

    return fig


def create_radar_chart() -> go.Figure:
    """Create weighted EDW metrics radar chart."""
    categories = list(WEIGHTED_METRICS.keys())
    values = list(WEIGHTED_METRICS.values())

    fig = go.Figure(
        data=[
            go.Scatterpolar(
                r=values,
                theta=categories,
                fill="toself",
                marker=dict(color="#d62728"),
            )
        ]
    )

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 50],
            )
        ),
        title="Weighted EDW Metrics",
        height=400,
    )

    return fig


def index() -> rx.Component:
    """Main POC page."""
    return rx.container(
        rx.vstack(
            # Header
            rx.heading("POC 3: Plotly Charts Integration", size="9"),
            rx.text("Testing Plotly chart rendering and interactivity", color="gray"),
            rx.divider(),

            # Instructions
            rx.box(
                rx.vstack(
                    rx.heading("Test Instructions", size="6"),
                    rx.unordered_list(
                        rx.list_item("Hover over chart elements to see tooltips"),
                        rx.list_item("Try zoom/pan on bar chart"),
                        rx.list_item("Resize browser window to test responsiveness"),
                        rx.list_item("Check all three chart types render correctly"),
                    ),
                ),
                background_color="lightblue",
                padding="4",
                border_radius="8px",
            ),

            # Bar chart
            rx.box(
                rx.heading("Bar Chart - Duty Day Distribution", size="6"),
                rx.plotly(data=create_bar_chart()),
                width="100%",
            ),

            # Pie chart
            rx.box(
                rx.heading("Pie Chart - EDW vs Non-EDW", size="6"),
                rx.plotly(data=create_pie_chart()),
                width="100%",
            ),

            # Radar chart
            rx.box(
                rx.heading("Radar Chart - Weighted Metrics", size="6"),
                rx.plotly(data=create_radar_chart()),
                width="100%",
            ),

            # POC Results
            rx.divider(),
            rx.box(
                rx.vstack(
                    rx.heading("POC Results", size="6"),
                    rx.text("🔍 TO TEST:", font_weight="bold"),
                    rx.text("✅ Plotly charts render in Reflex"),
                    rx.text("✅ Hover tooltips functional"),
                    rx.text("✅ Zoom/pan interactions work"),
                    rx.text("⏳ Test responsive behavior on mobile"),
                    rx.text("⏳ Validate export to static images for PDF"),
                    rx.text(""),
                    rx.text("Expected Outcome:", font_weight="bold"),
                    rx.text(
                        "✅ LOW RISK - Plotly officially supported, should work as-is",
                        color="green",
                    ),
                ),
                background_color="lightgray",
                padding="4",
                border_radius="8px",
            ),

            spacing="4",
            width="100%",
        ),
        max_width="1200px",
        padding="8",
    )


# Create POC app with light mode theme
app = rx.App(
    theme=rx.theme(
        appearance="light",
        has_background=True,
        radius="large",
        accent_color="blue",
    )
)
app.add_page(index, route="/", title="POC 3: Plotly Charts")
