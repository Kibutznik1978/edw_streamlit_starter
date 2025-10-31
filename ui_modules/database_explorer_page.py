"""
Database Explorer Page

This module provides a comprehensive query interface for historical bid period data.
Users can filter by multiple dimensions (domicile, aircraft, seat, date range) and
export results to CSV or Excel.

Phase 5: User Query Interface
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import pandas as pd
import streamlit as st

from database import get_bid_periods, query_pairings, query_bid_lines
from ui_components import render_csv_download


# ==============================================================================
# MAIN RENDER FUNCTION
# ==============================================================================


def render_database_explorer():
    """Main entry point for Database Explorer page."""
    st.title("🔍 Database Explorer")
    st.markdown("Query and analyze historical bid period data")

    # Initialize session state
    if "query_results" not in st.session_state:
        st.session_state["query_results"] = None
    if "query_filters" not in st.session_state:
        st.session_state["query_filters"] = {}

    # Render filters and get selected values
    filters = _render_filter_sidebar()

    # Main content area
    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown("### Query Results")

    with col2:
        if st.button("🔎 Run Query", type="primary", key="query_run_button"):
            with st.spinner("Querying database..."):
                st.session_state["query_results"] = _execute_query(filters)
                st.session_state["query_filters"] = filters

    # Display results if available
    if st.session_state["query_results"] is not None:
        _display_results(st.session_state["query_results"], filters)
    else:
        st.info(
            "👈 Select filters in the sidebar and click **Run Query** to view results"
        )


# ==============================================================================
# FILTER SIDEBAR
# ==============================================================================


def _render_filter_sidebar() -> Dict[str, Any]:
    """Render filter sidebar and return selected filter values."""
    st.sidebar.header("🔍 Query Filters")

    # Get available bid periods for filter options
    try:
        bid_periods_df = get_bid_periods()

        if bid_periods_df.empty:
            st.sidebar.warning(
                "⚠️ No bid periods found in database. Upload data first."
            )
            return {}

    except Exception as e:
        st.sidebar.error(f"❌ Error loading bid periods: {str(e)}")
        return {}

    # Data Type Selection
    st.sidebar.markdown("### Data Type")
    data_type = st.sidebar.radio(
        "Select data type to query:",
        ["Pairings", "Bid Lines"],
        key="query_data_type",
        help="Choose which type of data to query from the database",
    )

    # Domicile Filter
    st.sidebar.markdown("### Filters")
    domiciles = st.sidebar.multiselect(
        "Domicile",
        options=sorted(bid_periods_df["domicile"].unique()),
        default=[],
        key="query_domiciles",
        help="Select one or more domiciles (leave empty for all)",
    )

    # Aircraft Filter
    aircraft = st.sidebar.multiselect(
        "Aircraft",
        options=sorted(bid_periods_df["aircraft"].unique()),
        default=[],
        key="query_aircraft",
        help="Select one or more aircraft types (leave empty for all)",
    )

    # Seat Filter
    seats = st.sidebar.multiselect(
        "Seat Position",
        options=["CA", "FO"],
        default=[],
        format_func=lambda x: "Captain" if x == "CA" else "First Officer",
        key="query_seats",
        help="Select seat positions (leave empty for all)",
    )

    # Bid Period Filter
    bid_periods_list = sorted(bid_periods_df["period"].unique(), reverse=True)
    selected_periods = st.sidebar.multiselect(
        "Bid Periods",
        options=bid_periods_list,
        default=[],
        key="query_periods",
        help="Select specific bid periods (leave empty for all)",
    )

    # Date Range
    st.sidebar.markdown("### Date Range")
    quick_filter = st.sidebar.selectbox(
        "Quick Filter",
        ["Custom", "Last 3 months", "Last 6 months", "Last year", "All time"],
        key="query_quick_filter",
    )

    # Calculate date range based on quick filter
    if quick_filter == "Last 3 months":
        start_date = datetime.now() - timedelta(days=90)
        end_date = datetime.now()
        st.sidebar.caption(
            f"📅 {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        )
    elif quick_filter == "Last 6 months":
        start_date = datetime.now() - timedelta(days=180)
        end_date = datetime.now()
        st.sidebar.caption(
            f"📅 {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        )
    elif quick_filter == "Last year":
        start_date = datetime.now() - timedelta(days=365)
        end_date = datetime.now()
        st.sidebar.caption(
            f"📅 {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        )
    elif quick_filter == "All time":
        start_date = pd.to_datetime(bid_periods_df["start_date"]).min()
        end_date = pd.to_datetime(bid_periods_df["end_date"]).max()
        st.sidebar.caption(
            f"📅 {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        )
    else:  # Custom
        col1, col2 = st.sidebar.columns(2)
        with col1:
            start_date = st.date_input(
                "Start Date",
                value=datetime.now() - timedelta(days=180),
                key="query_start_date",
            )
        with col2:
            end_date = st.date_input(
                "End Date", value=datetime.now(), key="query_end_date"
            )

    # Advanced Options
    with st.sidebar.expander("⚙️ Advanced Options"):
        limit = st.number_input(
            "Max Results",
            min_value=100,
            max_value=10000,
            value=1000,
            step=100,
            key="query_limit",
            help="Maximum number of records to return",
        )

        show_deleted = st.checkbox(
            "Include deleted records",
            value=False,
            key="query_show_deleted",
            help="Show soft-deleted records",
        )

    # Build filters dictionary
    filters = {
        "data_type": data_type,
        "domiciles": domiciles if domiciles else None,
        "aircraft": aircraft if aircraft else None,
        "seats": seats if seats else None,
        "periods": selected_periods if selected_periods else None,
        "start_date": start_date,
        "end_date": end_date,
        "limit": limit,
        "show_deleted": show_deleted,
    }

    # Show filter summary
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Filter Summary")
    active_filters = []
    if domiciles:
        active_filters.append(f"Domiciles: {', '.join(domiciles)}")
    if aircraft:
        active_filters.append(f"Aircraft: {', '.join(aircraft)}")
    if seats:
        active_filters.append(
            f"Seats: {', '.join(['CA' if s == 'CA' else 'FO' for s in seats])}"
        )
    if selected_periods:
        active_filters.append(f"Periods: {', '.join(selected_periods)}")

    if active_filters:
        for f in active_filters:
            st.sidebar.caption(f"• {f}")
    else:
        st.sidebar.caption("_No filters applied (all data)_")

    return filters


# ==============================================================================
# QUERY EXECUTION
# ==============================================================================


def _execute_query(filters: Dict[str, Any]) -> Optional[pd.DataFrame]:
    """Execute query based on selected filters."""
    try:
        # Build query filters for database functions
        db_filters = {}

        if filters.get("domiciles"):
            db_filters["domiciles"] = filters["domiciles"]
        if filters.get("aircraft"):
            db_filters["aircraft"] = filters["aircraft"]
        if filters.get("seats"):
            db_filters["seats"] = filters["seats"]
        if filters.get("periods"):
            db_filters["periods"] = filters["periods"]

        # Add date range
        db_filters["start_date"] = filters["start_date"]
        db_filters["end_date"] = filters["end_date"]

        # Execute appropriate query
        if filters["data_type"] == "Pairings":
            df, total_count = query_pairings(db_filters, limit=filters["limit"])
        else:  # Bid Lines
            df, total_count = query_bid_lines(db_filters, limit=filters["limit"])

        # Add metadata
        if not df.empty:
            df.attrs["total_count"] = total_count
            df.attrs["data_type"] = filters["data_type"]

        return df

    except Exception as e:
        st.error(f"❌ Error executing query: {str(e)}")
        st.exception(e)
        return None


# ==============================================================================
# RESULTS DISPLAY
# ==============================================================================


def _display_results(df: pd.DataFrame, filters: Dict[str, Any]):
    """Display query results with export options and pagination."""
    if df is None or df.empty:
        st.warning("⚠️ No results found for the selected filters")
        return

    # Get metadata
    total_count = getattr(df.attrs, "total_count", len(df))
    data_type = getattr(df.attrs, "data_type", filters.get("data_type", "Unknown"))

    # Results summary
    st.markdown(f"**Found {total_count:,} {data_type.lower()} records**")

    if len(df) < total_count:
        st.caption(
            f"_Showing first {len(df):,} records (adjust limit in Advanced Options to see more)_"
        )

    # Export options
    st.markdown("#### Export Options")
    col1, col2, col3 = st.columns(3)

    with col1:
        render_csv_download(
            df,
            f"query_results_{data_type.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        )

    with col2:
        # Excel export button
        if st.button("📊 Download Excel", key="query_export_excel"):
            st.info("💡 Excel export coming soon!")

    with col3:
        # PDF export button
        if st.button("📄 Export PDF", key="query_export_pdf"):
            st.info("💡 PDF export coming soon!")

    st.markdown("---")

    # Pagination controls
    st.markdown("#### Results Table")
    page_size = st.selectbox(
        "Rows per page:", [25, 50, 100, 250], index=1, key="query_page_size"
    )

    total_pages = (len(df) - 1) // page_size + 1

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        page = st.number_input(
            f"Page (1-{total_pages})",
            min_value=1,
            max_value=total_pages,
            value=1,
            key="query_page",
        )

    # Calculate pagination
    start_idx = (page - 1) * page_size
    end_idx = min(start_idx + page_size, len(df))

    st.caption(f"Showing rows {start_idx + 1:,} to {end_idx:,} of {len(df):,}")

    # Display data
    _display_data_table(df.iloc[start_idx:end_idx], data_type)

    # Record detail viewer
    st.markdown("---")
    st.markdown("#### Record Details")
    _render_record_detail_viewer(df)


def _display_data_table(df: pd.DataFrame, data_type: str):
    """Display results in a formatted table."""
    # Customize display based on data type
    if data_type == "Pairings":
        # Select key columns for pairings
        display_cols = [
            "trip_id",
            "is_edw",
            "total_credit_time",
            "tafb_hours",
            "num_duty_days",
            "num_legs",
            "departure_time",
            "arrival_time",
        ]
        # Only include columns that exist
        display_cols = [col for col in display_cols if col in df.columns]
        display_df = df[display_cols] if display_cols else df
    else:  # Bid Lines
        # Select key columns for bid lines
        display_cols = [
            "line_number",
            "total_ct",
            "total_bt",
            "total_do",
            "total_dd",
            "is_reserve",
            "is_hot_standby",
            "vto_type",
        ]
        # Only include columns that exist
        display_cols = [col for col in display_cols if col in df.columns]
        display_df = df[display_cols] if display_cols else df

    # Display dataframe
    st.dataframe(
        display_df,
        use_container_width=True,
        height=400,
        hide_index=True,
    )


def _render_record_detail_viewer(df: pd.DataFrame):
    """Render expandable record detail viewer."""
    if df.empty:
        return

    # Let user select a record to view
    if "id" in df.columns:
        record_options = df["id"].tolist()
        format_func = lambda x: f"Record {str(x)[:8]}..."
    elif "trip_id" in df.columns:
        record_options = df.index.tolist()
        format_func = lambda x: f"Trip {df.iloc[x]['trip_id']}"
    elif "line_number" in df.columns:
        record_options = df.index.tolist()
        format_func = lambda x: f"Line {df.iloc[x]['line_number']}"
    else:
        record_options = df.index.tolist()
        format_func = lambda x: f"Row {x}"

    if not record_options:
        st.caption("_No records available_")
        return

    selected_idx = st.selectbox(
        "Select record to view full details:",
        record_options,
        format_func=format_func,
        key="query_detail_select",
    )

    if selected_idx is not None:
        with st.expander("📋 View Full Record", expanded=False):
            if "id" in df.columns:
                record = df[df["id"] == selected_idx].iloc[0]
            else:
                record = df.iloc[selected_idx]

            # Display as formatted JSON
            st.json(record.to_dict(), expanded=True)
