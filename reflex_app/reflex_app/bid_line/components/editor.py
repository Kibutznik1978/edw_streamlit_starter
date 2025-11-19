"""Interactive Data Editor Component for Bid Line Analyzer.

This component provides inline cell editing functionality for bid line data.
- Editable columns: CT, BT, DO, DD
- Read-only columns: Line, VTOType, VTOPeriod, pay period breakdowns, etc.
- Visual change tracking (highlighted rows)
- Real-time validation
- Responsive table layout
"""

import reflex as rx
from typing import List, Dict, Any, Optional
from ..bid_line_state import BidLineState


def editor_component() -> rx.Component:
    """Interactive data editor for bid line records.

    Features:
    - Displays filtered data from BidLineState.filtered_data
    - Inline editing for CT, BT, DO, DD columns
    - Read-only display for all other columns
    - Yellow highlighting for edited rows
    - Responsive scrollable table
    - Validation warnings display

    Returns:
        rx.Component: Complete editor component with table and controls
    """
    return rx.cond(
        BidLineState.has_results,
        rx.vstack(
            # Editor header with controls
            rx.hstack(
                rx.heading(
                    "Bid Line Editor",
                    size="6",
                    color=rx.color("gray", 12),
                ),
                rx.spacer(),
                # Advanced edit mode toggle
                rx.button(
                    rx.icon(
                        rx.cond(
                            BidLineState.advanced_edit_mode,
                            "lock-open",
                            "lock",
                        ),
                        size=18,
                    ),
                    rx.cond(
                        BidLineState.advanced_edit_mode,
                        "Advanced Edit Mode: ON",
                        "Advanced Edit Mode: OFF",
                    ),
                    on_click=BidLineState.toggle_advanced_edit_mode,
                    size="2",
                    variant=rx.cond(
                        BidLineState.advanced_edit_mode,
                        "solid",
                        "outline",
                    ),
                    color_scheme=rx.cond(
                        BidLineState.advanced_edit_mode,
                        "orange",
                        "gray",
                    ),
                ),
                # Line count indicator
                rx.badge(
                    f"{BidLineState.filtered_lines_count} lines",
                    color_scheme="blue",
                    size="2",
                ),
                # Edit indicator
                rx.cond(
                    BidLineState.has_edits,
                    rx.badge(
                        f"{BidLineState.edited_cells.length()} edits",
                        color_scheme="yellow",
                        size="2",
                    ),
                ),
                # Reset button
                rx.cond(
                    BidLineState.has_edits,
                    rx.button(
                        rx.icon("rotate-ccw", size=18),
                        "Reset Edits",
                        on_click=BidLineState.reset_edits,
                        size="2",
                        variant="outline",
                        color_scheme="red",
                    ),
                ),
                spacing="3",
                width="100%",
                align="center",
            ),

            # Validation warnings
            rx.cond(
                BidLineState.validation_warnings.length() > 0,
                rx.box(
                    rx.vstack(
                        rx.hstack(
                            rx.icon("alert-triangle", size=20, color=rx.color("amber", 9)),
                            rx.text(
                                "Validation Warnings",
                                weight="bold",
                                size="3",
                            ),
                            spacing="2",
                        ),
                        rx.foreach(
                            BidLineState.validation_warnings,
                            lambda warning: rx.text(
                                "• " + warning,
                                size="2",
                                color=rx.color("gray", 11),
                            ),
                        ),
                        spacing="2",
                    ),
                    padding="3",
                    border_radius="8px",
                    background=rx.color("amber", 2),
                    border=f"1px solid {rx.color('amber', 6)}",
                    width="100%",
                ),
            ),

            # Editable table
            _editable_table(),

            spacing="4",
            width="100%",
        ),
    )


_BASE_COLUMNS = ["Line", "CT", "BT", "DO", "DD"]
_READ_ONLY_DYNAMIC_COLUMNS = {"Hot Standby"}
_DYNAMIC_COLUMN_WIDTH = "180px"
_CUSTOM_COLUMN_LABELS = {
    "PayPeriodCode_PP1": "Code PP1",
    "PayPeriodCode_PP2": "Code PP2",
}


def _editable_table() -> rx.Component:
    """Render the data editor with a sticky header inside one scroll container."""
    return rx.box(
        _header_row(),
        rx.vstack(
            rx.foreach(
                BidLineState.filtered_data,
                lambda row, idx: _editable_row(row, idx),
            ),
            spacing="0",
            width="max-content",
            min_width="100%",
        ),
        width="100%",
        overflow="auto",
        max_height="500px",
        border="1px solid",
        border_color=rx.color("gray", 6),
        border_radius="8px",
        background="white",
    )


def _header_row() -> rx.Component:
    """Sticky header that stays visible while scrolling vertically and horizontally."""

    def metric_header(text_var: rx.Var, width: str) -> rx.Component:
        return _header_cell(
            rx.tooltip(
                rx.hstack(
                    rx.text(text_var),
                    rx.icon("info", size=14, color=rx.color("gray", 10)),
                    spacing="1",
                    align="center",
                ),
                content=BidLineState.averaging_tooltip,
            ),
            width=width,
            background=rx.color("blue", 2),
            border_color=rx.color("blue", 6),
        )

    base_headers = [
        _header_cell(
            rx.text("Line"),
            width="80px",
            background=rx.color("gray", 2),
            border_color=rx.color("gray", 6),
        ),
        metric_header(BidLineState.ct_header, "140px"),
        metric_header(BidLineState.bt_header, "140px"),
        metric_header(BidLineState.do_header, "120px"),
        metric_header(BidLineState.dd_header, "120px"),
    ]

    additional_headers = rx.foreach(
        BidLineState.table_column_names,
        lambda col: rx.cond(
            ~rx.Var.create(_BASE_COLUMNS).contains(col),
            _header_cell(
                rx.text(_format_column_label(col)),
                width=_DYNAMIC_COLUMN_WIDTH,
                background=rx.color("gray", 2),
                border_color=rx.color("gray", 6),
            ),
        ),
    )

    return rx.box(
        rx.hstack(
            *base_headers,
            additional_headers,
            spacing="0",
            width="max-content",
            min_width="100%",
        ),
        position="sticky",
        top="0",
        z_index="5",
        background="white",
        box_shadow="0 2px 4px rgba(0, 0, 0, 0.05)",
    )


def _header_cell(
    content: rx.Component,
    *,
    width: str,
    background: str,
    border_color: str,
) -> rx.Component:
    """Consistent styling for header cells."""
    return rx.box(
        content,
        style={
            "text-align": "center",
            "font-weight": "bold",
            "padding": "0.75rem",
            "background-color": background,
            "border-bottom": f"2px solid {border_color}",
            "width": width,
            "min-width": width,
            "max-width": width,
            "color": rx.color("gray", 12),
        },
    )


def _editable_row(row: Dict[str, Any], row_idx: int) -> rx.Component:
    """Render a single editable table row."""
    line_number = row["Line"]

    base_cells = [
        _read_only_cell(row["Line"], "80px", color=rx.color("gray", 11)),
        rx.cond(
            BidLineState.advanced_edit_mode,
            _editable_cell(row_idx, "CT", row["CT"], "float", (0.0, 200.0), "140px"),
            _read_only_cell(row["CT"], "140px"),
        ),
        rx.cond(
            BidLineState.advanced_edit_mode,
            _editable_cell(row_idx, "BT", row["BT"], "float", (0.0, 200.0), "140px"),
            _read_only_cell(row["BT"], "140px"),
        ),
        rx.cond(
            BidLineState.advanced_edit_mode,
            _editable_cell(row_idx, "DO", row["DO"], "int", (0, 31), "120px"),
            _read_only_cell(row["DO"], "120px"),
        ),
        rx.cond(
            BidLineState.advanced_edit_mode,
            _editable_cell(row_idx, "DD", row["DD"], "int", (0, 31), "120px"),
            _read_only_cell(row["DD"], "120px"),
        ),
    ]

    additional_cells = rx.foreach(
        row.keys(),
        lambda col: rx.cond(
            ~rx.Var.create(_BASE_COLUMNS).contains(col),
            rx.cond(
                BidLineState.advanced_edit_mode,
                rx.cond(
                    rx.Var.create(_READ_ONLY_DYNAMIC_COLUMNS).contains(col),
                    _read_only_cell(
                        row[col],
                        _DYNAMIC_COLUMN_WIDTH,
                        font_size="0.8rem",
                    ),
                    _editable_cell(
                        row_idx,
                        col,
                        row[col],
                        "text",
                        (None, None),
                        _DYNAMIC_COLUMN_WIDTH,
                    ),
                ),
                _read_only_cell(
                    row[col],
                    _DYNAMIC_COLUMN_WIDTH,
                    font_size="0.8rem",
                ),
            ),
        ),
    )

    return rx.hstack(
        *base_cells,
        additional_cells,
        spacing="0",
        width="max-content",
        min_width="100%",
        align="stretch",
        background_color=rx.cond(
            BidLineState.edited_line_numbers.contains(line_number),
            rx.color("yellow", 3),
            "white",
        ),
        style={
            "border-bottom": f"1px solid {rx.color('gray', 4)}",
            "transition": "background-color 0.2s ease",
            "_hover": {
                "background-color": rx.color("gray", 2),
            },
        },
    )


def _format_column_label(column: Any) -> Any:
    """Return a human-friendly header label for dynamic columns."""
    formatted = column
    for key, label in _CUSTOM_COLUMN_LABELS.items():
        formatted = rx.cond(column == key, label, formatted)
    return formatted


def _editable_cell(
    row_idx: int,
    column: str,
    value: Any,
    value_type: str,
    value_range: tuple,
    cell_width: str = "140px",
) -> rx.Component:
    """Render an editable table cell with change highlighting.

    Args:
        row_idx: Row index in filtered data
        column: Column name (e.g., CT, BT, DO, DD, or any other column in advanced mode)
        value: Current cell value
        value_type: Data type ("float", "int", or "text")
        value_range: (min, max) validation range (can be (None, None) for text fields)
        cell_width: Fixed width for cell to match header (e.g., "140px", "120px")

    Returns:
        rx.Component: Editable input cell with edit indicator if modified
    """
    min_val, max_val = value_range if value_range != (None, None) else (None, None)

    # Determine input type and step
    if value_type == "int":
        input_type = "number"
        step = "1"
    elif value_type == "float":
        input_type = "number"
        step = "0.1"
    else:
        input_type = "text"
        step = None

    # Check if this cell has been edited
    # Construct cell key and check if it's in the edited_cell_keys list
    cell_key = f"{row_idx}:{column}"
    cell_edited = BidLineState.edited_cell_keys.contains(cell_key)

    # Build input with conditional props
    # Use a fixed reasonable width for all inputs to avoid Var comparison issues
    input_kwargs = {
        "value": value.to(str),
        "type": input_type,
        "on_change": lambda new_val: BidLineState.update_cell(row_idx, column, new_val),
    }

    # Add optional number input props
    if step is not None:
        input_kwargs["step"] = step
    if min_val is not None:
        input_kwargs["min"] = min_val
    if max_val is not None:
        input_kwargs["max"] = max_val

    return rx.box(
        rx.box(
            rx.input(
                **input_kwargs,
                style={
                    "width": "100%",
                    "padding": "0.5rem",
                    "text-align": "center",
                    "border": "1px solid",
                    "border-color": rx.cond(
                        cell_edited,
                        rx.color("amber", 7),
                        rx.color("gray", 6),
                    ),
                    "border-radius": "4px",
                    "font-size": "14px",
                    "background-color": rx.cond(
                        cell_edited,
                        rx.color("amber", 2),
                        "white",
                    ),
                    ":focus": {
                        "outline": "2px solid",
                        "outline-color": rx.color("blue", 8),
                        "border-color": rx.color("blue", 8),
                    },
                    ":hover": {
                        "border-color": rx.cond(
                            cell_edited,
                            rx.color("amber", 8),
                            rx.color("gray", 8),
                        ),
                    },
                },
            ),
            # Small corner indicator for edited cells
            rx.cond(
                cell_edited,
                rx.box(
                    position="absolute",
                    top="2px",
                    right="2px",
                    width="6px",
                    height="6px",
                    background=rx.color("amber", 9),
                    border_radius="50%",
                ),
            ),
            position="relative",
            width=cell_width,
        ),
        style={
            "padding": "0.25rem",
            "width": cell_width,
            "min-width": cell_width,
            "max-width": cell_width,
        },
    )


def _read_only_cell(
    value: Any,
    width: str,
    *,
    text_align: str = "center",
    font_size: str = "0.875rem",
    color: Optional[str] = None,
) -> rx.Component:
    """Render a non-editable table cell while keeping widths synchronized."""
    resolved_color = color or rx.color("gray", 10)
    display_value = value.to(str) if hasattr(value, "to") else str(value)

    return rx.box(
        rx.text(
            display_value,
            style={
                "text-align": text_align,
                "color": resolved_color,
                "font-size": font_size,
                "width": "100%",
            },
        ),
        style={
            "padding": "0.5rem",
            "width": width,
            "min-width": width,
            "max-width": width,
        },
    )
