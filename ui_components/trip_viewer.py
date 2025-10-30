"""
Trip details viewer component for EDW analysis.

This module provides a reusable component for displaying detailed pairing information
with HTML-formatted tables showing duty days, flights, and trip summaries.
"""

import streamlit as st
from edw import parse_trip_for_table, is_edw_trip


def render_trip_details_viewer(trip_text_map: dict, filtered_df, key_prefix: str = "edw"):
    """
    Render interactive trip details viewer with formatted pairing display.

    Args:
        trip_text_map: Dictionary mapping Trip ID to raw trip text
        filtered_df: DataFrame with filtered trip records
        key_prefix: Unique key prefix for Streamlit widgets (default: "edw")

    Features:
        - Trip ID selector dropdown
        - HTML-formatted table with duty days, flights, and subtotals
        - Responsive width constraints (50% desktop, 80% tablet, 100% mobile)
        - Trip summary section with all metrics
        - Raw text viewer (expandable)
    """
    st.subheader("📋 View Pairing Details")

    if trip_text_map and len(filtered_df) > 0:
        # Get list of Trip IDs from filtered results
        available_trip_ids = sorted(filtered_df["Trip ID"].dropna().unique())

        if len(available_trip_ids) > 0:
            selected_trip_id = st.selectbox(
                "Select a Trip ID to view full pairing details:",
                options=available_trip_ids,
                format_func=lambda x: f"Trip {int(x)}",
                key=f"{key_prefix}_trip_selector"
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
                    st.markdown(_get_trip_table_styles(), unsafe_allow_html=True)
                    table_html = _build_trip_table_html(trip_data)
                    st.markdown(table_html, unsafe_allow_html=True)

                    # Raw text toggle
                    with st.expander("🔍 View Raw Text", expanded=False):
                        st.text_area(
                            "Raw Pairing Text",
                            value=trip_text,
                            height=400,
                            disabled=True,
                            label_visibility="collapsed",
                            key=f"{key_prefix}_raw_text"
                        )
            else:
                st.warning(f"Trip ID {int(selected_trip_id)} not found in trip text map.")
        else:
            st.info("No trips available in filtered results. Adjust your filters to see trip details.")
    else:
        st.info("Run analysis first to view trip details.")


def _get_trip_table_styles() -> str:
    """
    Get CSS styles for trip detail table.

    Returns:
        HTML string with <style> tag containing responsive table CSS
    """
    return """
    <style>
    .trip-detail-container {
        max-width: 60%;
        margin: 0 auto;
        overflow-x: auto;
        overflow-y: visible;
    }
    @media (max-width: 768px) {
        .trip-detail-container {
            max-width: 100%;
        }
    }
    .trip-table {
        width: 100%;
        min-width: 650px;
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
        white-space: nowrap;
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
    """


def _build_trip_table_html(trip_data: dict) -> str:
    """
    Build HTML table from parsed trip data.

    Args:
        trip_data: Dictionary with duty_days, trip_summary, date_freq

    Returns:
        HTML string with complete trip table
    """
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

    return table_html
