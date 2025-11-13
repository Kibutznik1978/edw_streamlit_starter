"""Authentication UI components for Reflex application."""

import reflex as rx
from .auth_state import AuthState
from ..theme import Colors, Spacing, Shadows


def login_page() -> rx.Component:
    """Login page with form.

    Returns:
        Login page component
    """
    return rx.fragment(
        # Load theme immediately to prevent flash
        rx.script("""
            (function() {
                const theme = localStorage.getItem('theme') || 'light';
                if (theme === 'dark') {
                    document.documentElement.classList.add('dark');
                }
            })();
        """),
        rx.container(
            rx.vstack(
                rx.heading("Aero Crew Data Analyzer", size="9", margin_bottom="2"),
                rx.text(
                    "Login to access your bid analysis tools",
                    size="4",
                    color="gray",
                    margin_bottom="8"
                ),

                # Error message
                rx.cond(
                    AuthState.error_message != "",
                    rx.callout.root(
                        rx.callout.text(AuthState.error_message),
                        color="red",
                        role="alert",
                        margin_bottom="4",
                    ),
                ),

                # Success message
                rx.cond(
                    AuthState.success_message != "",
                    rx.callout.root(
                        rx.callout.text(AuthState.success_message),
                        color="green",
                        role="status",
                        margin_bottom="4",
                    ),
                ),

                # Login form
                rx.card(
                    rx.vstack(
                        rx.text("Email", weight="bold", size="2"),
                        rx.input(
                            placeholder="your.email@example.com",
                            value=AuthState.login_email,
                            on_change=AuthState.set_login_email,
                            type="email",
                            size="3",
                            width="100%",
                        ),
                        rx.text("Password", weight="bold", size="2", margin_top="4"),
                        rx.input(
                            placeholder="Enter your password",
                            value=AuthState.login_password,
                            on_change=AuthState.set_login_password,
                            type="password",
                            size="3",
                            width="100%",
                        ),
                        rx.checkbox(
                            "Remember me for 7 days",
                            checked=AuthState.remember_me,
                            on_change=AuthState.set_remember_me,
                            margin_top="4",
                        ),
                        rx.button(
                            "Login",
                            on_click=AuthState.login,
                            loading=AuthState.is_loading,
                            size="3",
                            width="100%",
                            margin_top="6",
                            cursor="pointer",
                            style={
                                "transition": "all 150ms ease",
                                "_hover": {
                                    "transform": "translateY(-1px)",
                                },
                            },
                        ),
                        spacing="2",
                        width="100%",
                    ),
                    size="4",
                ),

                spacing="4",
                width="100%",
                max_width="400px",
                margin_top="8",
            ),
            padding="8",
            center_content=True,
        ),
        on_mount=AuthState.on_load,
    )


def navbar() -> rx.Component:
    """Navigation bar with authentication controls.

    Returns:
        Navbar component with logo, theme toggle, and user menu
    """
    # Import at function level to avoid circular imports
    from ..reflex_app import AppState

    return rx.box(
        rx.hstack(
            # Hamburger menu button (always visible)
            rx.icon_button(
                rx.icon("menu", size=24),
                on_click=AppState.toggle_sidebar,
                variant="ghost",
                cursor="pointer",
            ),

            rx.spacer(),

            # Right side - Theme toggle and user controls
            rx.hstack(
                # Dark mode toggle button (always visible)
                rx.icon_button(
                    rx.icon(
                        rx.cond(AuthState.is_dark_mode, "moon", "sun"),
                        size=20,
                    ),
                    on_click=AuthState.toggle_theme,
                    variant="ghost",
                    cursor="pointer",
                    color_scheme="gray",
                    title=rx.cond(AuthState.is_dark_mode, "Switch to Light Mode", "Switch to Dark Mode"),
                ),

                # Conditional user controls or login button
                rx.cond(
                    AuthState.is_authenticated,
                    rx.hstack(
                        # Admin badge (if admin)
                        rx.cond(
                            AuthState.user_role == "admin",
                            rx.badge("Admin", color_scheme="purple", size="2"),
                        ),

                        # User menu dropdown
                        rx.menu.root(
                            rx.menu.trigger(
                                rx.button(
                                    rx.hstack(
                                        rx.icon("user", size=18),
                                        rx.text(AuthState.user_email, size="2"),
                                        rx.icon("chevron-down", size=16),
                                        spacing="2",
                                        align="center",
                                    ),
                                    variant="ghost",
                                    cursor="pointer",
                                )
                            ),
                            rx.menu.content(
                                rx.menu.item(
                                    rx.hstack(
                                        rx.icon("user", size=16),
                                        rx.text("Profile"),
                                        spacing="2",
                                        align="center",
                                    ),
                                ),
                                rx.menu.item(
                                    rx.hstack(
                                        rx.icon("settings", size=16),
                                        rx.text("Settings"),
                                        spacing="2",
                                        align="center",
                                    ),
                                ),
                                rx.menu.separator(),
                                rx.menu.item(
                                    rx.hstack(
                                        rx.icon("log-out", size=16),
                                        rx.text("Logout"),
                                        spacing="2",
                                        align="center",
                                    ),
                                    on_click=AuthState.logout,
                                    color=Colors.error,
                                ),
                            ),
                        ),

                        spacing="3",
                        align="center",
                    ),
                    rx.button(
                        "Login",
                        on_click=lambda: rx.redirect("/login"),
                        variant="soft",
                        cursor="pointer",
                    ),
                ),

                spacing="3",
                align="center",
            ),

            width="100%",
            align="center",
        ),

        # Navbar container styling
        background=Colors.bg_primary,
        border_bottom=f"1px solid {Colors.gray_200}",
        box_shadow=Shadows.sm,
        padding="6",
        width="100%",
    )


def unauthorized_page() -> rx.Component:
    """Page shown when user lacks required role.

    Returns:
        Unauthorized page component
    """
    return rx.container(
        rx.vstack(
            rx.heading("Unauthorized", size="9", color="red"),
            rx.text(
                "You don't have permission to access this page.",
                size="5",
                margin_top="4",
            ),
            rx.text(
                f"Your current role: {AuthState.user_role}",
                size="3",
                color="gray",
                margin_top="2",
            ),
            rx.button(
                "Go to Home",
                on_click=lambda: rx.redirect("/"),
                size="3",
                margin_top="6",
                cursor="pointer",
                style={
                    "transition": "all 150ms ease",
                    "_hover": {
                        "transform": "translateY(-1px)",
                    },
                },
            ),
            spacing="4",
            align="center",
            margin_top="8",
        ),
        padding="8",
        center_content=True,
    )


def protected_page_wrapper(content: rx.Component, title: str = "Protected Page") -> rx.Component:
    """Wrapper for protected pages with navbar.

    Args:
        content: Page content component
        title: Page title

    Returns:
        Protected page with navbar
    """
    return rx.fragment(
        navbar(),
        rx.container(
            rx.vstack(
                rx.heading(title, size="8", margin_bottom="6"),
                content,
                width="100%",
            ),
            max_width="1400px",
            padding="8",
        ),
        on_mount=AuthState.on_load,
    )
