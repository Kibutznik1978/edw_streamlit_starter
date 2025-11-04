"""POC: JWT Authentication with Supabase in Reflex.

This POC tests JWT session handling and RLS policy enforcement in Reflex.

Critical Requirements:
1. Login with Supabase Auth (email/password)
2. JWT custom claims propagation (user_role)
3. RLS policy enforcement (admin vs regular user)
4. Session persistence across page reloads
5. Secure JWT storage

Success Criteria:
✅ Supabase login functional
✅ JWT token stored securely
✅ Custom claims accessible in state
✅ RLS policies enforced correctly
✅ Session persists on page reload

Risk: 🔴 CRITICAL - Complex JWT/RLS requirements
"""

import reflex as rx
from typing import Optional
import os


class JWTAuthState(rx.State):
    """State for JWT authentication POC."""

    # Authentication state
    is_authenticated: bool = False
    user_email: str = ""
    user_role: str = ""
    jwt_token: str = ""

    # Login form
    email_input: str = ""
    password_input: str = ""

    # Error handling
    error_message: str = ""
    success_message: str = ""

    # RLS test results
    can_query_all_data: bool = False
    can_query_own_data: bool = False

    async def login(self):
        """Login with Supabase Auth."""
        self.error_message = ""
        self.success_message = ""

        try:
            # TODO: Integrate actual Supabase client
            # from supabase import create_client
            # supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_ANON_KEY"))
            # response = supabase.auth.sign_in_with_password({
            #     "email": self.email_input,
            #     "password": self.password_input
            # })

            # Simulate successful login for POC
            if self.email_input and self.password_input:
                self.is_authenticated = True
                self.user_email = self.email_input
                self.user_role = "admin" if self.email_input == "giladswerdlow@gmail.com" else "user"
                self.jwt_token = "[Simulated JWT Token]"
                self.success_message = f"✅ Logged in as {self.user_email} (role: {self.user_role})"

                # Test RLS policies
                await self.test_rls_policies()
            else:
                self.error_message = "Please enter email and password"

        except Exception as e:
            self.error_message = f"Login failed: {str(e)}"

    async def test_rls_policies(self):
        """Test RLS policy enforcement."""
        # Simulate RLS policy checks
        if self.user_role == "admin":
            self.can_query_all_data = True
            self.can_query_own_data = True
        else:
            self.can_query_all_data = False
            self.can_query_own_data = True

    def logout(self):
        """Logout and clear session."""
        self.is_authenticated = False
        self.user_email = ""
        self.user_role = ""
        self.jwt_token = ""
        self.email_input = ""
        self.password_input = ""
        self.error_message = ""
        self.success_message = ""
        self.can_query_all_data = False
        self.can_query_own_data = False


def login_form() -> rx.Component:
    """Login form component."""
    return rx.vstack(
        rx.heading("Login", size="md"),
        rx.input(
            placeholder="Email",
            value=JWTAuthState.email_input,
            on_change=JWTAuthState.set_email_input,
            type="email",
            width="100%",
        ),
        rx.input(
            placeholder="Password",
            value=JWTAuthState.password_input,
            on_change=JWTAuthState.set_password_input,
            type="password",
            width="100%",
        ),
        rx.button(
            "Login",
            on_click=JWTAuthState.login,
            background_color="navy",
            color="white",
            width="100%",
        ),
        rx.text("Test with: giladswerdlow@gmail.com / any password", font_size="sm", color="gray"),
        spacing="1rem",
        width="100%",
    )


def user_info() -> rx.Component:
    """Display logged-in user info."""
    return rx.vstack(
        rx.heading("User Information", size="md"),
        rx.text(f"Email: {JWTAuthState.user_email}", font_weight="bold"),
        rx.text(f"Role: {JWTAuthState.user_role}"),
        rx.divider(),
        rx.heading("JWT Token (truncated)", size="sm"),
        rx.box(
            rx.text(JWTAuthState.jwt_token[:50] + "...", font_family="monospace", font_size="xs"),
            background_color="lightgray",
            padding="0.5rem",
            border_radius="4px",
            overflow_x="auto",
        ),
        rx.divider(),
        rx.heading("RLS Policy Test Results", size="sm"),
        rx.vstack(
            rx.text(
                f"{'✅' if JWTAuthState.can_query_all_data else '❌'} Can query all data (admin only)",
                color="green" if JWTAuthState.can_query_all_data else "red",
            ),
            rx.text(
                f"{'✅' if JWTAuthState.can_query_own_data else '❌'} Can query own data",
                color="green" if JWTAuthState.can_query_own_data else "red",
            ),
        ),
        rx.button(
            "Logout",
            on_click=JWTAuthState.logout,
            background_color="red",
            color="white",
            width="100%",
        ),
        spacing="1rem",
        width="100%",
    )


def index() -> rx.Component:
    """Main POC page."""
    return rx.container(
        rx.vstack(
            # Header
            rx.heading("POC: JWT Authentication with Supabase", size="xl"),
            rx.text("Testing JWT session handling and RLS policies", color="gray"),
            rx.divider(),

            # Instructions
            rx.box(
                rx.vstack(
                    rx.heading("Test Instructions", size="md"),
                    rx.unordered_list(
                        rx.list_item("Login with test email: giladswerdlow@gmail.com (admin)"),
                        rx.list_item("Check JWT token is stored"),
                        rx.list_item("Verify RLS policies show correct permissions"),
                        rx.list_item("Logout and login as regular user"),
                        rx.list_item("Verify regular user has limited permissions"),
                    ),
                ),
                background_color="lightblue",
                padding="1rem",
                border_radius="8px",
            ),

            # Error message
            rx.cond(
                JWTAuthState.error_message,
                rx.box(
                    rx.text(f"❌ {JWTAuthState.error_message}", color="red"),
                    background_color="lightcoral",
                    padding="1rem",
                    border_radius="4px",
                ),
            ),

            # Success message
            rx.cond(
                JWTAuthState.success_message,
                rx.box(
                    rx.text(JWTAuthState.success_message, color="green", font_weight="bold"),
                    background_color="lightgreen",
                    padding="1rem",
                    border_radius="4px",
                ),
            ),

            # Conditional rendering: login form or user info
            rx.box(
                rx.cond(
                    JWTAuthState.is_authenticated,
                    user_info(),
                    login_form(),
                ),
                width="100%",
                max_width="500px",
                padding="2rem",
                border="1px solid gray",
                border_radius="8px",
            ),

            # POC Results
            rx.divider(),
            rx.box(
                rx.vstack(
                    rx.heading("POC Results", size="md"),
                    rx.text("🔍 TO TEST:", font_weight="bold"),
                    rx.text("⏳ Integrate actual Supabase Auth client"),
                    rx.text("⏳ Test JWT custom claims extraction"),
                    rx.text("⏳ Validate RLS policies with real database queries"),
                    rx.text("⏳ Test session persistence across page reloads"),
                    rx.text("⏳ Verify JWT expiration and refresh"),
                    rx.text(""),
                    rx.text("Critical Questions:", font_weight="bold"),
                    rx.text("❓ How to pass JWT to Supabase client in Reflex?", color="orange"),
                    rx.text("❓ Does Supabase-py work with Reflex's async state?", color="orange"),
                    rx.text("❓ How to persist JWT across page reloads?", color="orange"),
                    rx.text("❓ Can we use cookies or local storage for JWT?", color="orange"),
                    rx.text(""),
                    rx.text("Expected Outcome:", font_weight="bold"),
                    rx.text("⚠️ MEDIUM-HIGH RISK - May need custom JWT handling", color="orange"),
                ),
                background_color="lightgray",
                padding="1rem",
                border_radius="8px",
            ),

            spacing="1rem",
            width="100%",
        ),
        max_width="1200px",
        padding="2rem",
    )


# Create POC app
app = rx.App()
app.add_page(index, route="/", title="JWT Auth POC")
