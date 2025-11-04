# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **unified Streamlit application** for analyzing airline bid packet data for pilots. The app uses a 4-tab interface combining analysis tools, database querying, and historical trend visualization:

1. **EDW Pairing Analyzer** (Tab 1) - Analyzes pairings PDF to identify Early/Day/Window (EDW) trips
2. **Bid Line Analyzer** (Tab 2) - Parses bid line PDFs for scheduling metrics (CT, BT, DO, DD)
3. **Database Explorer** (Tab 3) - Query historical data with multi-dimensional filters (Phase 5 complete)
4. **Historical Trends** (Tab 4) - Database-powered trend analysis and visualizations (Phase 6 planned)

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
│   ├── __init__.py                 (14 lines)
│   ├── edw_analyzer_page.py        (~640 lines - Tab 1)
│   ├── bid_line_analyzer_page.py   (~340 lines - Tab 2)
│   ├── database_explorer_page.py   (~470 lines - Tab 3)
│   ├── historical_trends_page.py   (31 lines - Tab 4)
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
├── database.py                      (Database integration - Phase 2)
├── auth.py                          (Authentication - Phase 2)
└── requirements.txt
```

#### `app.py` (89 lines)
Clean entry point with just navigation:
- Imports UI modules from `ui_modules/`
- Sets up Streamlit page config
- Authentication check and user info display
- Creates 4-tab navigation
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
- Trip details viewer with HTML table (60% width, responsive)
- Excel and PDF report downloads
- Database save functionality (Phase 2)
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
- Database save functionality (Phase 2)
- Uses `bid_parser.py`, `pdf_generation`, and `ui_components`

Functions:
- `render_bid_line_analyzer()` - Main entry point
- `_display_bid_line_results()` - Display parsed data (uses ui_components for filters/downloads)
- `_render_overview_tab()` - Data editor (uses ui_components.data_editor)
- `_render_summary_tab()` - Statistics (uses ui_components.statistics)
- `_render_visuals_tab()` - Distribution charts (uses ui_components reserve filtering)

#### `ui_modules/database_explorer_page.py` (~470 lines)
**Tab 3: Database Explorer**
- Multi-dimensional query interface for historical data (Phase 5 complete)
- Filter sidebar with domicile, aircraft, seat, bid period, and date range filters
- Quick date filters (Last 3/6 months, Last year, All time, Custom)
- Data type selector (Pairings or Bid Lines)
- Paginated results table with customizable rows per page
- Export to CSV (Excel and PDF coming in Phase 4 enhancements)
- Record detail viewer with expandable JSON display
- Uses `database.py` query functions

Functions:
- `render_database_explorer()` - Main entry point
- `_render_filter_sidebar()` - Multi-dimensional filter UI with active filter summary
- `_execute_query()` - Query execution with error handling
- `_display_results()` - Paginated results display with export options
- `_display_data_table()` - Smart column selection based on data type
- `_render_record_detail_viewer()` - Expandable record detail view

#### `ui_modules/historical_trends_page.py` (31 lines)
**Tab 4: Historical Trends**
- Placeholder for visualization features (Phase 6 planned)
- Future: Trend charts, multi-bid-period comparisons, anomaly detection
- Will use `database.py` query functions and Plotly for visualizations

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

### Core Analysis Modules

#### EDW Analysis Module (`edw/` - Session 19)

**Refactored from monolithic `edw_reporter.py` (1,631 lines) into 4 focused modules:**

**`edw/parser.py` (814 lines)** - PDF parsing and text extraction:
- **PDF Reading**: Uses `PyPDF2.PdfReader` to extract text from bid packet PDFs
- **Header Extraction**: `extract_pdf_header_info()` - bid period, domicile, fleet type
  - Checks up to 5 pages to find header (handles cover pages)
- **Trip Identification**: `parse_pairings()` - splits text into individual trips by "Trip Id" markers
  - Stops at "Open Trips Report" section to avoid duplicates
- **Metric Extraction**: `parse_tafb()`, `parse_duty_days()`, `parse_max_duty_day_length()`, etc.
- **Detailed Parsing**: `parse_duty_day_details()`, `parse_trip_for_table()` - structured trip data
  - Handles older PDF formats without "Briefing/Debriefing" labels
  - Flexible Premium/Per Diem parsing (optional colons)

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
  - Checks up to 5 pages to find header (handles cover pages)
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
- Pay period breakdown pages with individual distributions

Key entry points:
- `create_edw_pdf_report()` from `pdf_generation` - EDW PDF generation
- `create_bid_line_pdf_report()` from `pdf_generation` - Bid line PDF generation

#### Database Module (`database.py` - Phase 1-2)

**Supabase integration for persistent data storage:**

- **Client Management**: `get_supabase_client()` - creates authenticated Supabase client
  - Automatic JWT session handling for RLS policies
  - Extracts JWT from st.session_state and sets session context
- **Pairing Data Save**: `save_pairing_data_to_db()` - saves EDW analysis results
  - Deduplication by trip_id (detects and offers replace workflow)
  - Saves to `bid_periods`, `pairings`, `pairing_duty_days` tables
- **Bid Line Data Save**: `save_bid_line_data_to_db()` - saves bid line analysis results
  - Deduplication by line_number (detects and offers replace workflow)
  - Saves to `bid_periods`, `bid_lines` tables
- **Query Functions**: Placeholder for historical data queries
- **Error Handling**: Comprehensive error handling with user-friendly messages

Key entry points:
- `save_pairing_data_to_db()` - Save EDW pairing data
- `save_bid_line_data_to_db()` - Save bid line data

#### Authentication Module (`auth.py` - Phase 2)

**Supabase authentication integration:**

- **Login/Signup UI**: `render_auth_ui()` - sidebar authentication interface
  - Email/password login
  - New user registration
  - Profile creation on signup
- **Session Management**: JWT token handling and user state
- **JWT Debug Tools**: `debug_jwt_claims()` - displays JWT claims in sidebar (admin only)
- **Role Management**: Admin vs regular user permissions

Key functions:
- `render_auth_ui()` - Main authentication interface
- `debug_jwt_claims()` - JWT token debugging

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

## Database Schema

See `docs/IMPLEMENTATION_PLAN.md` and `docs/SUPABASE_SETUP.md` for comprehensive database integration plans.

**Database Schema** (7 tables, 1 materialized view):
1. `bid_periods` - Master table for bid period metadata
2. `pairings` - Individual pairing/trip records (EDW analysis)
3. `pairing_duty_days` - Duty day details for each pairing
4. `bid_lines` - Individual bid line records
5. `profiles` - User profiles and roles
6. `pdf_export_templates` - PDF template customization
7. `audit_log` - Change tracking and audit trail
8. `bid_period_trends` - Materialized view for trend analysis

**Key Features:**
- Row Level Security (RLS) with JWT-based policies
- JWT Custom Claims for role-based access control
- Audit triggers for change tracking
- Performance-optimized indexes
- Materialized view for fast trend queries

## Testing Changes

Since this is a Streamlit app without formal tests:

1. **Tab 1 (EDW Pairing Analyzer):**
   - Upload a pairing PDF and verify automatic header extraction
   - Run analysis and check all weighted EDW metrics
   - Test duty day criteria filtering (match modes: Any/All)
   - View trip details and verify table width constraint (60% on desktop)
   - Download Excel and PDF reports
   - Test "Save to Database" with duplicate detection

2. **Tab 2 (Bid Line Analyzer):**
   - Upload a bid line PDF and verify parsing completes
   - Apply filters (CT, BT, DO, DD ranges)
   - Check all three sub-tabs (Overview, Summary, Visuals)
   - Verify pay period analysis displays correctly
   - Test manual data editing and change tracking
   - Test CSV and PDF export
   - Test "Save to Database" with duplicate detection

3. **Tab 3 (Database Explorer):**
   - Select filters (domicile, aircraft, seat, bid periods)
   - Test quick date filters and custom date range
   - Run queries for both Pairings and Bid Lines
   - Verify pagination works correctly
   - Test CSV export functionality
   - View record details in expandable JSON viewer
   - Test with no filters (should show all data)

4. **Tab 4 (Historical Trends):**
   - Verify placeholder content displays
   - (After Phase 6 implementation) Test trend visualizations

5. **Cross-tab Testing:**
   - Verify session state isolation (no bleeding between tabs)
   - Test switching between tabs multiple times
   - Upload different PDFs in different tabs

6. **Authentication:**
   - Test login/signup flow
   - Verify JWT claims are set correctly
   - Test admin vs regular user permissions

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
- **Database errors**: Check JWT claims are set (use debug tools in sidebar)
- **RLS violations**: Ensure user is authenticated and JWT session is set in `get_supabase_client()`

## Manual Data Editing Feature

The Bid Line Analyzer supports inline data editing to fix missing or incorrect parsed values.

### Key Components:

**Data Editor** - Interactive editing interface:
- Uses `st.data_editor()` for interactive editing
- Editable columns: CT, BT, DO, DD (Line number is read-only)
- Always shows ALL parsed lines (filters don't affect editor)
- Column validation: CT/BT (0.0-200.0), DO/DD (0-31)

**Session State Management**:
- `bidline_original_df`: Original parsed data (never modified)
- `bidline_edited_df`: User-corrected data (contains edits)
- Data flow: All tabs, charts, and exports use edited data automatically

**Change Tracking**:
- Compares edited data against original
- Visual indicators: ✏️ "Data has been manually edited (N changes)"
- "View edited cells" expander shows Line, Column, Original, Current
- Handles NaN/None values properly

**Validation Warnings**:
- CT or BT > 150 hours
- BT > CT (block time exceeds credit time)
- DO or DD > 20 days
- DO + DD > 31 (exceeds month length)

**Important:** Data editor always uses `df` (all lines), never `filtered_df`. All calculations automatically use edited data.

## Recent Changes

### Latest Sessions (Detailed)

**Session 32 (October 30, 2025) - SDF Bid Line Parser Bug Fixes:**
- **Fixed:** Critical boolean logic bug in reserve line detection
  - `_detect_reserve_line()` was returning `None` instead of `False` for regular lines
  - Root cause: `(ct_zero and dd_fourteen)` evaluated to `None` when ct_zero was `None`
  - Solution: Wrapped expressions in `bool()` to prevent None propagation
- **Fixed:** Reserve lines included in main DataFrame (skewing averages)
  - Added exclusion logic in both pay period and fallback parsing paths
  - Reserve lines now tracked in diagnostics only, not in main data
  - Impact: SDF Bid2601 now shows 258 regular lines (was 296 with reserves)
- **Fixed:** VTO lines misclassified as reserve lines
  - Added early VTO check in `_detect_reserve_line()` to prevent false positives
  - Both VTO and reserve lines have CT:0, BT:0, DD:14 patterns
- **Implementation:** Modified 4 locations in `bid_parser.py`
- **Testing:** Created comprehensive test suite (7 scripts), all passing
- **Documentation:** Created `EXCLUSION_LOGIC.md` explaining reserve/VTO exclusion
- See `handoff/sessions/session-32.md` for detailed analysis

**Session 31 (October 29, 2025) - Older PDF Format Compatibility & Trip Summary Parsing:**
- **Fixed:** Debriefing time parsing for older PDFs without "Briefing/Debriefing" labels
- **Fixed:** Premium and Per Diem fields missing from trip summary display
- **Implementation:** Updated 3 parsing functions in `edw/parser.py` with fallback logic
- **Testing:** Older PDFs now parse correctly, zero regression on modern PDFs
- See `handoff/sessions/session-31.md` for detailed format analysis

**Session 30 (October 29, 2025) - UI Fixes & Critical Bug Resolution:**
- **Fixed:** Trip details table width (60% optimal for sidebar open/closed)
- **Fixed:** Distribution chart memory bug (27 PiB allocation error from NaN values)
- **Fixed:** Header extraction for final iteration PDFs (now checks up to 5 pages)
- **Implementation:** Multi-layer data validation in chart generation
- See `handoff/sessions/session-30.md` for comprehensive debugging documentation

**Session 29 (October 29, 2025) - Duplicate Trip Parsing Fix:**
- **Fixed:** Duplicate trip IDs in parsed pairing data (129 trips → 120 unique)
- **Root Cause:** "Open Trips Report" section contained duplicate trips
- **Solution:** Parser now stops at "Open Trips Report" heading
- See `handoff/sessions/session-29.md` for detailed investigation

### Recent Milestones

**Phase 2 Complete (October 29, 2025) - Authentication Integration & Database Save:**
- ✅ Fixed RLS policy violations with JWT session handling
- ✅ Implemented "Save to Database" for both EDW and bid line data
- ✅ Added deduplication logic and duplicate detection workflow
- ✅ JWT debug tools in sidebar
- See `handoff/sessions/session-28.md`

**Phase 1 Complete (October 29, 2025) - Supabase Database Schema Deployment:**
- ✅ Complete database schema deployed (7 tables, 32 RLS policies, 30+ indexes)
- ✅ JWT custom claims configured via Auth Hooks
- ✅ Admin user created (giladswerdlow@gmail.com)
- See `handoff/sessions/session-27.md`

### Older Sessions (Summary)

**Refactoring Sessions (18-25, October 26-27, 2025):**
- Session 25: Pay period distribution breakdown
- Session 24: Codebase cleanup, distribution chart bug fixes
- Session 23: Configuration & models extraction (config/, models/ packages)
- Session 22: Bid line distribution chart fixes (5-hour buckets, Plotly)
- Session 21: UI components extraction (ui_components/ package)
- Session 20: PDF generation consolidation (pdf_generation/ package)
- Session 19: EDW module refactoring (edw/ package)
- Session 18: Codebase modularization (ui_modules/, app.py reduced to 56 lines)

See individual session docs in `handoff/sessions/` for detailed information.

## Documentation

- **Main Handoff**: `HANDOFF.md` - Project overview and session history
- **Session Details**: `handoff/sessions/session-XX.md` - Detailed session documentation
- **Implementation Plan**: `docs/IMPLEMENTATION_PLAN.md` - 6-phase Supabase integration roadmap
- **Database Setup**: `docs/SUPABASE_SETUP.md` - Supabase project creation and SQL migrations
- **Migrations**: `docs/migrations/` - SQL migration files
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

### Phase 3: Testing & Optimization ✅ COMPLETE (Oct 31, 2025)
- ✅ Applied audit migration (002_add_audit_fields)
- ✅ Populated `created_by` and `updated_by` fields in database.py
- ✅ Tested with admin user
- ✅ Performance framework in place
- ✅ Comprehensive error handling implemented

### Phase 4: Admin Upload Interface ✅ COMPLETE (Oct 29, 2025)
- ✅ "Save to Database" in EDW Pairing Analyzer
- ✅ "Save to Database" in Bid Line Analyzer
- ✅ Duplicate detection and replace workflow
- ✅ Success/error messages with record counts
- ✅ Data persists correctly with audit fields

### Phase 5: User Query Interface ✅ COMPLETE (Oct 31, 2025)
- ✅ Database Explorer page created (Tab 3)
- ✅ Multi-dimensional filtering (domicile, aircraft, seat, bid periods, date range)
- ✅ Quick date filters (Last 3/6 months, Last year, All time, Custom)
- ✅ Data type selector (Pairings / Bid Lines)
- ✅ Paginated results table with customizable page size
- ✅ CSV export functionality
- ✅ Record detail viewer with JSON display
- ✅ Filter summary display
- ✅ Integrated into main app as Tab 3

### Future Phases (3-4 weeks)
- Phase 6: Historical Trends Tab - Trend visualizations and comparative analysis
- Phase 7: PDF Template Management - Admin-customizable PDF templates
- Phase 8: Data Migration - Backfill historical data from legacy PDFs
- Phase 9: Testing & QA - End-to-end testing and user acceptance
- Phase 10: Performance Optimization - Query optimization and caching improvements
