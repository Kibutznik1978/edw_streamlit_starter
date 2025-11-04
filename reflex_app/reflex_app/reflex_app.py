"""Aero Crew Data Analyzer - Main Reflex Application.

This is the main entry point for the Reflex version of the application.
Migration from Streamlit is in progress - see /docs/REFLEX_MIGRATION_*.md for details.
"""

import reflex as rx


class State(rx.State):
    """Main application state."""

    # Tab state
    current_tab: str = "edw_analyzer"

    # User authentication state
    is_authenticated: bool = False
    user_email: str = ""
    user_role: str = ""


def navbar() -> rx.Component:
    """Application navigation bar with branding."""
    return rx.hstack(
        rx.heading("Aero Crew Data Analyzer", size="lg"),
        rx.spacer(),
        rx.cond(
            State.is_authenticated,
            rx.hstack(
                rx.text(f"Welcome, {State.user_email}"),
                rx.button("Logout", on_click=lambda: None),  # TODO: Implement logout
            ),
            rx.button("Login", on_click=lambda: None),  # TODO: Implement login
        ),
        padding="1rem",
        background_color="navy",
        color="white",
        width="100%",
    )


def edw_analyzer_tab() -> rx.Component:
    """EDW Pairing Analyzer tab (Tab 1)."""
    return rx.vstack(
        rx.heading("EDW Pairing Analyzer", size="md"),
        rx.text("Analyzes pairings PDF to identify Early/Day/Window (EDW) trips"),
        rx.divider(),
        rx.text("🚧 Under Construction - Phase 2 (Weeks 4-6)"),
        padding="2rem",
        width="100%",
    )


def bid_line_analyzer_tab() -> rx.Component:
    """Bid Line Analyzer tab (Tab 2)."""
    return rx.vstack(
        rx.heading("Bid Line Analyzer", size="md"),
        rx.text("Parses bid line PDFs for scheduling metrics (CT, BT, DO, DD)"),
        rx.divider(),
        rx.text("🚧 Under Construction - Phase 3 (Weeks 7-9)"),
        padding="2rem",
        width="100%",
    )


def database_explorer_tab() -> rx.Component:
    """Database Explorer tab (Tab 3)."""
    return rx.vstack(
        rx.heading("Database Explorer", size="md"),
        rx.text("Query historical data with multi-dimensional filters"),
        rx.divider(),
        rx.text("🚧 Under Construction - Phase 4 (Weeks 10-11)"),
        padding="2rem",
        width="100%",
    )


def historical_trends_tab() -> rx.Component:
    """Historical Trends tab (Tab 4)."""
    return rx.vstack(
        rx.heading("Historical Trends", size="md"),
        rx.text("Database-powered trend analysis and visualizations"),
        rx.divider(),
        rx.text("🚧 Under Construction - Phase 4 (Weeks 10-11)"),
        padding="2rem",
        width="100%",
    )


def index() -> rx.Component:
    """Main application page with tab navigation."""
    return rx.fragment(
        navbar(),
        rx.container(
            rx.vstack(
                rx.heading("Airline Bid Packet Analysis Tool", size="xl", padding="1rem"),
                rx.tabs.root(
                    rx.tabs.list(
                        rx.tabs.trigger("EDW Pairing Analyzer", value="edw_analyzer"),
                        rx.tabs.trigger("Bid Line Analyzer", value="bid_line_analyzer"),
                        rx.tabs.trigger("Database Explorer", value="database_explorer"),
                        rx.tabs.trigger("Historical Trends", value="historical_trends"),
                    ),
                    rx.tabs.content(
                        edw_analyzer_tab(),
                        value="edw_analyzer",
                    ),
                    rx.tabs.content(
                        bid_line_analyzer_tab(),
                        value="bid_line_analyzer",
                    ),
                    rx.tabs.content(
                        database_explorer_tab(),
                        value="database_explorer",
                    ),
                    rx.tabs.content(
                        historical_trends_tab(),
                        value="historical_trends",
                    ),
                    default_value="edw_analyzer",
                    on_change=State.set_current_tab,
                ),
                width="100%",
            ),
            max_width="1400px",
            padding="2rem",
        ),
    )


# Create the app
app = rx.App()
app.add_page(index, route="/", title="Aero Crew Data Analyzer")
