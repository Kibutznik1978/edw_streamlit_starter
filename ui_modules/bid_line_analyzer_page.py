"""Bid Line Analyzer page (Tab 2)."""

import tempfile
from pathlib import Path
from typing import Optional

import pandas as pd
import streamlit as st

from bid_parser import parse_bid_lines, extract_bid_line_header_info
from pdf_generation import create_bid_line_pdf_report, ReportMetadata


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
        _display_bid_line_results()


def _display_bid_line_results():
    """Display bid line analysis results with filters and visualizations."""

    # Use edited data for all displays
    df = st.session_state.bidline_edited_df.copy()
    diagnostics = st.session_state.bidline_diagnostics

    st.divider()

    # === FILTER SIDEBAR ===
    st.sidebar.header("🔍 Filters")
    st.sidebar.caption("Filter bid lines by criteria")

    # CT Filter
    ct_min = float(df["CT"].min())
    ct_max = float(df["CT"].max())
    ct_range = st.sidebar.slider(
        "Credit Time (CT)",
        min_value=ct_min,
        max_value=ct_max,
        value=(ct_min, ct_max),
        step=0.1,
        key="ct_filter"
    )

    # BT Filter
    bt_min = float(df["BT"].min())
    bt_max = float(df["BT"].max())
    bt_range = st.sidebar.slider(
        "Block Time (BT)",
        min_value=bt_min,
        max_value=bt_max,
        value=(bt_min, bt_max),
        step=0.1,
        key="bt_filter"
    )

    # DO Filter
    do_min = int(df["DO"].min())
    do_max = int(df["DO"].max())
    do_range = st.sidebar.slider(
        "Days Off (DO)",
        min_value=do_min,
        max_value=do_max,
        value=(do_min, do_max),
        step=1,
        key="do_filter"
    )

    # DD Filter
    dd_min = int(df["DD"].min())
    dd_max = int(df["DD"].max())
    dd_range = st.sidebar.slider(
        "Duty Days (DD)",
        min_value=dd_min,
        max_value=dd_max,
        value=(dd_min, dd_max),
        step=1,
        key="dd_filter"
    )

    # Apply filters
    filtered_df = df[
        (df["CT"] >= ct_range[0]) & (df["CT"] <= ct_range[1]) &
        (df["BT"] >= bt_range[0]) & (df["BT"] <= bt_range[1]) &
        (df["DO"] >= do_range[0]) & (df["DO"] <= do_range[1]) &
        (df["DD"] >= dd_range[0]) & (df["DD"] <= dd_range[1])
    ]

    st.sidebar.caption(f"**Showing {len(filtered_df)} of {len(df)} lines**")

    # Reset filters button
    if st.sidebar.button("Reset Filters", key="reset_filters"):
        st.rerun()

    # Check if filters are actively applied (not at default full range)
    filters_active = (
        ct_range != (ct_min, ct_max) or
        bt_range != (bt_min, bt_max) or
        do_range != (do_min, do_max) or
        dd_range != (dd_min, dd_max)
    )

    # === TABS FOR DIFFERENT VIEWS ===
    tab1, tab2, tab3 = st.tabs(["📊 Overview", "📈 Summary", "📉 Visuals"])

    with tab1:
        _render_overview_tab(df, filtered_df, filters_active)

    with tab2:
        _render_summary_tab(df, filtered_df, diagnostics)

    with tab3:
        _render_visuals_tab(df, filtered_df, diagnostics)

    # === DOWNLOAD SECTION ===
    st.divider()
    st.header("⬇️ Downloads")

    col1, col2 = st.columns(2)

    with col1:
        # CSV Export (uses filtered data with edits)
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            "📊 Download CSV (Filtered)",
            data=csv,
            file_name="bid_lines_filtered.csv",
            mime="text/csv",
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

            pdf_bytes = create_bid_line_pdf_report(
                filtered_df,
                metadata=metadata,
                pay_periods=diagnostics.pay_periods if diagnostics else None,
                reserve_lines=diagnostics.reserve_lines if diagnostics else None
            )

            st.download_button(
                "📄 Download PDF Report",
                data=pdf_bytes,
                file_name=f"Bid_Lines_Analysis_Report.pdf",
                mime="application/pdf",
                key="download_bid_pdf"
            )
        except Exception as e:
            st.error(f"Error generating PDF: {e}")
            import traceback
            with st.expander("📋 Error Details"):
                st.code(traceback.format_exc())


def _render_overview_tab(df: pd.DataFrame, filtered_df: pd.DataFrame, filters_active: bool):
    """Render the Overview tab with data editor for manual corrections."""

    st.subheader("📋 Bid Line Data")
    st.caption("**Edit values directly in the table below to correct parsing errors**")

    # Display data editor - ALWAYS show ALL data (not filtered)
    # Use df (all lines) instead of filtered_df
    edited_df = st.data_editor(
        df,
        hide_index=True,
        use_container_width=True,
        num_rows="fixed",
        disabled=["Line"],  # Line number is read-only
        column_config={
            "Line": st.column_config.NumberColumn("Line", help="Bid line number (read-only)", width="small"),
            "CT": st.column_config.NumberColumn("CT", help="Credit Time (hours)", min_value=0.0, max_value=200.0, step=0.1, width="small"),
            "BT": st.column_config.NumberColumn("BT", help="Block Time (hours)", min_value=0.0, max_value=200.0, step=0.1, width="small"),
            "DO": st.column_config.NumberColumn("DO", help="Days Off", min_value=0, max_value=31, step=1, width="small"),
            "DD": st.column_config.NumberColumn("DD", help="Duty Days", min_value=0, max_value=31, step=1, width="small"),
        },
        key="bidline_data_editor"
    )

    # Save edited data back to session state
    # IMPORTANT: Use df.copy() as the base, not the parsed data
    st.session_state.bidline_edited_df = edited_df.copy()

    # Detect changes (compare edited vs original)
    original_df = st.session_state.bidline_original_df
    if original_df is not None:
        changes = _detect_changes(original_df, edited_df)

        if len(changes) > 0:
            st.success(f"✏️ **Data has been manually edited** ({len(changes)} change{'s' if len(changes) > 1 else ''})")

            # Show changed cells
            with st.expander("📝 View edited cells", expanded=False):
                st.dataframe(changes, hide_index=True, use_container_width=True)

            # Add validation warnings
            validation_issues = _validate_edits(edited_df)
            if validation_issues:
                st.warning("⚠️ **Validation Warnings:**")
                for issue in validation_issues:
                    st.warning(issue)

        # Reset button
        if st.button("🔄 Reset to Original Data", key="reset_edits"):
            st.session_state.bidline_edited_df = st.session_state.bidline_original_df.copy()
            st.rerun()

    # Display filter status (only if filters are actively applied by user)
    if filters_active and len(filtered_df) < len(df):
        st.info(f"ℹ️ Filters are active. Showing **{len(filtered_df)} of {len(df)}** lines. Adjust filters in sidebar to see more.")


def _detect_changes(original_df: pd.DataFrame, edited_df: pd.DataFrame) -> pd.DataFrame:
    """Detect changes between original and edited data."""

    changes = []
    for col in ["CT", "BT", "DO", "DD"]:
        if col not in original_df.columns or col not in edited_df.columns:
            continue

        # Compare column values
        diff_mask = original_df[col] != edited_df[col]

        # Handle NaN comparisons properly
        # Two NaNs should be considered equal
        nan_mask_orig = original_df[col].isna()
        nan_mask_edit = edited_df[col].isna()
        both_nan = nan_mask_orig & nan_mask_edit
        diff_mask = diff_mask & ~both_nan

        for idx in original_df[diff_mask].index:
            line_num = original_df.loc[idx, "Line"]
            orig_val = original_df.loc[idx, col]
            edit_val = edited_df.loc[idx, col]

            changes.append({
                "Line": line_num,
                "Column": col,
                "Original": orig_val if not pd.isna(orig_val) else "N/A",
                "Current": edit_val if not pd.isna(edit_val) else "N/A"
            })

    return pd.DataFrame(changes) if changes else pd.DataFrame(columns=["Line", "Column", "Original", "Current"])


def _validate_edits(df: pd.DataFrame) -> list[str]:
    """Validate edited data and return list of warnings."""

    warnings = []

    # Check for unusually high values
    if (df["CT"] > 150).any():
        high_ct_lines = df[df["CT"] > 150]["Line"].tolist()
        warnings.append(f"Lines with CT > 150: {high_ct_lines}")

    if (df["BT"] > 150).any():
        high_bt_lines = df[df["BT"] > 150]["Line"].tolist()
        warnings.append(f"Lines with BT > 150: {high_bt_lines}")

    # Check for BT > CT (block time should never exceed credit time)
    if (df["BT"] > df["CT"]).any():
        invalid_lines = df[df["BT"] > df["CT"]]["Line"].tolist()
        warnings.append(f"Lines where BT > CT (invalid): {invalid_lines}")

    # Check for unreasonable day counts
    if (df["DO"] > 20).any():
        high_do_lines = df[df["DO"] > 20]["Line"].tolist()
        warnings.append(f"Lines with DO > 20: {high_do_lines}")

    if (df["DD"] > 20).any():
        high_dd_lines = df[df["DD"] > 20]["Line"].tolist()
        warnings.append(f"Lines with DD > 20: {high_dd_lines}")

    # Check if DO + DD > 31 (more days than in a month)
    if ((df["DO"] + df["DD"]) > 31).any():
        invalid_sum_lines = df[(df["DO"] + df["DD"]) > 31]["Line"].tolist()
        warnings.append(f"Lines where DO + DD > 31 (exceeds month): {invalid_sum_lines}")

    return warnings


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
    col1, col2 = st.columns(2)

    with col1:
        st.metric("Total Lines", len(filtered_df))
        ct_stats = df_non_reserve['CT'].agg(['min', 'max', 'mean', 'median']) if not df_non_reserve.empty else filtered_df['CT'].agg(['min', 'max', 'mean', 'median'])
        st.metric("Average Credit Time", f"{ct_stats['mean']:.2f} hrs")
        st.metric("CT Range", f"{ct_stats['min']:.1f} - {ct_stats['max']:.1f} hrs")

    with col2:
        bt_stats = df_for_bt['BT'].agg(['min', 'max', 'mean', 'median']) if not df_for_bt.empty else filtered_df['BT'].agg(['min', 'max', 'mean', 'median'])
        do_stats = df_non_reserve['DO'].agg(['min', 'max', 'mean', 'median']) if not df_non_reserve.empty else filtered_df['DO'].agg(['min', 'max', 'mean', 'median'])
        dd_stats = df_non_reserve['DD'].agg(['min', 'max', 'mean', 'median']) if not df_non_reserve.empty else filtered_df['DD'].agg(['min', 'max', 'mean', 'median'])

        st.metric("Average Block Time", f"{bt_stats['mean']:.2f} hrs")
        st.metric("Average Days Off", f"{do_stats['mean']:.1f} days")
        st.metric("Average Duty Days", f"{dd_stats['mean']:.1f} days")

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
            # Group by period
            col1, col2 = st.columns(2)

            for period in sorted(filtered_pay_periods["Period"].unique()):
                period_data_non_reserve = pp_non_reserve[pp_non_reserve["Period"] == period]
                period_data_for_bt = pp_for_bt[pp_for_bt["Period"] == period]

                with col1 if period == 1 else col2:
                    st.markdown(f"**Pay Period {int(period)}**")

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

                    st.write(f"Avg CT: {pp_ct:.2f} hrs")
                    st.write(f"Avg BT: {pp_bt:.2f} hrs")
                    st.write(f"Avg DO: {pp_do:.1f} days")
                    st.write(f"Avg DD: {pp_dd:.1f} days")

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

    # CT Distribution
    st.markdown("**Credit Time (CT) Distribution**")
    col1, col2 = st.columns(2)
    with col1:
        if not df_non_reserve.empty:
            st.bar_chart(df_non_reserve["CT"].value_counts().sort_index(), x_label="Credit Time", y_label="Count")
        else:
            st.info("No data available (all lines are reserve)")
    with col2:
        if not df_non_reserve.empty:
            st.bar_chart(df_non_reserve["CT"].value_counts(normalize=True).sort_index() * 100, x_label="Credit Time", y_label="Percentage")
        else:
            st.info("No data available (all lines are reserve)")

    st.divider()

    # BT Distribution
    st.markdown("**Block Time (BT) Distribution**")
    col1, col2 = st.columns(2)
    with col1:
        if not df_for_bt.empty:
            st.bar_chart(df_for_bt["BT"].value_counts().sort_index(), x_label="Block Time", y_label="Count")
        else:
            st.info("No data available (all lines excluded)")
    with col2:
        if not df_for_bt.empty:
            st.bar_chart(df_for_bt["BT"].value_counts(normalize=True).sort_index() * 100, x_label="Block Time", y_label="Percentage")
        else:
            st.info("No data available (all lines excluded)")

    st.divider()

    # DO Distribution
    st.markdown("**Days Off (DO) Distribution**")
    col1, col2 = st.columns(2)
    with col1:
        if not df_non_reserve.empty:
            st.bar_chart(df_non_reserve["DO"].value_counts().sort_index(), x_label="Days Off", y_label="Count")
        else:
            st.info("No data available (all lines are reserve)")
    with col2:
        if not df_non_reserve.empty:
            st.bar_chart(df_non_reserve["DO"].value_counts(normalize=True).sort_index() * 100, x_label="Days Off", y_label="Percentage")
        else:
            st.info("No data available (all lines are reserve)")

    st.divider()

    # DD Distribution
    st.markdown("**Duty Days (DD) Distribution**")
    col1, col2 = st.columns(2)
    with col1:
        if not df_non_reserve.empty:
            st.bar_chart(df_non_reserve["DD"].value_counts().sort_index(), x_label="Duty Days", y_label="Count")
        else:
            st.info("No data available (all lines are reserve)")
    with col2:
        if not df_non_reserve.empty:
            st.bar_chart(df_non_reserve["DD"].value_counts(normalize=True).sort_index() * 100, x_label="Duty Days", y_label="Percentage")
        else:
            st.info("No data available (all lines are reserve)")
