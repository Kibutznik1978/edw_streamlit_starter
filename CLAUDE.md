# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **unified Streamlit application** for analyzing airline bid packet data for pilots. The app uses a 3-tab interface combining two analysis tools and historical trend visualization:

1. **EDW Pairing Analyzer** (Tab 1) - Analyzes pairings PDF to identify Early/Day/Window (EDW) trips
2. **Bid Line Analyzer** (Tab 2) - Parses bid line PDFs for scheduling metrics (CT, BT, DO, DD)
3. **Historical Trends** (Tab 3) - Database-powered trend analysis (planned, using Supabase)

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

1. Activate virtual environment (if not already active):
```bash
source .venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. (Optional) For database integration:
   - Create Supabase project at https://supabase.com
   - Copy `.env.example` to `.env`
   - Fill in `SUPABASE_URL` and `SUPABASE_ANON_KEY`
   - See `docs/SUPABASE_SETUP.md` for detailed setup instructions

## Architecture

### Application Structure (Modularized - Session 18)

The application has been refactored into a **modular structure** for better maintainability:

```
edw_streamlit_starter/
├── app.py                           (56 lines - main entry point)
├── ui_modules/                      (UI layer - modular pages)
│   ├── __init__.py                 (11 lines)
│   ├── edw_analyzer_page.py        (722 lines - Tab 1)
│   ├── bid_line_analyzer_page.py   (589 lines - Tab 2)
│   ├── historical_trends_page.py   (31 lines - Tab 3)
│   └── shared_components.py        (66 lines - common UI)
├── edw/                             (EDW analysis module - Session 19)
│   ├── __init__.py                 (47 lines - module exports)
│   ├── parser.py                   (814 lines - PDF parsing & text extraction)
│   ├── analyzer.py                 (73 lines - EDW detection logic)
│   ├── excel_export.py             (156 lines - Excel workbook generation)
│   └── reporter.py                 (383 lines - orchestration & PDF generation)
├── bid_parser.py                    (880 lines - bid line parsing)
├── export_pdf.py                    (1,122 lines - EDW PDF reports)
├── report_builder.py                (925 lines - bid line PDF reports)
└── requirements.txt
```

#### `app.py` (56 lines)
Clean entry point with just navigation:
- Imports UI modules from `ui_modules/`
- Sets up Streamlit page config
- Creates 3-tab navigation
- Delegates rendering to module functions

#### `ui_modules/edw_analyzer_page.py` (722 lines)
**Tab 1: EDW Pairing Analyzer**
- PDF upload with automatic header extraction
- Trip analysis with weighted EDW metrics
- Duty day distribution charts
- Advanced filtering (duty day criteria, trip length, legs)
- Trip details viewer with HTML table (50% width, responsive)
- Excel and PDF report downloads
- Uses `edw_reporter.py` for core logic

Functions:
- `render_edw_analyzer()` - Main entry point
- `display_edw_results()` - Results and visualizations

#### `ui_modules/bid_line_analyzer_page.py` (589 lines)
**Tab 2: Bid Line Analyzer**
- PDF upload with progress bar
- **Manual data editing** (Overview tab) - Interactive `st.data_editor()` for correcting parsed values
- Filter sidebar (CT, BT, DO, DD ranges) with smart "filters active" detection
- Three sub-tabs: Overview, Summary, Visuals
- Pay period comparison (PP1 vs PP2)
- Reserve line statistics (Captain/FO slots)
- CSV and PDF export (includes manual edits)
- Uses `bid_parser.py` and `pdf_generation.create_bid_line_pdf_report()`

Functions:
- `render_bid_line_analyzer()` - Main entry point
- `_display_bid_line_results()` - Display parsed data
- `_render_overview_tab()` - Data editor with change tracking
- `_render_summary_tab()` - Statistics
- `_render_visuals_tab()` - Charts
- `_detect_changes()` - Track manual edits
- `_validate_edits()` - Validate user input

#### `ui_modules/historical_trends_page.py` (31 lines)
**Tab 3: Historical Trends**
- Placeholder for Supabase integration
- Future: Trend charts, multi-bid-period comparisons
- Requires `database.py` module (not yet implemented)

#### `ui_modules/shared_components.py` (66 lines)
Common UI utilities:
- `display_header_info()` - PDF header display
- `show_parsing_warnings()` - Warning expander
- `show_error_details()` - Error details
- `progress_bar_callback()` - Progress updates

**Important:** All widgets have unique keys to prevent session state conflicts:
- Tab 1: `key="edw_pdf_uploader"`, etc.
- Tab 2: `key="bid_line_pdf_uploader"`, etc.

### Core Analysis Modules

#### EDW Analysis Module (`edw/` - Session 19)

**Refactored from monolithic `edw_reporter.py` (1,631 lines) into 4 focused modules:**

**`edw/parser.py` (814 lines)** - PDF parsing and text extraction:
- **PDF Reading**: Uses `PyPDF2.PdfReader` to extract text from bid packet PDFs
- **Header Extraction**: `extract_pdf_header_info()` - bid period, domicile, fleet type
  - Checks first page, then second page if needed (handles cover pages)
- **Trip Identification**: `parse_pairings()` - splits text into individual trips by "Trip Id" markers
- **Metric Extraction**: `parse_tafb()`, `parse_duty_days()`, `parse_max_duty_day_length()`, etc.
- **Detailed Parsing**: `parse_duty_day_details()`, `parse_trip_for_table()` - structured trip data
**`edw/analyzer.py` (73 lines)** - EDW detection logic:
- **Core EDW Detection**: `is_edw_trip()` - identifies Early/Day/Window trips
  - A trip is EDW if any duty day touches 02:30-05:00 local time (inclusive)
  - Local time extracted from pattern `(HH)MM:SS` where HH is local hour
- **Hot Standby Detection**: `is_hot_standby()` - identifies single-segment same-airport pairings

**`edw/excel_export.py` (156 lines)** - Excel workbook generation:
- **Excel Export**: `save_edw_excel()` - writes multi-sheet Excel workbooks
- **Statistics Builder**: `build_edw_dataframes()` - calculates all statistics from trip data
- **Weighted Metrics**: Computes three weighted EDW percentages:
  1. Trip-weighted: Simple ratio of EDW trips to total trips
  2. TAFB-weighted: EDW trip hours / total TAFB hours
  3. Duty-day-weighted: EDW duty days / total duty days

**`edw/reporter.py` (383 lines)** - Orchestration:
- **Main Orchestration**: `run_edw_report()` - coordinates entire analysis workflow
- **Excel Generation**: Creates multi-sheet Excel workbooks with all statistics
- **Workflow Coordination**: Manages parsing, analysis, and export generation

Key entry point:
- `run_edw_report()` from `edw/reporter.py` - main function orchestrating all analysis

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

#### PDF Generation Package (`pdf_generation/` - Session 20)

**Consolidated from `export_pdf.py` (1,122 lines) + `report_builder.py` (925 lines) into 5 focused modules:**

**`pdf_generation/base.py` (268 lines)** - Shared base components:
- `DEFAULT_BRANDING` - Aero Crew Data brand palette (Navy, Teal, Sky, Gray colors)
- `hex_to_reportlab_color()` - Hex to ReportLab color conversion
- `draw_header()` - Professional page header with logo and title
- `draw_footer()` - Page footer with timestamp and page numbers
- `KPIBadge` class - Custom flowable for KPI cards (with optional range display)
- `make_kpi_row()` - Creates row of KPI badges
- `make_styled_table()` - Generic professional table styling with zebra striping

**`pdf_generation/charts.py` (616 lines)** - All chart generation:
- **Generic Charts**: `save_bar_chart()`, `save_percentage_bar_chart()`, `save_pie_chart()`
- **EDW Charts**: `save_edw_pie_chart()`, `save_trip_length_bar_chart()`, `save_edw_percentages_comparison_chart()`, `save_weighted_method_pie_chart()`, `save_duty_day_grouped_bar_chart()`, `save_duty_day_radar_chart()`
- All charts use brand colors and professional styling

**`pdf_generation/edw_pdf.py` (425 lines)** - EDW pairing analysis PDF:
- `create_edw_pdf_report()` - Generates 3-page EDW analysis PDF
- EDW-specific table functions for weighted metrics, duty day stats, trip length tables
- Uses ReportLab for professional PDF generation

**`pdf_generation/bid_line_pdf.py` (652 lines)** - Bid line analysis PDF:
- `create_bid_line_pdf_report()` - Generates 3-page bid line analysis PDF
- Distribution helper functions for CT, BT, DO, DD
- Buy-up analysis (threshold: 75 CT hours)
- Smart reserve line filtering (regular reserve excluded, HSBY kept for CT/DO/DD)

**`pdf_generation/__init__.py` (95 lines)** - Module interface:
- Exports main functions: `create_edw_pdf_report()`, `create_bid_line_pdf_report()`, `ReportMetadata`
- Exports base components and chart functions for advanced usage
- Clean public API with `__all__` list

Key entry points:
- `create_edw_pdf_report()` from `pdf_generation` - EDW PDF generation
- `create_bid_line_pdf_report()` from `pdf_generation` - Bid line PDF generation

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

- **Virtual Environment**: Always activate `.venv` before running app or installing dependencies
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

**Session 20 (October 27, 2025) - Phase 3: PDF Generation Module Consolidation:**
- **Refactored:** Consolidated `export_pdf.py` (1,122 lines) + `report_builder.py` (925 lines) into modular `pdf_generation/` package
- **Created:** New directory `pdf_generation/` with 5 focused modules (2,056 total lines):
  - `base.py` (268 lines) - Shared base components (branding, colors, headers, footers, KPI badges)
  - `charts.py` (616 lines) - All chart generation (generic + EDW-specific)
  - `edw_pdf.py` (425 lines) - EDW pairing analysis PDF reports
  - `bid_line_pdf.py` (652 lines) - Bid line analysis PDF reports
  - `__init__.py` (95 lines) - Module exports and public API
- **Eliminated:** 4 duplicate functions that existed in both original files
- **Result:** Zero code duplication, better reusability, easier maintenance
- **Updated:** `ui_modules/edw_analyzer_page.py` and `ui_modules/bid_line_analyzer_page.py` to use new imports
- **Tested:** All functionality working identical to before refactoring
- **Branch:** `refractor`

**Session 19 (October 27, 2025) - Phase 2: EDW Module Refactoring:**
- **Refactored:** Split monolithic `edw_reporter.py` (1,631 lines) into modular `edw/` package
- **Created:** New directory `edw/` with 4 focused modules (1,473 total lines):
  - `parser.py` (814 lines) - PDF parsing & text extraction
  - `analyzer.py` (73 lines) - EDW detection logic
  - `excel_export.py` (156 lines) - Excel workbook generation
  - `reporter.py` (383 lines) - Orchestration & PDF generation
  - `__init__.py` (47 lines) - Module exports
- **Result:** Better separation of concerns, improved maintainability
- **Updated:** `ui_modules/edw_analyzer_page.py` to use new `from edw import` structure
- **Tested:** All functionality working identical to before refactoring
- **Branch:** `refractor`

**Session 18 (October 26, 2025) - Phase 1: Codebase Modularization:**
- **Refactored:** Split monolithic `app.py` (1,751 lines) into modular structure
- **Created:** `ui_modules/` directory with 5 focused modules (1,419 total lines)
  - `edw_analyzer_page.py` (722 lines) - Tab 1 UI
  - `bid_line_analyzer_page.py` (589 lines) - Tab 2 UI
  - `historical_trends_page.py` (31 lines) - Tab 3 placeholder
  - `shared_components.py` (66 lines) - Common utilities
- **Simplified:** `app.py` reduced to 56 lines (96.8% reduction!)
- **Fixed:** False "Filters are active" message (now only shows when filters applied)
- **Fixed:** Unwanted sidebar navigation (renamed `pages/` → `ui_modules/`)
- **Fixed:** NumPy 2.0 compatibility (downgraded to 1.26.4)
- **Branch:** `refractor`

**Session 17 (October 26, 2025) - Cover Page Support, VTO Split Lines:**
- PDF header extraction now checks page 2 if page 1 is cover page
- Added split VTO/VTOR/VOR line detection and parsing
- Implemented crew composition parsing (Captain/FO slots)
- Added helpful error messages for wrong PDF uploads

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

See `handoff/sessions/session-19.md` for Phase 2 EDW refactoring details, `handoff/sessions/session-18.md` for Phase 1 UI refactoring, or `handoff/sessions/session-16.md` for manual editing feature.

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
