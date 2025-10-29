"""Bid Line Analyzer page (Tab 2)."""

import tempfile
from pathlib import Path
from typing import Optional
from datetime import datetime

import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import numpy as np

from bid_parser import parse_bid_lines, extract_bid_line_header_info
from pdf_generation import create_bid_line_pdf_report, ReportMetadata
from config import CT_BT_BUCKET_SIZE_HOURS, CHART_HEIGHT_PX, CHART_LABEL_ANGLE
from ui_components import (
    create_bid_line_filters,
    apply_dataframe_filters,
    is_filter_active,
    render_filter_summary,
    render_filter_reset_button,
    create_bid_line_editor,
    render_editor_header,
    render_change_summary,
    render_reset_button,
    render_filter_status_message,
    render_csv_download,
    render_pdf_download,
    render_download_section,
    handle_pdf_generation_error,
)
from auth import is_admin
from database import (
    get_supabase_client,
    save_bid_period,
    save_bid_lines,
    refresh_trends,
    check_duplicate_bid_period,
)


def render_bid_line_analyzer():
    """Render the Bid Line Analyzer tab."""

    st.markdown(
        "Upload a **Bid Line PDF** to extract CT, BT, DO, DD data and generate analysis reports. "
        "You can **manually edit** parsed values in the Overview tab before downloading."
    )

    uploaded_file = st.file_uploader(
        "Choose a Bid Line PDF",
        type=["pdf"],
        key="bid_line_pdf_uploader"
    )

    # Initialize session state for header info
    if "bidline_header_info" not in st.session_state:
        st.session_state.bidline_header_info = None

    # Extract header info when file is uploaded
    if uploaded_file is not None:
        # Save to temp file to extract header info
        tmpdir = Path(tempfile.mkdtemp())
        pdf_path = tmpdir / uploaded_file.name
        pdf_path.write_bytes(uploaded_file.getvalue())

        # Extract header information
        with open(pdf_path, 'rb') as f:
            header_info = extract_bid_line_header_info(f)
        st.session_state.bidline_header_info = header_info

        # Display extracted information in an info box
        st.info(
            f"**Extracted from PDF:**\n\n"
            f"📅 Bid Period: **{header_info['bid_period']}**\n\n"
            f"🏠 Domicile: **{header_info['domicile']}**\n\n"
            f"✈️ Fleet Type: **{header_info['fleet_type']}**\n\n"
            f"📆 Date Range: **{header_info['bid_period_date_range']}**\n\n"
            f"🕒 Date/Time: **{header_info['date_time']}**"
        )

    # Initialize session state for parsed data and edits
    if "bidline_original_df" not in st.session_state:
        st.session_state.bidline_original_df = None
    if "bidline_edited_df" not in st.session_state:
        st.session_state.bidline_edited_df = None
    if "bidline_diagnostics" not in st.session_state:
        st.session_state.bidline_diagnostics = None

    run_button = st.button("Parse Bid Lines", disabled=(uploaded_file is None), key="parse_bid_lines")

    if run_button:
        if uploaded_file is None:
            st.warning("Please upload a PDF first.")
            st.stop()

        progress_bar = st.progress(0)
        status_text = st.empty()

        def update_progress(current, total):
            progress_bar.progress(current / total)
            status_text.text(f"Processing page {current} of {total}...")

        tmpdir = Path(tempfile.mkdtemp())
        pdf_path = tmpdir / uploaded_file.name
        pdf_path.write_bytes(uploaded_file.getvalue())

        try:
            with open(pdf_path, 'rb') as f:
                df, diagnostics = parse_bid_lines(f, progress_callback=update_progress)

            # Store original parsed data (never modified)
            st.session_state.bidline_original_df = df.copy()

            # Initialize edited data as a copy of original (will be modified by user)
            st.session_state.bidline_edited_df = df.copy()

            st.session_state.bidline_diagnostics = diagnostics

            progress_bar.empty()
            status_text.empty()

            st.success(f"✅ Parsed {len(df)} bid lines successfully!")

            # Display parsing diagnostics
            if diagnostics.warnings:
                with st.expander("⚠️ Parsing Warnings", expanded=False):
                    for warning in diagnostics.warnings[:20]:  # Show first 20
                        st.warning(warning)
                    if len(diagnostics.warnings) > 20:
                        st.caption(f"...and {len(diagnostics.warnings) - 20} more warnings")

        except ValueError as e:
            st.error(str(e))
            st.stop()
        except Exception as e:
            st.error(f"Error parsing PDF: {e}")
            import traceback
            with st.expander("📋 Error Details"):
                st.code(traceback.format_exc())
            st.stop()

    # Display results if data exists (use edited data)
    if st.session_state.bidline_edited_df is not None:
        # Add "Save to Database" button (admin only)
        _render_save_to_database_button()

        _display_bid_line_results()


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
    if "bidline_saved_to_db" not in st.session_state:
        st.session_state.bidline_saved_to_db = False

    # Get data
    if "bidline_edited_df" not in st.session_state or st.session_state.bidline_edited_df is None:
        return

    if "bidline_header_info" not in st.session_state or st.session_state.bidline_header_info is None:
        return

    st.divider()

    # Show save button
    col1, col2 = st.columns([3, 1])

    with col1:
        if st.session_state.bidline_saved_to_db:
            st.success("✅ Data already saved to database for this analysis")
        else:
            st.info("💾 **Admin:** Save this analysis to the database for historical tracking")

    with col2:
        if not st.session_state.bidline_saved_to_db:
            if st.button("💾 Save to Database", type="primary", key="bidline_save_button"):
                _save_bid_lines_to_database(
                    st.session_state.bidline_edited_df,
                    st.session_state.bidline_header_info,
                    supabase
                )


def _save_bid_lines_to_database(df: pd.DataFrame, header_info: dict, supabase):
    """Save bid line analysis results to database."""

    try:
        # Parse dates from header
        date_range = header_info.get("bid_period_date_range", "")
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
                end_date = (today.replace(day=28) + pd.Timedelta(days=4)).replace(day=1) - pd.Timedelta(days=1)
                end_date = end_date.date()
        except:
            # Default to current month if parsing fails
            today = datetime.now()
            start_date = today.replace(day=1).date()
            end_date = (today.replace(day=28) + pd.Timedelta(days=4)).replace(day=1) - pd.Timedelta(days=1)
            end_date = end_date.date()

        # Prepare bid period data
        bid_period_data = {
            "period": header_info["bid_period"],
            "domicile": header_info["domicile"],
            "aircraft": header_info["fleet_type"],
            "seat": "CA",  # Default to Captain, could be extracted from PDF in future
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }

        # Check for duplicate
        with st.spinner("Checking for existing data..."):
            existing = check_duplicate_bid_period(
                bid_period_data["period"],
                bid_period_data["domicile"],
                bid_period_data["aircraft"],
                bid_period_data["seat"]
            )

        if existing:
            st.warning(
                f"⚠️ Bid period {bid_period_data['period']} {bid_period_data['domicile']} "
                f"{bid_period_data['aircraft']} {bid_period_data['seat']} already exists in database.\n\n"
                f"Existing record ID: {existing['id']}\n\n"
                f"To avoid duplicates, this data will not be saved."
            )
            return

        # Save bid period
        with st.spinner("Saving bid period..."):
            bid_period_id = save_bid_period(bid_period_data)

        st.success(f"✅ Bid period saved (ID: {bid_period_id[:8]}...)")

        # Prepare bid lines data
        bid_lines_records = []
        for _, row in df.iterrows():
            record = {
                "line_number": int(row["Line"]),
                "total_ct": float(row["CT"]),
                "total_bt": float(row["BT"]),
                "total_do": int(row["DO"]),
                "total_dd": int(row["DD"]),
                "is_reserve": bool(row.get("IsReserve", False)),
                "vto_type": row.get("VTOType") if pd.notna(row.get("VTOType")) else None,
                "vto_period": int(row.get("VTOPeriod")) if pd.notna(row.get("VTOPeriod")) else None,
            }

            # Add PP1 and PP2 data if available
            if "PP1_CT" in row:
                record["pp1_ct"] = float(row["PP1_CT"]) if pd.notna(row["PP1_CT"]) else None
                record["pp1_bt"] = float(row["PP1_BT"]) if pd.notna(row["PP1_BT"]) else None
                record["pp1_do"] = int(row["PP1_DO"]) if pd.notna(row["PP1_DO"]) else None
                record["pp1_dd"] = int(row["PP1_DD"]) if pd.notna(row["PP1_DD"]) else None

            if "PP2_CT" in row:
                record["pp2_ct"] = float(row["PP2_CT"]) if pd.notna(row["PP2_CT"]) else None
                record["pp2_bt"] = float(row["PP2_BT"]) if pd.notna(row["PP2_BT"]) else None
                record["pp2_do"] = int(row["PP2_DO"]) if pd.notna(row["PP2_DO"]) else None
                record["pp2_dd"] = int(row["PP2_DD"]) if pd.notna(row["PP2_DD"]) else None

            bid_lines_records.append(record)

        # Create DataFrame for validation
        bid_lines_df = pd.DataFrame(bid_lines_records)

        # Save bid lines
        with st.spinner(f"Saving {len(bid_lines_df)} bid lines..."):
            count = save_bid_lines(bid_period_id, bid_lines_df)

        st.success(f"✅ Saved {count} bid lines")

        # Refresh materialized view
        with st.spinner("Refreshing trend statistics..."):
            refresh_trends()

        st.success("✅ Trend statistics updated")

        # Mark as saved
        st.session_state.bidline_saved_to_db = True

        st.success("🎉 All data saved successfully to database!")

    except Exception as e:
        st.error(f"❌ Error saving to database: {str(e)}")
        import traceback
        with st.expander("Show error details"):
            st.code(traceback.format_exc())


def _display_bid_line_results():
    """Display bid line analysis results with filters and visualizations."""

    # Use edited data for all displays
    df = st.session_state.bidline_edited_df.copy()
    diagnostics = st.session_state.bidline_diagnostics

    st.divider()

    # === FILTER SIDEBAR ===
    filter_ranges = create_bid_line_filters(df)
    filtered_df = apply_dataframe_filters(df, filter_ranges)
    render_filter_summary(df, filtered_df)

    # Reset filters button
    if render_filter_reset_button(key="reset_filters"):
        st.rerun()

    # Check if filters are actively applied
    filters_active = is_filter_active(filter_ranges)

    # === TABS FOR DIFFERENT VIEWS ===
    tab1, tab2, tab3 = st.tabs(["📊 Overview", "📈 Summary", "📉 Visuals"])

    with tab1:
        _render_overview_tab(df, filtered_df, filters_active)

    with tab2:
        _render_summary_tab(df, filtered_df, diagnostics)

    with tab3:
        _render_visuals_tab(df, filtered_df, diagnostics)

    # === DOWNLOAD SECTION ===
    render_download_section(title="⬇️ Downloads")

    col1, col2 = st.columns(2)

    with col1:
        # CSV Export (uses filtered data with edits)
        render_csv_download(
            filtered_df,
            filename="bid_lines_filtered.csv",
            button_label="📊 Download CSV (Filtered)",
            key="download_bid_csv"
        )

    with col2:
        # PDF Report (uses filtered data with edits)
        try:
            header = st.session_state.bidline_header_info
            title = f"{header['domicile']} {header['fleet_type']} – Bid {header['bid_period']}"
            subtitle = f"Bid Line Analysis Report • {header['bid_period_date_range']}"

            metadata = ReportMetadata(
                title=title,
                subtitle=subtitle
            )

            # Create branding to match pairing analyzer
            branding = {
                "primary_hex": "#1E40AF",  # Lighter blue (matches pairing analyzer)
                "accent_hex": "#F3F4F6",   # Light gray
                "rule_hex": "#E5E7EB",     # Medium gray
                "muted_hex": "#6B7280",    # Darker gray
                "bg_alt_hex": "#FAFAFA",   # Very light gray
                "logo_path": None,
                "title_left": f"{header['domicile']} {header['fleet_type']} – Bid {header['bid_period']} | Bid Line Analysis Report"
            }

            pdf_bytes = create_bid_line_pdf_report(
                filtered_df,
                metadata=metadata,
                pay_periods=diagnostics.pay_periods if diagnostics else None,
                reserve_lines=diagnostics.reserve_lines if diagnostics else None,
                branding=branding
            )

            render_pdf_download(
                pdf_bytes,
                filename="Bid_Lines_Analysis_Report.pdf",
                button_label="📄 Download PDF Report",
                key="download_bid_pdf"
            )
        except Exception as e:
            handle_pdf_generation_error(e, show_traceback=True)


def _render_overview_tab(df: pd.DataFrame, filtered_df: pd.DataFrame, filters_active: bool):
    """Render the Overview tab with data editor for manual corrections."""

    render_editor_header(show_all_data=True)

    # Display data editor - ALWAYS show ALL data (not filtered)
    edited_df = create_bid_line_editor(df, key="bidline_data_editor")

    # Save edited data back to session state
    st.session_state.bidline_edited_df = edited_df.copy()

    # Detect changes and show summary with validation
    original_df = st.session_state.bidline_original_df
    if original_df is not None:
        render_change_summary(original_df, edited_df, show_validation=True)

        # Reset button
        render_reset_button(
            session_state_key_edited="bidline_edited_df",
            session_state_key_original="bidline_original_df",
            button_key="reset_edits"
        )

    # Display filter status
    render_filter_status_message(df, filtered_df, filters_active)


def _render_summary_tab(df: pd.DataFrame, filtered_df: pd.DataFrame, diagnostics):
    """Render the Summary tab with statistics."""

    st.subheader("📊 Summary Statistics")

    # Use diagnostics.reserve_lines to filter out reserve lines
    reserve_line_numbers = set()
    hsby_line_numbers = set()

    if diagnostics and diagnostics.reserve_lines is not None:
        reserve_df = diagnostics.reserve_lines
        if 'IsReserve' in reserve_df.columns and 'IsHotStandby' in reserve_df.columns:
            # Regular reserve lines (not HSBY): exclude from everything
            regular_reserve_mask = (reserve_df['IsReserve'] == True) & (reserve_df['IsHotStandby'] == False)
            reserve_line_numbers = set(reserve_df[regular_reserve_mask]['Line'].tolist())

            # HSBY lines: exclude only from BT
            hsby_mask = reserve_df['IsHotStandby'] == True
            hsby_line_numbers = set(reserve_df[hsby_mask]['Line'].tolist())

    # For CT, DO, DD: exclude regular reserve (keep HSBY)
    df_non_reserve = filtered_df[~filtered_df['Line'].isin(reserve_line_numbers)] if reserve_line_numbers else filtered_df

    # For BT: exclude both regular reserve AND HSBY
    all_exclude_for_bt = reserve_line_numbers | hsby_line_numbers
    df_for_bt = filtered_df[~filtered_df['Line'].isin(all_exclude_for_bt)] if all_exclude_for_bt else filtered_df

    # Calculate statistics
    ct_stats = df_non_reserve['CT'].agg(['min', 'max', 'mean']) if not df_non_reserve.empty else filtered_df['CT'].agg(['min', 'max', 'mean'])
    bt_stats = df_for_bt['BT'].agg(['min', 'max', 'mean']) if not df_for_bt.empty else filtered_df['BT'].agg(['min', 'max', 'mean'])
    do_stats = df_non_reserve['DO'].agg(['min', 'max', 'mean']) if not df_non_reserve.empty else filtered_df['DO'].agg(['min', 'max', 'mean'])
    dd_stats = df_non_reserve['DD'].agg(['min', 'max', 'mean']) if not df_non_reserve.empty else filtered_df['DD'].agg(['min', 'max', 'mean'])

    # Create summary statistics table
    summary_data = {
        'Metric': ['Total Lines', 'Credit Time (CT)', 'Block Time (BT)', 'Days Off (DO)', 'Duty Days (DD)'],
        'Average': [
            f"{len(filtered_df)}",
            f"{ct_stats['mean']:.2f} hrs",
            f"{bt_stats['mean']:.2f} hrs",
            f"{do_stats['mean']:.1f} days",
            f"{dd_stats['mean']:.1f} days"
        ],
        'Range': [
            '—',
            f"{ct_stats['min']:.1f} - {ct_stats['max']:.1f} hrs",
            f"{bt_stats['min']:.1f} - {bt_stats['max']:.1f} hrs",
            f"{int(do_stats['min'])} - {int(do_stats['max'])} days",
            f"{int(dd_stats['min'])} - {int(dd_stats['max'])} days"
        ]
    }

    summary_df = pd.DataFrame(summary_data)
    st.dataframe(summary_df, hide_index=True, use_container_width=True)

    # Add note about reserve line exclusions
    st.caption("*Reserve lines excluded from averages. HSBY lines excluded from Block Time only.")

    st.divider()

    # Pay Period Analysis
    if diagnostics and diagnostics.pay_periods is not None:
        st.subheader("📅 Pay Period Analysis")

        pay_periods_df = diagnostics.pay_periods

        # Filter pay periods to match filtered lines
        filtered_pay_periods = pay_periods_df[pay_periods_df["Line"].isin(filtered_df["Line"])]

        # For pay period analysis: exclude reserve lines from CT/DO/DD, exclude reserve+HSBY from BT
        pp_non_reserve = filtered_pay_periods[~filtered_pay_periods["Line"].isin(reserve_line_numbers)] if reserve_line_numbers else filtered_pay_periods
        pp_for_bt = filtered_pay_periods[~filtered_pay_periods["Line"].isin(all_exclude_for_bt)] if all_exclude_for_bt else filtered_pay_periods

        if not filtered_pay_periods.empty:
            # Build pay period comparison table
            pp_data = {'Metric': ['Avg Credit Time (CT)', 'Avg Block Time (BT)', 'Avg Days Off (DO)', 'Avg Duty Days (DD)']}

            for period in sorted(filtered_pay_periods["Period"].unique()):
                period_data_non_reserve = pp_non_reserve[pp_non_reserve["Period"] == period]
                period_data_for_bt = pp_for_bt[pp_for_bt["Period"] == period]

                if not period_data_non_reserve.empty:
                    pp_ct = period_data_non_reserve["CT"].mean()
                    pp_do = period_data_non_reserve["DO"].mean()
                    pp_dd = period_data_non_reserve["DD"].mean()
                else:
                    pp_ct, pp_do, pp_dd = 0, 0, 0

                if not period_data_for_bt.empty:
                    pp_bt = period_data_for_bt["BT"].mean()
                else:
                    pp_bt = 0

                pp_data[f'Pay Period {int(period)}'] = [
                    f"{pp_ct:.2f} hrs",
                    f"{pp_bt:.2f} hrs",
                    f"{pp_do:.1f} days",
                    f"{pp_dd:.1f} days"
                ]

            pp_comparison_df = pd.DataFrame(pp_data)
            st.dataframe(pp_comparison_df, hide_index=True, use_container_width=True)

    # Reserve Line Statistics
    if diagnostics and diagnostics.reserve_lines is not None:
        st.divider()
        st.subheader("🔄 Reserve Lines")

        reserve_df = diagnostics.reserve_lines
        # Filter to only show reserve lines in the filtered dataset
        reserve_in_view = reserve_df[reserve_df["Line"].isin(filtered_df["Line"])]
        # Only show actual reserve lines (IsReserve == True)
        reserve_in_view = reserve_in_view[reserve_in_view["IsReserve"] == True]

        if not reserve_in_view.empty:
            total_reserve = len(reserve_in_view)
            captain_slots = int(reserve_in_view["CaptainSlots"].sum())
            fo_slots = int(reserve_in_view["FOSlots"].sum())
            total_slots = captain_slots + fo_slots
            total_regular = len(filtered_df) - total_reserve

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Reserve Lines", total_reserve)
                st.metric("Regular Lines", total_regular)
            with col2:
                st.metric("Captain Slots", captain_slots)
                st.metric("F/O Slots", fo_slots)
            with col3:
                st.metric("Total Reserve Slots", total_slots)
                reserve_pct = (total_slots / total_regular * 100) if total_regular > 0 else 0.0
                st.metric("Reserve %", f"{reserve_pct:.1f}%")
        else:
            st.info("No reserve lines found in current filter")


def _create_time_distribution_chart(data: pd.Series, metric_name: str, is_percentage: bool = False):
    """Create an interactive histogram chart for time metrics (CT/BT) with configurable buckets and angled labels."""
    if data.empty:
        return None

    # Create bins using configured bucket size
    bucket_size = CT_BT_BUCKET_SIZE_HOURS
    min_val = np.floor(data.min() / bucket_size) * bucket_size
    max_val = np.ceil(data.max() / bucket_size) * bucket_size
    bins = np.arange(min_val, max_val + bucket_size, bucket_size)

    # Create histogram
    counts, bin_edges = np.histogram(data, bins=bins)

    if is_percentage:
        values = (counts / counts.sum() * 100) if counts.sum() > 0 else counts
        ylabel = "Percentage (%)"
        hover_template = "%{y:.1f}%<extra></extra>"
    else:
        values = counts
        ylabel = "Count"
        hover_template = "%{y}<extra></extra>"

    # Create bin labels (e.g., "70-75", "75-80")
    bin_labels = [f"{int(bin_edges[i])}-{int(bin_edges[i+1])}" for i in range(len(bin_edges)-1)]

    # Create Plotly figure
    fig = go.Figure(data=[
        go.Bar(
            x=bin_labels,
            y=values,
            marker_color='#1f77b4',
            opacity=0.7,
            hovertemplate=hover_template
        )
    ])

    # Update layout with configured angle and height
    fig.update_layout(
        xaxis_title=f"{metric_name} (hrs)",
        yaxis_title=ylabel,
        xaxis_tickangle=CHART_LABEL_ANGLE,
        height=CHART_HEIGHT_PX,
        margin=dict(l=50, r=50, t=30, b=80),
        hovermode='x',
        yaxis=dict(gridcolor='lightgray', gridwidth=0.5)
    )

    return fig


def _render_visuals_tab(df: pd.DataFrame, filtered_df: pd.DataFrame, diagnostics):
    """Render the Visuals tab with charts."""

    st.subheader("📊 Distribution Charts")

    # Use diagnostics.reserve_lines to filter out reserve lines
    reserve_line_numbers = set()
    hsby_line_numbers = set()

    if diagnostics and diagnostics.reserve_lines is not None:
        reserve_df = diagnostics.reserve_lines
        if 'IsReserve' in reserve_df.columns and 'IsHotStandby' in reserve_df.columns:
            regular_reserve_mask = (reserve_df['IsReserve'] == True) & (reserve_df['IsHotStandby'] == False)
            reserve_line_numbers = set(reserve_df[regular_reserve_mask]['Line'].tolist())

            hsby_mask = reserve_df['IsHotStandby'] == True
            hsby_line_numbers = set(reserve_df[hsby_mask]['Line'].tolist())

    # For CT, DO, DD: exclude regular reserve (keep HSBY)
    df_non_reserve = filtered_df[~filtered_df['Line'].isin(reserve_line_numbers)] if reserve_line_numbers else filtered_df

    # For BT: exclude both regular reserve AND HSBY
    all_exclude_for_bt = reserve_line_numbers | hsby_line_numbers
    df_for_bt = filtered_df[~filtered_df['Line'].isin(all_exclude_for_bt)] if all_exclude_for_bt else filtered_df

    # Determine if we have multiple pay periods
    has_multiple_periods = False
    pay_periods_df = None
    if diagnostics and diagnostics.pay_periods is not None:
        pay_periods_df = diagnostics.pay_periods
        filtered_pay_periods = pay_periods_df[pay_periods_df["Line"].isin(filtered_df["Line"])]
        unique_periods = filtered_pay_periods["Period"].unique()
        has_multiple_periods = len(unique_periods) > 1

    # Overall Distributions Section
    st.markdown("### Overall Distributions")
    if has_multiple_periods:
        st.caption("Combined data across all pay periods")

    # CT Distribution (5-hour buckets with angled labels)
    st.markdown("**Credit Time (CT) Distribution**")
    col1, col2 = st.columns(2)
    with col1:
        if not df_non_reserve.empty:
            fig = _create_time_distribution_chart(df_non_reserve["CT"], "Credit Time", is_percentage=False)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available (all lines are reserve)")
    with col2:
        if not df_non_reserve.empty:
            fig = _create_time_distribution_chart(df_non_reserve["CT"], "Credit Time", is_percentage=True)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available (all lines are reserve)")

    st.divider()

    # BT Distribution (5-hour buckets with angled labels)
    st.markdown("**Block Time (BT) Distribution**")
    col1, col2 = st.columns(2)
    with col1:
        if not df_for_bt.empty:
            fig = _create_time_distribution_chart(df_for_bt["BT"], "Block Time", is_percentage=False)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available (all lines excluded)")
    with col2:
        if not df_for_bt.empty:
            fig = _create_time_distribution_chart(df_for_bt["BT"], "Block Time", is_percentage=True)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available (all lines excluded)")

    st.divider()

    # DO Distribution (whole numbers only) - Use pay periods data for accurate counts
    st.markdown("**Days Off (DO) Distribution**")
    col1, col2 = st.columns(2)

    # Get pay periods data if available (shows each period separately, not averaged)
    if diagnostics and diagnostics.pay_periods is not None:
        pay_periods_df = diagnostics.pay_periods
        # Filter to match filtered lines
        filtered_pay_periods = pay_periods_df[pay_periods_df["Line"].isin(filtered_df["Line"])]
        # Exclude reserve lines
        pp_non_reserve = filtered_pay_periods[~filtered_pay_periods["Line"].isin(reserve_line_numbers)] if reserve_line_numbers else filtered_pay_periods

        with col1:
            if not pp_non_reserve.empty:
                do_int = pp_non_reserve["DO"].round().astype(int)
                st.bar_chart(do_int.value_counts().sort_index(), x_label="Days Off", y_label="Count")
                st.caption("*Showing both pay periods (2 entries per line)")
            else:
                st.info("No data available (all lines are reserve)")
        with col2:
            if not pp_non_reserve.empty:
                do_int = pp_non_reserve["DO"].round().astype(int)
                st.bar_chart(do_int.value_counts(normalize=True).sort_index() * 100, x_label="Days Off", y_label="Percentage")
                st.caption("*Showing both pay periods (2 entries per line)")
            else:
                st.info("No data available (all lines are reserve)")
    else:
        # Fallback to averaged DO if pay_periods not available
        with col1:
            if not df_non_reserve.empty:
                do_int = df_non_reserve["DO"].round().astype(int)
                st.bar_chart(do_int.value_counts().sort_index(), x_label="Days Off", y_label="Count")
                st.caption("*Averaged across pay periods")
            else:
                st.info("No data available (all lines are reserve)")
        with col2:
            if not df_non_reserve.empty:
                do_int = df_non_reserve["DO"].round().astype(int)
                st.bar_chart(do_int.value_counts(normalize=True).sort_index() * 100, x_label="Days Off", y_label="Percentage")
                st.caption("*Averaged across pay periods")
            else:
                st.info("No data available (all lines are reserve)")

    st.divider()

    # DD Distribution (whole numbers only) - Use pay periods data for accurate counts
    st.markdown("**Duty Days (DD) Distribution**")
    col1, col2 = st.columns(2)

    # Get pay periods data if available (shows each period separately, not averaged)
    if diagnostics and diagnostics.pay_periods is not None:
        with col1:
            if not pp_non_reserve.empty:
                dd_int = pp_non_reserve["DD"].round().astype(int)
                st.bar_chart(dd_int.value_counts().sort_index(), x_label="Duty Days", y_label="Count")
                st.caption("*Showing both pay periods (2 entries per line)")
            else:
                st.info("No data available (all lines are reserve)")
        with col2:
            if not pp_non_reserve.empty:
                dd_int = pp_non_reserve["DD"].round().astype(int)
                st.bar_chart(dd_int.value_counts(normalize=True).sort_index() * 100, x_label="Duty Days", y_label="Percentage")
                st.caption("*Showing both pay periods (2 entries per line)")
            else:
                st.info("No data available (all lines are reserve)")
    else:
        # Fallback to averaged DD if pay_periods not available
        with col1:
            if not df_non_reserve.empty:
                dd_int = df_non_reserve["DD"].round().astype(int)
                st.bar_chart(dd_int.value_counts().sort_index(), x_label="Duty Days", y_label="Count")
                st.caption("*Averaged across pay periods")
            else:
                st.info("No data available (all lines are reserve)")
        with col2:
            if not df_non_reserve.empty:
                dd_int = df_non_reserve["DD"].round().astype(int)
                st.bar_chart(dd_int.value_counts(normalize=True).sort_index() * 100, x_label="Duty Days", y_label="Percentage")
                st.caption("*Averaged across pay periods")
            else:
                st.info("No data available (all lines are reserve)")

    # Pay Period Breakdown Section (only if multiple pay periods exist)
    if has_multiple_periods and pay_periods_df is not None:
        st.divider()
        st.markdown("### Pay Period Breakdown")
        st.caption("Individual distributions for each pay period")

        # Get filtered pay periods data
        filtered_pay_periods = pay_periods_df[pay_periods_df["Line"].isin(filtered_df["Line"])]
        # Exclude reserve lines
        pp_non_reserve = filtered_pay_periods[~filtered_pay_periods["Line"].isin(reserve_line_numbers)] if reserve_line_numbers else filtered_pay_periods
        pp_for_bt = filtered_pay_periods[~filtered_pay_periods["Line"].isin(all_exclude_for_bt)] if all_exclude_for_bt else filtered_pay_periods

        # Get sorted list of unique periods
        unique_periods = sorted(filtered_pay_periods["Period"].unique())

        # Create a distribution for each pay period
        for period in unique_periods:
            st.markdown(f"#### Pay Period {int(period)}")

            # Filter data for this specific pay period
            period_data_non_reserve = pp_non_reserve[pp_non_reserve["Period"] == period]
            period_data_for_bt = pp_for_bt[pp_for_bt["Period"] == period]

            # CT Distribution for this pay period
            st.markdown("**Credit Time (CT)**")
            col1, col2 = st.columns(2)
            with col1:
                if not period_data_non_reserve.empty:
                    fig = _create_time_distribution_chart(period_data_non_reserve["CT"], "Credit Time", is_percentage=False)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No data available")
            with col2:
                if not period_data_non_reserve.empty:
                    fig = _create_time_distribution_chart(period_data_non_reserve["CT"], "Credit Time", is_percentage=True)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No data available")

            # BT Distribution for this pay period
            st.markdown("**Block Time (BT)**")
            col1, col2 = st.columns(2)
            with col1:
                if not period_data_for_bt.empty:
                    fig = _create_time_distribution_chart(period_data_for_bt["BT"], "Block Time", is_percentage=False)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No data available")
            with col2:
                if not period_data_for_bt.empty:
                    fig = _create_time_distribution_chart(period_data_for_bt["BT"], "Block Time", is_percentage=True)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No data available")

            # DO Distribution for this pay period
            st.markdown("**Days Off (DO)**")
            col1, col2 = st.columns(2)
            with col1:
                if not period_data_non_reserve.empty:
                    do_int = period_data_non_reserve["DO"].round().astype(int)
                    st.bar_chart(do_int.value_counts().sort_index(), x_label="Days Off", y_label="Count")
                else:
                    st.info("No data available")
            with col2:
                if not period_data_non_reserve.empty:
                    do_int = period_data_non_reserve["DO"].round().astype(int)
                    st.bar_chart(do_int.value_counts(normalize=True).sort_index() * 100, x_label="Days Off", y_label="Percentage")
                else:
                    st.info("No data available")

            # DD Distribution for this pay period
            st.markdown("**Duty Days (DD)**")
            col1, col2 = st.columns(2)
            with col1:
                if not period_data_non_reserve.empty:
                    dd_int = period_data_non_reserve["DD"].round().astype(int)
                    st.bar_chart(dd_int.value_counts().sort_index(), x_label="Duty Days", y_label="Count")
                else:
                    st.info("No data available")
            with col2:
                if not period_data_non_reserve.empty:
                    dd_int = period_data_non_reserve["DD"].round().astype(int)
                    st.bar_chart(dd_int.value_counts(normalize=True).sort_index() * 100, x_label="Duty Days", y_label="Percentage")
                else:
                    st.info("No data available")

            # Add divider between pay periods (except after the last one)
            if period != unique_periods[-1]:
                st.divider()
