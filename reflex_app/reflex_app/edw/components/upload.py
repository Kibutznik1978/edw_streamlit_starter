"""PDF Upload Component for EDW Analyzer.

This component provides a drag-and-drop file upload interface with:
- Upload area with visual feedback
- Progress bar during processing
- Error/success messages
- Integration with EDWState.handle_upload()
"""

import reflex as rx


def upload_component() -> rx.Component:
    """PDF upload component with progress tracking.

    Features:
    - Drag-and-drop or click to select
    - Only accepts PDF files
    - Shows upload progress
    - Displays success/error messages
    - Resets for new uploads
    """
    from ..edw_state import EDWState

    return rx.vstack(
        # Upload instructions
        rx.heading("Upload Pairing PDF", size="7"),
        rx.text(
            "Upload your bid period pairing packet to analyze EDW trips",
            color="gray",
            size="3",
        ),

        # Upload area
        rx.upload(
            rx.vstack(
                rx.icon("upload", size=32, color="blue"),
                rx.text(
                    "Drag and drop PDF here",
                    font_weight="bold",
                    size="4",
                ),
                rx.text(
                    "or click to browse",
                    size="2",
                    color="gray",
                ),
                rx.text(
                    "Accepts .pdf files only",
                    size="1",
                    color="gray",
                    font_style="italic",
                ),
                spacing="2",
                align="center",
            ),
            id="edw_upload",
            border="2px dashed",
            border_color=rx.cond(
                EDWState.upload_error,
                "red",
                "gray",
            ),
            padding="8",
            border_radius="8px",
            background=rx.cond(
                EDWState.is_processing,
                "var(--gray-2)",
                "var(--gray-1)",
            ),
            width="100%",
            max_width="600px",
            cursor="pointer",
            _hover={
                "border_color": "blue",
                "background": "var(--blue-2)",
            },
        ),

        # Selected files indicator
        rx.cond(
            rx.selected_files("edw_upload").length() > 0,
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.icon("file", size=20, color="blue"),
                        rx.text(
                            "File selected:",
                            font_weight="bold",
                            size="3",
                        ),
                        spacing="2",
                    ),
                    rx.foreach(
                        rx.selected_files("edw_upload"),
                        lambda file: rx.text(file, size="2", color="gray"),
                    ),
                    spacing="1",
                ),
                background="var(--blue-3)",
                padding="3",
                border_radius="8px",
                border="1px solid var(--blue-6)",
                width="100%",
                max_width="600px",
            ),
        ),

        # Upload button
        rx.button(
            rx.cond(
                EDWState.is_processing,
                rx.hstack(
                    rx.spinner(size="3"),
                    rx.text("Processing..."),
                    spacing="2",
                ),
                rx.hstack(
                    rx.icon("file-up", size=20),
                    rx.text("Upload and Analyze"),
                    spacing="2",
                ),
            ),
            on_click=EDWState.handle_upload(
                rx.upload_files(upload_id="edw_upload")
            ),
            size="3",
            disabled=EDWState.is_processing,
            width="100%",
            max_width="600px",
            cursor="pointer",
        ),

        # Progress bar
        rx.cond(
            EDWState.is_processing,
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.spinner(size="3", color="blue"),
                        rx.text(
                            "Processing your PDF...",
                            font_weight="bold",
                            size="4",
                        ),
                        spacing="3",
                    ),
                    rx.progress(
                        value=EDWState.processing_progress,
                        max=100,
                        width="100%",
                        height="8px",
                        color_scheme="blue",
                    ),
                    rx.hstack(
                        rx.text(
                            EDWState.processing_message,
                            size="2",
                            color="gray",
                        ),
                        rx.text(
                            EDWState.processing_progress.to(str) + "%",
                            size="2",
                            font_weight="bold",
                            color="blue",
                        ),
                        spacing="2",
                        justify="between",
                        width="100%",
                    ),
                    spacing="3",
                    width="100%",
                    align="center",
                ),
                background="var(--blue-2)",
                padding="4",
                border_radius="8px",
                border="1px solid var(--blue-6)",
                width="100%",
                max_width="600px",
            ),
        ),

        # Success message
        rx.cond(
            EDWState.uploaded_file_name != "",
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.icon("circle-check", size=24, color="green"),
                        rx.text(
                            "File uploaded successfully",
                            font_weight="bold",
                            size="4",
                        ),
                        spacing="2",
                    ),
                    rx.text(
                        "Filename: " + EDWState.uploaded_file_name,
                        size="2",
                    ),
                    spacing="2",
                ),
                background="var(--green-3)",
                padding="4",
                border_radius="8px",
                border=f"1px solid var(--green-6)",
                width="100%",
                max_width="600px",
            ),
        ),

        # Error message
        rx.cond(
            EDWState.upload_error != "",
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.icon("circle-alert", size=24, color="red"),
                        rx.text(
                            "Upload Error",
                            font_weight="bold",
                            size="4",
                            color="red",
                        ),
                        spacing="2",
                    ),
                    rx.text(
                        EDWState.upload_error,
                        size="2",
                        white_space="pre-wrap",
                    ),
                    spacing="2",
                ),
                background="var(--red-3)",
                padding="4",
                border_radius="8px",
                border=f"1px solid var(--red-6)",
                width="100%",
                max_width="600px",
            ),
        ),

        spacing="4",
        width="100%",
        align="center",
    )
