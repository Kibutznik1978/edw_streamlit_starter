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

### Application Structure (Modularized - Sessions 18-23)

The application has been refactored into a **fully modular structure** for better maintainability:

```
edw_streamlit_starter/
├── app.py                           (56 lines - main entry point)
├── config/                          (Configuration - Phase 5)
│   ├── __init__.py                 (100 lines - module exports)
│   ├── constants.py                (75 lines - business logic constants)
│   ├── branding.py                 (60 lines - brand identity)
│   └── validation.py               (160 lines - validation rules)
├── models/                          (Data structures - Phase 5)
│   ├── __init__.py                 (40 lines - module exports)
│   ├── pdf_models.py               (75 lines - ReportMetadata, HeaderInfo)
│   ├── bid_models.py               (65 lines - BidLineData, ReserveLineInfo)
│   └── edw_models.py               (70 lines - TripData, EDWStatistics)
├── ui_modules/                      (UI layer - page modules)
│   ├── __init__.py                 (11 lines)
│   ├── edw_analyzer_page.py        (~640 lines - Tab 1)
│   ├── bid_line_analyzer_page.py   (~340 lines - Tab 2)
│   ├── historical_trends_page.py   (31 lines - Tab 3)
│   └── shared_components.py        (66 lines - PDF header display)
├── ui_components/                   (Reusable UI components - Session 21)
│   ├── __init__.py                 (95 lines - module exports)
│   ├── filters.py                  (169 lines - range sliders, filter logic)
│   ├── data_editor.py              (219 lines - data editor, validation, change tracking)
│   ├── exports.py                  (152 lines - download buttons, file generation)
│   └── statistics.py               (252 lines - metrics display, pay period analysis)
├── edw/                             (EDW analysis module - Session 19)
│   ├── __init__.py                 (47 lines - module exports)
│   ├── parser.py                   (814 lines - PDF parsing & text extraction)
│   ├── analyzer.py                 (73 lines - EDW detection logic)
│   ├── excel_export.py             (156 lines - Excel workbook generation)
│   └── reporter.py                 (383 lines - orchestration)
├── pdf_generation/                  (PDF report generation - Session 20)
│   ├── __init__.py                 (95 lines - module exports)
│   ├── base.py                     (268 lines - shared components)
│   ├── charts.py                   (616 lines - all chart generation)
│   ├── edw_pdf.py                  (425 lines - EDW reports)
│   └── bid_line_pdf.py             (652 lines - bid line reports)
├── bid_parser.py                    (880 lines - bid line parsing)
└── requirements.txt
```

#### `app.py` (56 lines)
Clean entry point with just navigation:
- Imports UI modules from `ui_modules/`
- Sets up Streamlit page config
- Creates 3-tab navigation
- Delegates rendering to module functions

#### Configuration & Models (Phase 5)

**`config/` package** - Centralized configuration (single source of truth):
- **`constants.py`** - Business logic constants
  - EDW time detection (02:30-05:00)
  - Buy-up threshold (75 hours)
  - Chart configuration (5-hour buckets, 400px height, -45° labels)
  - Reserve keywords (RA, SA, RB, etc.)
  - VTO keywords (VTO, VTOR, VOR)
  - Hot standby detection
- **`branding.py`** - Brand identity
  - `BrandColors` dataclass with Aero Crew Data palette
  - Logo path configuration
  - Default report title
- **`validation.py`** - Validation rules
  - CT/BT thresholds (150 hours warning, 0-200 range)
  - DO/DD thresholds (20 days warning, 0-31 range)
  - Combined validation (DO + DD ≤ 31)
  - Editable/readonly columns
  - Helper functions for validation

**`models/` package** - Type-safe data structures:
- **`pdf_models.py`** - PDF report models
  - `ReportMetadata` - Report metadata (title, subtitle, filters)
  - `HeaderInfo` - Parsed PDF headers (domicile, aircraft, bid period)
- **`bid_models.py`** - Bid line models
  - `BidLineData` - Individual line record with all metrics
  - `ReserveLineInfo` - Reserve line slot information
- **`edw_models.py`** - EDW analysis models
  - `TripData` - Individual trip/pairing record
  - `EDWStatistics` - Aggregated EDW statistics

**Benefits:**
- Single source of truth for all configuration
- Easy to change business rules in one place
- Type-safe data structures with validation
- Better testability (can mock/override config)
- Eliminated code duplication

#### `ui_modules/edw_analyzer_page.py` (722 lines)
**Tab 1: EDW Pairing Analyzer**
- PDF upload with automatic header extraction
- Trip analysis with weighted EDW metrics
- Duty day distribution charts
- Advanced filtering (duty day criteria, trip length, legs)
- Trip details viewer with HTML table (50% width, responsive)
- Excel and PDF report downloads
- Uses `edw/` module for core logic

Functions:
- `render_edw_analyzer()` - Main entry point
- `display_edw_results()` - Results and visualizations

#### `ui_modules/bid_line_analyzer_page.py` (~690 lines - includes pay period breakdown)
**Tab 2: Bid Line Analyzer**
- PDF upload with progress bar
- **Manual data editing** (Overview tab) - Interactive `st.data_editor()` for correcting parsed values
- Filter sidebar (CT, BT, DO, DD ranges) with smart "filters active" detection
- Three sub-tabs: Overview, Summary, Visuals
- Pay period comparison (PP1 vs PP2)
- **Pay period distribution breakdown** (Visuals tab) - Individual distributions for each pay period
  - Smart detection: only shown when multiple pay periods exist
  - All 4 metrics (CT, BT, DO, DD) with count and percentage charts
  - Consistent reserve line filtering
- Reserve line statistics (Captain/FO slots)
- CSV and PDF export (includes manual edits)
- Uses `bid_parser.py`, `pdf_generation`, and `ui_components`

Functions:
- `render_bid_line_analyzer()` - Main entry point
- `_display_bid_line_results()` - Display parsed data (uses ui_components for filters/downloads)
- `_render_overview_tab()` - Data editor (uses ui_components.data_editor)
- `_render_summary_tab()` - Statistics (uses ui_components.statistics)
- `_render_visuals_tab()` - Distribution charts (uses ui_components reserve filtering)

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

### UI Components Package (`ui_components/` - Session 21)

**Extracted reusable UI components from ui_modules for better code reuse and maintainability.**

#### `ui_components/filters.py` (169 lines)
Range sliders and filter logic:
- `create_metric_range_filter()` - Generic range slider builder
- `create_bid_line_filters()` - Complete CT/BT/DO/DD filter sidebar
- `apply_dataframe_filters()` - Apply filter ranges to DataFrame
- `is_filter_active()` - Detect if filters differ from defaults
- `render_filter_summary()` - Show "Showing X of Y lines" caption
- `render_filter_reset_button()` - Reset filters button

#### `ui_components/data_editor.py` (219 lines)
Data editor with validation and change tracking:
- `create_bid_line_editor()` - Configure `st.data_editor` for bid lines
- `detect_changes()` - Compare original vs edited DataFrames
- `validate_bid_line_edits()` - Validation rules (BT>CT, DO+DD>31, etc.)
- `render_change_summary()` - Display edit summary with expandable details
- `render_reset_button()` - Reset to original data button
- `render_editor_header()` - Data editor section header
- `render_filter_status_message()` - Filter status info message

#### `ui_components/exports.py` (152 lines)
Download buttons and file generation:
- `render_csv_download()` - CSV download button
- `render_pdf_download()` - PDF download button
- `render_excel_download()` - Excel file download button
- `generate_edw_filename()` - Consistent EDW filename generation
- `generate_bid_line_filename()` - Consistent bid line filename generation
- `render_download_section()` - Divider and header for download section
- `render_two_column_downloads()` - Side-by-side download buttons
- `handle_pdf_generation_error()` - PDF error display with traceback

#### `ui_components/statistics.py` (252 lines)
Metrics display and pay period analysis:
- `extract_reserve_line_numbers()` - Extract reserve/HSBY line numbers from diagnostics
- `filter_by_reserve_lines()` - Filter DataFrame to exclude reserve lines
- `calculate_metric_stats()` - Calculate min/max/mean/median for metrics
- `render_basic_statistics()` - CT, BT, DO, DD metrics grid (2 columns)
- `render_pay_period_analysis()` - PP1 vs PP2 comparison analysis
- `render_reserve_summary()` - Reserve line statistics display

#### `ui_components/__init__.py` (95 lines)
Module exports and public API:
- Exports all public functions from submodules
- `__all__` list for controlled API surface
- Clean imports: `from ui_components import create_bid_line_filters`

**Benefits:**
- **Reduced code duplication:** Common patterns extracted once
- **Improved maintainability:** Single source of truth for UI components
- **Better testability:** Isolated, reusable components
- **Consistent UX:** Same components used across different pages
- **Code reduction:** bid_line_analyzer_page.py reduced from 589 → 340 lines (42% reduction)

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

The `clean_text()` function in `edw/parser.py` normalizes Unicode and sanitizes special characters:
- Converts to NFKC normalization
- Replaces non-breaking spaces
- Converts bullet characters to hyphens

This is critical for reliable PDF text extraction and ReportLab PDF generation.

## PDF Libraries

**Two different PDF libraries are used**:
- `PyPDF2`: For EDW pairing analysis (Tab 1 → `edw/parser.py`)
- `pdfplumber`: For bid line analysis (Tab 2 → `bid_parser.py`)

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

**Session 30 (October 29, 2025) - UI Fixes & Critical Bug Resolution:**
- **Status:** ✅ COMPLETE - All UI and critical bugs resolved
- **Fixed:** Trip details table width (60% optimal for sidebar open/closed)
- **Fixed:** Distribution chart memory bug (27 PiB allocation error from NaN values)
- **Fixed:** Header extraction for final iteration PDFs (now checks up to 5 pages)
- **Implementation:**
  - `ui_components/trip_viewer.py`: Adjusted table width from 50% → 60%
  - `ui_modules/bid_line_analyzer_page.py`: Added 6-layer data validation to `_create_time_distribution_chart()`
  - `bid_parser.py`: Loop through up to 5 pages for header extraction (was 2)
- **Bug Fix Details:**
  - Root cause: NaN/inf values in data caused `np.arange()` to allocate massive array
  - Solution: Multi-layer validation (clean data, check empty, validate range, verify bins)
  - Result: Charts fail gracefully instead of crashing
- **Testing:** All fixes verified working
  - ✅ Table looks good with/without sidebar
  - ✅ Distribution charts render without errors
  - ✅ Header extraction works for PDFs with cover pages on first 5 pages
- **Files Modified:**
  - `ui_components/trip_viewer.py` (lines 86-96): Width adjustment
  - `ui_modules/bid_line_analyzer_page.py` (lines 611-642): Data validation
  - `bid_parser.py` (lines 130-154): Multi-page header extraction
- **Handoff Doc:** See `handoff/sessions/session-30.md` (comprehensive debugging documentation)
- **Duration:** ~1 hour
- **Branch:** `refractor`

**Session 29 (October 29, 2025) - Duplicate Trip Parsing Fix:**
- **Status:** ✅ COMPLETE - Parser now correctly handles all PDF variations
- **Fixed:** Duplicate trip IDs in parsed pairing data (129 trips → 120 unique)
- **Root Cause:** "Open Trips Report" section contained duplicate trips in open time
- **Solution:** Parser now stops at "Open Trips Report" heading
- **Implementation:**
  - Modified `edw/parser.py` to detect and stop at "Open Trips Report"
  - Uses Python `for...else` pattern for clean break handling
  - Works for PDFs with or without "Open Trips Report" section
- **Testing:** Verified with debug script - zero duplicates found
- **Files Modified:**
  - `edw/parser.py` (lines 128-180): Added stop condition
  - `database.py` (lines 555-557): Updated comment
- **Handoff Doc:** See `handoff/sessions/session-29.md` (detailed investigation & solution)
- **Duration:** ~1.5 hours
- **Branch:** `refractor`

**Phase 2 Complete (October 29, 2025) - Authentication Integration & Database Save:**
- **Status:** ✅ Phase 2 Complete - Database save functionality fully operational
- **Fixed:** RLS policy violations (42501 errors) by setting JWT session in `get_supabase_client()`
- **Fixed:** Duplicate key constraints (23505 errors) by adding deduplication logic
- **Implemented:**
  - Automatic JWT session handling in `get_supabase_client()`
  - Deduplication for pairing data (by trip_id) and bid line data (by line_number)
  - JWT debug tools (`debug_jwt_claims()` function and sidebar UI)
  - Clean duplicate detection and replace workflow
- **Testing:** Both EDW pairing and bid line data save successfully to database
  - Test save: 120 unique pairings (9 duplicates removed from 129 total)
  - Test save: 38 bid lines with replace workflow
  - JWT claims verified: `app_role: "admin"` present and working
- **Files Modified:**
  - `database.py` (+252 lines): JWT session handling, deduplication logic
  - `auth.py` (+16 lines): JWT debug UI in sidebar
  - `ui_modules/edw_analyzer_page.py` (+70 lines): Save workflow
  - `ui_modules/bid_line_analyzer_page.py` (+80 lines): Save workflow
- **Handoff Doc:** See `handoff/sessions/session-28.md` (complete session documentation)
- **Duration:** ~2 hours
- **Branch:** `refractor`
- **Next:** Phase 3 - Testing & Optimization (or Phase 4 - Admin Upload Interface)

**Phase 1 Complete (October 29, 2025) - Supabase Database Schema Deployment:**
- **Status:** ✅ Phase 1 Complete - Database backend fully deployed and operational
- **Deployed:** Complete database schema to Supabase (7 tables, 1 materialized view, 30+ indexes)
- **Created:** Fixed migration (v1.1) - `docs/migrations/001_initial_schema_fixed.sql`
  - Fixed auth.users trigger permission issue from original migration
  - Profiles now created via auth.py module (simpler implementation)
- **Configured:** JWT Custom Claims via Auth Hooks
  - Created `custom_access_token_hook` function
  - Enabled Customize Access Token (JWT) Claims hook
  - All JWTs now include `app_role` claim for RLS
- **Admin User:** Created giladswerdlow@gmail.com as first admin
- **Environment:** `.env` file created and secured (600 permissions, gitignored)
- **Testing:** `test_supabase_connection.py` passes all checks
- **Database Objects:**
  - Tables: bid_periods, pairings, pairing_duty_days, bid_lines, profiles, pdf_export_templates, audit_log
  - View: bid_period_trends (materialized)
  - Functions: is_admin, handle_new_user, log_changes, refresh_trends
  - Triggers: 3 audit triggers (bid_periods, pairings, bid_lines)
  - RLS Policies: 32 JWT-based policies (performance-optimized)
- **Handoff Doc:** See `handoff/sessions/session-27.md` (comprehensive session documentation)
- **Duration:** 45 minutes
- **Branch:** `refractor`

**Session 25 (October 27, 2025) - Pay Period Distribution Breakdown:**
- **Added:** Comprehensive pay period breakdown functionality to Bid Line Analyzer
- **App Visuals Tab:** New "Pay Period Breakdown" section (~250 lines added)
  - Shows individual distributions for each pay period (PP1, PP2)
  - All 4 metrics: CT, BT, DO, DD with count and percentage charts
  - Smart detection: only appears when multiple pay periods exist
  - Interactive Plotly charts for CT/BT, Streamlit bar charts for DO/DD
- **PDF Generation:** Added pay period breakdown pages (~310 lines added)
  - Dedicated pages for each pay period's distributions
  - All 4 metrics with tables and side-by-side charts
  - Professional formatting with automatic page breaks
- **Smart Behavior:** Single period = overall only, Multiple periods = overall + per-period breakdown
- **Files Modified:** `ui_modules/bid_line_analyzer_page.py`, `pdf_generation/bid_line_pdf.py`
- **Testing:** All syntax validation passing, zero breaking changes
- **Branch:** `refractor`

**Session 24 (October 27, 2025) - Phase 6: Codebase Cleanup & Distribution Chart Bug Fixes:**
- **Deleted:** 3 obsolete legacy files (~3,700 lines): `edw_reporter.py`, `export_pdf.py`, `report_builder.py`
- **Refactored:** `edw/reporter.py` (423 → 206 lines, 51% reduction) - now uses centralized PDF generation
- **Created:** `ui_components/trip_viewer.py` (281 lines) - reusable trip details viewer component
- **Updated:** `ui_modules/edw_analyzer_page.py` (726 → 498 lines, 31% reduction)
- **Fixed:** Critical distribution chart bugs:
  - PDF distributions now correctly exclude reserve lines (matched with app)
  - DO/DD distributions now use pay period data instead of averaged values
  - Issue: `df['DO']` showed averages (1 entry per line), now uses `pay_periods['DO']` (2 entries per line)
  - Added captions: "*Showing both pay periods (2 entries per line)"
- **Result:** Removed ~4,000 lines, fixed critical data accuracy bugs
- **Branch:** `refractor`

**Session 23 (October 27, 2025) - Phase 5: Configuration & Models Extraction:**
- **Created:** `config/` package with all application constants (4 modules, ~300 lines)
  - `constants.py` - Business logic (EDW times, buy-up threshold, chart config, keywords)
  - `branding.py` - Brand identity (BrandColors dataclass, logo, colors)
  - `validation.py` - Validation rules (CT/BT/DO/DD thresholds, ranges, helper functions)
  - `__init__.py` - Module exports with clean public API
- **Created:** `models/` package with type-safe data structures (4 modules, ~200 lines)
  - `pdf_models.py` - ReportMetadata, HeaderInfo dataclasses
  - `bid_models.py` - BidLineData, ReserveLineInfo dataclasses
  - `edw_models.py` - TripData, EDWStatistics dataclasses
  - `__init__.py` - Module exports with clean public API
- **Updated:** 7 modules to use centralized config/models
  - `edw/analyzer.py` - Uses EDW time constants from config
  - `pdf_generation/base.py` - Uses brand colors from config.branding
  - `pdf_generation/bid_line_pdf.py` - Uses models.ReportMetadata + config (eliminated duplicate)
  - `ui_components/data_editor.py` - Uses all validation constants from config
  - `ui_modules/bid_line_analyzer_page.py` - Uses chart config constants
  - `bid_parser.py` - Uses keyword config for dynamic regex patterns
- **Benefits:** Single source of truth, type safety, zero duplication, better testability, easy configuration changes
- **Testing:** All syntax validation passing, all module imports successful, app runs without errors
- **Result:** Professional architecture, excellent maintainability, fully modularized codebase
- **Branch:** `refractor`
- **Refactoring Complete:** All 5 phases (UI, EDW, PDF, Components, Config/Models) finished! 🎉

**Session 22 (October 27, 2025) - Bid Line Distribution Chart Fixes:**
- **Fixed:** Credit Time (CT) and Block Time (BT) distribution charts showing incorrect sparse distributions
- **Implemented:** 5-hour bucket histograms for CT/BT (70-75, 75-80, 80-85 hrs)
- **Added:** Interactive Plotly charts with hover tooltips replacing static charts
- **Fixed:** Angled labels (-45°) for better readability without overlap
- **Fixed:** Days Off (DO) and Duty Days (DD) to show whole numbers only (no fractional days)
- **Created:** Reusable `_create_time_distribution_chart()` helper function
- **Result:** Accurate, interactive, professional distribution charts with meaningful patterns
- **Tested:** All syntax and import validation passing
- **Branch:** `refractor`

**Session 24 (October 27, 2025) - Phase 6: Codebase Cleanup & Distribution Chart Bug Fixes:**
- **Deleted:** 3 obsolete legacy files (~3,700 lines): `edw_reporter.py`, `export_pdf.py`, `report_builder.py`
- **Refactored:** `edw/reporter.py` (423 → 206 lines, 51% reduction) - now uses centralized PDF generation
- **Created:** `ui_components/trip_viewer.py` (281 lines) - reusable trip details viewer component
- **Updated:** `ui_modules/edw_analyzer_page.py` (726 → 498 lines, 31% reduction)
- **Fixed:** Critical distribution chart bugs:
  - PDF distributions now correctly exclude reserve lines (matched with app)
  - DO/DD distributions now use pay period data instead of averaged values
  - Issue: `df['DO']` showed averages (1 entry per line), now uses `pay_periods['DO']` (2 entries per line)
  - Added captions: "*Showing both pay periods (2 entries per line)"
- **Result:** Removed ~4,000 lines, fixed critical data accuracy bugs
- **Branch:** `refractor`

**Session 21 (October 27, 2025) - Phase 4: UI Components Extraction:**
- **Refactored:** Extracted reusable UI components from ui_modules into new `ui_components/` package
- **Created:** New directory `ui_components/` with 4 focused modules (887 total lines):
  - `filters.py` (169 lines) - Range sliders and filter logic
  - `data_editor.py` (219 lines) - Data editor, validation, change tracking
  - `exports.py` (152 lines) - Download buttons and file generation
  - `statistics.py` (252 lines) - Metrics display and pay period analysis
  - `__init__.py` (95 lines) - Module exports and public API
- **Updated:** `ui_modules/bid_line_analyzer_page.py` (589 → 340 lines, 42% reduction)
- **Updated:** `ui_modules/edw_analyzer_page.py` to use export components
- **Result:** Better code reuse, improved maintainability, consistent UX across pages
- **Tested:** All imports successful, zero breaking changes
- **Branch:** `refractor`

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

See `handoff/sessions/session-22.md` for distribution chart fixes, `handoff/sessions/session-21.md` for UI components extraction, `handoff/sessions/session-19.md` for Phase 2 EDW refactoring details, `handoff/sessions/session-18.md` for Phase 1 UI refactoring, or `handoff/sessions/session-16.md` for manual editing feature.

## Documentation

- **Main Handoff**: `HANDOFF.md` - Project overview and session history
- **Session Details**: `handoff/sessions/session-XX.md` - Detailed session documentation
- **Implementation Plan**: `docs/IMPLEMENTATION_PLAN.md` - 6-phase Supabase integration roadmap
- **Database Setup**: `docs/SUPABASE_SETUP.md` - Supabase project creation and SQL migrations
- **Session 26**: `handoff/sessions/session-26.md` - Supabase planning & preparation (Oct 28, 2025)
- **Session 27**: `handoff/sessions/session-27.md` - Phase 1: Database deployment (Oct 29, 2025) ✅
- **Session 28**: `handoff/sessions/session-28.md` - Phase 2: Authentication & database save (Oct 29, 2025) ✅
- **Session 29**: `handoff/sessions/session-29.md` - Duplicate trip parsing fix (Oct 29, 2025) ✅
- **Environment Template**: `.env.example` - Supabase credentials template

## Current Status & Next Steps

### Phase 1: Database Schema ✅ COMPLETE (Oct 29, 2025)
- ✅ Supabase project created and configured
- ✅ Database schema deployed (7 tables, 30+ indexes, 4 functions, 32 RLS policies)
- ✅ JWT custom claims configured
- ✅ Admin user created (giladswerdlow@gmail.com)
- ✅ All tests passing
- ✅ `.env` file configured and secured

### Phase 2: Authentication Integration ✅ COMPLETE (Oct 29, 2025)
- ✅ Fixed RLS policy violations with JWT session handling
- ✅ Implemented "Save to Database" for EDW pairing data
- ✅ Implemented "Save to Database" for bid line data
- ✅ Added deduplication logic for both data types
- ✅ JWT debug tools in sidebar
- ✅ Tested with admin user account
- ✅ Duplicate detection and replace workflow

### Phase 3: Testing & Optimization 🔜 NEXT (2-3 days)
1. Apply audit migration (002_add_audit_fields)
2. Populate `created_by` and `updated_by` fields
3. Test with multiple users (admin and regular)
4. Performance testing with large datasets
5. Improve error handling and retry logic

### Future Phases (4-5 weeks)
- Phase 3: Database Module Testing & Optimization
- Phase 4: Admin Upload Interface
- Phase 5: User Query Interface
- Phase 6: Historical Trends Tab (visualization)
- Phase 7: PDF Template Management
- Phase 8: Data Migration from Legacy Files
- Phase 9: Testing & QA
- Phase 10: Performance Optimization & Production Readiness
