"""EDW Analyzer Downloads Component.

This module provides download buttons for Excel and PDF reports.
"""

import reflex as rx
from ..edw_state import EDWState


def downloads_component() -> rx.Component:
    """Downloads component with Excel and PDF export buttons.

    Provides two download buttons:
    - Excel: Multi-sheet workbook with trip data and statistics
    - PDF: Professional multi-page report with charts and tables

    Only shown when analysis results are available.

    Returns:
        rx.Component: Downloads section with Excel and PDF buttons
    """
    return rx.cond(
        EDWState.has_results,
        rx.vstack(
            # Section header
            rx.hstack(
                rx.icon("download", size=24, color=rx.color("green", 9)),
                rx.heading(
                    "Download Reports",
                    size="5",
                    weight="bold",
                ),
                spacing="3",
                align="center",
            ),
            # Description
            rx.box(
                rx.text(
                    "Export your analysis results as Excel or PDF. Downloads include all filtered trip data, ",
                    "statistics, and visualizations based on your current filter settings.",
                    size="2",
                    color=rx.color("gray", 10),
                ),
                padding="3",
                border_radius="6px",
                background=rx.color("gray", 3),
                width="100%",
            ),
            # Download buttons
            rx.flex(
                # Excel download button
                rx.button(
                    rx.icon("file-spreadsheet", size=20),
                    "Download Excel",
                    on_click=EDWState.download_excel,
                    size="3",
                    variant="soft",
                    color="green",
                    cursor="pointer",
                ),
                # PDF download button
                rx.button(
                    rx.icon("file-text", size=20),
                    "Download PDF",
                    on_click=EDWState.download_pdf,
                    size="3",
                    variant="soft",
                    color="blue",
                    cursor="pointer",
                ),
                # Database save button
                rx.button(
                    rx.cond(
                        EDWState.save_in_progress,
                        rx.spinner(size="3"),
                        rx.icon("database", size=20),
                    ),
                    rx.cond(
                        EDWState.save_in_progress,
                        "Saving...",
                        "Save to Database"
                    ),
                    on_click=EDWState.save_to_database,
                    size="3",
                    variant="soft",
                    color="violet",
                    cursor="pointer",
                    disabled=EDWState.save_in_progress,
                ),
                direction="row",
                spacing="4",
                wrap="wrap",
                width="100%",
            ),
            # Save status feedback
            rx.cond(
                EDWState.save_status != "",
                rx.box(
                    rx.cond(
                        EDWState.save_status.contains("Error") | EDWState.save_status.contains("Warning"),
                        # Error/Warning message
                        rx.callout.root(
                            rx.callout.icon(rx.icon("alert-circle")),
                            rx.callout.text(EDWState.save_status),
                            color="red",
                            size="2",
                        ),
                        # Success or progress message
                        rx.callout.root(
                            rx.callout.icon(
                                rx.cond(
                                    EDWState.save_status.contains("✅"),
                                    rx.icon("check-circle"),
                                    rx.icon("info"),
                                )
                            ),
                            rx.callout.text(EDWState.save_status),
                            color=rx.cond(
                                EDWState.save_status.contains("✅"),
                                "green",
                                "blue",
                            ),
                            size="2",
                        ),
                    ),
                    width="100%",
                ),
                rx.fragment(),
            ),
            # Export details
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.icon("info", size=16, color=rx.color("gray", 9)),
                        rx.text(
                            "Excel Export Includes:",
                            size="2",
                            weight="bold",
                            color=rx.color("gray", 11),
                        ),
                        spacing="2",
                        align="center",
                    ),
                    rx.unordered_list(
                        rx.list_item("Trip Records (filtered data)"),
                        rx.list_item("Duty Distribution"),
                        rx.list_item("Trip Summary"),
                        rx.list_item("Weighted EDW Metrics"),
                        rx.list_item("Duty Day Statistics"),
                        size="2",
                        color=rx.color("gray", 10),
                        spacing="1",
                    ),
                    spacing="2",
                    align="start",
                    width="100%",
                ),
                padding="4",
                border_radius="8px",
                border=f"1px solid {rx.color('gray', 6)}",
                background=rx.color("gray", 2),
                width="100%",
            ),
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.icon("info", size=16, color=rx.color("gray", 9)),
                        rx.text(
                            "PDF Export Includes:",
                            size="2",
                            weight="bold",
                            color=rx.color("gray", 11),
                        ),
                        spacing="2",
                        align="center",
                    ),
                    rx.unordered_list(
                        rx.list_item("Executive summary dashboard"),
                        rx.list_item("Trip length distribution charts"),
                        rx.list_item("EDW percentages analysis"),
                        rx.list_item("Duty day statistics comparison"),
                        rx.list_item("Multi-day trip breakdown"),
                        size="2",
                        color=rx.color("gray", 10),
                        spacing="1",
                    ),
                    spacing="2",
                    align="start",
                    width="100%",
                ),
                padding="4",
                border_radius="8px",
                border=f"1px solid {rx.color('gray', 6)}",
                background=rx.color("gray", 2),
                width="100%",
            ),
            # Divider after section
            rx.divider(),
            spacing="4",
            width="100%",
        ),
        rx.fragment(),  # Show nothing if no results
    )
