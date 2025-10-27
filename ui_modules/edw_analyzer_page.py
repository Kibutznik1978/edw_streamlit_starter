"""EDW Pairing Analyzer page (Tab 1)."""

import io
import tempfile
from pathlib import Path
from typing import Dict

import streamlit as st

from edw import run_edw_report, parse_trip_for_table, extract_pdf_header_info, is_edw_trip
from export_pdf import create_pdf_report


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

    # Extract header info when file is uploaded
    if uploaded is not None:
        # Save to temp file to extract header info
        tmpdir = Path(tempfile.mkdtemp())
        pdf_path = tmpdir / uploaded.name
        pdf_path.write_bytes(uploaded.getvalue())

        # Extract header information
        header_info = extract_pdf_header_info(pdf_path)
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
        key="edw_notes"
    )

    # Initialize session state for results
    if "edw_results" not in st.session_state:
        st.session_state.edw_results = None

    run = st.button("Run Analysis", disabled=(uploaded is None), key="edw_run")
    if run:
        if uploaded is None:
            st.warning("Please upload a PDF first.")
            st.stop()

        if st.session_state.edw_header_info is None:
            st.error("Could not extract header information from PDF. Please check the PDF format.")
            st.stop()

        # Create progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()

        def update_progress(progress, message):
            progress_bar.progress(progress / 100)
            status_text.text(message)

        tmpdir = Path(tempfile.mkdtemp())
        pdf_path = tmpdir / uploaded.name
        pdf_path.write_bytes(uploaded.getvalue())

        out_dir = tmpdir / "outputs"
        out_dir.mkdir(exist_ok=True)

        # Use extracted header info
        header = st.session_state.edw_header_info
        dom = header['domicile']
        ac = header['fleet_type']
        bid = header['bid_period']

        res = run_edw_report(
            pdf_path,
            out_dir,
            domicile=dom,
            aircraft=ac,
            bid_period=bid,
            progress_callback=update_progress,
        )

        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()

        # Store results in session state
        st.session_state.edw_results = {
            "res": res,
            "out_dir": out_dir,
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
        display_edw_results(st.session_state.edw_results)

    st.caption(
        "Notes: EDW = any duty day touches 02:30–05:00 local (inclusive). "
        "Local hour comes from the number in parentheses ( ), minutes from the following Z time."
    )


def display_edw_results(result_data: Dict):
    """Display EDW analysis results."""

    out_dir = result_data["out_dir"]
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

    # Duty Day Distribution
    st.subheader("Trip Length Distribution (excludes Hot Standby)")

    # Calculate 1-day trip count for display
    original_duty_dist = res["duty_dist"].copy()
    one_day_trips = original_duty_dist[original_duty_dist["Duty Days"] == 1]["Trips"].sum() if 1 in original_duty_dist["Duty Days"].values else 0
    multi_day_trips = original_duty_dist[original_duty_dist["Duty Days"] != 1]["Trips"].sum()
    total_dist_trips = original_duty_dist["Trips"].sum()

    # Toggle to exclude 1-day trips
    exclude_turns = st.checkbox(
        "Exclude 1-day trips (turns)",
        value=False,
        help=f"Remove {one_day_trips} single-day trips ({one_day_trips/total_dist_trips*100:.1f}% of total) to focus on {multi_day_trips} multi-day pairings",
        key="edw_exclude_turns"
    )

    duty_dist = original_duty_dist.copy()

    # Filter out 1-day trips if checkbox is checked
    if exclude_turns:
        duty_dist = duty_dist[duty_dist["Duty Days"] != 1].copy()
        # Recalculate percentages based on filtered data
        if len(duty_dist) > 0:
            duty_dist["Percent"] = (duty_dist["Trips"] / duty_dist["Trips"].sum() * 100).round(1)
            st.caption(f"📊 Showing {multi_day_trips} multi-day trips (excluding {one_day_trips} turns)")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Duty Days vs Trips**")
        if len(duty_dist) > 0:
            st.bar_chart(duty_dist.set_index("Duty Days")["Trips"], x_label="Duty Days", y_label="Trips")
        else:
            st.info("No trips to display with current filter")
    with col2:
        st.markdown("**Duty Days vs Percentage**")
        if len(duty_dist) > 0:
            st.bar_chart(duty_dist.set_index("Duty Days")["Percent"], x_label="Duty Days", y_label="Percent")
        else:
            st.info("No trips to display with current filter")

    st.divider()

    # === TRIP RECORDS PREVIEW ===
    st.header("🗂️ Trip Records")
    df_trips = res["df_trips"]

    # Filters section
    st.subheader("Advanced Filters")

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
            key="edw_duty_threshold"
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
            key="edw_legs_threshold"
        )

    # Duty Day Criteria Filters
    st.markdown("---")
    st.markdown("**🔍 Duty Day Criteria** - Find duty days matching multiple conditions")
    st.caption("Filter pairings where a single duty day meets ALL selected criteria below")

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
            key="edw_duty_duration_min"
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
            key="edw_legs_min"
        )

    with col_dd3:
        st.markdown("**EDW Status**")
        duty_day_edw_filter = st.selectbox(
            "Status:",
            ["Any", "EDW Only", "Non-EDW Only"],
            index=0,
            help="Filter by whether the duty day touches the EDW window (02:30-05:00 local)",
            key="edw_dd_edw_filter"
        )

    # Match mode
    match_mode = st.radio(
        "Match mode:",
        ["Disabled", "Any duty day matches", "All duty days match"],
        index=0,
        horizontal=True,
        help="'Any' = at least one duty day meets criteria. 'All' = every duty day meets criteria.",
        key="edw_match_mode"
    )

    st.markdown("---")

    # Add filters
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_edw = st.selectbox("Filter by EDW:", ["All", "EDW Only", "Day Only"], key="edw_filter_edw")
    with col2:
        filter_hs = st.selectbox("Filter by Hot Standby:", ["All", "Hot Standby Only", "Exclude Hot Standby"], key="edw_filter_hs")
    with col3:
        sort_by = st.selectbox("Sort by:", ["Trip ID", "Frequency", "TAFB Hours", "Duty Days", "Max Duty Length", "Max Legs/Duty"], key="edw_sort_by")

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
            duration_ok = duty_day['duration_hours'] >= duty_duration_min
            legs_ok = duty_day['num_legs'] >= legs_min

            # Check EDW status
            edw_ok = True
            if duty_day_edw_filter == "EDW Only":
                edw_ok = duty_day.get('is_edw', False) == True
            elif duty_day_edw_filter == "Non-EDW Only":
                edw_ok = duty_day.get('is_edw', False) == False
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
        filtered_df = filtered_df[filtered_df["EDW"] == True]
    elif filter_edw == "Day Only":
        filtered_df = filtered_df[filtered_df["EDW"] == False]

    # Filter by Hot Standby status
    if filter_hs == "Hot Standby Only":
        filtered_df = filtered_df[filtered_df["Hot Standby"] == True]
    elif filter_hs == "Exclude Hot Standby":
        filtered_df = filtered_df[filtered_df["Hot Standby"] == False]

    # Sort
    filtered_df = filtered_df.sort_values(by=sort_by, ascending=False if sort_by in ["Frequency", "TAFB Hours", "Duty Days", "Max Duty Length", "Max Legs/Duty"] else True)

    st.dataframe(filtered_df[[col for col in filtered_df.columns if col != "Duty Day Details"]], hide_index=True)
    st.caption(f"Showing {len(filtered_df)} of {len(df_trips)} pairings")

    # === TRIP DETAILS VIEWER ===
    st.subheader("📋 View Pairing Details")

    # Get trip text map from result data
    trip_text_map = result_data.get("trip_text_map", {})

    if trip_text_map and len(filtered_df) > 0:
        # Get list of Trip IDs from filtered results
        available_trip_ids = sorted(filtered_df["Trip ID"].dropna().unique())

        if len(available_trip_ids) > 0:
            selected_trip_id = st.selectbox(
                "Select a Trip ID to view full pairing details:",
                options=available_trip_ids,
                format_func=lambda x: f"Trip {int(x)}",
                key="edw_trip_selector"
            )

            # Display the selected trip details in an expander
            if selected_trip_id in trip_text_map:
                with st.expander(f"📄 Trip Details - {int(selected_trip_id)}", expanded=True):
                    trip_text = trip_text_map[selected_trip_id]

                    # Parse the trip
                    trip_data = parse_trip_for_table(trip_text, is_edw_trip)

                    # Display date/frequency if available
                    if trip_data['date_freq']:
                        st.caption(trip_data['date_freq'])

                    # Display as styled HTML table
                    st.markdown("""
                    <style>
                    .trip-detail-container {
                        max-width: 50%;
                        margin: 0 auto;
                        overflow-x: auto;
                    }
                    @media (max-width: 1200px) {
                        .trip-detail-container {
                            max-width: 80%;
                        }
                    }
                    @media (max-width: 768px) {
                        .trip-detail-container {
                            max-width: 100%;
                        }
                    }
                    .trip-table {
                        width: 100%;
                        border-collapse: collapse;
                        font-family: 'Courier New', monospace;
                        font-size: 11px;
                    }
                    .trip-table th {
                        background-color: #e0e0e0;
                        padding: 6px 4px;
                        text-align: left;
                        border: 1px solid #999;
                        font-weight: bold;
                        font-size: 10px;
                    }
                    .trip-table td {
                        padding: 4px;
                        border: 1px solid #ccc;
                        font-size: 11px;
                    }
                    .trip-table .subtotal-row {
                        background-color: #f5f5f5;
                        font-weight: bold;
                        border-top: 2px solid #666;
                    }
                    .trip-table .summary-row {
                        background-color: #d6eaf8;
                        font-weight: bold;
                        border-top: 3px solid #333;
                    }
                    </style>
                    """, unsafe_allow_html=True)

                    # Build table HTML (wrapped in container for width control)
                    table_html = """
                    <div class="trip-detail-container">
                    <table class="trip-table">
                        <thead>
                            <tr>
                                <th>Day</th>
                                <th>Flight</th>
                                <th>Dep-Arr</th>
                                <th>Depart (L) Z</th>
                                <th>Arrive (L) Z</th>
                                <th>Blk</th>
                                <th>Cxn</th>
                                <th>Duty</th>
                                <th>Cr</th>
                                <th>L/O</th>
                            </tr>
                        </thead>
                        <tbody>
                    """

                    # Add rows for each duty day
                    for duty_idx, duty in enumerate(trip_data['duty_days'], 1):
                        # Add duty start row (Briefing)
                        if duty.get('duty_start'):
                            table_html += "<tr style='background-color: #f9f9f9; font-style: italic;'>"
                            table_html += "<td colspan='3'><i>Briefing</i></td>"
                            table_html += f"<td>{duty['duty_start']}</td>"  # Depart column
                            table_html += "<td></td>"  # Arrive column
                            table_html += "<td colspan='5'></td>"
                            table_html += "</tr>"

                        # Add flights for this duty day
                        for flight_idx, flight in enumerate(duty['flights']):
                            table_html += "<tr>"

                            # Day
                            table_html += f"<td>{flight.get('day') or ''}</td>"

                            # Flight number
                            table_html += f"<td>{flight.get('flight') or ''}</td>"

                            # Route
                            table_html += f"<td>{flight.get('route') or ''}</td>"

                            # Depart time
                            table_html += f"<td>{flight.get('depart') or ''}</td>"

                            # Arrive time
                            table_html += f"<td>{flight.get('arrive') or ''}</td>"

                            # Block time
                            table_html += f"<td>{flight.get('block') or ''}</td>"

                            # Connection
                            table_html += f"<td>{flight.get('connection') or ''}</td>"

                            # Duty, Cr, L/O only on first row of duty day
                            if flight_idx == 0:
                                table_html += f"<td rowspan='{len(duty['flights'])}'></td>"
                                table_html += f"<td rowspan='{len(duty['flights'])}'></td>"
                                table_html += f"<td rowspan='{len(duty['flights'])}'></td>"

                            table_html += "</tr>"

                        # Add duty end row (Debriefing)
                        if duty.get('duty_end'):
                            table_html += "<tr style='background-color: #f9f9f9; font-style: italic;'>"
                            table_html += "<td colspan='3'><i>Debriefing</i></td>"
                            table_html += "<td></td>"  # Depart column
                            table_html += f"<td>{duty['duty_end']}</td>"  # Arrive column
                            table_html += "<td colspan='5'></td>"
                            table_html += "</tr>"

                        # Subtotal row for this duty day
                        table_html += "<tr class='subtotal-row'>"
                        table_html += "<td colspan='5' style='text-align: right;'>Duty Day Subtotal:</td>"
                        table_html += f"<td>{duty.get('block_total') or ''}</td>"
                        table_html += "<td></td>"
                        table_html += f"<td>{duty.get('duty_time') or ''}</td>"
                        table_html += f"<td>{duty.get('credit') or ''}</td>"
                        table_html += f"<td>{duty.get('rest') or ''}</td>"
                        table_html += "</tr>"

                    # Add trip summary section at bottom of table
                    summary = trip_data['trip_summary']
                    if summary:
                        # Header row for trip summary
                        table_html += "<tr style='border-top: 3px solid #333; background-color: #d6eaf8;'>"
                        table_html += "<td colspan='10' style='padding: 6px; font-weight: bold; text-align: center; font-size: 12px;'>TRIP SUMMARY</td>"
                        table_html += "</tr>"

                        # Create structured table within the summary row
                        table_html += "<tr style='background-color: #f0f8ff;'>"
                        table_html += "<td colspan='10' style='padding: 10px;'>"
                        table_html += "<table style='width: 100%; border-collapse: collapse; font-family: \"Courier New\", monospace; font-size: 11px;'>"

                        # Row 1: Credit, Blk, Duty Time, TAFB, Duty Days
                        table_html += "<tr>"
                        if 'Credit' in summary:
                            table_html += f"<td style='padding: 3px; white-space: nowrap;'><b>Credit:</b> {summary['Credit']}</td>"
                        if 'Blk' in summary:
                            table_html += f"<td style='padding: 3px; white-space: nowrap;'><b>Blk:</b> {summary['Blk']}</td>"
                        if 'Duty Time' in summary:
                            table_html += f"<td style='padding: 3px; white-space: nowrap;'><b>Duty Time:</b> {summary['Duty Time']}</td>"
                        if 'TAFB' in summary:
                            table_html += f"<td style='padding: 3px; white-space: nowrap;'><b>TAFB:</b> {summary['TAFB']}</td>"
                        if 'Duty Days' in summary:
                            table_html += f"<td style='padding: 3px; white-space: nowrap;'><b>Duty Days:</b> {summary['Duty Days']}</td>"
                        table_html += "</tr>"

                        # Row 2: Prem, PDiem, LDGS, Crew, Domicile
                        table_html += "<tr>"
                        if 'Prem' in summary:
                            prem_val = summary['Prem'] if summary['Prem'].startswith('$') else f"${summary['Prem']}"
                            table_html += f"<td style='padding: 3px; white-space: nowrap;'><b>Prem:</b> {prem_val}</td>"
                        if 'PDiem' in summary:
                            pdiem_val = summary['PDiem'] if summary['PDiem'].startswith('$') else f"${summary['PDiem']}"
                            table_html += f"<td style='padding: 3px; white-space: nowrap;'><b>PDiem:</b> {pdiem_val}</td>"
                        if 'LDGS' in summary:
                            table_html += f"<td style='padding: 3px; white-space: nowrap;'><b>LDGS:</b> {summary['LDGS']}</td>"
                        if 'Crew' in summary:
                            table_html += f"<td style='padding: 3px; white-space: nowrap;'><b>Crew:</b> {summary['Crew']}</td>"
                        if 'Domicile' in summary:
                            table_html += f"<td style='padding: 3px; white-space: nowrap;'><b>Domicile:</b> {summary['Domicile']}</td>"
                        table_html += "</tr>"

                        table_html += "</table>"
                        table_html += "</td>"
                        table_html += "</tr>"

                    table_html += """
                        </tbody>
                    </table>
                    </div>
                    """

                    st.markdown(table_html, unsafe_allow_html=True)

                    # Raw text toggle
                    with st.expander("🔍 View Raw Text", expanded=False):
                        st.text_area(
                            "Raw Pairing Text",
                            value=trip_text,
                            height=400,
                            disabled=True,
                            label_visibility="collapsed",
                            key="edw_raw_text"
                        )
            else:
                st.warning(f"Trip ID {int(selected_trip_id)} not found in trip text map.")
        else:
            st.info("No trips available in filtered results. Adjust your filters to see trip details.")
    else:
        st.info("Run analysis first to view trip details.")

    st.divider()

    # === DOWNLOAD SECTION ===
    st.header("⬇️ Download Reports")

    col1, col2 = st.columns(2)

    with col1:
        # Excel
        xlsx = out_dir / f"{dom}_{ac}_Bid{bid}_EDW_Report_Data.xlsx"
        st.download_button(
            "📊 Download Excel Workbook",
            data=xlsx.read_bytes(),
            file_name=xlsx.name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="download_edw_excel",
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
                    "Trip-weighted EDW trip %": result_data["res"]["weighted_summary"].loc[0, "Value"],
                    "TAFB-weighted EDW trip %": result_data["res"]["weighted_summary"].loc[1, "Value"],
                    "Duty-day-weighted EDW trip %": result_data["res"]["weighted_summary"].loc[2, "Value"],
                },
                "duty_day_stats": [
                    ["Metric", "All", "EDW", "Non-EDW"],
                    ["Avg Legs/Duty Day",
                     str(result_data["res"]["duty_day_stats"].loc[0, "All"]),
                     str(result_data["res"]["duty_day_stats"].loc[0, "EDW"]),
                     str(result_data["res"]["duty_day_stats"].loc[0, "Non-EDW"])],
                    ["Avg Duty Day Length",
                     str(result_data["res"]["duty_day_stats"].loc[1, "All"]),
                     str(result_data["res"]["duty_day_stats"].loc[1, "EDW"]),
                     str(result_data["res"]["duty_day_stats"].loc[1, "Non-EDW"])],
                    ["Avg Block Time",
                     str(result_data["res"]["duty_day_stats"].loc[2, "All"]),
                     str(result_data["res"]["duty_day_stats"].loc[2, "EDW"]),
                     str(result_data["res"]["duty_day_stats"].loc[2, "Non-EDW"])],
                    ["Avg Credit Time",
                     str(result_data["res"]["duty_day_stats"].loc[3, "All"]),
                     str(result_data["res"]["duty_day_stats"].loc[3, "EDW"]),
                     str(result_data["res"]["duty_day_stats"].loc[3, "Non-EDW"])],
                ],
                "trip_length_distribution": [
                    {
                        "duty_days": int(row["Duty Days"]),
                        "trips": int(row["Trips"])
                    }
                    for _, row in result_data["res"]["duty_dist"].iterrows()
                ],
                "notes": result_data.get("notes", ""),
                "generated_by": "Hot Standby pairings were excluded from trip-length distribution.",
            }

            # Create branding with proper header
            branding = {
                "primary_hex": "#1E40AF",
                "accent_hex": "#F3F4F6",
                "rule_hex": "#E5E7EB",
                "muted_hex": "#6B7280",
                "bg_alt_hex": "#FAFAFA",
                "logo_path": None,
                "title_left": f"{dom} {ac} – Bid {bid} | Pairing Analysis Report"
            }

            # Create temporary file for PDF
            temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            create_pdf_report(pdf_data, temp_pdf.name, branding)

            # Read the PDF bytes
            with open(temp_pdf.name, 'rb') as f:
                pdf_bytes = f.read()

            # Clean up temp file
            import os
            os.unlink(temp_pdf.name)

            st.download_button(
                "📄 Download Executive PDF Report",
                data=pdf_bytes,
                file_name=f"{dom}_{ac}_Bid{bid}_Executive_Report.pdf",
                mime="application/pdf",
                key="download_edw_pdf",
            )
        except Exception as e:
            st.error(f"Error generating professional PDF: {e}")
            # Fallback to old PDF if available
            if "report_pdf" in res:
                st.download_button(
                    "📄 Download PDF Report (Basic)",
                    data=res["report_pdf"].read_bytes(),
                    file_name=res["report_pdf"].name,
                    mime="application/pdf",
                    key="download_edw_pdf_fallback",
                )
