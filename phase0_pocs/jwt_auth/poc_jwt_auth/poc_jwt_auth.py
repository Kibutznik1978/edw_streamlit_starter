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
from typing import Optional, List, Dict, Any
import os
import json
import base64
from dotenv import load_dotenv
from supabase import create_client, Client
from datetime import datetime

# Load environment variables
load_dotenv(dotenv_path="../../.env")

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise ValueError("Missing Supabase credentials. Please set SUPABASE_URL and SUPABASE_ANON_KEY in .env")

# Create base client (will be recreated with JWT for each authenticated request)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


class JWTAuthState(rx.State):
    """State for JWT authentication POC."""

    # Authentication state
    is_authenticated: bool = False
    user_email: str = ""
    user_id: str = ""
    user_role: str = ""
    jwt_token: str = ""
    jwt_expires_at: str = ""

    # Login form
    email_input: str = ""
    password_input: str = ""

    # Error handling
    error_message: str = ""
    success_message: str = ""
    info_message: str = ""

    # RLS test results
    can_query_all_data: bool = False
    can_query_own_data: bool = False
    all_data_count: int = 0
    own_data_count: int = 0
    test_data_results: List[Dict[str, Any]] = []

    # JWT claims for debugging
    jwt_claims_str: str = ""

    def decode_jwt_payload(self, token: str) -> Dict[str, Any]:
        """Decode JWT payload without verification (for debugging)."""
        try:
            # JWT format: header.payload.signature
            parts = token.split('.')
            if len(parts) != 3:
                return {}

            # Decode payload (second part)
            payload = parts[1]
            # Add padding if needed
            padding = 4 - len(payload) % 4
            if padding != 4:
                payload += '=' * padding

            decoded = base64.urlsafe_b64decode(payload)
            return json.loads(decoded)
        except Exception as e:
            return {"error": str(e)}

    async def login(self):
        """Login with Supabase Auth."""
        self.error_message = ""
        self.success_message = ""
        self.info_message = ""

        try:
            if not self.email_input or not self.password_input:
                self.error_message = "Please enter email and password"
                return

            # Authenticate with Supabase
            response = supabase.auth.sign_in_with_password({
                "email": self.email_input,
                "password": self.password_input
            })

            if response.user:
                # Extract user info
                self.is_authenticated = True
                self.user_email = response.user.email or self.email_input
                self.user_id = response.user.id
                self.jwt_token = response.session.access_token

                # Decode JWT to extract custom claims
                claims = self.decode_jwt_payload(self.jwt_token)
                self.jwt_claims_str = json.dumps(claims, indent=2)

                # Extract user_role from custom claims (if present)
                self.user_role = claims.get("user_role", "user")

                # Extract expiration
                exp_timestamp = claims.get("exp", 0)
                if exp_timestamp:
                    exp_date = datetime.fromtimestamp(exp_timestamp)
                    self.jwt_expires_at = exp_date.strftime("%Y-%m-%d %H:%M:%S")

                self.success_message = f"✅ Logged in as {self.user_email} (role: {self.user_role})"
                self.info_message = f"User ID: {self.user_id}"

                # Test RLS policies
                await self.test_rls_policies()
            else:
                self.error_message = "Login failed: No user returned"

        except Exception as e:
            self.error_message = f"Login failed: {str(e)}"

    async def test_rls_policies(self):
        """Test RLS policy enforcement with real database queries."""
        try:
            if not self.jwt_token:
                self.error_message = "No JWT token available"
                return

            # Create authenticated Supabase client with JWT
            auth_client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
            auth_client.postgrest.auth(self.jwt_token)

            # Test 1: Query all data (should work for admin, fail for regular user)
            try:
                all_data_response = auth_client.table("poc_test_data").select("*").execute()
                self.can_query_all_data = True
                self.all_data_count = len(all_data_response.data) if all_data_response.data else 0
                self.test_data_results = all_data_response.data[:3] if all_data_response.data else []
            except Exception as e:
                self.can_query_all_data = False
                self.all_data_count = 0
                # This is expected for non-admin users
                if "pgrst" not in str(e).lower():  # Only log unexpected errors
                    print(f"Query all data failed: {e}")

            # Test 2: Query own data (should work for all authenticated users)
            try:
                own_data_response = auth_client.table("poc_test_data").select("*").eq("user_id", self.user_id).execute()
                self.can_query_own_data = True
                self.own_data_count = len(own_data_response.data) if own_data_response.data else 0
            except Exception as e:
                self.can_query_own_data = False
                self.own_data_count = 0
                print(f"Query own data failed: {e}")

        except Exception as e:
            self.error_message = f"RLS test failed: {str(e)}"

    def logout(self):
        """Logout and clear session."""
        try:
            supabase.auth.sign_out()
        except:
            pass  # Ignore logout errors

        self.is_authenticated = False
        self.user_email = ""
        self.user_id = ""
        self.user_role = ""
        self.jwt_token = ""
        self.jwt_expires_at = ""
        self.email_input = ""
        self.password_input = ""
        self.error_message = ""
        self.success_message = ""
        self.info_message = ""
        self.can_query_all_data = False
        self.can_query_own_data = False
        self.all_data_count = 0
        self.own_data_count = 0
        self.test_data_results = []
        self.jwt_claims_str = ""


def login_form() -> rx.Component:
    """Login form component."""
    return rx.vstack(
        rx.heading("Login", size="6"),
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
        rx.text("Test with any Supabase Auth user email/password", font_size="sm", color="gray"),
        spacing="4",
        width="100%",
    )


def user_info() -> rx.Component:
    """Display logged-in user info."""
    return rx.vstack(
        rx.heading("User Information", size="6"),
        rx.vstack(
            rx.text(f"Email: {JWTAuthState.user_email}", font_weight="bold"),
            rx.text(f"User ID: {JWTAuthState.user_id}", font_size="sm", font_family="monospace"),
            rx.text(f"Role: {JWTAuthState.user_role}", color="blue"),
            rx.text(f"Token Expires: {JWTAuthState.jwt_expires_at}", font_size="sm", color="gray"),
            spacing="2",
        ),

        rx.divider(),

        rx.heading("JWT Token (first 80 chars)", size="4"),
        rx.box(
            rx.text(JWTAuthState.jwt_token[:80] + "...", font_family="monospace", font_size="xs"),
            background_color="#f0f0f0",
            padding="4",
            border_radius="4px",
            overflow_x="auto",
        ),

        rx.divider(),

        rx.heading("JWT Claims (Decoded)", size="4"),
        rx.box(
            rx.code_block(
                JWTAuthState.jwt_claims_str,
                language="json",
                font_size="xs",
                max_height="200px",
                overflow_y="auto",
            ),
            width="100%",
        ),

        rx.divider(),

        rx.heading("RLS Policy Test Results", size="4"),
        rx.vstack(
            rx.cond(
                JWTAuthState.can_query_all_data,
                rx.text(
                    f"✅ Can query all data (admin only) - {JWTAuthState.all_data_count} rows",
                    color="green",
                    font_weight="bold",
                ),
                rx.text(
                    f"❌ Can query all data (admin only) - {JWTAuthState.all_data_count} rows",
                    color="red",
                    font_weight="bold",
                ),
            ),
            rx.cond(
                JWTAuthState.can_query_own_data,
                rx.text(
                    f"✅ Can query own data - {JWTAuthState.own_data_count} rows",
                    color="green",
                    font_weight="bold",
                ),
                rx.text(
                    f"❌ Can query own data - {JWTAuthState.own_data_count} rows",
                    color="red",
                    font_weight="bold",
                ),
            ),
            spacing="2",
        ),

        rx.cond(
            JWTAuthState.test_data_results.length() > 0,
            rx.vstack(
                rx.heading("Sample Data (first 3 rows)", size="4"),
                rx.foreach(
                    JWTAuthState.test_data_results,
                    lambda row: rx.box(
                        rx.vstack(
                            rx.text(f"Title: {row['title']}", font_weight="bold"),
                            rx.text(f"Content: {row['content']}", font_size="sm"),
                            rx.text(f"Public: {row['is_public']}", font_size="xs", color="gray"),
                            spacing="1",
                        ),
                        background_color="#f9f9f9",
                        padding="3",
                        border_radius="4px",
                        border="1px solid #ddd",
                        width="100%",
                    )
                ),
                spacing="2",
                width="100%",
            ),
        ),

        rx.divider(),

        rx.button(
            "Logout",
            on_click=JWTAuthState.logout,
            background_color="red",
            color="white",
            width="100%",
        ),
        spacing="4",
        width="100%",
    )


def index() -> rx.Component:
    """Main POC page."""
    return rx.container(
        rx.vstack(
            # Header
            rx.heading("POC 4: JWT Authentication with Supabase", size="9"),
            rx.text("Testing JWT session handling and RLS policies in Reflex", color="gray", font_size="lg"),
            rx.divider(),

            # Instructions
            rx.box(
                rx.vstack(
                    rx.heading("Test Instructions", size="6"),
                    rx.ordered_list(
                        rx.list_item("Create test users in Supabase Dashboard (Admin + Regular user)"),
                        rx.list_item("Run SQL migration: sql/poc_test_table.sql"),
                        rx.list_item("Update user_id values in sample data with real user IDs"),
                        rx.list_item("Login with admin email and verify ✅ Can query all data"),
                        rx.list_item("Check JWT claims show user_role = 'admin' (if configured)"),
                        rx.list_item("Logout and login as regular user"),
                        rx.list_item("Verify ❌ Cannot query all data, ✅ Can query own data"),
                        rx.list_item("Refresh browser page and verify session persists"),
                    ),
                    spacing="2",
                ),
                background_color="#e3f2fd",
                padding="6",
                border_radius="8px",
                border="1px solid #2196f3",
            ),

            # Info message
            rx.cond(
                JWTAuthState.info_message,
                rx.box(
                    rx.text(f"ℹ️ {JWTAuthState.info_message}", color="#1976d2"),
                    background_color="#e3f2fd",
                    padding="4",
                    border_radius="4px",
                ),
            ),

            # Error message
            rx.cond(
                JWTAuthState.error_message,
                rx.box(
                    rx.text(f"❌ {JWTAuthState.error_message}", color="red", font_weight="bold"),
                    background_color="#ffebee",
                    padding="4",
                    border_radius="4px",
                    border="1px solid #f44336",
                ),
            ),

            # Success message
            rx.cond(
                JWTAuthState.success_message,
                rx.box(
                    rx.text(JWTAuthState.success_message, color="green", font_weight="bold"),
                    background_color="#e8f5e9",
                    padding="4",
                    border_radius="4px",
                    border="1px solid #4caf50",
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
                max_width="600px",
                padding="8",
                border="2px solid #ddd",
                border_radius="8px",
                box_shadow="0 2px 8px rgba(0,0,0,0.1)",
            ),

            # POC Requirements Status
            rx.divider(),
            rx.box(
                rx.vstack(
                    rx.heading("POC Success Criteria", size="6"),
                    rx.vstack(
                        rx.text("✅ Supabase login functional (email/password)", color="green"),
                        rx.text("✅ JWT token stored in Reflex State", color="green"),
                        rx.text("✅ JWT custom claims decoded and accessible", color="green"),
                        rx.text("🔍 RLS policies enforce correctly (requires testing)", color="orange"),
                        rx.text("⏳ Session persists on page reload (to be tested)", color="gray"),
                        rx.text("⏳ JWT expiration/refresh (to be tested)", color="gray"),
                        spacing="2",
                    ),
                    rx.divider(),
                    rx.heading("Critical Findings", size="5"),
                    rx.vstack(
                        rx.text("✅ Supabase-py works with Reflex async State", color="green"),
                        rx.text("✅ JWT passed to Supabase client via .postgrest.auth(jwt)", color="green"),
                        rx.text("✅ JWT decoded successfully with base64 decoding", color="green"),
                        rx.text("⚠️ Session persistence requires client-side storage", color="orange"),
                        rx.text("⚠️ user_role claim must be added via Supabase hooks", color="orange"),
                        spacing="2",
                    ),
                    spacing="4",
                ),
                background_color="#f5f5f5",
                padding="6",
                border_radius="8px",
            ),

            spacing="6",
            width="100%",
        ),
        max_width="1200px",
        padding="8",
    )


# Create POC app
app = rx.App()
app.add_page(index, route="/", title="JWT Auth POC")
