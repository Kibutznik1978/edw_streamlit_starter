"""Historical Trends page (Tab 3) - Placeholder for future database integration."""

import streamlit as st


def render_historical_trends():
    """Render the Historical Trends tab (placeholder)."""

    st.header("📈 Historical Trends")
    st.info(
        "**Coming Soon!**\n\n"
        "This tab will display historical trend analysis once database integration is complete.\n\n"
        "**Planned Features:**\n"
        "- Trend charts comparing multiple bid periods\n"
        "- EDW percentage trends over time\n"
        "- Bid line metric comparisons (CT, BT, DO, DD)\n"
        "- Fleet and domicile comparisons\n"
        "- Interactive Altair visualizations"
    )

    st.divider()

    st.markdown("### 🗄️ Database Integration Status")
    st.warning(
        "**Database setup required:**\n\n"
        "1. Create Supabase project\n"
        "2. Configure `.env` with credentials\n"
        "3. Implement `database.py` module\n"
        "4. Add 'Save to Database' buttons to analyzers\n\n"
        "See `docs/SUPABASE_SETUP.md` for details."
    )
