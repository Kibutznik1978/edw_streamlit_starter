"""
Pairing Analyzer Tool 1.0
Multi-tab application for analyzing airline bid packets.
"""

import io
import math
import tempfile
from pathlib import Path
from typing import Dict, Tuple, Optional

import numpy as np
import pandas as pd
import streamlit as st

try:
    import altair as alt
except ImportError:
    alt = None

from edw_reporter import run_edw_report, parse_trip_for_table, extract_pdf_header_info
from bid_parser import parse_bid_lines
from report_builder import ReportMetadata, build_analysis_pdf


#==============================================================================
# APP CONFIGURATION
#==============================================================================

st.set_page_config(
    page_title="Pairing Analyzer Tool 1.0",
    layout="wide",
    initial_sidebar_state="expanded"
)


#==============================================================================
# MAIN TABS
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


#==============================================================================
# TAB 1: EDW PAIRING ANALYZER
#==============================================================================

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
                    trip_data = parse_trip_for_table(trip_text)

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
        # Report PDF
        report_pdf = res["report_pdf"]
        st.download_button(
            "📄 Download PDF Report",
            data=report_pdf.read_bytes(),
            file_name=report_pdf.name,
            mime="application/pdf",
            key="download_edw_pdf",
        )


#==============================================================================
# TAB 2: BID LINE ANALYZER
#==============================================================================

def render_bid_line_analyzer():
    """Render the Bid Line Analyzer tab."""

    st.markdown("Upload a bid roster PDF to analyze line data including credit time, block time, days off, and duty days.")

    uploaded_file = st.file_uploader("Upload a bid roster PDF", type="pdf", key="bidline_uploader")

    # Initialize session state
    if "bidline_last_upload_name" not in st.session_state:
        st.session_state.bidline_last_upload_name = ""
    if "bidline_filters" not in st.session_state:
        st.session_state.bidline_filters = {}

    if uploaded_file is not None:
        file_name = getattr(uploaded_file, "name", "uploaded_roster.pdf")
        file_bytes = uploaded_file.getvalue()

        if st.session_state.get("bidline_last_upload_name") != file_name:
            st.session_state["bidline_parsed_df"] = None
            st.session_state["bidline_parsed_diag"] = None
            st.session_state["bidline_last_upload_name"] = file_name

        parse_col, _ = st.columns([1, 3])
        with parse_col:
            if st.button("Parse PDF", key="bidline_parse"):
                progress_bar = st.progress(0, text="Initializing parser...")
                status_text = st.empty()

                def update_progress(current: int, total: int):
                    progress = current / total
                    progress_bar.progress(progress, text=f"Processing page {current} of {total}...")
                    status_text.text(f"📄 Parsing: {int(progress * 100)}% complete")

                try:
                    parsed_df, diagnostics = _parse_uploaded_pdf(file_bytes, file_name, _progress_callback=update_progress)
                    progress_bar.progress(1.0, text="Parsing complete!")
                    status_text.text("✅ PDF parsed successfully")
                    st.session_state["bidline_parsed_df"] = parsed_df
                    st.session_state["bidline_parsed_diag"] = diagnostics
                finally:
                    # Clear progress indicators after a brief delay
                    import time
                    time.sleep(0.5)
                    progress_bar.empty()
                    status_text.empty()

        parsed_df = st.session_state.get("bidline_parsed_df")
        diagnostics_dict = st.session_state.get("bidline_parsed_diag")

        if parsed_df is None or diagnostics_dict is None:
            st.info("Click 'Parse PDF' to extract line data.")
        else:
            df = parsed_df.copy()

            # Convert dict entries to DataFrames as needed
            pay_periods_df = _get_dataframe_from_dict(diagnostics_dict, 'pay_periods')
            reserve_lines_df = _get_dataframe_from_dict(diagnostics_dict, 'reserve_lines')

            extraction_sources = []
            if diagnostics_dict.get('used_text'):
                extraction_sources.append("text")
            if diagnostics_dict.get('used_tables'):
                extraction_sources.append("tables")
            if extraction_sources:
                st.caption(f"Parsed via {' + '.join(extraction_sources)} extraction")

            show_diagnostics = st.sidebar.checkbox('Show parser diagnostics', value=False, key="bidline_diagnostics")
            warnings = diagnostics_dict.get('warnings', [])
            if warnings:
                if show_diagnostics:
                    with st.sidebar.expander('Parser diagnostics', expanded=True):
                        for msg in warnings:
                            st.warning(f'⚠️ {msg}')
                else:
                    st.sidebar.caption('Parser noted minor inconsistencies; enable diagnostics for details.')

            if df.empty:
                st.warning("⚠️ Could not find line data. Try exporting the PDF as Excel if issue persists.")
            else:
                filters = _build_filters(df)
                filtered_df = _apply_filters(df, filters)

                csv_buffer = io.StringIO()
                filtered_df.to_csv(csv_buffer, index=False)
                st.sidebar.download_button(
                    label="Download filtered CSV",
                    data=csv_buffer.getvalue(),
                    file_name=f"{st.session_state['bidline_last_upload_name'].rsplit('.', 1)[0]}_filtered.csv",
                    mime="text/csv",
                    key="bidline_download_csv"
                )

                try:
                    metadata = ReportMetadata(
                        title="Bid Line Analysis",
                        subtitle=f"Source: {st.session_state['bidline_last_upload_name']}",
                        filters={
                            "CT Range": [f"{filters['ct_range'][0]:.2f}", f"{filters['ct_range'][1]:.2f}"],
                            "BT Range": [f"{filters['bt_range'][0]:.2f}", f"{filters['bt_range'][1]:.2f}"],
                            "Days Off": sorted(filters['do_values']),
                            "Duty Days": sorted(filters['dd_values']),
                        },
                    )
                    pdf_bytes = build_analysis_pdf(filtered_df, metadata, pay_periods=pay_periods_df, reserve_lines=reserve_lines_df)
                    st.sidebar.download_button(
                        label="Download PDF report",
                        data=pdf_bytes,
                        file_name=f"{st.session_state['bidline_last_upload_name'].rsplit('.', 1)[0]}_analysis.pdf",
                        mime="application/pdf",
                        key="bidline_download_pdf"
                    )
                except RuntimeError as error:
                    st.sidebar.warning(str(error))
                except ValueError:
                    st.sidebar.warning("Unable to generate PDF report for the current selection.")

                st.sidebar.caption(f"Last upload: {st.session_state['bidline_last_upload_name']}")

                overview_tab, summary_tab, visuals_tab = st.tabs(["Overview", "Summary", "Visuals"])
                with overview_tab:
                    _render_overview_tab(df, filtered_df)
                with summary_tab:
                    _render_summary_tab(filtered_df, pay_periods_df, reserve_lines_df)
                with visuals_tab:
                    _render_visuals_tab(filtered_df, pay_periods_df)
    else:
        st.info("Upload a bid roster PDF to begin analysis.")


# Helper functions for Bid Line Analyzer

def _parse_uploaded_pdf(file_bytes: bytes, file_name: str, _progress_callback=None):
    """Parse uploaded PDF - caching disabled due to DataFrame serialization issues."""
    buffer = io.BytesIO(file_bytes)
    buffer.name = file_name
    df, diagnostics = parse_bid_lines(buffer, progress_callback=_progress_callback)

    # Convert diagnostics to a dict format for session state
    diag_dict = {
        'used_text': diagnostics.used_text,
        'used_tables': diagnostics.used_tables,
        'warnings': diagnostics.warnings,
        'pay_periods': diagnostics.pay_periods.to_dict('records') if diagnostics.pay_periods is not None else None,
        'reserve_lines': diagnostics.reserve_lines.to_dict('records') if diagnostics.reserve_lines is not None else None,
    }

    return df, diag_dict


def _get_dataframe_from_dict(diag_dict: dict, key: str) -> Optional[pd.DataFrame]:
    """Convert a diagnostics dict entry back to DataFrame."""
    data = diag_dict.get(key)
    if data is None or (isinstance(data, list) and len(data) == 0):
        return None
    return pd.DataFrame(data)


def _range_slider(label: str, minimum: float, maximum: float, default: Tuple[float, float]) -> Tuple[float, float]:
    if minimum == maximum:
        st.sidebar.info(f"{label}: {minimum:.1f}")
        return minimum, maximum

    low, high = default
    low = max(minimum, float(low))
    high = min(maximum, float(high))
    if low > high:
        low, high = minimum, maximum
    return st.sidebar.slider(label, minimum, maximum, value=(low, high), key=f"bidline_{label}")


def _build_filters(df: pd.DataFrame) -> Dict[str, Tuple]:
    filters = st.session_state.get("bidline_filters", {})

    st.sidebar.header("Filters")
    ct_range = filters.get("ct_range", (float(df["CT"].min()), float(df["CT"].max())))
    bt_range = filters.get("bt_range", (float(df["BT"].min()), float(df["BT"].max())))

    ct_range = _range_slider("Credit (CT)", float(df["CT"].min()), float(df["CT"].max()), ct_range)
    bt_range = _range_slider("Block (BT)", float(df["BT"].min()), float(df["BT"].max()), bt_range)

    do_options = sorted(df["DO"].unique().tolist())
    dd_options = sorted(df["DD"].unique().tolist())

    default_do = filters.get("do_values", tuple(do_options))
    default_dd = filters.get("dd_values", tuple(dd_options))

    default_do = tuple(value for value in default_do if value in do_options)
    default_dd = tuple(value for value in default_dd if value in dd_options)
    if not default_do:
        default_do = tuple(do_options)
    if not default_dd:
        default_dd = tuple(dd_options)

    selected_do = st.sidebar.multiselect("Days Off (DO)", do_options, default=list(default_do), key="bidline_do_filter")
    selected_dd = st.sidebar.multiselect("Duty Days (DD)", dd_options, default=list(default_dd), key="bidline_dd_filter")

    if not selected_do:
        selected_do = do_options
    if not selected_dd:
        selected_dd = dd_options

    active_filters = {
        "ct_range": ct_range,
        "bt_range": bt_range,
        "do_values": tuple(selected_do),
        "dd_values": tuple(selected_dd),
    }
    st.session_state["bidline_filters"] = active_filters
    return active_filters


def _apply_filters(df: pd.DataFrame, filters: Dict[str, Tuple]) -> pd.DataFrame:
    filtered = df[
        (df["CT"].between(filters["ct_range"][0], filters["ct_range"][1]))
        & (df["BT"].between(filters["bt_range"][0], filters["bt_range"][1]))
        & (df["DO"].isin(filters["do_values"]))
        & (df["DD"].isin(filters["dd_values"]))
    ]
    return filtered.copy()


def _render_overview_tab(df: pd.DataFrame, filtered_df: pd.DataFrame) -> None:
    st.write(f"Showing {len(filtered_df)} of {len(df)} parsed lines.")

    # Format the display dataframe
    display_df = filtered_df.copy()
    display_df["CT"] = display_df["CT"].round(2)
    display_df["BT"] = display_df["BT"].round(2)
    display_df["DO"] = display_df["DO"].astype(int)
    display_df["DD"] = display_df["DD"].astype(int)
    st.dataframe(display_df)

    if filtered_df.empty:
        return

    left, right = st.columns(2)
    top_credit = filtered_df.nlargest(5, "CT")[["Line", "CT", "BT", "DO", "DD"]].copy()
    most_days_off = filtered_df.nlargest(5, "DO")[["Line", "CT", "BT", "DO", "DD"]].copy()

    for df_subset in [top_credit, most_days_off]:
        df_subset["CT"] = df_subset["CT"].round(2)
        df_subset["BT"] = df_subset["BT"].round(2)
        df_subset["DO"] = df_subset["DO"].astype(int)
        df_subset["DD"] = df_subset["DD"].astype(int)

    left.markdown("**Highest Credit Lines**")
    left.dataframe(top_credit)

    right.markdown("**Most Days Off**")
    right.dataframe(most_days_off.sort_values(["DO", "CT"], ascending=[False, False]))


def _render_summary_tab(filtered_df: pd.DataFrame, pay_periods: Optional[pd.DataFrame] = None, reserve_lines: Optional[pd.DataFrame] = None) -> None:
    if filtered_df.empty:
        st.info("Add filters or upload a different roster to see summary metrics.")
        return

    metrics = filtered_df.agg({
        "CT": ["mean", "min", "max"],
        "BT": ["mean", "min", "max"],
        "DO": ["mean", "min", "max"],
        "DD": ["mean", "min", "max"],
    }).round(1)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Avg Credit", f"{metrics.loc['mean', 'CT']:.1f}", delta=f"Range {metrics.loc['min', 'CT']:.1f}-{metrics.loc['max', 'CT']:.1f}")
    col2.metric("Avg Block", f"{metrics.loc['mean', 'BT']:.1f}", delta=f"Range {metrics.loc['min', 'BT']:.1f}-{metrics.loc['max', 'BT']:.1f}")
    col3.metric("Avg Days Off", f"{metrics.loc['mean', 'DO']:.1f}", delta=f"Range {metrics.loc['min', 'DO']:.0f}-{metrics.loc['max', 'DO']:.0f}")
    col4.metric("Avg Duty Days", f"{metrics.loc['mean', 'DD']:.1f}", delta=f"Range {metrics.loc['min', 'DD']:.0f}-{metrics.loc['max', 'DD']:.0f}")

    if pay_periods is not None and not pay_periods.empty:
        subset = pay_periods[pay_periods["Line"].isin(filtered_df["Line"])]
        if not subset.empty:
            period_metrics = subset.groupby("Period")[["CT", "BT", "DO", "DD"]].mean().round(1)
            st.markdown("**Per Pay Period Averages**")
            st.dataframe(period_metrics.rename(index=lambda idx: f"PP{int(idx)}"))


def _render_visuals_tab(filtered_df: pd.DataFrame, pay_periods: Optional[pd.DataFrame] = None) -> None:
    if filtered_df.empty:
        st.info("No data to visualize with the current filters.")
        return

    st.markdown("**Credit and Block by Line**")
    chart_data = filtered_df.set_index("Line")["CT"].to_frame()
    chart_data["BT"] = filtered_df.set_index("Line")["BT"]
    st.line_chart(chart_data)

    if alt is None:
        st.info("Install altair to unlock detailed distribution charts.")
        return

    # Basic distribution charts (simplified)
    st.markdown("**Days Off Distribution**")
    do_dist = filtered_df.groupby("DO").size().reset_index(name="Lines")
    do_chart = alt.Chart(do_dist).mark_bar(color="#457B9D").encode(
        x=alt.X("DO:O", title="Days Off"),
        y=alt.Y("Lines:Q", title="Count"),
        tooltip=["DO", "Lines"]
    )
    st.altair_chart(do_chart, use_container_width=True)


#==============================================================================
# TAB 3: HISTORICAL TRENDS (PLACEHOLDER)
#==============================================================================

def render_historical_trends():
    """Render the Historical Trends tab (placeholder for now)."""

    st.markdown("### 📈 Historical Trends & Analysis")
    st.info("This feature is coming soon! It will allow you to:")
    st.markdown("""
    - 📊 View EDW percentage trends over time
    - 📉 Compare credit/block time across bid periods
    - 📅 Analyze pay period patterns
    - 🎯 Identify long-term scheduling trends
    - 💾 Requires database integration (Supabase)
    """)

    st.markdown("---")
    st.markdown("**Next Steps:**")
    st.markdown("1. Set up Supabase database (see `docs/SUPABASE_SETUP.md`)")
    st.markdown("2. Save analyzed data from EDW and Bid Line tabs")
    st.markdown("3. Build trend visualizations with historical data")


#==============================================================================
# ENTRY POINT
#==============================================================================

if __name__ == "__main__":
    main()
