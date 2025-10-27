"""Reusable data editor components with validation and change tracking."""

import pandas as pd
import streamlit as st
from typing import List, Dict, Optional


def create_bid_line_editor(df: pd.DataFrame, key: str = "bidline_data_editor") -> pd.DataFrame:
    """Create an editable data grid for bid line data.

    Args:
        df: DataFrame with Line, CT, BT, DO, DD columns
        key: Unique key for the data editor widget

    Returns:
        Edited DataFrame
    """
    edited_df = st.data_editor(
        df,
        hide_index=True,
        use_container_width=True,
        num_rows="fixed",
        disabled=["Line"],  # Line number is read-only
        column_config={
            "Line": st.column_config.NumberColumn(
                "Line",
                help="Bid line number (read-only)",
                width="small"
            ),
            "CT": st.column_config.NumberColumn(
                "CT",
                help="Credit Time (hours)",
                min_value=0.0,
                max_value=200.0,
                step=0.1,
                width="small"
            ),
            "BT": st.column_config.NumberColumn(
                "BT",
                help="Block Time (hours)",
                min_value=0.0,
                max_value=200.0,
                step=0.1,
                width="small"
            ),
            "DO": st.column_config.NumberColumn(
                "DO",
                help="Days Off",
                min_value=0,
                max_value=31,
                step=1,
                width="small"
            ),
            "DD": st.column_config.NumberColumn(
                "DD",
                help="Duty Days",
                min_value=0,
                max_value=31,
                step=1,
                width="small"
            ),
        },
        key=key
    )

    return edited_df


def detect_changes(original_df: pd.DataFrame, edited_df: pd.DataFrame) -> pd.DataFrame:
    """Detect changes between original and edited data.

    Args:
        original_df: Original DataFrame before edits
        edited_df: DataFrame after user edits

    Returns:
        DataFrame with columns: Line, Column, Original, Current
    """
    changes = []
    editable_columns = ["CT", "BT", "DO", "DD"]

    for col in editable_columns:
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

    return pd.DataFrame(changes) if changes else pd.DataFrame(
        columns=["Line", "Column", "Original", "Current"]
    )


def validate_bid_line_edits(df: pd.DataFrame) -> List[str]:
    """Validate edited bid line data and return list of warnings.

    Args:
        df: DataFrame with CT, BT, DO, DD columns

    Returns:
        List of warning messages
    """
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


def render_change_summary(
    original_df: pd.DataFrame,
    edited_df: pd.DataFrame,
    show_validation: bool = True
) -> int:
    """Render summary of changes with expandable details and validation warnings.

    Args:
        original_df: Original DataFrame before edits
        edited_df: DataFrame after user edits
        show_validation: Whether to show validation warnings

    Returns:
        Number of changes detected
    """
    changes = detect_changes(original_df, edited_df)
    num_changes = len(changes)

    if num_changes > 0:
        st.success(
            f"✏️ **Data has been manually edited** "
            f"({num_changes} change{'s' if num_changes > 1 else ''})"
        )

        # Show changed cells
        with st.expander("📝 View edited cells", expanded=False):
            st.dataframe(changes, hide_index=True, use_container_width=True)

        # Add validation warnings
        if show_validation:
            validation_issues = validate_bid_line_edits(edited_df)
            if validation_issues:
                st.warning("⚠️ **Validation Warnings:**")
                for issue in validation_issues:
                    st.warning(issue)

    return num_changes


def render_reset_button(
    session_state_key_edited: str,
    session_state_key_original: str,
    button_key: str = "reset_edits"
) -> None:
    """Render a button to reset edited data to original.

    Args:
        session_state_key_edited: Session state key for edited DataFrame
        session_state_key_original: Session state key for original DataFrame
        button_key: Unique key for the reset button
    """
    if st.button("🔄 Reset to Original Data", key=button_key):
        if session_state_key_original in st.session_state:
            st.session_state[session_state_key_edited] = (
                st.session_state[session_state_key_original].copy()
            )
            st.rerun()


def render_editor_header(show_all_data: bool = True) -> None:
    """Render header for the data editor section.

    Args:
        show_all_data: If True, show caption about editing all data regardless of filters
    """
    st.subheader("📋 Bid Line Data")
    if show_all_data:
        st.caption("**Edit values directly in the table below to correct parsing errors**")


def render_filter_status_message(
    df_all: pd.DataFrame,
    df_filtered: pd.DataFrame,
    filters_active: bool
) -> None:
    """Render informational message about filter status.

    Args:
        df_all: Complete DataFrame (all lines)
        df_filtered: Filtered DataFrame
        filters_active: Whether filters are actively applied
    """
    if filters_active and len(df_filtered) < len(df_all):
        st.info(
            f"ℹ️ Filters are active. Showing **{len(df_filtered)} of {len(df_all)}** lines. "
            f"Adjust filters in sidebar to see more."
        )
