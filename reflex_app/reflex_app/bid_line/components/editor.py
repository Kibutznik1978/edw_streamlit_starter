"""Interactive Data Editor Component for Bid Line Analyzer.

This component provides inline cell editing functionality for bid line data.
- Editable columns: CT, BT, DO, DD
- Read-only columns: Line, VTOType, VTOPeriod, pay period breakdowns, etc.
- Visual change tracking (highlighted rows)
- Real-time validation
- Responsive table layout
"""

import reflex as rx
from typing import List, Dict, Any
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


def _editable_table() -> rx.Component:
    """Create the editable table component.

    Returns:
        rx.Component: Scrollable table with editable cells
    """
    # Define which columns are editable
    editable_columns = {"CT", "BT", "DO", "DD"}

    # Get column metadata
    column_config = {
        "Line": {"type": "int", "range": (0, 1000), "header": "Line"},
        "CT": {"type": "float", "range": (0.0, 200.0), "header": "CT (hours)"},
        "BT": {"type": "float", "range": (0.0, 200.0), "header": "BT (hours)"},
        "DO": {"type": "int", "range": (0, 31), "header": "DO (days)"},
        "DD": {"type": "int", "range": (0, 31), "header": "DD (days)"},
    }

    return rx.box(
        rx.table.root(
            # Table header
            rx.table.header(
                rx.table.row(
                    # Line column
                    rx.table.column_header_cell(
                        "Line",
                        style={
                            "text-align": "center",
                            "font-weight": "bold",
                            "padding": "0.75rem",
                            "background-color": rx.color("gray", 2),
                            "position": "sticky",
                            "top": 0,
                            "z-index": 10,
                        },
                    ),
                    # CT column
                    rx.table.column_header_cell(
                        "CT",
                        style={
                            "text-align": "center",
                            "font-weight": "bold",
                            "padding": "0.75rem",
                            "background-color": rx.color("blue", 2),
                            "position": "sticky",
                            "top": 0,
                            "z-index": 10,
                        },
                    ),
                    # BT column
                    rx.table.column_header_cell(
                        "BT",
                        style={
                            "text-align": "center",
                            "font-weight": "bold",
                            "padding": "0.75rem",
                            "background-color": rx.color("blue", 2),
                            "position": "sticky",
                            "top": 0,
                            "z-index": 10,
                        },
                    ),
                    # DO column
                    rx.table.column_header_cell(
                        "DO",
                        style={
                            "text-align": "center",
                            "font-weight": "bold",
                            "padding": "0.75rem",
                            "background-color": rx.color("blue", 2),
                            "position": "sticky",
                            "top": 0,
                            "z-index": 10,
                        },
                    ),
                    # DD column
                    rx.table.column_header_cell(
                        "DD",
                        style={
                            "text-align": "center",
                            "font-weight": "bold",
                            "padding": "0.75rem",
                            "background-color": rx.color("blue", 2),
                            "position": "sticky",
                            "top": 0,
                            "z-index": 10,
                        },
                    ),
                    # Additional columns (dynamic based on data)
                    # VTOType, VTOPeriod, pay period columns, etc.
                    rx.foreach(
                        BidLineState.filtered_data[0].keys(),
                        lambda col: rx.cond(
                            ~rx.Var.create(["Line", "CT", "BT", "DO", "DD"]).contains(col),
                            rx.table.column_header_cell(
                                col,
                                style={
                                    "text-align": "center",
                                    "font-weight": "bold",
                                    "padding": "0.75rem",
                                    "background-color": rx.color("gray", 2),
                                    "position": "sticky",
                                    "top": 0,
                                    "z-index": 10,
                                },
                            ),
                        ),
                    ),
                ),
            ),
            # Table body
            rx.table.body(
                rx.foreach(
                    BidLineState.filtered_data,
                    lambda row, idx: _editable_row(row, idx),
                ),
            ),
            width="100%",
            variant="surface",
        ),
        width="100%",
        overflow_x="auto",
        overflow_y="auto",
        max_height="600px",
        border="1px solid",
        border_color=rx.color("gray", 6),
        border_radius="8px",
    )


def _editable_row(row: Dict[str, Any], row_idx: int) -> rx.Component:
    """Render a single editable table row.

    Args:
        row: Row data dictionary
        row_idx: Index of this row

    Returns:
        rx.Component: Table row with editable and read-only cells
    """
    # Check if this row has been edited
    # We'll use the Line number to track edits
    line_number = row["Line"]

    return rx.table.row(
        # Line (read-only)
        rx.table.cell(
            rx.text(
                row["Line"].to(str),
                style={
                    "text-align": "center",
                    "padding": "0.5rem",
                    "color": rx.color("gray", 11),
                },
            ),
        ),
        # CT (editable)
        _editable_cell(row_idx, "CT", row["CT"], "float", (0.0, 200.0)),
        # BT (editable)
        _editable_cell(row_idx, "BT", row["BT"], "float", (0.0, 200.0)),
        # DO (editable)
        _editable_cell(row_idx, "DO", row["DO"], "int", (0, 31)),
        # DD (editable)
        _editable_cell(row_idx, "DD", row["DD"], "int", (0, 31)),
        # Additional columns (read-only)
        rx.foreach(
            row.keys(),
            lambda col: rx.cond(
                ~rx.Var.create(["Line", "CT", "BT", "DO", "DD"]).contains(col),
                rx.table.cell(
                    rx.text(
                        row[col].to(str),
                        style={
                            "text-align": "center",
                            "padding": "0.5rem",
                            "color": rx.color("gray", 10),
                            "font-size": "0.875rem",
                        },
                    ),
                ),
            ),
        ),
        # Highlight if row has edits
        background_color=rx.cond(
            BidLineState.edited_cells.contains(
                lambda edit: edit["line"] == line_number
            ),
            rx.color("yellow", 3),
            "white",
        ),
        style={
            "transition": "background-color 0.2s ease",
            ":hover": {
                "background-color": rx.color("gray", 2),
            },
        },
    )


def _editable_cell(
    row_idx: int,
    column: str,
    value: Any,
    value_type: str,
    value_range: tuple,
) -> rx.Component:
    """Render an editable table cell.

    Args:
        row_idx: Row index in filtered data
        column: Column name (CT, BT, DO, or DD)
        value: Current cell value
        value_type: Data type ("float" or "int")
        value_range: (min, max) validation range

    Returns:
        rx.Component: Editable input cell
    """
    min_val, max_val = value_range

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

    return rx.table.cell(
        rx.input(
            value=value.to(str),
            type=input_type,
            step=step,
            min=min_val,
            max=max_val,
            on_change=lambda new_val: BidLineState.update_cell(
                row_idx, column, new_val
            ),
            style={
                "width": "100%",
                "padding": "0.5rem",
                "text-align": "center",
                "border": "1px solid",
                "border-color": rx.color("gray", 6),
                "border-radius": "4px",
                "font-size": "14px",
                "background-color": "white",
                ":focus": {
                    "outline": "2px solid",
                    "outline-color": rx.color("blue", 8),
                    "border-color": rx.color("blue", 8),
                },
                ":hover": {
                    "border-color": rx.color("gray", 8),
                },
            },
        ),
        style={
            "padding": "0.25rem",
        },
    )
