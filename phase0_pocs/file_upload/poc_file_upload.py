"""POC: PDF File Upload in Reflex.

This POC tests PDF file upload and processing with PyPDF2/pdfplumber.

Critical Requirements:
1. Upload PDF files (5-10 MB)
2. Display upload progress
3. Extract text with PyPDF2 (for EDW analysis)
4. Extract text with pdfplumber (for bid line analysis)
5. Handle errors gracefully

Success Criteria:
✅ File upload widget works
✅ PDF text extraction successful
✅ Progress indicator during processing
✅ Error handling for invalid files
✅ Memory efficient for large files

Risk: 🟡 MEDIUM - Reflex has file upload, need to test with PDF libraries
"""

import reflex as rx
from typing import List
import io


class FileUploadState(rx.State):
    """State for file upload POC."""

    # Upload state
    upload_progress: int = 0
    is_processing: bool = False
    uploaded_filename: str = ""
    file_size: str = ""

    # Extracted text
    pypdf2_text: str = ""
    pdfplumber_text: str = ""

    # Error handling
    error_message: str = ""

    async def handle_upload(self, files: List[rx.UploadFile]):
        """Handle PDF file upload."""
        self.error_message = ""
        self.is_processing = True
        self.upload_progress = 0

        try:
            for file in files:
                # Validate file type
                if not file.filename.endswith(".pdf"):
                    self.error_message = "Error: Only PDF files are supported"
                    self.is_processing = False
                    return

                self.uploaded_filename = file.filename
                upload_data = await file.read()
                self.file_size = f"{len(upload_data) / 1024 / 1024:.2f} MB"

                self.upload_progress = 50

                # Simulate PDF processing
                # In real implementation, would use PyPDF2 and pdfplumber here
                self.pypdf2_text = f"[PyPDF2 extracted text from {file.filename}]\n\nSimulated text extraction..."
                self.pdfplumber_text = f"[pdfplumber extracted text from {file.filename}]\n\nSimulated text extraction..."

                self.upload_progress = 100
                self.is_processing = False

        except Exception as e:
            self.error_message = f"Error processing file: {str(e)}"
            self.is_processing = False

    def reset_upload(self):
        """Reset upload state."""
        self.upload_progress = 0
        self.is_processing = False
        self.uploaded_filename = ""
        self.file_size = ""
        self.pypdf2_text = ""
        self.pdfplumber_text = ""
        self.error_message = ""


def index() -> rx.Component:
    """Main POC page."""
    return rx.container(
        rx.vstack(
            # Header
            rx.heading("POC: PDF File Upload", size="xl"),
            rx.text("Testing PDF upload with PyPDF2 and pdfplumber", color="gray"),
            rx.divider(),

            # Instructions
            rx.box(
                rx.vstack(
                    rx.heading("Test Instructions", size="md"),
                    rx.unordered_list(
                        rx.list_item("Upload a PDF file (pairing or bid line)"),
                        rx.list_item("Observe upload progress indicator"),
                        rx.list_item("Check extracted text from both libraries"),
                        rx.list_item("Try uploading non-PDF file (should error)"),
                        rx.list_item("Test with large PDF (5-10 MB)"),
                    ),
                ),
                background_color="lightblue",
                padding="1rem",
                border_radius="8px",
            ),

            # File upload
            rx.upload(
                rx.vstack(
                    rx.button("Select PDF File", background_color="navy", color="white"),
                    rx.text("Drag and drop or click to select", font_size="sm", color="gray"),
                ),
                id="upload1",
                border="2px dashed gray",
                padding="2rem",
                border_radius="8px",
            ),
            rx.button(
                "Upload",
                on_click=FileUploadState.handle_upload(rx.upload_files(upload_id="upload1")),
                background_color="green",
                color="white",
            ),

            # Progress indicator
            rx.cond(
                FileUploadState.is_processing,
                rx.vstack(
                    rx.text("Processing..."),
                    rx.progress(value=FileUploadState.upload_progress),
                    rx.text(f"{FileUploadState.upload_progress}%"),
                ),
            ),

            # Upload success
            rx.cond(
                FileUploadState.uploaded_filename,
                rx.box(
                    rx.vstack(
                        rx.text(f"✅ Uploaded: {FileUploadState.uploaded_filename}", font_weight="bold"),
                        rx.text(f"Size: {FileUploadState.file_size}"),
                    ),
                    background_color="lightgreen",
                    padding="1rem",
                    border_radius="4px",
                ),
            ),

            # Error message
            rx.cond(
                FileUploadState.error_message,
                rx.box(
                    rx.text(f"❌ {FileUploadState.error_message}", color="red"),
                    background_color="lightcoral",
                    padding="1rem",
                    border_radius="4px",
                ),
            ),

            # Extracted text
            rx.cond(
                FileUploadState.pypdf2_text,
                rx.vstack(
                    rx.heading("PyPDF2 Extraction", size="md"),
                    rx.box(
                        rx.text(FileUploadState.pypdf2_text, font_family="monospace", font_size="sm"),
                        max_height="200px",
                        overflow_y="auto",
                        background_color="lightgray",
                        padding="1rem",
                        border_radius="4px",
                    ),
                ),
            ),

            rx.cond(
                FileUploadState.pdfplumber_text,
                rx.vstack(
                    rx.heading("pdfplumber Extraction", size="md"),
                    rx.box(
                        rx.text(FileUploadState.pdfplumber_text, font_family="monospace", font_size="sm"),
                        max_height="200px",
                        overflow_y="auto",
                        background_color="lightgray",
                        padding="1rem",
                        border_radius="4px",
                    ),
                ),
            ),

            # Reset button
            rx.cond(
                FileUploadState.uploaded_filename,
                rx.button(
                    "Reset",
                    on_click=FileUploadState.reset_upload,
                    background_color="red",
                    color="white",
                ),
            ),

            # POC Results
            rx.divider(),
            rx.box(
                rx.vstack(
                    rx.heading("POC Results", size="md"),
                    rx.text("🔍 TO TEST:", font_weight="bold"),
                    rx.text("✅ Reflex upload widget functional"),
                    rx.text("⏳ Need to integrate PyPDF2 library"),
                    rx.text("⏳ Need to integrate pdfplumber library"),
                    rx.text("⏳ Test with actual PDF files from app"),
                    rx.text("⏳ Validate memory usage with 5-10 MB files"),
                    rx.text(""),
                    rx.text("Expected Outcome:", font_weight="bold"),
                    rx.text("✅ LOW RISK - File upload should work with existing PDF libraries", color="green"),
                ),
                background_color="lightgray",
                padding="1rem",
                border_radius="8px",
            ),

            spacing="1rem",
            width="100%",
        ),
        max_width="1200px",
        padding="2rem",
    )


# Create POC app
app = rx.App()
app.add_page(index, route="/", title="File Upload POC")
