"""
Authentication Module - Supabase Auth Integration
=================================================

This module provides authentication functionality for the Aero Crew Data application.

Key Features:
- User login/signup with email/password
- Session management with automatic token refresh
- Role-based access control (admin vs user)
- Admin guard for protected operations
- User info display in sidebar
- Session persistence across page refreshes

Usage:
    from auth import init_auth, login_page, show_user_info, require_admin
    from database import get_supabase_client

    # Initialize authentication
    supabase = get_supabase_client()
    user = init_auth(supabase)

    if not user:
        login_page(supabase)
        st.stop()

    # Show user info in sidebar
    show_user_info(supabase)

    # Protect admin operations
    if require_admin(supabase):
        # Admin-only code here
        pass

Version: 1.0
Date: 2025-10-28
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import streamlit as st
from supabase import Client

# =====================================================================
# SESSION MANAGEMENT
# =====================================================================


def init_auth(supabase: Client) -> Optional[Dict[str, Any]]:
    """
    Initialize authentication with automatic token refresh.

    This function should be called at the start of your Streamlit app
    to check if the user is logged in and refresh their session if needed.

    Session tokens expire after a certain period. This function checks
    if the token is expiring within 5 minutes and refreshes it automatically.

    Args:
        supabase: Supabase client instance

    Returns:
        User dict if authenticated, None if not logged in

    Example:
        supabase = get_supabase_client()
        user = init_auth(supabase)

        if not user:
            login_page(supabase)
            st.stop()

        # User is authenticated, continue with app
        st.write(f"Welcome, {user.email}!")
    """
    # Check if user has an active session
    if "supabase_session" not in st.session_state:
        return None

    session = st.session_state["supabase_session"]

    # Check if session has expired
    if not session or not hasattr(session, "expires_at"):
        return None

    expires_at = datetime.fromtimestamp(session.expires_at)

    # Refresh if expiring within 5 minutes
    if expires_at < datetime.now() + timedelta(minutes=5):
        try:
            response = supabase.auth.refresh_session()

            # Update session state
            st.session_state["supabase_session"] = response.session
            st.session_state["user"] = response.user

            # Set session on client
            supabase.auth.set_session(response.session.access_token, response.session.refresh_token)

            return response.user

        except Exception as e:
            st.error(f"Session expired. Please log in again. Error: {str(e)}")
            logout()
            return None

    return st.session_state.get("user")


def logout() -> None:
    """
    Clear session and redirect to login.

    This function clears all session state variables and triggers
    a rerun to show the login page.

    Example:
        if st.sidebar.button("Logout"):
            logout()
    """
    # Clear all session state
    for key in list(st.session_state.keys()):
        del st.session_state[key]

    # Trigger rerun to show login page
    st.rerun()


# =====================================================================
# USER ROLE MANAGEMENT
# =====================================================================


def get_user_role(supabase: Client) -> str:
    """
    Get current user's role from profiles table.

    The role is cached in session state to avoid repeated database queries.

    Args:
        supabase: Supabase client instance

    Returns:
        User role ('admin' or 'user')

    Example:
        role = get_user_role(supabase)
        if role == 'admin':
            st.write("Admin features enabled")
    """
    # Return 'user' if not authenticated
    if "user" not in st.session_state:
        return "user"

    # Return cached role if available
    if "user_role" in st.session_state:
        return st.session_state["user_role"]

    # Fetch role from database
    user_id = st.session_state["user"].id

    try:
        response = supabase.table("profiles").select("role").eq("id", user_id).single().execute()
        role = response.data["role"]

        # Cache role in session state
        st.session_state["user_role"] = role

        return role

    except Exception as e:
        # Default to 'user' if query fails
        st.warning(f"Could not fetch user role: {str(e)}")
        return "user"


def is_admin(supabase: Client) -> bool:
    """
    Check if current user has admin role.

    Args:
        supabase: Supabase client instance

    Returns:
        True if admin, False otherwise

    Example:
        if is_admin(supabase):
            # Show admin controls
            pass
    """
    return get_user_role(supabase) == "admin"


def require_admin(supabase: Client) -> bool:
    """
    Require admin role or show error message.

    This is a convenience function for protecting admin-only operations.
    If the user is not an admin, it displays an error message and returns False.

    Args:
        supabase: Supabase client instance

    Returns:
        True if admin, False if not admin

    Example:
        if not require_admin(supabase):
            st.stop()

        # Admin-only code here
        st.write("Admin controls...")
    """
    role = get_user_role(supabase)

    if role != "admin":
        st.error("🚫 Admin access required")
        st.info("Contact your administrator to request admin privileges.")
        return False

    return True


# =====================================================================
# LOGIN/SIGNUP UI
# =====================================================================


def login_page(supabase: Client) -> None:
    """
    Display login/signup form.

    This function shows a complete authentication UI with two tabs:
    - Login: For existing users to sign in
    - Sign Up: For new users to create an account

    Args:
        supabase: Supabase client instance

    Example:
        supabase = get_supabase_client()
        user = init_auth(supabase)

        if not user:
            login_page(supabase)
            st.stop()
    """
    st.title("🔐 Aero Crew Data - Login")

    st.markdown(
        """
    Welcome to the Aero Crew Data analysis platform.

    **Features:**
    - EDW Pairing Analysis
    - Bid Line Analysis
    - Historical Trend Tracking
    - Customizable PDF Reports
    """
    )

    st.markdown("---")

    # Create tabs for login and signup
    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    # === LOGIN TAB ===
    with tab1:
        st.markdown("### Sign in to your account")

        with st.form("login_form"):
            email = st.text_input("Email", placeholder="pilot@airline.com")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submitted = st.form_submit_button("Login", type="primary")

            if submitted:
                # Validate inputs
                if not email or not password:
                    st.error("❌ Please enter both email and password")
                    return

                try:
                    # Attempt login
                    response = supabase.auth.sign_in_with_password(
                        {"email": email, "password": password}
                    )

                    # Store session and user in session state
                    st.session_state["supabase_session"] = response.session
                    st.session_state["user"] = response.user

                    # Set session on client
                    supabase.auth.set_session(
                        response.session.access_token, response.session.refresh_token
                    )

                    st.success("✅ Login successful!")
                    st.rerun()

                except Exception as e:
                    error_msg = str(e)

                    # Provide helpful error messages
                    if "Invalid login credentials" in error_msg:
                        st.error("❌ Invalid email or password. Please try again.")
                    elif "Email not confirmed" in error_msg:
                        st.error("❌ Please verify your email before logging in.")
                        st.info("Check your inbox for a confirmation email.")
                    else:
                        st.error(f"❌ Login failed: {error_msg}")

    # === SIGNUP TAB ===
    with tab2:
        st.markdown("### Create a new account")

        with st.form("signup_form"):
            email = st.text_input("Email", key="signup_email", placeholder="pilot@airline.com")
            password = st.text_input(
                "Password",
                type="password",
                key="signup_password",
                placeholder="At least 8 characters",
            )
            confirm_password = st.text_input(
                "Confirm Password", type="password", placeholder="Re-enter your password"
            )
            submitted = st.form_submit_button("Sign Up", type="primary")

            if submitted:
                # Validate inputs
                if not email or not password or not confirm_password:
                    st.error("❌ Please fill in all fields")
                    return

                if password != confirm_password:
                    st.error("❌ Passwords don't match")
                    return

                if len(password) < 8:
                    st.error("❌ Password must be at least 8 characters")
                    return

                try:
                    # Attempt signup
                    response = supabase.auth.sign_up({"email": email, "password": password})

                    st.success("✅ Account created successfully!")
                    st.info(
                        "📧 Please check your email to verify your account. "
                        "After verifying, return here to log in."
                    )

                    # Show login tab hint
                    st.markdown("---")
                    st.markdown("Once verified, switch to the **Login** tab to sign in.")

                except Exception as e:
                    error_msg = str(e)

                    # Provide helpful error messages
                    if "User already registered" in error_msg:
                        st.error("❌ This email is already registered. Please log in instead.")
                    elif "Password should be at least" in error_msg:
                        st.error("❌ Password does not meet requirements")
                        st.info("Password must be at least 8 characters long")
                    else:
                        st.error(f"❌ Sign up failed: {error_msg}")

    # Footer
    st.markdown("---")
    st.caption(
        "Need help? Contact your system administrator to request access " "or for admin privileges."
    )


# =====================================================================
# USER INFO DISPLAY
# =====================================================================


def show_user_info(supabase: Client) -> None:
    """
    Display user info in sidebar.

    Shows the current user's email, role, and a logout button
    in the sidebar.

    Args:
        supabase: Supabase client instance

    Example:
        # At the top of your Streamlit app
        show_user_info(supabase)

        # This will add user info to the sidebar automatically
    """
    user = st.session_state.get("user")

    if not user:
        return

    # Add separator
    st.sidebar.markdown("---")

    # User email
    st.sidebar.markdown(f"👤 **{user.email}**")

    # User role
    role = get_user_role(supabase)
    role_emoji = "👑" if role == "admin" else "👥"
    st.sidebar.markdown(f"{role_emoji} Role: **{role.title()}**")

    # Logout button
    if st.sidebar.button("🚪 Logout", type="secondary", width="stretch"):
        # Sign out from Supabase
        try:
            supabase.auth.sign_out()
        except Exception:
            pass  # Ignore errors, we're logging out anyway

        # Clear local session
        logout()

    # Debug JWT claims (for troubleshooting RLS issues)
    with st.sidebar.expander("🔍 Debug JWT Claims", expanded=False):
        from database import debug_jwt_claims

        debug_info = debug_jwt_claims()

        if debug_info["error"]:
            st.error(f"Error: {debug_info['error']}")
        else:
            st.json(
                {
                    "has_session": debug_info["has_session"],
                    "has_access_token": debug_info["has_access_token"],
                    "app_role": debug_info.get("app_role", "NOT FOUND"),
                    "claims": debug_info.get("claims", {}),
                }
            )


# =====================================================================
# ADMIN OPERATIONS
# =====================================================================


def promote_user_to_admin(supabase: Client, user_email: str) -> bool:
    """
    Promote a user to admin role (admin-only operation).

    This function is for programmatic admin promotion. In production,
    you would typically do this via the Supabase SQL Editor for the
    first admin, then use this function for subsequent promotions.

    Args:
        supabase: Supabase client instance
        user_email: Email of user to promote

    Returns:
        True if successful, False otherwise

    Example:
        # This should only be called by existing admins
        if is_admin(supabase):
            success = promote_user_to_admin(supabase, "newadmin@airline.com")
            if success:
                st.success("User promoted to admin")
    """
    # Check if current user is admin
    if not is_admin(supabase):
        st.error("Only admins can promote users")
        return False

    try:
        # Get user ID from email
        response = supabase.auth.admin.list_users()
        target_user = None

        for user in response:
            if user.email == user_email:
                target_user = user
                break

        if not target_user:
            st.error(f"User not found: {user_email}")
            return False

        # Update role in profiles table
        supabase.table("profiles").update({"role": "admin"}).eq("id", target_user.id).execute()

        st.success(f"✅ User {user_email} promoted to admin")
        return True

    except Exception as e:
        st.error(f"Failed to promote user: {str(e)}")
        return False


# =====================================================================
# UTILITY FUNCTIONS
# =====================================================================


def get_current_user_id() -> Optional[str]:
    """
    Get current user's ID from session state.

    Returns:
        User ID (UUID string) or None if not logged in

    Example:
        user_id = get_current_user_id()
        if user_id:
            print(f"Current user ID: {user_id}")
    """
    user = st.session_state.get("user")
    return user.id if user else None


def get_current_user_email() -> Optional[str]:
    """
    Get current user's email from session state.

    Returns:
        User email or None if not logged in

    Example:
        email = get_current_user_email()
        if email:
            st.write(f"Logged in as: {email}")
    """
    user = st.session_state.get("user")
    return user.email if user else None


def is_authenticated() -> bool:
    """
    Check if user is currently authenticated.

    Returns:
        True if authenticated, False otherwise

    Example:
        if not is_authenticated():
            st.warning("Please log in to continue")
            st.stop()
    """
    return "user" in st.session_state and st.session_state["user"] is not None
