"""Reusable statistics and metrics display components."""

from typing import Any, Dict, Optional, Set, Tuple

import pandas as pd
import streamlit as st


def extract_reserve_line_numbers(diagnostics) -> Tuple[Set[int], Set[int]]:
    """Extract reserve and HSBY line numbers from diagnostics.

    Args:
        diagnostics: Parsing diagnostics object with reserve_lines attribute

    Returns:
        Tuple of (regular_reserve_line_numbers, hsby_line_numbers)
    """
    reserve_line_numbers = set()
    hsby_line_numbers = set()

    if diagnostics and diagnostics.reserve_lines is not None:
        reserve_df = diagnostics.reserve_lines
        if "IsReserve" in reserve_df.columns and "IsHotStandby" in reserve_df.columns:
            # Regular reserve lines (not HSBY): exclude from everything
            regular_reserve_mask = (reserve_df["IsReserve"] == True) & (
                reserve_df["IsHotStandby"] == False
            )
            reserve_line_numbers = set(reserve_df[regular_reserve_mask]["Line"].tolist())

            # HSBY lines: exclude only from BT
            hsby_mask = reserve_df["IsHotStandby"] == True
            hsby_line_numbers = set(reserve_df[hsby_mask]["Line"].tolist())

    return reserve_line_numbers, hsby_line_numbers


def filter_by_reserve_lines(
    df: pd.DataFrame,
    reserve_line_numbers: Set[int],
    hsby_line_numbers: Set[int],
    exclude_hsby: bool = False,
) -> pd.DataFrame:
    """Filter DataFrame to exclude reserve lines.

    Args:
        df: DataFrame with 'Line' column
        reserve_line_numbers: Set of regular reserve line numbers to exclude
        hsby_line_numbers: Set of HSBY line numbers
        exclude_hsby: If True, also exclude HSBY lines (for BT calculations)

    Returns:
        Filtered DataFrame
    """
    exclude_lines = reserve_line_numbers.copy()
    if exclude_hsby:
        exclude_lines |= hsby_line_numbers

    if exclude_lines:
        return df[~df["Line"].isin(exclude_lines)]
    return df


def calculate_metric_stats(df: pd.DataFrame, column: str) -> pd.Series:
    """Calculate min, max, mean, median for a metric column.

    Args:
        df: DataFrame containing the metric column
        column: Name of the column to calculate stats for

    Returns:
        Series with 'min', 'max', 'mean', 'median' indices
    """
    if df.empty:
        return pd.Series({"min": 0, "max": 0, "mean": 0, "median": 0})

    return df[column].agg(["min", "max", "mean", "median"])


def render_basic_statistics(filtered_df: pd.DataFrame, diagnostics: Optional[Any] = None) -> None:
    """Render basic CT, BT, DO, DD statistics in a 2-column layout.

    Args:
        filtered_df: Filtered DataFrame with CT, BT, DO, DD columns
        diagnostics: Optional diagnostics object with reserve_lines
    """
    st.subheader("📊 Summary Statistics")

    # Extract reserve line numbers
    reserve_line_numbers, hsby_line_numbers = extract_reserve_line_numbers(diagnostics)

    # For CT, DO, DD: exclude regular reserve (keep HSBY)
    df_non_reserve = filter_by_reserve_lines(
        filtered_df, reserve_line_numbers, hsby_line_numbers, exclude_hsby=False
    )

    # For BT: exclude both regular reserve AND HSBY
    df_for_bt = filter_by_reserve_lines(
        filtered_df, reserve_line_numbers, hsby_line_numbers, exclude_hsby=True
    )

    # Calculate statistics
    col1, col2 = st.columns(2)

    with col1:
        st.metric("Total Lines", len(filtered_df))

        ct_stats = calculate_metric_stats(
            df_non_reserve if not df_non_reserve.empty else filtered_df, "CT"
        )
        st.metric("Average Credit Time", f"{ct_stats['mean']:.2f} hrs")
        st.metric("CT Range", f"{ct_stats['min']:.1f} - {ct_stats['max']:.1f} hrs")

    with col2:
        bt_stats = calculate_metric_stats(df_for_bt if not df_for_bt.empty else filtered_df, "BT")
        do_stats = calculate_metric_stats(
            df_non_reserve if not df_non_reserve.empty else filtered_df, "DO"
        )
        dd_stats = calculate_metric_stats(
            df_non_reserve if not df_non_reserve.empty else filtered_df, "DD"
        )

        st.metric("Average Block Time", f"{bt_stats['mean']:.2f} hrs")
        st.metric("Average Days Off", f"{do_stats['mean']:.1f} days")
        st.metric("Average Duty Days", f"{dd_stats['mean']:.1f} days")

    st.divider()


def render_pay_period_analysis(
    filtered_df: pd.DataFrame, diagnostics: Optional[Any] = None
) -> None:
    """Render pay period comparison analysis.

    Args:
        filtered_df: Filtered DataFrame with Line column
        diagnostics: Diagnostics object with pay_periods and reserve_lines
    """
    if not diagnostics or diagnostics.pay_periods is None:
        return

    st.subheader("📅 Pay Period Analysis")

    pay_periods_df = diagnostics.pay_periods

    # Filter pay periods to match filtered lines
    filtered_pay_periods = pay_periods_df[pay_periods_df["Line"].isin(filtered_df["Line"])]

    if filtered_pay_periods.empty:
        st.info("No pay period data available for filtered lines.")
        return

    # Extract reserve line numbers
    reserve_line_numbers, hsby_line_numbers = extract_reserve_line_numbers(diagnostics)

    # For pay period analysis: exclude reserve lines from CT/DO/DD, exclude reserve+HSBY from BT
    pp_non_reserve = filter_by_reserve_lines(
        filtered_pay_periods, reserve_line_numbers, hsby_line_numbers, exclude_hsby=False
    )

    pp_for_bt = filter_by_reserve_lines(
        filtered_pay_periods, reserve_line_numbers, hsby_line_numbers, exclude_hsby=True
    )

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

            st.metric("Avg Credit Time", f"{pp_ct:.2f} hrs")
            st.metric("Avg Block Time", f"{pp_bt:.2f} hrs")
            st.metric("Avg Days Off", f"{pp_do:.1f} days")
            st.metric("Avg Duty Days", f"{pp_dd:.1f} days")

    st.divider()


def render_reserve_summary(
    diagnostics: Optional[Any] = None, filtered_df: Optional[pd.DataFrame] = None
) -> None:
    """Render reserve line summary statistics.

    Args:
        diagnostics: Diagnostics object with reserve_lines
        filtered_df: Optional filtered DataFrame to match filtered lines
    """
    if not diagnostics or diagnostics.reserve_lines is None:
        return

    reserve_df = diagnostics.reserve_lines

    # Filter reserve lines to match filtered data if provided
    if filtered_df is not None:
        reserve_df = reserve_df[reserve_df["Line"].isin(filtered_df["Line"])]

    if reserve_df.empty:
        return

    st.subheader("🔄 Reserve Lines")

    # Count by type
    if "IsReserve" in reserve_df.columns and "IsHotStandby" in reserve_df.columns:
        regular_reserve = reserve_df[
            (reserve_df["IsReserve"] == True) & (reserve_df["IsHotStandby"] == False)
        ]
        hsby = reserve_df[reserve_df["IsHotStandby"] == True]

        col1, col2 = st.columns(2)

        with col1:
            st.metric("Regular Reserve Lines", len(regular_reserve))
            if "CaptainSlots" in reserve_df.columns and "FOSlots" in reserve_df.columns:
                total_capt = regular_reserve["CaptainSlots"].sum()
                total_fo = regular_reserve["FOSlots"].sum()
                st.caption(f"Captain: {int(total_capt)} | FO: {int(total_fo)}")

        with col2:
            st.metric("Hot Standby (HSBY) Lines", len(hsby))
            if "CaptainSlots" in reserve_df.columns and "FOSlots" in reserve_df.columns:
                hsby_capt = hsby["CaptainSlots"].sum()
                hsby_fo = hsby["FOSlots"].sum()
                st.caption(f"Captain: {int(hsby_capt)} | FO: {int(hsby_fo)}")

    st.divider()
