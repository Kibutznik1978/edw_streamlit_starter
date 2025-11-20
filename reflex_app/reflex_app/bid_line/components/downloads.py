"""Bid Line Analyzer downloads component."""

import reflex as rx

from ..bid_line_state import BidLineState


def downloads_component() -> rx.Component:
    """Downloads component with Excel and PDF export buttons."""
    return rx.cond(
        BidLineState.has_results,
        rx.card(
            rx.vstack(
                # Section header
                rx.hstack(
                    rx.icon("download", size=24, color=rx.color("blue", 9)),
                    rx.heading("Download Reports", size="5", weight="bold"),
                    spacing="3",
                    align="center",
                ),
                # Description
                rx.box(
                    rx.text(
                        "Export your filtered bid line analysis as Excel or PDF. "
                        "Downloads reflect any edits you have made and honor the active filters.",
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
                    rx.button(
                        rx.icon("file-spreadsheet", size=20),
                        "Download Excel",
                        on_click=BidLineState.download_excel,
                        size="3",
                        variant="soft",
                        color="green",
                        cursor="pointer",
                        style={
                            "transition": "all 150ms ease",
                            "_hover": {"transform": "translateY(-2px)"},
                        },
                    ),
                    rx.button(
                        rx.icon("file-text", size=20),
                        "Download PDF",
                        on_click=BidLineState.download_pdf,
                        size="3",
                        variant="soft",
                        color="blue",
                        cursor="pointer",
                        style={
                            "transition": "all 150ms ease",
                            "_hover": {"transform": "translateY(-2px)"},
                        },
                    ),
                    direction="row",
                    spacing="4",
                    wrap="wrap",
                    width="100%",
                ),
                # Details about export contents
                rx.box(
                    rx.vstack(
                        rx.hstack(
                            rx.icon("info", size=16, color=rx.color("gray", 9)),
                            rx.text(
                                "Downloads include:",
                                size="2",
                                weight="bold",
                                color=rx.color("gray", 11),
                            ),
                            spacing="2",
                            align="center",
                        ),
                        rx.unordered_list(
                            rx.list_item(
                                "Bid Lines sheet with all filtered rows and crew slot details.",
                                size="2",
                                color=rx.color("gray", 10),
                            ),
                            rx.list_item(
                                "Summary sheet with CT/BT/DO/DD averages and reserve counts.",
                                size="2",
                                color=rx.color("gray", 10),
                            ),
                            rx.list_item(
                                "Pay period and reserve diagnostics (Excel) plus the same multi-page PDF "
                                "layout available in the Streamlit app.",
                                size="2",
                                color=rx.color("gray", 10),
                            ),
                            spacing="1",
                        ),
                        spacing="3",
                        width="100%",
                    ),
                    padding="3",
                    border_radius="6px",
                    background=rx.color("gray", 2),
                    width="100%",
                ),
                spacing="4",
                width="100%",
            ),
            size="4",
            width="100%",
        ),
    )
