# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **unified Streamlit application** for analyzing airline bid packet data for pilots. The app uses a 3-tab interface combining two analysis tools and historical trend visualization:

1. **EDW Pairing Analyzer** (Tab 1) - Analyzes pairings PDF to identify Early/Day/Window (EDW) trips
2. **Bid Line Analyzer** (Tab 2) - Parses bid line PDFs for scheduling metrics (CT, BT, DO, DD)
3. **Historical Trends** (Tab 3) - Database-powered trend analysis (planned, using Supabase)

## Python Requirements

**Required Python Version:** **3.11+** (Project uses Python 3.11.1)

**Important:** This project requires Python 3.11 or higher. Python 3.10 may work but is not tested.

The Python 3.11 requirement applies to:
- Streamlit application (main branch)
- Reflex migration development (reflex-migration branch)

**Why Python 3.11?**
- Reflex framework requires Python 3.10+ (discovered during migration)
- Python 3.9 reaches EOL October 2025
- Modern typing support and performance improvements
- Full compatibility with all project dependencies

**Checking Your Python Version:**
```bash
python --version  # Should show Python 3.11.x
python3.11 --version  # Check if Python 3.11 is available
```

**Installing Python 3.11:**
- macOS: `brew install python@3.11`
- Ubuntu: `sudo apt install python3.11`
- Windows: Download from python.org

## Running the Application

Start the Streamlit app:
```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies (first time only)
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

The app will be available at `http://localhost:8501` (or `8502` if port in use).

## Development Setup

**Prerequisites:**
- Python 3.11+ installed (check with `python --version`)
- Git

**Setup Steps:**

1. **Create virtual environment** (first time only):
```bash
# Ensure you're using Python 3.11
python3.11 -m venv .venv
```

2. **Activate virtual environment:**
```bash
source .venv/bin/activate
```

3. **Verify Python version:**
```bash
python --version  # Should show Python 3.11.x
```

4. **Install dependencies:**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

5. **(Optional) For database integration:**
   - Create Supabase project at https://supabase.com
   - Copy `.env.example` to `.env`
   - Fill in `SUPABASE_URL` and `SUPABASE_ANON_KEY`
   - See `docs/SUPABASE_SETUP.md` for detailed setup instructions

## Architecture

### Application Structure (`app.py`)

The main application file contains a **3-tab interface** (~650+ lines):

**Tab 1: EDW Pairing Analyzer** (lines 1-350+)
- PDF upload with automatic header extraction
- Trip analysis with weighted EDW metrics
- Duty day distribution charts
- Advanced filtering (duty day criteria, trip length, legs)
- Trip details viewer with HTML table (50% width, responsive)
- Excel and PDF report downloads
- Uses `edw_reporter.py` for core logic

**Tab 2: Bid Line Analyzer** (lines 351-1750+)
- PDF upload with progress bar
- **Manual data editing** (Overview tab) - Interactive `st.data_editor()` for correcting parsed values
- Filter sidebar (CT, BT, DO, DD ranges)
- Three sub-tabs: Overview, Summary, Visuals
- Pay period comparison (PP1 vs PP2)
- Reserve line statistics (Captain/FO slots)
- CSV and PDF export (includes manual edits)
- Uses `bid_parser.py` and `report_builder.py`

**Tab 3: Historical Trends** (lines 657-680)
- Placeholder for Supabase integration
- Future: Trend charts, multi-bid-period comparisons
- Requires `database.py` module (not yet implemented)

**Important:** All widgets have unique keys to prevent session state conflicts:
- Tab 1: `key="edw_pdf_uploader"`, etc.
- Tab 2: `key="bid_line_pdf_uploader"`, etc.

### Core Analysis Modules

#### EDW Reporter (`edw_reporter.py`)

This module contains the main business logic for EDW trip analysis:

- **PDF Parsing**: Uses `PyPDF2.PdfReader` to extract text from bid packet PDFs
- **Header Extraction**: Automatic extraction of bid period, domicile, fleet type from PDF header
  - Function: `extract_pdf_header_info()` (lines 120-192)
  - Checks first page, then second page if needed (handles cover pages)
- **Trip Identification**: Splits extracted text into individual trips by looking for "Trip Id" markers
- **EDW Detection Logic**: A trip is flagged as EDW if any duty day touches 02:30-05:00 local time (inclusive)
  - Local time is extracted from pattern `(HH)MM:SS` where HH is local hour
  - The function `is_edw_trip()` implements this core logic
- **Metrics Calculation**: Computes three weighted EDW percentages:
  1. Trip-weighted: Simple ratio of EDW trips to total trips
  2. TAFB-weighted: EDW trip hours / total TAFB hours
  3. Duty-day-weighted: EDW duty days / total duty days
- **Output Generation**: Creates both Excel workbooks and multi-page PDF reports using `reportlab`

Key functions:
- `extract_pdf_header_info()` - Extracts bid period, domicile, fleet type from PDF header
- `parse_pairings()` - Extracts trips from PDF text
- `is_edw_trip()` - Core EDW detection algorithm
- `run_edw_report()` - Main orchestration function that generates all outputs
- `parse_trip_for_table()` - Parses individual trips for HTML table display
- `parse_duty_day_details()` - Extracts duty day metrics (legs, duration, EDW status, credit time)

#### Bid Line Parser (`bid_parser.py`)

This module handles parsing of bid line PDFs:

- **PDF Parsing**: Uses `pdfplumber` library to extract text and tables
- **Header Extraction**: Automatic extraction of bid period, domicile, fleet type, date range
  - Function: `extract_bid_line_header_info()` (lines 52-147)
  - Checks first page, then second page if needed (handles cover pages)
- **Line Detection**: Parses bid line data including CT, BT, DO, DD metrics
- **Pay Period Analysis**: Separates data by pay period (PP1 vs PP2)
- **VTO/VTOR/VOR Split Line Handling**: Detects and includes split lines (one period regular, one VTO)
  - Function: `_detect_split_vto_line()` (lines 280-334)
  - Split lines are included in parsed data with VTOType and VTOPeriod fields
  - Regular pay period data is included in averages and distributions
  - VTO pay period is automatically excluded from calculations
  - Non-split VTO lines (both periods VTO) are skipped entirely
- **Reserve Line Detection**: Identifies reserve lines and counts Captain/FO slots
- **Diagnostics**: Returns parsing diagnostics for debugging

Key functions:
- `extract_bid_line_header_info()` - Extracts header metadata with cover page fallback
- `parse_bid_lines()` - Main entry point for bid line parsing
- `_detect_reserve_line()` - Detects and parses reserve line slots
- `_detect_split_vto_line()` - Detects split VTO/VTOR/VOR lines
- `_parse_line_blocks()` - Parses individual line blocks from pages
- `_aggregate_pay_periods()` - Aggregates data by pay period, excludes VTO periods from calculations

#### Report Builder (`report_builder.py`)

This module generates PDF reports for bid line analysis:

- **PDF Generation**: Uses `fpdf2` library to create formatted PDFs
- **Charts**: Uses `matplotlib` to generate distribution charts, pie charts
- **Tables**: Creates formatted tables with summary statistics
- **Analysis**: Buy-up vs non buy-up analysis (threshold: 75 CT hours)

Key functions:
- `build_analysis_pdf()` - Main report generation function
- `_add_summary_table()` - Summary statistics table
- `_add_pay_period_averages()` - Per-pay-period averages table
- `_add_reserve_statistics()` - Reserve line statistics table
- `_add_distribution_charts()` - Distribution visualizations
- `_add_buy_up_chart()` - Buy-up analysis pie chart

### Text Handling

The `clean_text()` function in edw_reporter.py normalizes Unicode and sanitizes special characters:
- Converts to NFKC normalization
- Replaces non-breaking spaces
- Converts bullet characters to hyphens

This is critical for reliable PDF text extraction and ReportLab PDF generation.

## PDF Libraries

**Two different PDF libraries are used**:
- `PyPDF2`: For EDW pairing analysis (Tab 1 → edw_reporter.py)
- `pdfplumber`: For bid line analysis (Tab 2 → bid_parser.py)

Keep this distinction when making changes - don't assume they're interchangeable.

## File Naming Convention

### EDW Reports
Generated files follow the pattern:
```
{domicile}_{aircraft}_Bid{bid_period}_EDW_Report_Data.xlsx
{domicile}_{aircraft}_Bid{bid_period}_EDW_Report.pdf
```

Example: `ONT_757_Bid2507_EDW_Report_Data.xlsx`

### Bid Line Reports
```
Bid_Lines_Analysis_Report.pdf
bid_lines_filtered.csv
```

## Database Integration (Planned)

See `docs/IMPLEMENTATION_PLAN.md` and `docs/SUPABASE_SETUP.md` for comprehensive database integration plans.

**Database Schema** (6 tables):
1. `bid_periods` - Master table for bid period metadata
2. `trips` - Individual trip records (EDW analysis)
3. `edw_summary_stats` - Aggregated EDW statistics
4. `bid_lines` - Individual bid line records
5. `bid_line_summary_stats` - Aggregated bid line statistics
6. `pay_period_data` - Pay period breakdowns

**Pending Implementation Tasks:**
1. Create `database.py` module with Supabase client
2. Add "Save to Database" buttons to both analyzers
3. Build Historical Trends tab with visualizations
4. Replace matplotlib with Altair for interactive charts
5. Add theme configuration and custom CSS

## Testing Changes

Since this is a Streamlit app without formal tests:

1. **Tab 1 (EDW Pairing Analyzer):**
   - Upload a pairing PDF and verify automatic header extraction
   - Run analysis and check all weighted EDW metrics
   - Test duty day criteria filtering (match modes: Any/All)
   - View trip details and verify table width constraint (50% on desktop)
   - Download Excel and PDF reports

2. **Tab 2 (Bid Line Analyzer):**
   - Upload a bid line PDF and verify parsing completes
   - Apply filters (CT, BT, DO, DD ranges)
   - Check all three sub-tabs (Overview, Summary, Visuals)
   - Verify pay period analysis displays correctly
   - Test CSV and PDF export

3. **Tab 3 (Historical Trends):**
   - Verify placeholder content displays
   - (After database integration) Test trend visualizations

4. **Cross-tab Testing:**
   - Verify session state isolation (no bleeding between tabs)
   - Test switching between tabs multiple times
   - Upload different PDFs in different tabs

## Common Issues

- **Python Version**: Project requires Python 3.11+. If you see typing errors or import issues, check `python --version`. Python 3.9 is NOT supported (EOL October 2025). See "Python Requirements" section above for details.
- **Virtual Environment**: Always activate `.venv` before running app or installing dependencies. Recreate with Python 3.11 if needed: `rm -rf .venv && python3.11 -m venv .venv`
- **Port Conflicts**: If port 8501 is in use, Streamlit will auto-increment (8502, 8503, etc.)
- **Wrong PDF Upload**: Both analyzers now provide helpful error messages if the wrong PDF type is uploaded:
  - **Tab 1 (EDW Pairing Analyzer)**: Detects bid line PDFs and suggests uploading to Tab 2
  - **Tab 2 (Bid Line Analyzer)**: Detects pairing PDFs and suggests uploading to Tab 1
- **Chart memory management**: Charts are saved to BytesIO, converted to PIL Image before PDF embedding
- **Unicode handling**: Always use `clean_text()` when preparing text for ReportLab or Excel
- **Session state conflicts**: Ensure all widget keys are unique across tabs
- **Table width**: Pairing detail table uses responsive CSS (50%/80%/100% based on screen width)

## Manual Data Editing Feature (Session 16)

The Bid Line Analyzer now supports inline data editing to fix missing or incorrect parsed values.

### Key Components:

**Data Editor (`_render_overview_tab()` in `app.py` lines 1143-1380)**
- Uses `st.data_editor()` for interactive editing
- Editable columns: CT, BT, DO, DD (Line number is read-only)
- Always shows ALL parsed lines (filters don't affect editor)
- Column validation: CT/BT (0.0-200.0), DO/DD (0-31)
- Compact column widths for better UX

**Session State Management (lines 875-884)**
- `bidline_original_df`: Original parsed data (never modified)
- `bidline_edited_df`: User-corrected data (contains edits)
- Data flow: All tabs, charts, and exports use edited data automatically

**Change Tracking (lines 1223-1327)**
- Compares edited data against original
- Visual indicators: ✏️ "Data has been manually edited (N changes)"
- "View edited cells" expander shows Line, Column, Original, Current
- Handles NaN/None values properly

**Validation Warnings (lines 1266-1286)**
- CT or BT > 150 hours
- BT > CT (block time exceeds credit time)
- DO or DD > 20 days
- DO + DD > 31 (exceeds month length)

**Reset Functionality (lines 1304-1322)**
- "Reset to Original Data" button
- Deletes edited data and restores parsed values
- Simple one-click operation

### Important Implementation Details:

1. **Data editor always uses `df` (all lines), never `filtered_df`** (line 1152)
2. **When saving edits, use `df.copy()` as base, not parsed data** (line 1290)
3. **All calculations automatically use edited data** - no manual updates needed
4. **CSV/PDF exports include edits** - filtered_df already contains edited values

### Testing:
- Upload PDF, parse, edit a value in Overview tab
- Switch to Summary/Visuals tabs → should see updated calculations
- Download CSV/PDF → should include edits
- Click Reset → should restore original parsed data

## Recent Changes

**Session 16 (October 26, 2025) - Manual Data Editing:**
- Implemented interactive data editor with `st.data_editor()`
- Added session state management for original vs. edited data
- Built change tracking and validation system
- Fixed data loss bugs when editing with filters
- Ensured all tabs and exports use edited data automatically

**Session 11 (October 20, 2025) - Multi-App Merger:**

- **Merged Applications**: Combined separate EDW and Bid Line analyzers into unified 3-tab interface
- **New Files**: `bid_parser.py`, `report_builder.py`, `.env.example`
- **Documentation**: Created `docs/IMPLEMENTATION_PLAN.md` and `docs/SUPABASE_SETUP.md`
- **Restored Features**: Detailed pairing viewer, duty day criteria analyzer
- **Fixed**: Pairing detail table width constraint with responsive CSS
- **Dependencies**: Added numpy, pdfplumber, altair, fpdf2, supabase, python-dotenv, plotly

See `handoff/sessions/session-16.md` for the latest session notes, or `handoff/sessions/session-11.md` for the multi-app merger details.

## Documentation

- **Main Handoff**: `HANDOFF.md` - Project overview and session history
- **Session Details**: `handoff/sessions/session-XX.md` - Detailed session documentation
- **Implementation Plan**: `docs/IMPLEMENTATION_PLAN.md` - 6-phase Supabase integration roadmap
- **Database Setup**: `docs/SUPABASE_SETUP.md` - Supabase project creation and SQL migrations
- **Environment Template**: `.env.example` - Supabase credentials template

## Next Steps

1. User creates Supabase project and configures `.env`
2. Implement `database.py` with Supabase integration
3. Add save functionality to both analyzer tabs
4. Build Historical Trends tab with visualizations
5. Add theme customization and custom CSS
6. Replace matplotlib with Altair for consistent interactive charts
