"""Aero Crew Data Analyzer - Main Reflex Application.

This is the main entry point for the Reflex version of the application.
Migration from Streamlit is in progress - see /docs/REFLEX_MIGRATION_*.md for details.
"""

import reflex as rx
from .auth.auth_state import AuthState
from .auth.components import login_page, navbar, unauthorized_page
from .database.base_state import DatabaseState
from .edw.components import upload_component, header_component, summary_component, charts_component, filters_component, details_component, table_component, downloads_component
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

        # Header information display
        header_component(),

        # Results summary display
        summary_component(),

        # Duty day distribution charts
        charts_component(),

        # Advanced filtering controls
        filters_component(),

        # Trip details viewer - temporarily disabled due to Reflex 0.8.18 type inference issues
        # TODO: Fix nested foreach and dynamic property access in details component
        # details_component(),
        rx.cond(
            EDWState.has_results,
            rx.callout.root(
                rx.callout.text(
                    "Trip Details Viewer temporarily disabled - fixing Reflex 0.8.18 compatibility",
                ),
                icon="info",
                color="amber",
            ),
            rx.fragment(),
        ),

        # Trip records table
        table_component(),

        # Downloads component (Excel and PDF exports)
        downloads_component(),

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
        rx.callout.root(
            rx.callout.text(
                "Phase 3 Implementation - Coming in Weeks 7-9",
            ),
            icon="construction",
            color="amber",
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
        rx.callout.root(
            rx.callout.text(
                "Phase 4 Implementation - Coming in Weeks 10-11",
            ),
            icon="construction",
            color="amber",
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
        rx.callout.root(
            rx.callout.text(
                "Phase 4 Implementation - Coming in Weeks 10-11",
            ),
            icon="construction",
            color="amber",
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
                    rx.callout.root(
                        rx.callout.text(
                            f"Logged in as {AppState.user_email}",
                        ),
                        icon="circle-check",
                        color="green",
                    ),
                    rx.callout.root(
                        rx.callout.text(
                            "Some features require authentication. Please login to access all functionality.",
                        ),
                        icon="info",
                        color="blue",
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
