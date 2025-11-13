"""Trip Records Table Component.

This module provides a sortable, paginated table of trip records for the EDW
Pairing Analyzer, with row selection and CSV export functionality.
"""

import reflex as rx
from typing import Dict, Any

from ..edw_state import EDWState
from reflex_app.theme import Colors, Typography, Spacing


def table_component() -> rx.Component:
    """Trip records table component.

    Displays a sortable, paginated table of all filtered trips with:
    - Sortable columns
    - Pagination controls
    - Row selection (updates selected_trip_id)
    - CSV export button

    Only shown when results are available.
    """
    return rx.cond(
        EDWState.has_results,
        rx.card(
            rx.vstack(
                # Header with title and export button
                rx.hstack(
                rx.heading("Trip Records", size="6", weight="bold"),
                rx.spacer(),
                _export_button(),
                width="100%",
                align="center",
            ),
                # Table container
                rx.box(
                    _render_table(),
                    width="100%",
                    overflow_x="auto",
                ),
                # Pagination controls
                _pagination_controls(),
                spacing="4",
                width="100%",
            ),
            size="4",
            width="100%",
        ),
        rx.fragment(),
    )


def _export_button() -> rx.Component:
    """CSV export button."""
    return rx.button(
        rx.icon("download", size=16),
        "Export CSV",
        on_click=EDWState.download_csv,
        size="2",
        variant="soft",
        disabled=~EDWState.has_results,
        cursor="pointer",
    )


def _render_table() -> rx.Component:
    """Render the trip records table."""
    return rx.table.root(
        rx.table.header(
            rx.table.row(
                _sortable_header("Trip ID"),
                _sortable_header("Frequency"),
                _sortable_header("TAFB Hours"),
                _sortable_header("Duty Days"),
                _sortable_header("EDW"),
                _sortable_header("Hot Standby"),
                _sortable_header("Max Duty Length"),
                _sortable_header("Max Legs/Duty"),
            ),
        ),
        rx.table.body(
            rx.foreach(
                EDWState.paginated_trips,
                lambda trip: _render_trip_row(trip),
            )
        ),
        variant="surface",
        size="2",
        width="100%",
    )


def _sortable_header(column: str, align: str = "left") -> rx.Component:
    """Render a sortable column header with modern styling.

    Args:
        column: Column name to display and sort by.
        align: Text alignment ("left" or "right"). Default is "left".

    Returns:
        Table header cell with sort icon and click handler.
    """
    # Determine if this is a numeric column (right-aligned)
    numeric_columns = ["Frequency", "TAFB Hours", "Duty Days", "Max Duty Length", "Max Legs/Duty"]
    is_numeric = column in numeric_columns
    text_align = "right" if is_numeric else "left"
    justify = "end" if is_numeric else "start"

    return rx.table.column_header_cell(
        rx.hstack(
            rx.text(column, weight="bold", size="2"),
            # Show sort indicator if this column is active
            rx.cond(
                EDWState.table_sort_column == column,
                rx.cond(
                    EDWState.table_sort_ascending,
                    rx.icon("chevron-up", size=14),
                    rx.icon("chevron-down", size=14),
                ),
                rx.fragment(),
            ),
            spacing="1",
            align="center",
            justify=justify,
        ),
        on_click=lambda: EDWState.table_sort(column),
        cursor="pointer",
        style={
            # Sticky header with proper stacking
            "position": "sticky",
            "top": "0",
            "z_index": "10",
            # Modern background and border
            "background": Colors.gray_50,
            "border_bottom": f"2px solid {Colors.gray_300}",
            # Typography
            "font_weight": Typography.weight_bold,
            "font_size": "13px",
            "text_align": text_align,
            "color": Colors.gray_700,
            # Spacing
            "padding": "12px 16px",
            # Interaction states
            "transition": "background-color 0.15s ease",
            "_hover": {
                "background": Colors.gray_100,
            },
        },
    )


def _render_trip_row(trip: Dict[str, Any]) -> rx.Component:
    """Render a single trip row with modern table styling.

    Args:
        trip: Trip data dictionary (Reflex Var when used in rx.foreach).

    Returns:
        Table row with trip data and click handler.
    """
    # Base cell style - shared by all cells
    cell_base_style = {
        "padding": "12px 16px",
        "border_bottom": f"1px solid {Colors.gray_200}",
        "font_size": "13px",
        "color": Colors.gray_800,
    }

    # Text cell style (left-aligned)
    cell_text_style = {
        **cell_base_style,
        "text_align": "left",
    }

    # Numeric cell style (right-aligned, monospace for tabular numbers)
    cell_numeric_style = {
        **cell_base_style,
        "text_align": "right",
        "font_family": Typography.font_mono,
        "font_variant_numeric": "tabular-nums",
    }

    return rx.table.row(
        # Text columns (left-aligned)
        rx.table.cell(trip["Trip ID"], style=cell_text_style),
        # Numeric columns (right-aligned, monospace)
        rx.table.cell(trip["Frequency"], style=cell_numeric_style),
        rx.table.cell(trip["TAFB Hours"], style=cell_numeric_style),
        rx.table.cell(trip["Duty Days"], style=cell_numeric_style),
        # Badge columns (left-aligned)
        rx.table.cell(
            _render_badge(trip["EDW"], "EDW", "Day"),
            style=cell_text_style,
        ),
        rx.table.cell(
            _render_badge(trip["Hot Standby"], "HS", "No"),
            style=cell_text_style,
        ),
        # Numeric columns (right-aligned, monospace)
        rx.table.cell(trip["Max Duty Length"], style=cell_numeric_style),
        rx.table.cell(trip["Max Legs/Duty"], style=cell_numeric_style),
        # Row interaction - selection and hover
        on_click=lambda: EDWState.select_trip_from_table(trip["Trip ID"]),
        cursor="pointer",
        background_color=rx.cond(
            EDWState.selected_trip_id == trip["Trip ID"],
            rx.color("blue", 3),
            "transparent",
        ),
        style={
            "transition": "background-color 0.15s ease",
            "_hover": {
                "background": Colors.gray_50,
            },
        },
    )


def _render_badge(is_true: bool, true_label: str, false_label: str) -> rx.Component:
    """Render a badge for boolean values.

    Args:
        is_true: Boolean value to display.
        true_label: Label when True.
        false_label: Label when False.

    Returns:
        Badge component.
    """
    return rx.cond(
        is_true,
        rx.badge(true_label, color_scheme="blue", variant="soft"),
        rx.badge(false_label, color_scheme="gray", variant="soft"),
    )


def _pagination_controls() -> rx.Component:
    """Render pagination controls."""
    return rx.hstack(
        # Page size selector
        rx.hstack(
            rx.text("Rows per page:", size="2", weight="medium"),
            rx.select.root(
                rx.select.trigger(placeholder=str(EDWState.table_page_size)),
                rx.select.content(
                    rx.select.item("25", value="25"),
                    rx.select.item("50", value="50"),
                    rx.select.item("100", value="100"),
                ),
                value=str(EDWState.table_page_size),
                on_change=EDWState.set_table_page_size,
                size="1",
            ),
            spacing="2",
            align="center",
        ),
        rx.spacer(),
        # Page info
        rx.text(
            f"Page {EDWState.table_page} of {EDWState.total_pages} ({EDWState.sorted_filtered_trips.length()} trips)",
            size="2",
            color=rx.color("gray", 11),
        ),
        rx.spacer(),
        # Navigation buttons
        rx.hstack(
            rx.button(
                rx.icon("chevrons-left", size=16),
                on_click=lambda: EDWState.set_table_page(1),
                size="1",
                variant="soft",
                disabled=EDWState.table_page == 1,
            ),
            rx.button(
                rx.icon("chevron-left", size=16),
                on_click=lambda: EDWState.set_table_page(EDWState.table_page - 1),
                size="1",
                variant="soft",
                disabled=EDWState.table_page == 1,
            ),
            rx.button(
                rx.icon("chevron-right", size=16),
                on_click=lambda: EDWState.set_table_page(EDWState.table_page + 1),
                size="1",
                variant="soft",
                disabled=EDWState.table_page >= EDWState.total_pages,
            ),
            rx.button(
                rx.icon("chevrons-right", size=16),
                on_click=lambda: EDWState.set_table_page(EDWState.total_pages),
                size="1",
                variant="soft",
                disabled=EDWState.table_page >= EDWState.total_pages,
            ),
            spacing="1",
        ),
        width="100%",
        align="center",
        padding="0.5rem",
    )
