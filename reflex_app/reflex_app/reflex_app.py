"""Aero Crew Data Analyzer - Main Reflex Application.

This is the main entry point for the Reflex version of the application.
Migration from Streamlit is in progress - see /docs/REFLEX_MIGRATION_*.md for details.
"""

import reflex as rx
from .auth.auth_state import AuthState
from .auth.components import login_page, unauthorized_page
from .database.base_state import DatabaseState
from .edw.components import upload_component, header_component, summary_component, charts_component, filters_component, details_component, table_component, downloads_component
from .edw.edw_state import EDWState
from .theme import get_theme_config, get_global_styles, Colors
from .components.layout import sidebar


class AppState(DatabaseState):
    """Main application state.

    Extends DatabaseState which provides:
    - Authentication (from AuthState)
    - Database CRUD operations (from DatabaseState)
    """

    # Tab state
    current_tab: str = "home"

    # Sidebar state for responsive behavior
    sidebar_open: bool = False  # Default closed on mobile, CSS will keep it visible on desktop

    def set_current_tab(self, tab: str):
        """Set the current active tab and close sidebar on mobile.

        Args:
            tab: Tab identifier to switch to
        """
        self.current_tab = tab
        # Close sidebar on mobile after navigation
        # Desktop sidebar won't be affected due to CSS
        self.sidebar_open = False

    def toggle_sidebar(self):
        """Toggle sidebar visibility for mobile/tablet."""
        self.sidebar_open = not self.sidebar_open


def home_tab() -> rx.Component:
    """Home/Welcome tab."""
    return rx.vstack(
        rx.text(
            "Welcome to the Airline Bid Packet Analysis Tool",
            size="6",
            weight="medium",
            color=Colors.gray_700,
        ),
        rx.text(
            "Select a tool from the sidebar to get started.",
            size="4",
            color=Colors.gray_600,
        ),
        spacing="4",
        width="100%",
    )


def settings_tab() -> rx.Component:
    """Settings tab."""
    return rx.vstack(
        rx.callout.root(
            rx.callout.text(
                "Settings configuration - Coming soon",
            ),
            icon="settings",
            color="blue",
        ),
        spacing="4",
        width="100%",
    )


def edw_analyzer_tab() -> rx.Component:
    """Pairing Analyzer tab (Tab 1)."""
    return rx.vstack(
        # Upload component (wrapped in card)
        upload_component(),

        # Header information display (wrapped in card)
        header_component(),

        # Results summary display (wrapped in card)
        summary_component(),

        # Duty day distribution charts (wrapped in card)
        charts_component(),

        # Advanced filtering controls (wrapped in card)
        filters_component(),

        # Trip details viewer (wrapped in card)
        details_component(),

        # Trip records table (wrapped in card)
        table_component(),

        # Downloads component (wrapped in card)
        downloads_component(),

        spacing="6",  # 24px spacing between cards for visual separation
        width="100%",
    )


def bid_line_analyzer_tab() -> rx.Component:
    """Bid Line Analyzer tab (Tab 2)."""
    return rx.vstack(
        rx.callout.root(
            rx.callout.text(
                "Phase 3 Implementation - Coming in Weeks 7-9",
            ),
            icon="construction",
            color="amber",
        ),
        spacing="4",
        width="100%",
    )


def database_explorer_tab() -> rx.Component:
    """Database Explorer tab (Tab 3)."""
    return rx.vstack(
        rx.callout.root(
            rx.callout.text(
                "Phase 4 Implementation - Coming in Weeks 10-11",
            ),
            icon="construction",
            color="amber",
        ),
        spacing="4",
        width="100%",
    )


def historical_trends_tab() -> rx.Component:
    """Historical Trends tab (Tab 4)."""
    return rx.vstack(
        rx.callout.root(
            rx.callout.text(
                "Phase 4 Implementation - Coming in Weeks 10-11",
            ),
            icon="construction",
            color="amber",
        ),
        spacing="4",
        width="100%",
    )


def index() -> rx.Component:
    """Main application page with sidebar navigation."""
    return rx.fragment(
        # Load theme immediately to prevent flash of unstyled content
        rx.script("""
            (function() {
                const theme = localStorage.getItem('theme') || 'light';
                if (theme === 'dark') {
                    document.documentElement.classList.add('dark');
                }
            })();
        """),

        # Hamburger menu button for mobile (fixed position, top-right)
        # Show on mobile/tablet when sidebar is closed, hide on desktop
        rx.cond(
            ~AppState.sidebar_open,  # Only show when sidebar is closed
            rx.box(
                rx.icon_button(
                    rx.icon("menu", size=24),
                    on_click=AppState.toggle_sidebar,
                    variant="surface",  # More visible surface variant
                    cursor="pointer",
                    size="3",  # Medium size
                    color_scheme="gray",  # Gray color scheme
                ),
                position="fixed",
                top="1rem",  # 16px from top
                right="1rem",  # 16px from right
                z_index="101",  # Above sidebar (z-index 100)
                class_name="hamburger-menu-button",  # CSS class for responsive visibility
            ),
        ),

        # Overlay/backdrop for mobile when sidebar is open
        rx.cond(
            AppState.sidebar_open,
            rx.box(
                width="100vw",
                height="100vh",
                position="fixed",
                top="0",
                left="0",
                background="rgba(0, 0, 0, 0.5)",
                z_index="90",  # Below sidebar (z-index 100)
                display=["block", "block", "none"],  # Show on mobile/tablet, hide on desktop
                on_click=AppState.toggle_sidebar,
                class_name="sidebar-backdrop",
            ),
        ),

        # Sidebar navigation
        sidebar(AppState.current_tab, AppState.set_current_tab, AppState.sidebar_open, AppState.toggle_sidebar),

        rx.box(
            rx.container(
                rx.vstack(
                    # Page title and description (dynamic based on current_tab)
                    rx.match(
                        AppState.current_tab,
                        ("home", rx.heading("Home", size="8")),
                        ("edw_analyzer", rx.heading("Pairing Analyzer", size="8")),
                        ("bid_line_analyzer", rx.heading("Bid Line Analyzer", size="8")),
                        ("database_explorer", rx.heading("Database Explorer", size="8")),
                        ("historical_trends", rx.heading("Historical Trends", size="8")),
                        ("settings", rx.heading("Settings", size="8")),
                        rx.heading("Home", size="8"),  # default
                    ),
                    rx.match(
                        AppState.current_tab,
                        ("home", rx.text("Welcome to Aero Crew Data Analyzer", size="4", color=Colors.gray_600)),
                        ("edw_analyzer", rx.text("Analyzes pairings PDF to identify Early/Day/Window (EDW) trips", size="4", color=Colors.gray_600)),
                        ("bid_line_analyzer", rx.text("Parses bid line PDFs for scheduling metrics (CT, BT, DO, DD)", size="4", color=Colors.gray_600)),
                        ("database_explorer", rx.text("Query historical data with multi-dimensional filters", size="4", color=Colors.gray_600)),
                        ("historical_trends", rx.text("Database-powered trend analysis and visualizations", size="4", color=Colors.gray_600)),
                        ("settings", rx.text("Configure application preferences", size="4", color=Colors.gray_600)),
                        rx.text("Welcome to Aero Crew Data Analyzer", size="4", color=Colors.gray_600),  # default
                    ),
                    rx.divider(),

                    # Content based on current tab
                    rx.cond(
                        AppState.current_tab == "home",
                        home_tab(),
                    ),
                    rx.cond(
                        AppState.current_tab == "edw_analyzer",
                        edw_analyzer_tab(),
                    ),
                    rx.cond(
                        AppState.current_tab == "bid_line_analyzer",
                        bid_line_analyzer_tab(),
                    ),
                    rx.cond(
                        AppState.current_tab == "database_explorer",
                        database_explorer_tab(),
                    ),
                    rx.cond(
                        AppState.current_tab == "historical_trends",
                        historical_trends_tab(),
                    ),
                    rx.cond(
                        AppState.current_tab == "settings",
                        settings_tab(),
                    ),

                    spacing="6",
                    width="100%",
                ),
                max_width="1400px",
                class_name="main-content-container",  # CSS class for responsive padding
            ),
            # Content margin: always 260px on desktop (sidebar always visible)
            # On mobile: 0 (sidebar overlays content, doesn't push it)
            margin_left=["0", "0", "260px"],  # 0 on mobile/tablet, 260px on desktop
            min_height="100vh",
            background=Colors.gray_50,
            transition="margin-left 0.3s ease",
        ),
        on_mount=AppState.on_load,
    )


# Create the app with custom theme
app = rx.App(
    theme=rx.theme(**get_theme_config()),
    stylesheets=[
        "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap",
        "https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap",
        "/theme_overrides.css",  # Custom Navy/Teal/Sky color overrides for Radix UI
    ],
    style=get_global_styles(),
)

# Add routes
app.add_page(index, route="/", title="Aero Crew Data Analyzer")
app.add_page(login_page, route="/login", title="Login")
app.add_page(unauthorized_page, route="/unauthorized", title="Unauthorized")
