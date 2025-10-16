# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a multi-page Streamlit application for analyzing airline bid packet data for pilots. The app consists of two main analysis tools:

1. **EDW Pairing Analyzer** (`app.py`) - Analyzes pairings PDF to identify Early/Day/Window (EDW) trips
2. **Bid Line Analyzer** (`pages/pages:2_Bid_Line_Analyzer.py`) - Parses bid packet lines for scheduling metrics

## Running the Application

Start the Streamlit app:
```bash
streamlit run app.py
```

The app will be available at `http://localhost:8501`. The multi-page structure automatically includes pages in the `pages/` directory.

## Development Setup

1. Activate virtual environment (if not already active):
```bash
source .venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Architecture

### Core Analysis Module (`edw_reporter.py`)

This module contains the main business logic for EDW trip analysis:

- **PDF Parsing**: Uses `PyPDF2.PdfReader` to extract text from bid packet PDFs
- **Trip Identification**: Splits extracted text into individual trips by looking for "Trip Id" markers
- **EDW Detection Logic**: A trip is flagged as EDW if any duty day touches 02:30-05:00 local time (inclusive)
  - Local time is extracted from pattern `(HH)MM:SS` where HH is local hour
  - The function `is_edw_trip()` at edw_reporter.py:69 implements this core logic
- **Metrics Calculation**: Computes three weighted EDW percentages:
  1. Trip-weighted: Simple ratio of EDW trips to total trips
  2. TAFB-weighted: EDW trip hours / total TAFB hours
  3. Duty-day-weighted: EDW duty days / total duty days
- **Output Generation**: Creates both Excel workbooks and multi-page PDF reports using `reportlab`

Key functions:
- `parse_pairings()` - Extracts trips from PDF text
- `is_edw_trip()` - Core EDW detection algorithm
- `run_edw_report()` - Main orchestration function that generates all outputs

### Streamlit Pages

**Main Page (`app.py`)**:
- Uses `st.file_uploader()` for PDF upload
- Calls `run_edw_report()` from `edw_reporter` module
- Provides download buttons for Excel and PDF reports
- Accepts optional labels: domicile (default: "ONT"), aircraft (default: "757"), bid period (default: "2507")

**Bid Line Analyzer Page (`pages/pages:2_Bid_Line_Analyzer.py`)**:
- Uses `pdfplumber` library (different from PyPDF2 used in main analyzer)
- Parses line data with regex pattern: `ONT\s+(\d+)\s+CT:\s(\d+):(\d+)\s+BT:\s(\d+):(\d+)\s+DO:\s(\d+)\s+DD:\s(\d+)`
- Identifies "buy-up" lines as those with CT (Credit Time) < 75 hours
- Generates summary statistics (min, max, average, median, std dev) for CT, BT, DO metrics

### Text Handling

The `clean_text()` function in edw_reporter.py:27 normalizes Unicode and sanitizes special characters:
- Converts to NFKC normalization
- Replaces non-breaking spaces
- Converts bullet characters to hyphens

This is critical for reliable PDF text extraction and ReportLab PDF generation.

## PDF Libraries

**Two different PDF libraries are used**:
- `PyPDF2`: For EDW pairing analysis (app.py → edw_reporter.py)
- `pdfplumber`: For bid line analysis (pages/pages:2_Bid_Line_Analyzer.py)

Keep this distinction when making changes - don't assume they're interchangeable.

## File Naming Convention

Generated files follow the pattern:
```
{domicile}_{aircraft}_Bid{bid_period}_EDW_Report_Data.xlsx
{domicile}_{aircraft}_Bid{bid_period}_EDW_Report.pdf
```

Example: `ONT_757_Bid2507_EDW_Report_Data.xlsx`

## Testing Changes

Since this is a Streamlit app without formal tests:

1. Run the app and test with sample PDFs
2. Verify EDW detection logic by checking trips that touch 02:30-05:00 local time
3. Confirm all chart generation works (matplotlib figures must be saved to BytesIO before conversion)
4. Validate Excel output structure (check all sheets are present and properly formatted)
5. Test both pages independently

## Common Issues

- **Page filename**: Note the unusual filename `pages:2_Bid_Line_Analyzer.py` - this is intentional for Streamlit page ordering
- **Chart memory management**: Charts are saved to BytesIO, converted to PIL Image, then saved to disk before adding to PDF
- **Unicode handling**: Always use `clean_text()` when preparing text for ReportLab or Excel to avoid encoding errors
