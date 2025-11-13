"""Sidebar navigation component."""
import reflex as rx
from ...theme import Colors
from ...auth.auth_state import AuthState


def nav_item(label: str, icon_name: str, tab_value: str, current_tab: str, on_click_handler) -> rx.Component:
    """Navigation item with active state.

    Args:
        label: Display text for the navigation item
        icon_name: Reflex icon name (e.g., "home", "plane")
        tab_value: Value to set when clicked (matches AppState.current_tab)
        current_tab: Current active tab value
        on_click_handler: Event handler for navigation (AppState.set_current_tab)

    Returns:
        Navigation item component
    """
    is_active = current_tab == tab_value

    return rx.box(
        rx.hstack(
            rx.icon(icon_name, size=20),
            rx.text(label, size="3", weight="medium"),
            spacing="2",
            align="center",
            width="100%",
        ),
        padding="3",
        border_radius="8px",
        width="100%",
        background=rx.cond(is_active, Colors.navy_100, "transparent"),
        color=rx.cond(is_active, Colors.navy_700, Colors.gray_700),
        border_left=rx.cond(is_active, f"3px solid {Colors.navy_600}", "3px solid transparent"),
        cursor="pointer",
        transition="all 150ms ease",
        _hover={
            "background": rx.cond(is_active, Colors.navy_100, Colors.gray_100),
        },
        on_click=lambda: on_click_handler(tab_value),
    )


def sidebar(current_tab: str, on_click_handler, is_open: bool, toggle_handler) -> rx.Component:
    """Main sidebar navigation with responsive behavior.

    Args:
        current_tab: Current active tab value
        on_click_handler: Event handler for navigation (AppState.set_current_tab)
        is_open: Whether sidebar is open (for mobile responsiveness)
        toggle_handler: Event handler to toggle sidebar (AppState.toggle_sidebar)

    Returns:
        Sidebar component with navigation items
    """
    return rx.box(
        rx.vstack(
            # Mobile header with close button
            rx.box(
                rx.hstack(
                    rx.heading("Menu", size="5", weight="medium", color=Colors.gray_700),
                    rx.spacer(),
                    rx.icon_button(
                        rx.icon("x", size=24),
                        on_click=toggle_handler,
                        variant="ghost",
                        cursor="pointer",
                        size="2",
                    ),
                    width="100%",
                    align="center",
                ),
                padding="4",
                display=["flex", "flex", "none"],  # Show on mobile/tablet, hide on desktop
            ),

            # Logo section
            rx.box(
                rx.image(
                    src="/logo-full.svg",
                    alt="Aero Crew Data logo",
                    height="80px",
                    width="auto",
                ),
                padding="6",
                display="flex",
                justify_content="center",
                align_items="center",
            ),

            rx.divider(),

            # Navigation items - wrap on_click to close sidebar on mobile
            rx.vstack(
                nav_item("Home", "home", "home", current_tab, on_click_handler),
                nav_item("Pairing Analyzer", "plane", "edw_analyzer", current_tab, on_click_handler),
                nav_item("Bid Line Analyzer", "clipboard-list", "bid_line_analyzer", current_tab, on_click_handler),
                nav_item("Database Explorer", "database", "database_explorer", current_tab, on_click_handler),
                nav_item("Historical Trends", "trending-up", "historical_trends", current_tab, on_click_handler),
                spacing="1",
                padding="3",
                width="100%",
            ),

            rx.spacer(),

            # Bottom section
            rx.vstack(
                rx.divider(),

                # Dark mode toggle
                rx.box(
                    rx.hstack(
                        rx.icon(
                            rx.cond(AuthState.is_dark_mode, "moon", "sun"),
                            size=20,
                        ),
                        rx.text("Theme", size="3", weight="medium"),
                        rx.spacer(),
                        rx.switch(
                            checked=AuthState.is_dark_mode,
                            on_change=AuthState.toggle_theme,
                        ),
                        spacing="2",
                        align="center",
                        width="100%",
                    ),
                    padding="3",
                    width="100%",
                ),

                # Settings
                nav_item("Settings", "settings", "settings", current_tab, on_click_handler),

                # Authentication section
                rx.cond(
                    AuthState.is_authenticated,
                    # Logged in - show user info and logout
                    rx.vstack(
                        rx.divider(),

                        # User info section
                        rx.box(
                            rx.vstack(
                                rx.hstack(
                                    rx.icon("user", size=20, color=Colors.navy_600),
                                    rx.text(
                                        AuthState.user_email,
                                        size="2",
                                        weight="medium",
                                        color=Colors.gray_700,
                                    ),
                                    spacing="2",
                                    align="center",
                                    width="100%",
                                ),
                                # Admin badge if admin
                                rx.cond(
                                    AuthState.user_role == "admin",
                                    rx.badge("Admin", color_scheme="purple", size="1"),
                                ),
                                spacing="2",
                                width="100%",
                            ),
                            padding="3",
                            width="100%",
                        ),

                        # Logout button
                        rx.box(
                            rx.hstack(
                                rx.icon("log-out", size=20),
                                rx.text("Logout", size="3", weight="medium"),
                                spacing="2",
                                align="center",
                                width="100%",
                            ),
                            padding="3",
                            border_radius="8px",
                            width="100%",
                            color=Colors.error,
                            cursor="pointer",
                            transition="all 150ms ease",
                            _hover={
                                "background": Colors.gray_100,
                            },
                            on_click=AuthState.logout,
                        ),

                        spacing="1",
                        width="100%",
                    ),
                    # Not logged in - show login button
                    rx.vstack(
                        rx.divider(),
                        rx.box(
                            rx.hstack(
                                rx.icon("log-in", size=20),
                                rx.text("Login", size="3", weight="medium"),
                                spacing="2",
                                align="center",
                                width="100%",
                            ),
                            padding="3",
                            border_radius="8px",
                            width="100%",
                            background=Colors.gray_100,
                            color=Colors.gray_700,
                            border=f"1px solid {Colors.gray_300}",
                            cursor="pointer",
                            transition="all 150ms ease",
                            _hover={
                                "background": Colors.gray_200,
                                "border_color": Colors.gray_400,
                            },
                            on_click=lambda: rx.redirect("/login"),
                        ),
                        spacing="1",
                        width="100%",
                    ),
                ),

                spacing="1",
                padding="3",
                width="100%",
            ),

            spacing="0",
            height="100vh",
            width="100%",
        ),
        width="260px",
        position="fixed",
        left="0",
        top="0",
        height="100vh",
        background=Colors.gray_50,
        border_right=f"1px solid {Colors.gray_200}",
        box_shadow="0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)",
        z_index="100",
        # Use class_name for custom CSS animations
        class_name="sidebar-nav",
        # Use transform for smooth animations instead of display
        # Mobile/tablet: hidden by default (translateX(-100%)), slides in when open (translateX(0))
        # Desktop: always visible (translateX(0)) via CSS media query override
        style={
            "transform": rx.cond(
                is_open,
                "translateX(0)",  # Open state: visible
                "translateX(-100%)"  # Closed state: hidden off-screen (CSS overrides this on desktop)
            ),
            "transition": "transform 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
        },
    )
