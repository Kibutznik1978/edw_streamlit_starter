import tempfile
from pathlib import Path
import streamlit as st
import pandas as pd
from edw_reporter import run_edw_report, parse_trip_for_table

st.set_page_config(page_title="EDW Pairing Analyzer", layout="centered")
st.title("EDW Pairing Analyzer")

st.markdown(
    "Upload a formatted bid-pack PDF. I'll return an **Excel** workbook and a **3-page PDF** "
    "with the trip-length breakdown, EDW vs Day, and length-weighted explanation."
)

with st.expander("Labels (optional)"):
    dom = st.text_input("Domicile", value="ONT")
    ac  = st.text_input("Aircraft", value="757")
    bid = st.text_input("Bid period", value="2507")

uploaded = st.file_uploader("Pairings PDF", type=["pdf"])

# Initialize session state for results
if "results" not in st.session_state:
    st.session_state.results = None

run = st.button("Run Analysis", disabled=(uploaded is None))
if run:
    if uploaded is None:
        st.warning("Please upload a PDF first.")
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

    res = run_edw_report(
        pdf_path,
        out_dir,
        domicile=dom.strip() or "DOM",
        aircraft=ac.strip() or "AC",
        bid_period=bid.strip() or "0000",
        progress_callback=update_progress,
    )

    # Clear progress indicators
    progress_bar.empty()
    status_text.empty()

    # Store results in session state
    st.session_state.results = {
        "res": res,
        "out_dir": out_dir,
        "dom": dom,
        "ac": ac,
        "bid": bid,
        "trip_text_map": res["trip_text_map"],
    }

    st.success("Done! Download your files below:")

# Display download buttons and visualizations if results exist
if st.session_state.results is not None:
    result_data = st.session_state.results
    out_dir = result_data["out_dir"]
    res = result_data["res"]
    dom = result_data["dom"]
    ac = result_data["ac"]
    bid = result_data["bid"]

    # === SUMMARY SECTION ===
    st.header("📊 Analysis Summary")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("Trip Summary")
        st.dataframe(res["trip_summary"], hide_index=True, width="stretch")

    with col2:
        st.subheader("Weighted Summary")
        st.dataframe(res["weighted_summary"], hide_index=True, width="stretch")

    with col3:
        st.subheader("Hot Standby Summary")
        st.dataframe(res["hot_standby_summary"], hide_index=True, width="stretch")

    st.divider()

    # === CHARTS SECTION ===
    st.header("📈 Visualizations")

    # Duty Day Distribution
    st.subheader("Trip Length Distribution (excludes Hot Standby)")
    duty_dist = res["duty_dist"]

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Duty Days vs Trips**")
        st.bar_chart(duty_dist.set_index("Duty Days")["Trips"], x_label="Duty Days", y_label="Trips")
    with col2:
        st.markdown("**Duty Days vs Percentage**")
        st.bar_chart(duty_dist.set_index("Duty Days")["Percent"], x_label="Duty Days", y_label="Percent")

    st.divider()

    # === TRIP RECORDS PREVIEW ===
    st.header("🗂️ Trip Records")
    df_trips = res["df_trips"]

    # Duty Day Length Filter (slider)
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
            help="Filter to show only pairings where the longest duty day exceeds this threshold"
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
            help="Filter to show only pairings where any duty day has this many legs or more"
        )

    # Add filters
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_edw = st.selectbox("Filter by EDW:", ["All", "EDW Only", "Day Only"])
    with col2:
        filter_hs = st.selectbox("Filter by Hot Standby:", ["All", "Hot Standby Only", "Exclude Hot Standby"])
    with col3:
        sort_by = st.selectbox("Sort by:", ["Trip ID", "Frequency", "TAFB Hours", "Duty Days", "Max Duty Length", "Max Legs/Duty"])

    # Apply filters
    filtered_df = df_trips.copy()

    # Filter by duty day length threshold
    if min_duty_threshold > 0:
        filtered_df = filtered_df[filtered_df["Max Duty Length"] >= min_duty_threshold]

    # Filter by legs per duty day threshold
    if min_legs_threshold > 0:
        filtered_df = filtered_df[filtered_df["Max Legs/Duty"] >= min_legs_threshold]

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

    st.dataframe(filtered_df, hide_index=True, width="stretch")
    st.caption(f"Showing {len(filtered_df)} of {len(df_trips)} pairings")

    # === TRIP DETAILS VIEWER ===
    st.subheader("📋 View Pairing Details")

    # Get trip text map from session state
    trip_text_map = result_data.get("trip_text_map", {})

    if trip_text_map and len(filtered_df) > 0:
        # Get list of Trip IDs from filtered results
        available_trip_ids = sorted(filtered_df["Trip ID"].dropna().unique())

        if len(available_trip_ids) > 0:
            selected_trip_id = st.selectbox(
                "Select a Trip ID to view full pairing details:",
                options=available_trip_ids,
                format_func=lambda x: f"Trip {int(x)}"
            )

            # Display the selected trip details in an expander
            if selected_trip_id in trip_text_map:
                with st.expander(f"📄 Trip Details - {int(selected_trip_id)} - ONT 757", expanded=True):
                    trip_text = trip_text_map[selected_trip_id]

                    # Parse the trip
                    trip_data = parse_trip_for_table(trip_text)

                    # Display date/frequency if available
                    if trip_data['date_freq']:
                        st.caption(trip_data['date_freq'])

                    # Display as styled HTML table
                    st.markdown("""
                    <style>
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

                    # Build table HTML
                    table_html = """
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

                    # Trip summary row
                    summary = trip_data['trip_summary']
                    table_html += "<tr class='summary-row'>"
                    table_html += "<td colspan='10' style='text-align: left; padding: 8px;'>"
                    summary_parts = []
                    if 'Credit' in summary:
                        summary_parts.append(f"<b>Credit:</b> {summary['Credit']}")
                    if 'Blk' in summary:
                        summary_parts.append(f"<b>Blk:</b> {summary['Blk']}")
                    if 'Duty Time' in summary:
                        summary_parts.append(f"<b>Duty Time:</b> {summary['Duty Time']}")
                    if 'Prem' in summary:
                        summary_parts.append(f"<b>Prem:</b> {summary['Prem']}")
                    if 'PDiem' in summary:
                        summary_parts.append(f"<b>PDiem:</b> {summary['PDiem']}")
                    if 'TAFB' in summary:
                        summary_parts.append(f"<b>TAFB:</b> {summary['TAFB']}")
                    if 'Duty Days' in summary:
                        summary_parts.append(f"<b>Duty Days:</b> {summary['Duty Days']}")

                    table_html += " &nbsp;&nbsp;&nbsp; ".join(summary_parts)
                    table_html += "</td></tr>"

                    table_html += """
                        </tbody>
                    </table>
                    """

                    st.markdown(table_html, unsafe_allow_html=True)

                    # Raw text toggle
                    with st.expander("🔍 View Raw Text", expanded=False):
                        st.text_area(
                            "Raw Pairing Text",
                            value=trip_text,
                            height=400,
                            disabled=True,
                            label_visibility="collapsed"
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
            key="download_excel",
        )

    with col2:
        # Report PDF
        report_pdf = res["report_pdf"]
        st.download_button(
            "📄 Download PDF Report",
            data=report_pdf.read_bytes(),
            file_name=report_pdf.name,
            mime="application/pdf",
            key="download_pdf",
        )

    st.divider()
    st.caption("Raw CSV outputs (optional)")
    for fn in [
        "trip_level_edw_flags.csv",
        "trip_length_summary.csv",
        "edw_vs_day_summary.csv",
        "edw_by_length.csv",
        "edw_weighting_summary.csv",
        "edw_trip_ids.csv",
    ]:
        fp = out_dir / fn
        if fp.exists():
            st.download_button(
                f"Download {fn}",
                data=fp.read_bytes(),
                file_name=fp.name,
                mime="text/csv",
                key=f"download_{fn}",
            )

st.caption(
    "Notes: EDW = any duty day touches 02:30–05:00 local (inclusive). "
    "Local hour comes from the number in parentheses ( ), minutes from the following Z time."
)
