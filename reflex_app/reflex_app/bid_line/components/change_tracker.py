"""Change Tracking Component for Bid Line Analyzer.

This component displays detailed change history including:
- List of all edits with before/after values
- Ability to undo individual edits
- Change summary statistics
- Visual indicators for validation status
"""

import reflex as rx
from ..bid_line_state import BidLineState


def change_tracker_component() -> rx.Component:
    """Change tracking panel showing all edits and validation warnings.

    Features:
    - Table of all changes with Line, Column, Old Value, New Value
    - Undo button for each edit
    - Change summary (total edits, edits by column)
    - Validation warnings display
    - Reset all edits button

    Returns:
        rx.Component: Complete change tracking panel
    """
    return rx.cond(
        BidLineState.has_edits,
        rx.card(
            rx.vstack(
                # Header
                rx.hstack(
                    rx.hstack(
                        rx.icon("history", size=24, color=rx.color("blue", 9)),
                        rx.heading(
                            "Change History",
                            size="6",
                            color=rx.color("gray", 12),
                        ),
                        spacing="2",
                        align="center",
                    ),
                    rx.spacer(),
                    rx.icon_button(
                        rx.cond(
                            BidLineState.change_history_expanded,
                            rx.icon("chevron-up", size=18),
                            rx.icon("chevron-down", size=18),
                        ),
                        on_click=BidLineState.toggle_change_history,
                        variant="ghost",
                        size="2",
                        aria_label="Toggle change history",
                        color_scheme="gray",
                    ),
                    # Edit count badge
                    rx.badge(
                        f"{BidLineState.edited_cells.length()} changes",
                        color_scheme="blue",
                        size="2",
                    ),
                    # Reset all button
                    rx.button(
                        rx.icon("rotate-ccw", size=18),
                        "Reset All",
                        on_click=BidLineState.reset_edits,
                        size="2",
                        variant="outline",
                        color_scheme="red",
                    ),
                    spacing="3",
                    width="100%",
                    align="center",
                ),

                rx.cond(
                    BidLineState.change_history_expanded,
                    rx.vstack(
                        # Change summary
                        _change_summary(),

                        # Changes table
                        rx.box(
                            rx.table.root(
                                # Header
                                rx.table.header(
                                    rx.table.row(
                                        rx.table.column_header_cell(
                                            "Line",
                                            style={
                                                "text-align": "center",
                                                "font-weight": "bold",
                                                "padding": "0.75rem",
                                            },
                                        ),
                                        rx.table.column_header_cell(
                                            "Column",
                                            style={
                                                "text-align": "center",
                                                "font-weight": "bold",
                                                "padding": "0.75rem",
                                            },
                                        ),
                                        rx.table.column_header_cell(
                                            "Old Value",
                                            style={
                                                "text-align": "center",
                                                "font-weight": "bold",
                                                "padding": "0.75rem",
                                            },
                                        ),
                                        rx.table.column_header_cell(
                                            "→",
                                            style={
                                                "text-align": "center",
                                                "font-weight": "bold",
                                                "padding": "0.75rem",
                                                "width": "40px",
                                            },
                                        ),
                                        rx.table.column_header_cell(
                                            "New Value",
                                            style={
                                                "text-align": "center",
                                                "font-weight": "bold",
                                                "padding": "0.75rem",
                                            },
                                        ),
                                        rx.table.column_header_cell(
                                            "Action",
                                            style={
                                                "text-align": "center",
                                                "font-weight": "bold",
                                                "padding": "0.75rem",
                                                "width": "100px",
                                            },
                                        ),
                                    ),
                                ),
                                # Body
                                rx.table.body(
                                    rx.foreach(
                                        BidLineState.edited_cells,
                                        lambda edit, idx: _change_row(edit, idx),
                                    ),
                                ),
                                width="100%",
                                variant="surface",
                            ),
                            width="100%",
                            overflow_x="auto",
                            max_height="400px",
                            overflow_y="auto",
                            border="1px solid",
                            border_color=rx.color("gray", 6),
                            border_radius="8px",
                        ),

                        spacing="4",
                        width="100%",
                    ),
                    rx.box(),
                ),

                spacing="4",
                width="100%",
            ),
            size="4",
            width="100%",
        ),
    )


def _change_summary() -> rx.Component:
    """Display summary of changes by column.

    Returns:
        rx.Component: Change summary display
    """
    return rx.box(
        rx.hstack(
            rx.text(
                "Changes by column:",
                weight="medium",
                size="2",
                color=rx.color("gray", 11),
            ),
            # Count edits by column type
            # We'll show badges for CT, BT, DO, DD edit counts
            _column_edit_badge("CT"),
            _column_edit_badge("BT"),
            _column_edit_badge("DO"),
            _column_edit_badge("DD"),
            spacing="3",
            wrap="wrap",
        ),
        padding="3",
        border_radius="6px",
        background=rx.color("blue", 2),
        border=f"1px solid {rx.color('blue', 6)}",
        width="100%",
    )


def _column_edit_badge(column: str) -> rx.Component:
    """Create a badge showing edit count for a specific column.

    Args:
        column: Column name (CT, BT, DO, or DD)

    Returns:
        rx.Component: Badge with edit count
    """
    # Map column to its corresponding edit count computed variable
    count_map = {
        "CT": BidLineState.ct_edit_count,
        "BT": BidLineState.bt_edit_count,
        "DO": BidLineState.do_edit_count,
        "DD": BidLineState.dd_edit_count,
    }

    count_var = count_map.get(column, 0)

    return rx.cond(
        count_var > 0,
        rx.badge(
            column + ": " + count_var.to(str),
            color_scheme="blue",
            variant="soft",
            size="2",
        ),
    )


def _change_row(edit: dict, idx: int) -> rx.Component:
    """Render a single change history row.

    Args:
        edit: Edit dictionary with line, column, old_value, new_value
        idx: Index of this edit in the edited_cells list

    Returns:
        rx.Component: Table row showing the edit
    """
    return rx.table.row(
        # Line number
        rx.table.cell(
            rx.badge(
                edit["line"].to(str),
                color_scheme="gray",
                variant="soft",
            ),
            style={"text-align": "center", "padding": "0.75rem"},
        ),
        # Column name
        rx.table.cell(
            rx.badge(
                edit["column"].to(str),
                color_scheme="blue",
            ),
            style={"text-align": "center", "padding": "0.75rem"},
        ),
        # Old value
        rx.table.cell(
            rx.text(
                edit["old_value"].to(str),
                size="2",
                color=rx.color("red", 10),
                style={"text-decoration": "line-through"},
            ),
            style={"text-align": "center", "padding": "0.75rem"},
        ),
        # Arrow
        rx.table.cell(
            rx.icon("arrow-right", size=16, color=rx.color("gray", 9)),
            style={"text-align": "center", "padding": "0.75rem"},
        ),
        # New value
        rx.table.cell(
            rx.text(
                edit["new_value"].to(str),
                size="2",
                weight="bold",
                color=rx.color("green", 10),
            ),
            style={"text-align": "center", "padding": "0.75rem"},
        ),
        # Undo button
        rx.table.cell(
            rx.button(
                rx.icon("undo", size=16),
                on_click=lambda: BidLineState.undo_edit(idx),
                size="1",
                variant="soft",
                color_scheme="orange",
            ),
            style={"text-align": "center", "padding": "0.5rem"},
        ),
        style={
            "transition": "background-color 0.2s",
            ":hover": {
                "background-color": rx.color("gray", 2),
            },
        },
    )
