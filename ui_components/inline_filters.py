"""
Inline Filter Components

Provides reusable components for rendering filter panels inline within tab content
rather than in the sidebar. This improves UX by showing only relevant controls
for the current tab.

Created: Session 39 - UI/UX Sidebar Removal
"""

import streamlit as st
from typing import Any


def render_inline_filter_panel(
    title: str,
    icon: str = "🔍",
    expanded: bool = False
) -> Any:
    """
    Render an inline filter panel with expand/collapse functionality.

    This creates a collapsible expander that can contain filter controls,
    replacing the traditional sidebar pattern with inline filters that are
    only visible on the relevant tab.

    Args:
        title: Title for the filter panel (e.g., "Filter Bid Lines")
        icon: Emoji icon to display (default: 🔍)
        expanded: Whether panel starts expanded (default: False)

    Returns:
        Streamlit expander object to use in a 'with' statement

    Example:
        >>> with render_inline_filter_panel("Filter Options", icon="🎯"):
        ...     st.slider("Credit Time", 0, 200)
        ...     st.button("Apply Filters")
    """
    label = f"{icon} {title}"

    return st.expander(
        label,
        expanded=expanded
    )


def render_filter_actions(
    apply_key: str,
    reset_key: str,
    apply_disabled: bool = False,
    show_count: bool = False,
    active_filter_count: int = 0
) -> tuple[bool, bool]:
    """
    Render standard Apply/Reset filter action buttons.

    Args:
        apply_key: Unique key for Apply button (e.g., "apply_bid_filters")
        reset_key: Unique key for Reset button (e.g., "reset_bid_filters")
        apply_disabled: Whether Apply button should be disabled
        show_count: Whether to show active filter count
        active_filter_count: Number of active filters

    Returns:
        Tuple of (apply_clicked, reset_clicked) booleans

    Example:
        >>> apply, reset = render_filter_actions("apply_bid", "reset_bid")
        >>> if apply:
        ...     # Apply filters
        >>> if reset:
        ...     # Reset filters
    """
    col1, col2, col3 = st.columns([2, 2, 6])

    with col1:
        apply_clicked = st.button(
            "Apply Filters",
            type="primary",
            key=apply_key,
            disabled=apply_disabled,
            use_container_width=True
        )

    with col2:
        reset_clicked = st.button(
            "Reset Filters",
            key=reset_key,
            use_container_width=True
        )

    with col3:
        if show_count and active_filter_count > 0:
            st.caption(f"✓ {active_filter_count} filter(s) active")

    return apply_clicked, reset_clicked


def render_inline_section_header(
    title: str,
    subtitle: str = None,
    icon: str = "📊"
) -> None:
    """
    Render a consistent section header for inline content areas.

    This provides visual separation between different sections within a tab,
    replacing sidebar-based organization with clear inline sections.

    Args:
        title: Main section title
        subtitle: Optional subtitle or description
        icon: Emoji icon to display

    Example:
        >>> render_inline_section_header(
        ...     "Distribution Charts",
        ...     subtitle="Visual analysis of credit time and duty days",
        ...     icon="📊"
        ... )
    """
    st.markdown(f"### {icon} {title}")
    if subtitle:
        st.caption(subtitle)


def render_filter_summary(
    filters: dict,
    label: str = "Active Filters"
) -> None:
    """
    Render a compact summary of currently active filters.

    Shows users what filters are currently applied in a clear,
    easy-to-scan format.

    Args:
        filters: Dictionary of filter names and values
        label: Label for the summary section

    Example:
        >>> filters = {"Domicile": ["ONT", "SDF"], "Aircraft": ["757"]}
        >>> render_filter_summary(filters)
    """
    active_filters = {k: v for k, v in filters.items() if v}

    if not active_filters:
        st.caption(f"_{label}: None (showing all data)_")
        return

    filter_strings = []
    for key, value in active_filters.items():
        if isinstance(value, list):
            if value:  # Non-empty list
                filter_strings.append(f"**{key}:** {', '.join(str(v) for v in value)}")
        elif value is not None:
            filter_strings.append(f"**{key}:** {value}")

    if filter_strings:
        st.caption(f"_{label}: {' | '.join(filter_strings)}_")
    else:
        st.caption(f"_{label}: None (showing all data)_")
