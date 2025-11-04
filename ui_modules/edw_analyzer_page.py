"""EDW Pairing Analyzer page (Tab 1)."""

import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict

import pandas as pd
import streamlit as st

from auth import get_current_user_id, is_admin
from database import (
    check_duplicate_bid_period,
    check_pairings_exist,
    delete_pairings,
    get_supabase_client,
    refresh_trends,
    save_bid_period,
    save_pairings,
)
from edw import extract_pdf_header_info, run_edw_report
from pdf_generation import create_edw_pdf_report
from ui_components import (
    generate_edw_filename,
    handle_pdf_generation_error,
    render_download_section,
    render_excel_download,
    render_no_upload_state,
    render_pdf_download,
    render_trip_details_viewer,
)


# ===================================================================
# CACHED FUNCTIONS (Performance Optimization)
# ===================================================================


@st.cache_data(show_spinner="Extracting header information...")
def _extract_edw_header_cached(file_bytes: bytes, filename: str) -> dict:
    """
    Extract header info from EDW PDF with caching.

    This function caches the result so header extraction only happens once
    per file, preventing expensive re-parsing on every widget interaction.

    Args:
        file_bytes: Raw PDF file bytes
        filename: Original filename (for temp file creation)

    Returns:
        Dictionary with header information
    """
    tmpdir = Path(tempfile.mkdtemp())
    pdf_path = tmpdir / filename
    pdf_path.write_bytes(file_bytes)

    return extract_pdf_header_info(pdf_path)


@st.cache_data(show_spinner="Running EDW analysis...")
def _run_edw_report_cached(
    file_bytes: bytes,
    filename: str,
    domicile: str,
    aircraft: str,
    bid_period: str
):
    """
    Run EDW report analysis with caching.

    This function caches the result so the expensive PDF parsing and analysis
    only happens once per file, dramatically improving performance.

    Args:
        file_bytes: Raw PDF file bytes
        filename: Original filename
        domicile: Domicile code
        aircraft: Aircraft type
        bid_period: Bid period identifier

    Returns:
        EDW analysis results dictionary
    """
    tmpdir = Path(tempfile.mkdtemp())
    pdf_path = tmpdir / filename
    pdf_path.write_bytes(file_bytes)

    out_dir = tmpdir / "outputs"
    out_dir.mkdir(exist_ok=True)

    # Note: progress callback doesn't work with caching
    # Results are instant after first analysis anyway
    return run_edw_report(
        pdf_path,
        out_dir,
        domicile=domicile,
        aircraft=aircraft,
        bid_period=bid_period,
        progress_callback=None,
    )


def render_edw_analyzer():
    """Render the EDW Pairing Analyzer tab."""

    st.markdown(
        "Upload a formatted Pairing PDF. I'll return an **Excel** workbook and a **3-page PDF** "
        "with the trip-length breakdown, EDW vs Day, and length-weighted explanation."
    )

    uploaded = st.file_uploader("Pairings PDF", type=["pdf"], key="edw_uploader")

    # Initialize session state for header info
    if "edw_header_info" not in st.session_state:
        st.session_state.edw_header_info = None

    # Extract header info when file is uploaded (CACHED - only runs once per file)
    if uploaded is not None:
        # Use cached extraction - this only runs once per unique file
        header_info = _extract_edw_header_cached(
            uploaded.getvalue(),
            uploaded.name
        )
        st.session_state.edw_header_info = header_info

        # Display extracted information in an info box
        st.info(
            f"**Extracted from PDF:**\n\n"
            f"📅 Bid Period: **{header_info['bid_period']}**\n\n"
            f"🏠 Domicile: **{header_info['domicile']}**\n\n"
            f"✈️ Fleet Type: **{header_info['fleet_type']}**\n\n"
            f"📆 Date Range: **{header_info['date_range']}**\n\n"
            f"🕒 Report Date: **{header_info['report_date']}**"
        )

    # Add notes section
    notes = st.text_area(
        "Notes (Optional)",
        placeholder="e.g., Final Data, Round 1, Round 2, etc.",
        help="Add any notes about this data set (e.g., whether this is final data or an early round)",
        key="edw_notes",
    )

    # Initialize session state for results
    if "edw_results" not in st.session_state:
        st.session_state.edw_results = None

    run = st.button("Run Analysis", disabled=(uploaded is None), key="edw_run")
    if run:
        if uploaded is None:
            render_no_upload_state(
                upload_type="pairing PDF",
                file_description="pairing PDF from your computer"
            )
            st.stop()

        if st.session_state.edw_header_info is None:
            st.error("Could not extract header information from PDF. Please check the PDF format.")
            st.stop()

        # Use extracted header info
        header = st.session_state.edw_header_info
        dom = header["domicile"]
        ac = header["fleet_type"]
        bid = header["bid_period"]

        # Use cached analysis - after first run, results are instant!
        res = _run_edw_report_cached(
            uploaded.getvalue(),
            uploaded.name,
            domicile=dom,
            aircraft=ac,
            bid_period=bid,
        )

        # Store results in session state (no need for separate temp dir - files already created)
        st.session_state.edw_results = {
            "res": res,
            "dom": dom,
            "ac": ac,
            "bid": bid,
            "trip_text_map": res["trip_text_map"],
            "notes": notes,
            "header_info": header,
        }

        st.success("Done! Download your files below:")

    # Display download buttons and visualizations if results exist
    if st.session_state.edw_results is not None:
        # Add "Save to Database" button (admin only)
        _render_save_to_database_button()

        display_edw_results(st.session_state.edw_results)

    st.caption(
        "Notes: EDW = any duty day touches 02:30–05:00 local (inclusive). "
        "Local hour comes from the number in parentheses ( ), minutes from the following Z time."
    )


def _render_save_to_database_button():
    """Render the 'Save to Database' button (admin only)."""

    # Get Supabase client
    try:
        supabase = get_supabase_client()
    except ValueError:
        return  # Silently skip if Supabase not configured

    # Check if user is admin
    if not is_admin(supabase):
        return  # Only admins can save to database

    # Check if already saved
    if "edw_saved_to_db" not in st.session_state:
        st.session_state.edw_saved_to_db = False

    # Get result data
    if "edw_results" not in st.session_state or st.session_state.edw_results is None:
        return

    result_data = st.session_state.edw_results

    st.divider()

    # Show save button
    col1, col2 = st.columns([3, 1])

    with col1:
        if st.session_state.edw_saved_to_db:
            st.success("✅ Data already saved to database for this analysis")
        else:
            st.info("💾 **Admin:** Save this analysis to the database for historical tracking")

    with col2:
        if not st.session_state.edw_saved_to_db:
            if st.button("💾 Save to Database", type="primary", key="edw_save_button"):
                _save_edw_to_database(result_data, supabase)


def _save_edw_to_database(result_data: Dict, supabase):
    """Save EDW analysis results to database."""

    try:
        header = result_data["header_info"]
        res = result_data["res"]

        # Parse dates from header
        date_range = header.get("date_range", "")
        try:
            # Extract start and end dates from "MM/DD/YY - MM/DD/YY" format
            parts = date_range.split(" - ")
            if len(parts) == 2:
                start_date = datetime.strptime(parts[0].strip(), "%m/%d/%y").date()
                end_date = datetime.strptime(parts[1].strip(), "%m/%d/%y").date()
            else:
                # Default to current month if parsing fails
                today = datetime.now()
                start_date = today.replace(day=1).date()
                end_date = (today.replace(day=28) + pd.Timedelta(days=4)).replace(
                    day=1
                ) - pd.Timedelta(days=1)
                end_date = end_date.date()
        except Exception:
            # Default to current month if parsing fails
            today = datetime.now()
            start_date = today.replace(day=1).date()
            end_date = (today.replace(day=28) + pd.Timedelta(days=4)).replace(day=1) - pd.Timedelta(
                days=1
            )
            end_date = end_date.date()

        # Get current user ID for audit fields
        user_id = get_current_user_id()

        if not user_id:
            st.error("❌ Could not get user ID. Please try logging out and back in.")
            return

        # Prepare bid period data
        bid_period_data = {
            "period": header["bid_period"],
            "domicile": header["domicile"],
            "aircraft": header["fleet_type"],
            "seat": "CA",  # Default to Captain, could be extracted from PDF in future
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "created_by": user_id,
            "updated_by": user_id,
        }

        # Check if bid period exists
        with st.spinner("Checking for existing bid period..."):
            existing = check_duplicate_bid_period(
                bid_period_data["period"],
                bid_period_data["domicile"],
                bid_period_data["aircraft"],
                bid_period_data["seat"],
            )

        # Reuse existing or create new bid period
        if existing:
            bid_period_id = existing["id"]
            st.info(
                f"ℹ️ Bid period {bid_period_data['period']} {bid_period_data['domicile']} "
                f"{bid_period_data['aircraft']} {bid_period_data['seat']} already exists.\n\n"
                f"Reusing existing record (ID: {bid_period_id[:8]}...)"
            )
        else:
            with st.spinner("Creating new bid period..."):
                bid_period_id = save_bid_period(bid_period_data)
            st.success(f"✅ New bid period created (ID: {bid_period_id[:8]}...)")

        # Prepare pairings data from df_trips
        df_trips = res["df_trips"]

        # Convert to database format (matching actual schema)
        pairings_records = []
        for _, row in df_trips.iterrows():
            record = {
                "trip_id": str(row["Trip ID"]),
                "is_edw": bool(row["EDW"]),
                "edw_reason": "touches_edw_window" if row["EDW"] else None,
                "tafb_hours": float(row["TAFB Hours"]),
                "num_duty_days": int(row["Duty Days"]),
                "total_credit_time": None,  # Not available in current data
                "num_legs": None,  # Not available in trip summary data
                "created_by": user_id,
                "updated_by": user_id,
            }
            pairings_records.append(record)

        # Create DataFrame for validation
        pairings_df = pd.DataFrame(pairings_records)

        # Check if pairings already exist for this bid period
        pairings_exist = check_pairings_exist(bid_period_id)

        if pairings_exist:
            # Show confirmation dialog
            st.warning(
                f"⚠️ Pairings data already exists for this bid period ({len(pairings_df)} records)"
            )
            st.markdown(
                "**Do you want to delete the existing pairings and replace with new data?**"
            )

            col1, col2 = st.columns(2)

            # Use session state to track confirmation
            if "confirm_replace_pairings" not in st.session_state:
                st.session_state.confirm_replace_pairings = False

            with col1:
                if st.button("🗑️ Delete and Replace", key="btn_replace_pairings", type="primary"):
                    st.session_state.confirm_replace_pairings = True
                    st.rerun()

            with col2:
                if st.button("❌ Cancel", key="btn_cancel_pairings"):
                    st.info("❌ Save cancelled. Existing pairings data unchanged.")
                    return

            # If confirmation flag not set, stop here
            if not st.session_state.confirm_replace_pairings:
                return

            # User confirmed - delete old pairings
            with st.spinner("Deleting existing pairings..."):
                deleted_count = delete_pairings(bid_period_id)
            st.success(f"✅ Deleted {deleted_count} existing pairings")

            # Clear confirmation flag
            st.session_state.confirm_replace_pairings = False

        # Save pairings
        with st.spinner(f"Saving {len(pairings_df)} pairings..."):
            count = save_pairings(bid_period_id, pairings_df)

        st.success(f"✅ Saved {count} pairings")

        # Refresh materialized view
        with st.spinner("Refreshing trend statistics..."):
            refresh_trends()

        st.success("✅ Trend statistics updated")

        # Mark as saved
        st.session_state.edw_saved_to_db = True

        st.success("🎉 All data saved successfully to database!")

    except Exception as e:
        st.error(f"❌ Error saving to database: {str(e)}")
        import traceback

        with st.expander("Show error details"):
            st.code(traceback.format_exc())


def display_edw_results(result_data: Dict):
    """Display EDW analysis results."""

    res = result_data["res"]
    dom = result_data["dom"]
    ac = result_data["ac"]
    bid = result_data["bid"]

    # === SUMMARY SECTION ===
    st.header("📊 Analysis Summary")

    # Display PDF header information
    if "header_info" in result_data and result_data["header_info"]:
        header = result_data["header_info"]
        st.info(
            f"**PDF Information:** Bid Period: **{header['bid_period']}** | "
            f"Domicile: **{header['domicile']}** | Fleet: **{header['fleet_type']}** | "
            f"Date Range: **{header['date_range']}**"
        )

    # Display notes if provided
    if "notes" in result_data and result_data["notes"]:
        st.success(f"**Notes:** {result_data['notes']}")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("Trip Summary")
        st.dataframe(res["trip_summary"], hide_index=True)

    with col2:
        st.subheader("Weighted Summary")
        st.dataframe(res["weighted_summary"], hide_index=True)

    with col3:
        st.subheader("Hot Standby Summary")
        st.dataframe(res["hot_standby_summary"], hide_index=True)

    # Second row - Duty Day Statistics
    st.markdown("")  # Add spacing

    st.subheader("Duty Day Statistics")
    st.dataframe(res["duty_day_stats"], hide_index=True)

    st.divider()

    # === CHARTS SECTION ===
    st.header("📈 Visualizations")

    with st.expander("📊 Trip Length Distribution", expanded=True):
        st.caption("*Excludes Hot Standby")

        # Calculate 1-day trip count for display
        original_duty_dist = res["duty_dist"].copy()
        one_day_trips = (
            original_duty_dist[original_duty_dist["Duty Days"] == 1]["Trips"].sum()
            if 1 in original_duty_dist["Duty Days"].values
            else 0
        )
        multi_day_trips = original_duty_dist[original_duty_dist["Duty Days"] != 1]["Trips"].sum()
        total_dist_trips = original_duty_dist["Trips"].sum()

        # Toggle to exclude 1-day trips
        exclude_turns = st.checkbox(
            "Exclude 1-day trips (turns)",
            value=False,
            help=f"Remove {one_day_trips} single-day trips ({one_day_trips/total_dist_trips*100:.1f}% of total) to focus on {multi_day_trips} multi-day pairings",
            key="edw_exclude_turns",
        )

        duty_dist = original_duty_dist.copy()

        # Filter out 1-day trips if checkbox is checked
        if exclude_turns:
            duty_dist = duty_dist[duty_dist["Duty Days"] != 1].copy()
            # Recalculate percentages based on filtered data
            if len(duty_dist) > 0:
                duty_dist["Percent"] = (duty_dist["Trips"] / duty_dist["Trips"].sum() * 100).round(1)
                st.caption(
                    f"📊 Showing {multi_day_trips} multi-day trips (excluding {one_day_trips} turns)"
                )

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Duty Days vs Trips**")
            if len(duty_dist) > 0:
                st.bar_chart(
                    duty_dist.set_index("Duty Days")["Trips"], x_label="Duty Days", y_label="Trips"
                )
            else:
                st.info("No trips to display with current filter")
        with col2:
            st.markdown("**Duty Days vs Percentage**")
            if len(duty_dist) > 0:
                st.bar_chart(
                    duty_dist.set_index("Duty Days")["Percent"], x_label="Duty Days", y_label="Percent"
                )
            else:
                st.info("No trips to display with current filter")

    st.divider()

    # === TRIP RECORDS PREVIEW ===
    st.header("🗂️ Trip Records")
    df_trips = res["df_trips"]

    # Filters section
    st.subheader("Filters")

    col_filter1, col_filter2 = st.columns(2)

    with col_filter1:
        st.markdown("**Max Duty Day Length**")
        max_duty_in_data = df_trips["Max Duty Length"].max()
        min_duty_threshold = st.slider(
            "Show pairings with max duty day length ≥ (hours):",
            min_value=0.0,
            max_value=float(max_duty_in_data) if max_duty_in_data > 0 else 24.0,
            value=0.0,
            step=0.5,
            help="Filter to show only pairings where the longest duty day exceeds this threshold",
            key="edw_duty_threshold",
        )

    with col_filter2:
        st.markdown("**Max Legs per Duty Day**")
        max_legs_in_data = df_trips["Max Legs/Duty"].max()
        min_legs_threshold = st.slider(
            "Show pairings with max legs per duty ≥:",
            min_value=0,
            max_value=int(max_legs_in_data) if max_legs_in_data > 0 else 10,
            value=0,
            step=1,
            help="Filter to show only pairings where any duty day has this many legs or more",
            key="edw_legs_threshold",
        )

    # Duty Day Criteria Filters
    st.markdown("---")
    st.markdown("**Duty Day Criteria**")
    st.caption("🔍 Find duty days matching multiple conditions • Filter pairings where a single duty day meets ALL selected criteria below")

    col_dd1, col_dd2, col_dd3 = st.columns(3)

    with col_dd1:
        st.markdown("**Min Duty Duration**")
        duty_duration_min = st.number_input(
            "Hours:",
            min_value=0.0,
            max_value=24.0,
            value=0.0,
            step=0.5,
            help="Show duty days with duration >= this value",
            key="edw_duty_duration_min",
        )

    with col_dd2:
        st.markdown("**Min Legs**")
        legs_min = st.number_input(
            "Legs:",
            min_value=0,
            max_value=20,
            value=0,
            step=1,
            help="Show duty days with legs >= this value",
            key="edw_legs_min",
        )

    with col_dd3:
        st.markdown("**EDW Status**")
        duty_day_edw_filter = st.selectbox(
            "Status:",
            ["Any", "EDW Only", "Non-EDW Only"],
            index=0,
            help="Filter by whether the duty day touches the EDW window (02:30-05:00 local)",
            key="edw_dd_edw_filter",
        )

    # Match mode
    match_mode = st.radio(
        "Match mode:",
        ["Disabled", "Any duty day matches", "All duty days match"],
        index=0,
        horizontal=True,
        help="'Any' = at least one duty day meets criteria. 'All' = every duty day meets criteria.",
        key="edw_match_mode",
    )

    st.markdown("---")

    # Add filters
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_edw = st.selectbox(
            "Filter by EDW:", ["All", "EDW Only", "Day Only"], key="edw_filter_edw"
        )
    with col2:
        filter_hs = st.selectbox(
            "Filter by Hot Standby:",
            ["All", "Hot Standby Only", "Exclude Hot Standby"],
            key="edw_filter_hs",
        )
    with col3:
        sort_by = st.selectbox(
            "Sort by:",
            ["Trip ID", "Frequency", "TAFB Hours", "Duty Days", "Max Duty Length", "Max Legs/Duty"],
            key="edw_sort_by",
        )

    # Apply filters
    filtered_df = df_trips.copy()

    # Filter by duty day length threshold
    if min_duty_threshold > 0:
        filtered_df = filtered_df[filtered_df["Max Duty Length"] >= min_duty_threshold]

    # Filter by legs per duty day threshold
    if min_legs_threshold > 0:
        filtered_df = filtered_df[filtered_df["Max Legs/Duty"] >= min_legs_threshold]

    # Filter by duty day criteria (combined conditions on same duty day)
    if match_mode != "Disabled":

        def duty_day_meets_criteria(duty_day):
            """Check if a single duty day meets all criteria"""
            duration_ok = duty_day["duration_hours"] >= duty_duration_min
            legs_ok = duty_day["num_legs"] >= legs_min

            # Check EDW status
            edw_ok = True
            if duty_day_edw_filter == "EDW Only":
                edw_ok = duty_day.get("is_edw", False)
            elif duty_day_edw_filter == "Non-EDW Only":
                edw_ok = not duty_day.get("is_edw", False)
            # "Any" means no EDW filter, edw_ok stays True

            return duration_ok and legs_ok and edw_ok

        def trip_matches_criteria(duty_day_details):
            """Check if trip matches based on match mode"""
            if not duty_day_details or len(duty_day_details) == 0:
                return False

            matching_days = [dd for dd in duty_day_details if duty_day_meets_criteria(dd)]

            if match_mode == "Any duty day matches":
                return len(matching_days) > 0
            elif match_mode == "All duty days match":
                return len(matching_days) == len(duty_day_details)
            return False

        filtered_df = filtered_df[filtered_df["Duty Day Details"].apply(trip_matches_criteria)]

    # Filter by EDW status
    if filter_edw == "EDW Only":
        filtered_df = filtered_df[filtered_df["EDW"]]
    elif filter_edw == "Day Only":
        filtered_df = filtered_df[~filtered_df["EDW"]]

    # Filter by Hot Standby status
    if filter_hs == "Hot Standby Only":
        filtered_df = filtered_df[filtered_df["Hot Standby"]]
    elif filter_hs == "Exclude Hot Standby":
        filtered_df = filtered_df[~filtered_df["Hot Standby"]]

    # Sort
    filtered_df = filtered_df.sort_values(
        by=sort_by,
        ascending=(
            False
            if sort_by
            in ["Frequency", "TAFB Hours", "Duty Days", "Max Duty Length", "Max Legs/Duty"]
            else True
        ),
    )

    st.dataframe(
        filtered_df[[col for col in filtered_df.columns if col != "Duty Day Details"]],
        hide_index=True,
    )
    st.caption(f"Showing {len(filtered_df)} of {len(df_trips)} pairings")

    # === TRIP DETAILS VIEWER ===
    # Get trip text map from result data
    trip_text_map = result_data.get("trip_text_map", {})

    # Use centralized trip viewer component
    render_trip_details_viewer(trip_text_map, filtered_df, key_prefix="edw")

    st.divider()

    # === DOWNLOAD SECTION ===
    render_download_section(title="⬇️ Download Reports")

    col1, col2 = st.columns(2)

    with col1:
        # Excel - use path from results (files already generated by run_edw_report)
        xlsx = res["excel"]
        render_excel_download(
            xlsx, button_label="📊 Download Excel Workbook", key="download_edw_excel"
        )

    with col2:
        # Professional Executive PDF Report
        try:
            # Prepare data for professional PDF
            pdf_data = {
                "title": f"{dom} {ac} – Bid {bid}",
                "subtitle": "Executive Dashboard • Pairing Breakdown & Duty-Day Metrics",
                "trip_summary": {
                    "Unique Pairings": result_data["res"]["trip_summary"].loc[0, "Value"],
                    "Total Trips": result_data["res"]["trip_summary"].loc[1, "Value"],
                    "EDW Trips": result_data["res"]["trip_summary"].loc[2, "Value"],
                    "Day Trips": result_data["res"]["trip_summary"].loc[3, "Value"],
                },
                "weighted_summary": {
                    "Trip-weighted EDW trip %": result_data["res"]["weighted_summary"].loc[
                        0, "Value"
                    ],
                    "TAFB-weighted EDW trip %": result_data["res"]["weighted_summary"].loc[
                        1, "Value"
                    ],
                    "Duty-day-weighted EDW trip %": result_data["res"]["weighted_summary"].loc[
                        2, "Value"
                    ],
                },
                "duty_day_stats": [
                    ["Metric", "All", "EDW", "Non-EDW"],
                    [
                        "Avg Legs/Duty Day",
                        str(result_data["res"]["duty_day_stats"].loc[0, "All"]),
                        str(result_data["res"]["duty_day_stats"].loc[0, "EDW"]),
                        str(result_data["res"]["duty_day_stats"].loc[0, "Non-EDW"]),
                    ],
                    [
                        "Avg Duty Day Length",
                        str(result_data["res"]["duty_day_stats"].loc[1, "All"]),
                        str(result_data["res"]["duty_day_stats"].loc[1, "EDW"]),
                        str(result_data["res"]["duty_day_stats"].loc[1, "Non-EDW"]),
                    ],
                    [
                        "Avg Block Time",
                        str(result_data["res"]["duty_day_stats"].loc[2, "All"]),
                        str(result_data["res"]["duty_day_stats"].loc[2, "EDW"]),
                        str(result_data["res"]["duty_day_stats"].loc[2, "Non-EDW"]),
                    ],
                    [
                        "Avg Credit Time",
                        str(result_data["res"]["duty_day_stats"].loc[3, "All"]),
                        str(result_data["res"]["duty_day_stats"].loc[3, "EDW"]),
                        str(result_data["res"]["duty_day_stats"].loc[3, "Non-EDW"]),
                    ],
                ],
                "trip_length_distribution": [
                    {"duty_days": int(row["Duty Days"]), "trips": int(row["Trips"])}
                    for _, row in result_data["res"]["duty_dist"].iterrows()
                ],
                "notes": result_data.get("notes", ""),
                "generated_by": "",
            }

            # Create branding with proper header
            branding = {
                "primary_hex": "#1E40AF",
                "accent_hex": "#F3F4F6",
                "rule_hex": "#E5E7EB",
                "muted_hex": "#6B7280",
                "bg_alt_hex": "#FAFAFA",
                "logo_path": None,
                "title_left": f"{dom} {ac} – Bid {bid} | Pairing Analysis Report",
            }

            # Create temporary file for PDF
            temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            create_edw_pdf_report(pdf_data, temp_pdf.name, branding)

            # Read the PDF bytes
            with open(temp_pdf.name, "rb") as f:
                pdf_bytes = f.read()

            # Clean up temp file
            import os

            os.unlink(temp_pdf.name)

            render_pdf_download(
                pdf_bytes,
                filename=f"{dom}_{ac}_Bid{bid}_Executive_Report.pdf",
                button_label="📄 Download Executive PDF Report",
                key="download_edw_pdf",
            )
        except Exception as e:
            handle_pdf_generation_error(e, show_traceback=False)
            # Fallback to old PDF if available
            if "report_pdf" in res:
                st.download_button(
                    "📄 Download PDF Report (Basic)",
                    data=res["report_pdf"].read_bytes(),
                    file_name=res["report_pdf"].name,
                    mime="application/pdf",
                    key="download_edw_pdf_fallback",
                )
