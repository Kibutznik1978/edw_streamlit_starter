"""EDW Analyzer UI Components.

This module contains reusable UI components for the EDW Pairing Analyzer:
- upload: PDF file upload with progress tracking
- header: Extracted header information display
- summary: Results summary statistics
- charts: Duty day distribution visualizations
- filters: Advanced filtering controls
- details: Trip details viewer
- table: Trip records data table
"""

from .upload import upload_component

__all__ = ["upload_component"]
