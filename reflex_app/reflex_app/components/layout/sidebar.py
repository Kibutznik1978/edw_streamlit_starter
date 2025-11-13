"""Sidebar navigation component."""
import reflex as rx
from ...theme import Colors


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


def sidebar(current_tab: str, on_click_handler, is_open: bool) -> rx.Component:
    """Main sidebar navigation with responsive behavior.

    Args:
        current_tab: Current active tab value
        on_click_handler: Event handler for navigation (AppState.set_current_tab)
        is_open: Whether sidebar is open (for mobile responsiveness)

    Returns:
        Sidebar component with navigation items
    """
    return rx.box(
        rx.vstack(
            # Logo section
            rx.hstack(
                rx.icon("plane", size=28, color=Colors.navy_700),
                rx.text("Aero Crew", size="5", weight="bold", color=Colors.navy_800),
                spacing="2",
                padding="4",
                align="center",
            ),

            rx.divider(),

            # Navigation items
            rx.vstack(
                nav_item("Home", "home", "home", current_tab, on_click_handler),
                nav_item("EDW Analyzer", "plane", "edw_analyzer", current_tab, on_click_handler),
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
                nav_item("Settings", "settings", "settings", current_tab, on_click_handler),
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
        left=rx.cond(is_open, "0", "-260px"),  # Slide off-screen when closed
        top="0",
        height="100vh",
        background=Colors.gray_50,
        border_right=f"1px solid {Colors.gray_200}",
        box_shadow="0 1px 3px 0 rgba(0, 0, 0, 0.1)",
        z_index="100",
        transition="left 300ms ease",  # Smooth slide animation (300ms standard)
        # Always visible on desktop (md+), slide on mobile (xs/sm)
        display=["block", "block", "block"],
    )
