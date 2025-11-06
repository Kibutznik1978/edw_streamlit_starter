"""Protected route decorators for Reflex application."""

import reflex as rx
from typing import Callable
from .auth_state import AuthState


def require_auth(page_function: Callable) -> Callable:
    """Decorator to protect routes requiring authentication.

    Args:
        page_function: Page function to protect

    Returns:
        Wrapped function that checks authentication

    Example:
        @require_auth
        def protected_page() -> rx.Component:
            return rx.text("Protected content")
    """

    def wrapper() -> rx.Component:
        """Wrapper that checks authentication before rendering page."""
        return rx.cond(
            AuthState.is_authenticated,
            page_function(),
            rx.redirect("/login")
        )

    return wrapper


def require_role(role: str):
    """Decorator to protect routes requiring specific role.

    Args:
        role: Required role (e.g., "admin")

    Returns:
        Decorator function

    Example:
        @require_role("admin")
        def admin_page() -> rx.Component:
            return rx.text("Admin content")
    """

    def decorator(page_function: Callable) -> Callable:
        def wrapper() -> rx.Component:
            return rx.cond(
                AuthState.is_authenticated & (AuthState.user_role == role),
                page_function(),
                rx.cond(
                    AuthState.is_authenticated,
                    rx.redirect("/unauthorized"),  # Logged in but wrong role
                    rx.redirect("/login")  # Not logged in
                )
            )
        return wrapper
    return decorator


# Convenience decorators
require_admin = require_role("admin")
