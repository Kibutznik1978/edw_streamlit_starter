"""Authentication UI components for Reflex application."""

import reflex as rx
from .auth_state import AuthState


def login_page() -> rx.Component:
    """Login page with form.

    Returns:
        Login page component
    """
    return rx.fragment(
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
                    rx.callout(
                        AuthState.error_message,
                        color_scheme="red",
                        role="alert",
                        margin_bottom="4",
                    ),
                ),

                # Success message
                rx.cond(
                    AuthState.success_message != "",
                    rx.callout(
                        AuthState.success_message,
                        color_scheme="green",
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
        Navbar component
    """
    return rx.box(
        rx.hstack(
            rx.heading("Aero Crew Data Analyzer", size="7"),
            rx.spacer(),
            rx.cond(
                AuthState.is_authenticated,
                rx.hstack(
                    rx.badge(
                        AuthState.user_email,
                        color_scheme="blue",
                        size="2",
                    ),
                    rx.cond(
                        AuthState.user_role == "admin",
                        rx.badge("Admin", color_scheme="purple", size="2"),
                    ),
                    rx.button(
                        "Logout",
                        on_click=AuthState.logout,
                        variant="soft",
                        color_scheme="gray",
                    ),
                    spacing="3",
                ),
                rx.button(
                    "Login",
                    on_click=lambda: rx.redirect("/login"),
                    variant="soft",
                ),
            ),
            width="100%",
            padding="4",
        ),
        background_color="var(--accent-2)",
        border_bottom="1px solid var(--gray-6)",
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
