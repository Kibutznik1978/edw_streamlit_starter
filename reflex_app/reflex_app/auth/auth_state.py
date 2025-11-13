"""Authentication state management for Reflex application."""

import reflex as rx
from typing import Optional
from supabase import Client
from .session import JWTSession
from ..config.auth_config import auth_config


class AuthState(rx.State):
    """Authentication state management."""

    # Authentication state
    is_authenticated: bool = False
    user_id: str = ""
    user_email: str = ""
    user_role: str = "user"
    jwt_token: str = ""
    jwt_expires_at: str = ""

    # Login form
    login_email: str = ""
    login_password: str = ""
    remember_me: bool = False

    # Error/success messages
    error_message: str = ""
    success_message: str = ""

    # Loading state
    is_loading: bool = False

    # Theme state
    is_dark_mode: bool = False

    def toggle_theme(self):
        """Toggle dark mode and persist preference."""
        self.is_dark_mode = not self.is_dark_mode
        # Apply theme via client-side script
        return rx.call_script(
            f"""
            const isDark = {str(self.is_dark_mode).lower()};
            if (isDark) {{
                document.documentElement.classList.add('dark');
            }} else {{
                document.documentElement.classList.remove('dark');
            }}
            localStorage.setItem('theme', isDark ? 'dark' : 'light');
            """
        )

    def on_load(self):
        """Called when page loads - restore session and theme from storage."""
        # TODO: Cookie persistence - requires proper Reflex cookie API
        # Temporarily disabled to test login flow
        # See: https://reflex.dev/docs/api-reference/state/#cookies

        # Load theme preference from localStorage
        return rx.call_script(
            """
            const theme = localStorage.getItem('theme') || 'light';
            const isDark = theme === 'dark';
            if (isDark) {
                document.documentElement.classList.add('dark');
            } else {
                document.documentElement.classList.remove('dark');
            }
            """
        )

    def restore_session(self, jwt_token: str):
        """Restore user session from JWT.

        Args:
            jwt_token: JWT token string
        """
        self.jwt_token = jwt_token
        self.user_id = JWTSession.get_user_id(jwt_token) or ""
        self.user_email = JWTSession.get_user_email(jwt_token) or ""
        self.user_role = JWTSession.get_user_role(jwt_token)

        exp_time = JWTSession.get_expiration_time(jwt_token)
        if exp_time:
            self.jwt_expires_at = exp_time.strftime("%Y-%m-%d %H:%M:%S")

        self.is_authenticated = True

    async def login(self):
        """Login with Supabase Auth."""
        from ..database.client import get_supabase_client

        self.error_message = ""
        self.success_message = ""
        self.is_loading = True

        try:
            if not self.login_email or not self.login_password:
                self.error_message = "Please enter email and password"
                self.is_loading = False
                return

            # Authenticate with Supabase
            client = get_supabase_client()
            response = client.auth.sign_in_with_password({
                "email": self.login_email,
                "password": self.login_password
            })

            if response.user:
                # Extract JWT
                jwt_token = response.session.access_token

                # Restore session
                self.restore_session(jwt_token)

                # Set cookie
                max_age = (auth_config.remember_me_duration
                          if self.remember_me
                          else auth_config.cookie_max_age)

                self.success_message = f"Welcome back, {self.user_email}!"

                # Clear password (keep email for convenience)
                self.login_password = ""

                self.is_loading = False

                # TODO: Cookie persistence - implement with correct Reflex API
                # For now, session only persists during browser session
                # See: https://reflex.dev/docs/api-reference/state/#cookies

                # Redirect to main page after successful login
                return rx.redirect("/")
            else:
                self.error_message = "Login failed: No user returned"
                self.is_loading = False

        except Exception as e:
            self.error_message = f"Login failed: {str(e)}"
            self.is_loading = False

    def logout(self):
        """Logout and clear session."""
        from ..database.client import get_supabase_client

        try:
            # Sign out from Supabase
            client = get_supabase_client()
            client.auth.sign_out()
        except:
            pass  # Ignore logout errors

        # Clear state
        self.is_authenticated = False
        self.user_id = ""
        self.user_email = ""
        self.user_role = "user"
        self.jwt_token = ""
        self.jwt_expires_at = ""
        self.login_email = ""
        self.login_password = ""
        self.error_message = ""
        self.success_message = ""

        # TODO: Cookie removal - implement with correct Reflex API

    async def refresh_token_if_needed(self):
        """Refresh JWT if nearing expiration."""
        from ..database.client import get_supabase_client

        if not self.jwt_token:
            return

        if JWTSession.needs_refresh(
            self.jwt_token,
            auth_config.jwt_refresh_threshold
        ):
            try:
                client = get_supabase_client()
                response = client.auth.refresh_session()

                if response.session:
                    jwt_token = response.session.access_token
                    self.restore_session(jwt_token)

                    # TODO: Cookie update - implement with correct Reflex API
                    pass
            except Exception as e:
                print(f"Token refresh failed: {e}")
                # If refresh fails, logout
                return self.logout()

    def get_authenticated_client(self) -> Optional[Client]:
        """Get Supabase client with JWT authentication.

        Returns:
            Authenticated Supabase client or None
        """
        from ..database.client import get_supabase_client

        if not self.is_authenticated or not self.jwt_token:
            return None
        return get_supabase_client(self.jwt_token)
