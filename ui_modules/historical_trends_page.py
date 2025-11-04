"""
Historical Trends Page

This module provides trend visualization and comparative analysis for historical bid
period data using the bid_period_trends materialized view.

Phase 6: Analysis & Visualization
"""

from datetime import datetime
from typing import List, Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from database import get_historical_trends, get_bid_periods


# ==============================================================================
# MAIN RENDER FUNCTION
# ==============================================================================


def render_historical_trends():
    """Main entry point for Historical Trends page."""
    st.header("📈 Historical Trends")
    st.caption(
        "Analyze trends and patterns across bid periods with interactive visualizations"
    )

    # Initialize session state
    if "trends_data" not in st.session_state:
        st.session_state["trends_data"] = None

    # Render filter controls
    filters = _render_filter_controls()

    # Load data button
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("Trend Analysis")
    with col2:
        if st.button("📊 Load Trends", type="primary", key="load_trends_button"):
            with st.spinner("Loading trend data..."):
                st.session_state["trends_data"] = _load_trend_data(filters)

    # Display trends if data available
    if st.session_state["trends_data"] is not None:
        df = st.session_state["trends_data"]

        if df.empty:
            st.warning(
                "⚠️ No trend data available for the selected filters. Try uploading bid period data first."
            )
        else:
            _display_trends(df, filters)
    else:
        st.info(
            "👈 Select filters in the sidebar and click **Load Trends** to view analysis"
        )


# ==============================================================================
# FILTER CONTROLS
# ==============================================================================


def _render_filter_controls() -> dict:
    """Render sidebar filter controls and return selected values."""
    st.sidebar.header("📊 Trend Filters")

    # Get available bid periods for filter options
    try:
        bid_periods_df = get_bid_periods()

        if bid_periods_df.empty:
            st.sidebar.warning("⚠️ No bid periods in database")
            return {}

    except Exception as e:
        st.sidebar.error(f"❌ Error loading data: {str(e)}")
        return {}

    # Domicile Filter
    domiciles = sorted(bid_periods_df["domicile"].unique())
    selected_domicile = st.sidebar.selectbox(
        "Domicile",
        options=["All"] + domiciles,
        key="trends_domicile",
        help="Select a domicile to analyze (or 'All' for comparison)",
    )

    # Aircraft Filter
    aircraft_list = sorted(bid_periods_df["aircraft"].unique())
    selected_aircraft = st.sidebar.selectbox(
        "Aircraft",
        options=["All"] + aircraft_list,
        key="trends_aircraft",
        help="Select an aircraft type (or 'All' for comparison)",
    )

    # Seat Filter
    selected_seat = st.sidebar.selectbox(
        "Seat Position",
        options=["All", "CA", "FO"],
        format_func=lambda x: (
            "All" if x == "All" else ("Captain" if x == "CA" else "First Officer")
        ),
        key="trends_seat",
        help="Select seat position (or 'All' for comparison)",
    )

    # Metric Selection
    st.sidebar.markdown("### Metrics to Display")

    selected_metrics = []

    st.sidebar.markdown("**Bid Line Metrics:**")
    if st.sidebar.checkbox("Credit Time (CT)", value=True, key="metric_ct"):
        selected_metrics.append("ct_avg")
    if st.sidebar.checkbox("Block Time (BT)", value=True, key="metric_bt"):
        selected_metrics.append("bt_avg")
    if st.sidebar.checkbox("Days Off (DO)", value=False, key="metric_do"):
        selected_metrics.append("do_avg")
    if st.sidebar.checkbox("Duty Days (DD)", value=False, key="metric_dd"):
        selected_metrics.append("dd_avg")

    st.sidebar.markdown("**Pairing Metrics:**")
    if st.sidebar.checkbox("EDW Trip %", value=True, key="metric_edw_pct"):
        selected_metrics.append("edw_trip_pct")
    if st.sidebar.checkbox("Total Trips", value=False, key="metric_trips"):
        selected_metrics.append("total_trips_detail")

    # Build filters dict
    filters = {
        "domicile": None if selected_domicile == "All" else selected_domicile,
        "aircraft": None if selected_aircraft == "All" else selected_aircraft,
        "seat": None if selected_seat == "All" else selected_seat,
        "metrics": selected_metrics,
    }

    # Show filter summary
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Filter Summary")
    st.sidebar.caption(f"**Domicile:** {selected_domicile}")
    st.sidebar.caption(f"**Aircraft:** {selected_aircraft}")
    st.sidebar.caption(f"**Seat:** {selected_seat}")
    st.sidebar.caption(f"**Metrics:** {len(selected_metrics)} selected")

    return filters


# ==============================================================================
# DATA LOADING
# ==============================================================================


def _load_trend_data(filters: dict) -> pd.DataFrame:
    """Load trend data based on selected filters."""
    try:
        df = get_historical_trends(
            domicile=filters.get("domicile"),
            aircraft=filters.get("aircraft"),
            seat=filters.get("seat"),
        )

        if not df.empty:
            # Convert dates
            df["start_date"] = pd.to_datetime(df["start_date"])
            df["end_date"] = pd.to_datetime(df["end_date"])

            # Sort by date
            df = df.sort_values("start_date")

        return df

    except Exception as e:
        st.error(f"❌ Error loading trend data: {str(e)}")
        return pd.DataFrame()


# ==============================================================================
# TREND DISPLAY
# ==============================================================================


def _display_trends(df: pd.DataFrame, filters: dict):
    """Display trend visualizations and analysis."""
    metrics = filters.get("metrics", [])

    if not metrics:
        st.warning("⚠️ Please select at least one metric to display")
        return

    # Summary statistics
    _display_summary_stats(df, filters)

    st.markdown("---")

    # Time series charts
    st.subheader("📈 Trend Analysis")

    # Determine if we're comparing multiple entities
    is_comparison = (
        filters.get("domicile") is None
        or filters.get("aircraft") is None
        or filters.get("seat") is None
    )

    if is_comparison:
        _display_comparison_charts(df, metrics, filters)
    else:
        _display_time_series_charts(df, metrics, filters)

    st.markdown("---")

    # Data table
    _display_data_table(df)


def _display_summary_stats(df: pd.DataFrame, filters: dict):
    """Display summary statistics for the selected data."""
    st.subheader("📊 Summary Statistics")

    # Determine what we're analyzing
    if filters.get("domicile") and filters.get("aircraft") and filters.get("seat"):
        title = f"{filters['domicile']} {filters['aircraft']} {filters['seat']}"
    elif filters.get("domicile"):
        title = f"{filters['domicile']} (All Aircraft/Seats)"
    elif filters.get("aircraft"):
        title = f"{filters['aircraft']} (All Domiciles/Seats)"
    else:
        title = "All Bid Periods"

    st.caption(f"**Analyzing:** {title}")
    st.caption(
        f"**Bid Periods:** {len(df)} | **Date Range:** {df['start_date'].min().strftime('%Y-%m-%d')} to {df['end_date'].max().strftime('%Y-%m-%d')}"
    )

    # Show metrics in columns
    cols = st.columns(4)

    # Bid Line Metrics
    with cols[0]:
        if "ct_avg" in df.columns and df["ct_avg"].notna().any():
            avg_ct = df["ct_avg"].mean()
            st.metric("Avg Credit Time", f"{avg_ct:.1f} hrs")

    with cols[1]:
        if "bt_avg" in df.columns and df["bt_avg"].notna().any():
            avg_bt = df["bt_avg"].mean()
            st.metric("Avg Block Time", f"{avg_bt:.1f} hrs")

    with cols[2]:
        if "do_avg" in df.columns and df["do_avg"].notna().any():
            avg_do = df["do_avg"].mean()
            st.metric("Avg Days Off", f"{avg_do:.1f}")

    with cols[3]:
        if "dd_avg" in df.columns and df["dd_avg"].notna().any():
            avg_dd = df["dd_avg"].mean()
            st.metric("Avg Duty Days", f"{avg_dd:.1f}")

    # Pairing Metrics (second row)
    cols2 = st.columns(4)

    with cols2[0]:
        if "edw_trip_pct" in df.columns and df["edw_trip_pct"].notna().any():
            avg_edw = df["edw_trip_pct"].mean()
            st.metric("Avg EDW %", f"{avg_edw:.1f}%")

    with cols2[1]:
        if (
            "total_trips_detail" in df.columns
            and df["total_trips_detail"].notna().any()
        ):
            avg_trips = df["total_trips_detail"].mean()
            st.metric("Avg Total Trips", f"{avg_trips:.0f}")


def _display_time_series_charts(df: pd.DataFrame, metrics: List[str], filters: dict):
    """Display time series charts for a single entity."""
    st.markdown("**Time Series Trends**")

    # Create metric label map
    metric_labels = {
        "ct_avg": "Average Credit Time (hours)",
        "bt_avg": "Average Block Time (hours)",
        "do_avg": "Average Days Off",
        "dd_avg": "Average Duty Days",
        "edw_trip_pct": "EDW Trip Percentage (%)",
        "total_trips_detail": "Total Trips",
    }

    for metric in metrics:
        if metric in df.columns and df[metric].notna().any():
            fig = px.line(
                df,
                x="start_date",
                y=metric,
                title=metric_labels.get(metric, metric),
                markers=True,
            )

            fig.update_layout(
                xaxis_title="Bid Period Start Date",
                yaxis_title=metric_labels.get(metric, metric),
                hovermode="x unified",
                height=400,
            )

            st.plotly_chart(fig, width="stretch")


def _display_comparison_charts(df: pd.DataFrame, metrics: List[str], filters: dict):
    """Display comparison charts across multiple entities."""
    st.markdown("**Comparative Analysis**")

    # Determine comparison dimension
    if filters.get("domicile") is None:
        color_by = "domicile"
        title_suffix = "by Domicile"
    elif filters.get("aircraft") is None:
        color_by = "aircraft"
        title_suffix = "by Aircraft"
    elif filters.get("seat") is None:
        color_by = "seat"
        title_suffix = "by Seat Position"
    else:
        # Shouldn't happen, but fallback
        color_by = "domicile"
        title_suffix = ""

    # Create metric label map
    metric_labels = {
        "ct_avg": "Average Credit Time (hours)",
        "bt_avg": "Average Block Time (hours)",
        "do_avg": "Average Days Off",
        "dd_avg": "Average Duty Days",
        "edw_trip_pct": "EDW Trip Percentage (%)",
        "total_trips_detail": "Total Trips",
    }

    for metric in metrics:
        if metric in df.columns and df[metric].notna().any():
            fig = px.line(
                df,
                x="start_date",
                y=metric,
                color=color_by,
                title=f"{metric_labels.get(metric, metric)} {title_suffix}",
                markers=True,
            )

            fig.update_layout(
                xaxis_title="Bid Period Start Date",
                yaxis_title=metric_labels.get(metric, metric),
                hovermode="x unified",
                height=400,
                legend_title=color_by.title(),
            )

            st.plotly_chart(fig, width="stretch")


def _display_data_table(df: pd.DataFrame):
    """Display raw trend data in a table."""
    with st.expander("📋 View Raw Data"):
        # Select display columns
        display_cols = [
            "period",
            "domicile",
            "aircraft",
            "seat",
            "start_date",
            "end_date",
            "ct_avg",
            "bt_avg",
            "do_avg",
            "dd_avg",
            "edw_trip_pct",
            "total_trips_detail",
        ]

        # Only include columns that exist
        display_cols = [col for col in display_cols if col in df.columns]

        st.dataframe(
            df[display_cols],
            width="stretch",
            hide_index=True,
        )
