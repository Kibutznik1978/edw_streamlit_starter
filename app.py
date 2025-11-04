"""
Pairing Analyzer Tool 1.0
Multi-tab application for analyzing airline bid packets.

This is the main entry point. All tab logic has been modularized into the pages/ directory.

Phase 2: Authentication Integration
- Requires user login via Supabase Auth
- Session management with automatic token refresh
- Role-based access control (admin vs user)
- User info displayed in sidebar
"""

import streamlit as st

from auth import init_auth, login_page, show_user_info
from database import get_supabase_client
from ui_components import apply_brand_styling, render_app_header
from ui_modules import (
    render_bid_line_analyzer,
    render_database_explorer,
    render_edw_analyzer,
    render_historical_trends,
)

# ==============================================================================
# APP CONFIGURATION
# ==============================================================================

st.set_page_config(
    page_title="Pairing Analyzer Tool 1.0", layout="wide", initial_sidebar_state="expanded"
)


# ==============================================================================
# MAIN APPLICATION
# ==============================================================================


def main():
    """Main application entry point with authentication and tab navigation."""

    # Initialize Supabase client
    try:
        supabase = get_supabase_client()
    except ValueError as e:
        st.error(f"❌ Configuration Error: {str(e)}")
        st.info("Please ensure .env file exists with SUPABASE_URL and SUPABASE_ANON_KEY")
        st.stop()

    # Initialize authentication
    user = init_auth(supabase)

    # If not authenticated, show login page and stop
    if not user:
        login_page(supabase)
        st.stop()

    # User is authenticated - show user info in sidebar
    show_user_info(supabase)

    # Apply brand styling
    apply_brand_styling()

    # Render branded header
    render_app_header()
    st.divider()

    # Create main tabs
    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "📊 EDW Pairing Analyzer",
            "📋 Bid Line Analyzer",
            "🔍 Database Explorer",
            "📈 Historical Trends",
        ]
    )

    with tab1:
        render_edw_analyzer()

    with tab2:
        render_bid_line_analyzer()

    with tab3:
        render_database_explorer()

    with tab4:
        render_historical_trends()


if __name__ == "__main__":
    main()
