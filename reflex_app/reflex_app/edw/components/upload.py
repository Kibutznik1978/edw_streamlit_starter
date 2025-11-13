"""PDF Upload Component for EDW Analyzer.

This component provides a drag-and-drop file upload interface with:
- Upload area with visual feedback
- Progress bar during processing
- Error/success messages
- Integration with EDWState.handle_upload()
"""

import reflex as rx
from reflex_app.theme import Colors, Spacing, BorderRadius, Shadows, Typography


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

    return rx.card(
        rx.vstack(
            # Upload instructions
            rx.heading(
                "Upload Pairing PDF",
                size="8",
                color=Colors.navy_800,
                font_weight=Typography.weight_bold,
            ),
            rx.text(
                "Upload your bid period pairing packet to analyze EDW trips",
                color=Colors.gray_600,
                size="4",
                font_weight=Typography.weight_normal,
            ),

            # Upload area
            rx.upload(
            rx.vstack(
                rx.icon("upload", size=48, color=Colors.sky_500),
                rx.text(
                    "Drag and drop PDF here",
                    font_weight=Typography.weight_bold,
                    size="5",
                    color=Colors.gray_800,
                ),
                rx.text(
                    "or click to browse",
                    size="3",
                    color=Colors.gray_600,
                ),
                rx.text(
                    "Accepts .pdf files only",
                    size="2",
                    color=Colors.gray_500,
                    font_style="italic",
                ),
                spacing="3",
                align="center",
            ),
            id="edw_upload",
            border="2px dashed",
            border_color=rx.cond(
                EDWState.upload_error,
                Colors.error,
                Colors.gray_300,
            ),
            padding=Spacing.xl,
            border_radius=BorderRadius.lg,
            background=rx.cond(
                EDWState.is_processing,
                Colors.gray_100,
                Colors.gray_50,
            ),
            box_shadow=Shadows.base,
            width="100%",
            max_width="600px",
            cursor="pointer",
            transition="all 200ms ease",
            _hover={
                "border_color": Colors.navy_500,
                "background": Colors.navy_50,
                "box_shadow": Shadows.glow_blue,
                "transform": "scale(1.01)",
            },
        ),

        # Selected files indicator
        rx.cond(
            rx.selected_files("edw_upload").length() > 0,
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.icon("file", size=20, color=Colors.sky_500),
                        rx.text(
                            "File selected:",
                            font_weight=Typography.weight_bold,
                            size="3",
                            color=Colors.navy_800,
                        ),
                        spacing="2",
                    ),
                    rx.foreach(
                        rx.selected_files("edw_upload"),
                        lambda file: rx.text(
                            file,
                            size="2",
                            color=Colors.gray_700,
                            font_family=Typography.font_mono,
                        ),
                    ),
                    spacing="2",
                ),
                background=Colors.info_light,
                padding=Spacing.lg,
                border_radius=BorderRadius.md,
                border=f"1px solid {Colors.info}",
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
                        rx.spinner(size="3", color=Colors.sky_500),
                        rx.text(
                            "Processing your PDF...",
                            font_weight=Typography.weight_bold,
                            size="4",
                            color=Colors.navy_800,
                        ),
                        spacing="3",
                    ),
                    rx.progress(
                        value=EDWState.processing_progress,
                        max=100,
                        width="100%",
                        height="10px",
                        color_scheme="blue",
                    ),
                    rx.hstack(
                        rx.text(
                            EDWState.processing_message,
                            size="2",
                            color=Colors.gray_600,
                        ),
                        rx.text(
                            EDWState.processing_progress.to(str) + "%",
                            size="2",
                            font_weight=Typography.weight_bold,
                            color=Colors.sky_500,
                        ),
                        spacing="2",
                        justify="between",
                        width="100%",
                    ),
                    spacing="3",
                    width="100%",
                    align="center",
                ),
                background=Colors.info_light,
                padding=Spacing.lg,
                border_radius=BorderRadius.md,
                border=f"1px solid {Colors.info}",
                box_shadow=Shadows.sm,
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
                        rx.icon("circle-check", size=24, color=Colors.success),
                        rx.text(
                            "File uploaded successfully",
                            font_weight=Typography.weight_bold,
                            size="4",
                            color=Colors.success_dark,
                        ),
                        spacing="2",
                    ),
                    rx.text(
                        "Filename: " + EDWState.uploaded_file_name,
                        size="2",
                        color=Colors.gray_700,
                        font_family=Typography.font_mono,
                    ),
                    spacing="2",
                ),
                background=Colors.success_light,
                padding=Spacing.lg,
                border_radius=BorderRadius.md,
                border=f"1px solid {Colors.success}",
                box_shadow=Shadows.sm,
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
                        rx.icon("circle-alert", size=24, color=Colors.error),
                        rx.text(
                            "Upload Error",
                            font_weight=Typography.weight_bold,
                            size="4",
                            color=Colors.error_dark,
                        ),
                        spacing="2",
                    ),
                    rx.text(
                        EDWState.upload_error,
                        size="2",
                        color=Colors.gray_700,
                        white_space="pre-wrap",
                    ),
                    spacing="2",
                ),
                background=Colors.error_light,
                padding=Spacing.lg,
                border_radius=BorderRadius.md,
                border=f"1px solid {Colors.error}",
                box_shadow=Shadows.sm,
                width="100%",
                max_width="600px",
            ),
        ),

            spacing="5",
            width="100%",
            align="center",
        ),
        size="4",
        width="100%",
    )
