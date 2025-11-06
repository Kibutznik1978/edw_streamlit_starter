"""Aero Crew Data Analyzer - Main Reflex Application.

This is the main entry point for the Reflex version of the application.
Migration from Streamlit is in progress - see /docs/REFLEX_MIGRATION_*.md for details.
"""

import reflex as rx
from .auth.auth_state import AuthState
from .auth.components import login_page, navbar, unauthorized_page
from .database.base_state import DatabaseState
from .edw.components import upload_component
from .edw.edw_state import EDWState


class AppState(DatabaseState):
    """Main application state.

    Extends DatabaseState which provides:
    - Authentication (from AuthState)
    - Database CRUD operations (from DatabaseState)
    """

    # Tab state
    current_tab: str = "edw_analyzer"


def edw_analyzer_tab() -> rx.Component:
    """EDW Pairing Analyzer tab (Tab 1)."""
    return rx.vstack(
        rx.heading("EDW Pairing Analyzer", size="8"),
        rx.text(
            "Analyzes pairings PDF to identify Early/Day/Window (EDW) trips",
            size="4",
            color="gray"
        ),
        rx.divider(),

        # Upload component
        upload_component(),

        # TODO: Add header display component (Task 3.3)
        # TODO: Add results display components (Task 3.4)
        # TODO: Add duty day distribution charts (Task 3.5)
        # TODO: Add filtering UI (Task 3.6)
        # TODO: Add trip details viewer (Task 3.7)
        # TODO: Add trip records table (Task 3.8)

        spacing="4",
        padding="8",
        width="100%",
    )


def bid_line_analyzer_tab() -> rx.Component:
    """Bid Line Analyzer tab (Tab 2)."""
    return rx.vstack(
        rx.heading("Bid Line Analyzer", size="8"),
        rx.text(
            "Parses bid line PDFs for scheduling metrics (CT, BT, DO, DD)",
            size="4",
            color="gray"
        ),
        rx.divider(),
        rx.callout(
            "Phase 3 Implementation - Coming in Weeks 7-9",
            icon="construction",
            color_scheme="amber",
        ),
        spacing="4",
        padding="8",
        width="100%",
    )


def database_explorer_tab() -> rx.Component:
    """Database Explorer tab (Tab 3)."""
    return rx.vstack(
        rx.heading("Database Explorer", size="8"),
        rx.text(
            "Query historical data with multi-dimensional filters",
            size="4",
            color="gray"
        ),
        rx.divider(),
        rx.callout(
            "Phase 4 Implementation - Coming in Weeks 10-11",
            icon="construction",
            color_scheme="amber",
        ),
        spacing="4",
        padding="8",
        width="100%",
    )


def historical_trends_tab() -> rx.Component:
    """Historical Trends tab (Tab 4)."""
    return rx.vstack(
        rx.heading("Historical Trends", size="8"),
        rx.text(
            "Database-powered trend analysis and visualizations",
            size="4",
            color="gray"
        ),
        rx.divider(),
        rx.callout(
            "Phase 4 Implementation - Coming in Weeks 10-11",
            icon="construction",
            color_scheme="amber",
        ),
        spacing="4",
        padding="8",
        width="100%",
    )


def index() -> rx.Component:
    """Main application page with tab navigation."""
    return rx.fragment(
        navbar(),
        rx.container(
            rx.vstack(
                rx.heading("Airline Bid Packet Analysis Tool", size="9", margin_bottom="6"),

                # Authentication status indicator
                rx.cond(
                    AppState.is_authenticated,
                    rx.callout(
                        f"Logged in as {AppState.user_email}",
                        icon="circle-check",
                        color_scheme="green",
                    ),
                    rx.callout(
                        "Some features require authentication. Please login to access all functionality.",
                        icon="info",
                        color_scheme="blue",
                    ),
                ),

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
                    on_change=AppState.set_current_tab,
                ),
                spacing="6",
                width="100%",
            ),
            max_width="1400px",
            padding="8",
        ),
        on_mount=AppState.on_load,
    )


# Create the app
app = rx.App()

# Add routes
app.add_page(index, route="/", title="Aero Crew Data Analyzer")
app.add_page(login_page, route="/login", title="Login")
app.add_page(unauthorized_page, route="/unauthorized", title="Unauthorized")
