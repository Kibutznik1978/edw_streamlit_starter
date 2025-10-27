"""
Pairing Analyzer Tool 1.0
Multi-tab application for analyzing airline bid packets.

This is the main entry point. All tab logic has been modularized into the pages/ directory.
"""

import streamlit as st

from ui_modules import (
    render_edw_analyzer,
    render_bid_line_analyzer,
    render_historical_trends
)


#==============================================================================
# APP CONFIGURATION
#==============================================================================

st.set_page_config(
    page_title="Pairing Analyzer Tool 1.0",
    layout="wide",
    initial_sidebar_state="expanded"
)


#==============================================================================
# MAIN APPLICATION
#==============================================================================

def main():
    """Main application entry point with tab navigation."""

    st.title("✈️ Pairing Analyzer Tool 1.0")
    st.caption("Comprehensive analysis tool for airline bid packets and pairings")

    # Create main tabs
    tab1, tab2, tab3 = st.tabs([
        "📊 EDW Pairing Analyzer",
        "📋 Bid Line Analyzer",
        "📈 Historical Trends"
    ])

    with tab1:
        render_edw_analyzer()

    with tab2:
        render_bid_line_analyzer()

    with tab3:
        render_historical_trends()


if __name__ == "__main__":
    main()
