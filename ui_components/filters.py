"""Reusable filter components for Streamlit UI."""

from typing import Dict, Tuple

import pandas as pd
import streamlit as st


def create_metric_range_filter(
    label: str,
    min_value: float,
    max_value: float,
    step: float = 1.0,
    key: str = None,
    is_integer: bool = False,
) -> Tuple[float, float]:
    """Create a range slider filter for a metric.

    Args:
        label: Display label for the slider
        min_value: Minimum value for the range
        max_value: Maximum value for the range
        step: Step size for the slider
        key: Unique key for the widget
        is_integer: If True, cast values to int

    Returns:
        Tuple of (min_selected, max_selected)
    """
    if is_integer:
        min_value = int(min_value)
        max_value = int(max_value)
        step = int(step)
    else:
        min_value = float(min_value)
        max_value = float(max_value)
        step = float(step)

    selected_range = st.sidebar.slider(
        label,
        min_value=min_value,
        max_value=max_value,
        value=(min_value, max_value),
        step=step,
        key=key,
    )

    return selected_range


def create_bid_line_filters(df: pd.DataFrame) -> Dict[str, Tuple[float, float]]:
    """Create complete filter sidebar for bid line data.

    Args:
        df: DataFrame with CT, BT, DO, DD columns

    Returns:
        Dictionary with filter ranges: {'ct': (min, max), 'bt': (min, max), ...}
    """
    st.sidebar.header("🔍 Filters")
    st.sidebar.caption("Filter bid lines by criteria")

    # CT Filter
    ct_min = float(df["CT"].min())
    ct_max = float(df["CT"].max())
    ct_range = create_metric_range_filter(
        "Credit Time (CT)", ct_min, ct_max, step=0.1, key="ct_filter", is_integer=False
    )

    # BT Filter
    bt_min = float(df["BT"].min())
    bt_max = float(df["BT"].max())
    bt_range = create_metric_range_filter(
        "Block Time (BT)", bt_min, bt_max, step=0.1, key="bt_filter", is_integer=False
    )

    # DO Filter
    do_min = int(df["DO"].min())
    do_max = int(df["DO"].max())
    do_range = create_metric_range_filter(
        "Days Off (DO)", do_min, do_max, step=1, key="do_filter", is_integer=True
    )

    # DD Filter
    dd_min = int(df["DD"].min())
    dd_max = int(df["DD"].max())
    dd_range = create_metric_range_filter(
        "Duty Days (DD)", dd_min, dd_max, step=1, key="dd_filter", is_integer=True
    )

    return {
        "ct": ct_range,
        "bt": bt_range,
        "do": do_range,
        "dd": dd_range,
        "defaults": {
            "ct": (ct_min, ct_max),
            "bt": (bt_min, bt_max),
            "do": (do_min, do_max),
            "dd": (dd_min, dd_max),
        },
    }


def apply_dataframe_filters(
    df: pd.DataFrame, filter_ranges: Dict[str, Tuple[float, float]]
) -> pd.DataFrame:
    """Apply filter ranges to a DataFrame.

    Args:
        df: DataFrame to filter
        filter_ranges: Dictionary with 'ct', 'bt', 'do', 'dd' keys containing (min, max) tuples

    Returns:
        Filtered DataFrame
    """
    ct_range = filter_ranges["ct"]
    bt_range = filter_ranges["bt"]
    do_range = filter_ranges["do"]
    dd_range = filter_ranges["dd"]

    filtered_df = df[
        (df["CT"] >= ct_range[0])
        & (df["CT"] <= ct_range[1])
        & (df["BT"] >= bt_range[0])
        & (df["BT"] <= bt_range[1])
        & (df["DO"] >= do_range[0])
        & (df["DO"] <= do_range[1])
        & (df["DD"] >= dd_range[0])
        & (df["DD"] <= dd_range[1])
    ]

    return filtered_df


def is_filter_active(filter_ranges: Dict[str, Tuple[float, float]]) -> bool:
    """Check if any filters are actively applied (different from defaults).

    Args:
        filter_ranges: Dictionary with filter ranges including 'defaults' key

    Returns:
        True if any filter is different from its default range
    """
    defaults = filter_ranges.get("defaults", {})

    return (
        filter_ranges["ct"] != defaults.get("ct")
        or filter_ranges["bt"] != defaults.get("bt")
        or filter_ranges["do"] != defaults.get("do")
        or filter_ranges["dd"] != defaults.get("dd")
    )


def render_filter_summary(df_original: pd.DataFrame, df_filtered: pd.DataFrame) -> None:
    """Render a summary caption showing filtered vs total lines.

    Args:
        df_original: Original unfiltered DataFrame
        df_filtered: Filtered DataFrame
    """
    st.sidebar.caption(f"**Showing {len(df_filtered)} of {len(df_original)} lines**")


def render_filter_reset_button(key: str = "reset_filters") -> bool:
    """Render a reset filters button in the sidebar.

    Args:
        key: Unique key for the button

    Returns:
        True if button was clicked
    """
    return st.sidebar.button("Reset Filters", key=key)
