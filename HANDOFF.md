# EDW Pairing Analyzer - Handoff Document

**Last Updated:** October 24, 2025
**Project:** EDW Streamlit Starter
**Repository:** https://github.com/Kibutznik1978/edw_streamlit_starter
**Version:** 1.1 (SAFTE Fatigue Analysis)

---

## Project Overview

The **Pairing Analyzer Tool 1.0** (formerly "EDW Pairing Analyzer") is a Streamlit web application designed for airline pilots to analyze bid packet PDFs. It identifies Early/Day/Window (EDW) trips and provides comprehensive statistics, visualizations, and downloadable reports.

### Key Features

**EDW Pairing Analyzer (Tab 1):**
- Automatic PDF header extraction (bid period, domicile, fleet type)
- Parse airline pairings PDF documents (supports 757, MD-11, and other formats)
- Identify EDW trips (any duty day touching 02:30-05:00 local time)
- Track trip frequencies and Hot Standby assignments
- Advanced filtering (duty day length, legs per duty day, duty day criteria, exclude 1-day trips)
- Interactive trip details viewer with formatted pairing display
- **🆕 SAFTE Fatigue Analysis** - Professional SAFTE-FAST aligned fatigue modeling for each pairing
  - Dual y-axis chart: Effectiveness (left) and Sleep Reservoir (right) with independent scales
  - Industry-standard danger thresholds: 82% warning, 70% danger, 60% severe impairment
  - Enhanced circadian rhythm visualization with area fill and prominent wave pattern
  - Flight route markers showing airport codes at departure times
  - 3-tier bottom visualization: duty periods (work), layovers, and predicted sleep periods
  - 0-100 fatigue risk score with color-coded risk levels (Very High/High/Moderate/Low)
  - Sleep replenishment verification debug panel
- **Professional 5-page executive PDF reports** with KPI cards and 13 charts
- Duty day statistics (average legs, duty length, block time, credit time)

**Bid Line Analyzer (Tab 2):**
- **Automatic PDF header extraction** (bid period, domicile, fleet type, date range)
- Parse bid line PDFs for scheduling metrics (CT, BT, DO, DD)
- Filter by Credit Time, Block Time, Days Off, Duty Days ranges
- Pay period comparison analysis (PP1 vs PP2)
- Reserve line detection and statistics (Captain/FO slots)
- Buy-up line identification (CT < 75 hours)
- **Professional 3-page PDF reports** with KPI cards showing ranges
- Distribution charts and summary tables
- CSV and PDF export functionality
- **Notes/comments support** for tracking data iterations

**Historical Trends (Tab 3):**
- Placeholder for Supabase-powered trend analysis (coming soon)
- Future: Multi-bid-period comparisons and visualizations

---

## Current Status (Session 18)

✅ **Critical SAFTE Bugs Fixed** - Corrected time parsing, AutoSleep prediction, and date advancement bugs. Enhanced PDF exports with hot standby metrics and interactive tooltips.

### Latest Updates (October 24, 2025)

**Session 18 - PDF Export Enhancements & SAFTE Model Fixes:**
- **Fixed:** Critical time parsing bug in `parse_local_time()` - was parsing (LOCAL_HH)ZULU_HH:ZULU_MM as (LOCAL_HH)MM:SS
- **Fixed:** AutoSleep rigid night-time restrictions - removed forced 23:00 bedtime, allows daytime sleep after red-eyes
- **Fixed:** Date advancement bug - multiple duties on same day now handled correctly (was skipping Oct 26 duty)
- **Fixed:** Trip length table percentages - now matches chart by excluding hot standby from total
- **Fixed:** PDF header extraction - handles cover pages by checking first 3 pages instead of just page 0
- **Enhanced:** PDF exports with 5th KPI card showing hot standby trips
- **Enhanced:** Total Trips KPI with "Non-HSBY: XXX" subtitle
- **Added:** Interactive tooltips to SAFTE chart - hover over duty/layover/sleep bars for details
- **Added:** Flight routes in tooltips (e.g., "ONT-PHL, PHL-CAE") extracted from duty day structure
- **Attempted:** Pan/zoom functionality (rolled back due to poor UX)
- **Result:** SAFTE model now correctly predicts sleep after every duty period with realistic reservoir recovery

**Session 17 - SAFTE Model Scientific Validation & Core Algorithm Fixes:**
- **Analyzed:** Complete component-by-component analysis as expert fatigue researcher
- **Fixed:** Sleep reservoir exponential saturation formula (critical bug - was allowing negative accumulation during sleep)
- **Fixed:** Circadian rhythm time reference (critical bug - was using elapsed time instead of clock time)
- **Fixed:** Sleep inertia awakening capture (was using variable decay rate instead of constant)
- **Validated:** Effectiveness calculation and performance rhythm (verified correct, no changes needed)
- **Created:** 3 comprehensive test suites with 19 tests total (all passing)
- **Verified:** All formulas match official SAFTE specification (Hursh et al., 2004; DTIC ADA452991)
- **Note:** Performance rhythm and effectiveness calculations need deeper validation in next session

**Session 16 - SAFTE Visualization Alignment with Industry Standards:**
- **Aligned:** SAFTE chart visualization with professional SAFTE-FAST standards (analyzed real-world reference chart IMG_5742.PNG)
- **Implemented:** Dual y-axis system - Effectiveness (left, 0-105%) and Sleep Reservoir (right, 50-105%) with independent scales
- **Updated:** Industry-standard danger thresholds - 82% warning (yellow), 70% danger (orange), 60% severe (pink)
- **Enhanced:** Circadian rhythm prominence with area fill (sky blue, 15% opacity) and brighter line (Dodger blue, 2.5px)
- **Added:** Flight route markers with airport codes positioned at departure times (angled -45° like SAFTE-FAST)
- **Created:** Sleep replenishment verification debug panel showing reservoir statistics and sleep period analysis
- **Fixed:** Multi-day trip parsing - duty_end fallback to last flight arrival time when Debriefing marker missing
- **Fixed:** Effectiveness capping at 100% (was mathematically allowing >122% at circadian peaks)
- **Fixed:** Sleep prediction before first duty (23:00 to wake time) to prevent unrealistic initial fatigue
- **Improved:** Fatigue scoring aligned with industry thresholds (Very High <60%, High <70%, Moderate <82%, Low ≥82%)
- **Verified:** 3-tier bottom visualization (work/layover/sleep) with proper temporal alignment

**Session 15 - SAFTE Fatigue Analysis Integration:**
- **Implemented:** Complete SAFTE (Sleep, Activity, Fatigue, Task Effectiveness) fatigue model
- **Created:** `safte_model.py` (260 lines) - Core biomathematical model with circadian rhythm, sleep debt, and sleep inertia
- **Created:** `safte_integration.py` (279 lines) - Data bridge converting parsed trips to SAFTE format
- **Fixed:** 7 critical bugs from previous Gemini implementation (sleep accumulation, effectiveness clamping, sleep inertia)
- **Validated:** 25 comprehensive tests passing (4 basic + 12 scientific validation + 9 integration tests)
- **Added:** Interactive UI with effectiveness timeline chart showing duty periods and layover recovery
- **Integrated:** Real-time fatigue analysis for any pairing with danger thresholds (77.5% = 0.05% BAC)
- **Enhanced:** Visualization with full trip timeline, duty period shading, and color-coded risk levels

**Session 14 - Brand Integration & PDF Layout Refinements:**
- **Integrated:** Official Aero Crew Data brand palette (Navy, Teal, Sky, Gray)
- **Updated:** All 20 charts across both PDFs with brand colors
- **Added:** Logo support to both PDF headers (`logo-full.svg`)
- **Fixed:** Bid Line PDF layout (side-by-side charts, section grouping)
- **Enhanced:** Professional appearance with consistent brand identity
- **Improved:** KeepTogether logic prevents awkward page breaks

**Session 13 - PDF Enhancements & Professional Integration:**
- **Rewrote:** Complete `report_builder.py` (717 lines) with ReportLab for professional styling
- **Added:** KPI cards with range display (e.g., "Avg Credit: 75.3 ↑ Range 65.8-85.7")
- **Implemented:** PDF header extraction for bid line PDFs (`extract_bid_line_header_info()`)
- **Added:** Notes/comments text area to Bid Line Analyzer (Tab 2)
- **Integrated:** Professional EDW PDF (`export_pdf.py`) that was created but never connected
- **Fixed:** Data format mismatch, page break issues, filter clutter
- **Enhanced:** Intelligent title generation from extracted PDF metadata

**Session 12 - Professional PDF Report Export System:**
- **Created:** Complete PDF export system with `export_pdf.py` (1,150+ lines)
- **Implemented:** 13 professional charts (pie, bar, grouped bar, radar/spider)
- **Built:** 3-page executive report layout with branded headers/footers
- **Added:** Duty day statistics visualizations (grouped bar + radar chart)
- **Fixed:** 7 layout issues (pie chart shapes, text visibility, page breaks)
- **Updated:** Report terminology from "EDW Analysis" to "Pairing Analysis"

**Session 11 - Multi-App Merger & Supabase Planning:**
- **Merged:** Bid Line Analyzer from separate repo into unified 3-tab interface
- **Created:** Comprehensive Supabase integration plan (500+ lines)
- **Added:** Complete database schema design (6 tables)
- **Restored:** Detailed pairing viewer and duty day criteria analyzer
- **Fixed:** Pairing detail table width constraint with responsive CSS
- **Documentation:** IMPLEMENTATION_PLAN.md and SUPABASE_SETUP.md created

**Session 9 - Documentation & Organization:**
- **Restructured:** HANDOFF.md from 2,183-line monolith to organized session-based system (90% size reduction)
- **Organized:** Moved 49 debug/test scripts to `debug/` folder
- **Cleaned:** Root directory now contains only production code and documentation

### Parser Accuracy
- **BID2601 (757 Format):** ✅ 100% success (272 trips, 1,127 duty days)
- **BID2507 (757 Format):** ✅ 100% success
- **BID2501 (MD-11 Format):** ✅ 100% success (handles multi-day trips)

---

## Quick Start

### Running the Application
```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies (first time only)
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

The app will be available at `http://localhost:8501`

### Using the App
1. Upload a pairing PDF file (app automatically extracts bid period, domicile, fleet type)
2. (Optional) Add notes to track data iteration (e.g., "Final Data", "Round 1")
3. Click "Run Analysis" and wait for processing
4. Download Excel and PDF reports
5. Explore interactive visualizations and trip details

---

## Session History

Detailed documentation for each development session:

| Session | Date | Focus | Link |
|---------|------|-------|------|
| Session 1 | Oct 17, 2025 | Core Features and EDW Analysis | [session-01.md](handoff/sessions/session-01.md) |
| Session 2 | Oct 17, 2025 | Advanced Filtering and Trip Details | [session-02.md](handoff/sessions/session-02.md) |
| Session 3 | Oct 17, 2025 | DH/GT Flight Support | [session-03.md](handoff/sessions/session-03.md) |
| Session 4 | Oct 18, 2025 | Trip Summary Data Display | [session-04.md](handoff/sessions/session-04.md) |
| Session 5 | Oct 18, 2025 | Duty Day Criteria Filtering | [session-05.md](handoff/sessions/session-05.md) |
| Session 6 | Oct 18, 2025 | Multi-Format PDF Support | [session-06.md](handoff/sessions/session-06.md) |
| Session 7 | Oct 18, 2025 | MD-11 Format Support | [session-07.md](handoff/sessions/session-07.md) |
| Session 8 | Oct 19, 2025 | Parser Bug Fixes and UI Enhancements | [session-08.md](handoff/sessions/session-08.md) |
| Session 9 | Oct 19, 2025 | Documentation Restructuring and Codebase Cleanup | [session-09.md](handoff/sessions/session-09.md) |
| Session 10 | Oct 19, 2025 | Automatic PDF Header Extraction and Enhanced Statistics | [session-10.md](handoff/sessions/session-10.md) |
| Session 11 | Oct 20, 2025 | Multi-App Merger and Supabase Integration Planning | [session-11.md](handoff/sessions/session-11.md) |
| Session 12 | Oct 20, 2025 | Professional PDF Report Export System | [session-12.md](handoff/sessions/session-12.md) |
| Session 13 | Oct 20, 2025 | PDF Enhancements & Professional Integration | [session-13.md](handoff/sessions/session-13.md) |
| Session 14 | Oct 21, 2025 | Brand Integration & PDF Layout Refinements | [session-14.md](handoff/sessions/session-14.md) |
| Session 15 | Oct 22, 2025 | SAFTE Fatigue Analysis Integration | [session-15.md](handoff/sessions/session-15.md) |
| Session 16 | Oct 22, 2025 | SAFTE Visualization Alignment with Industry Standards | [session-16.md](handoff/sessions/session-16.md) |
| Session 17 | Oct 22, 2025 | SAFTE Model Scientific Validation & Core Algorithm Fixes | [session-17.md](handoff/sessions/session-17.md) |
| Session 18 | Oct 24, 2025 | PDF Export Enhancements & SAFTE Model Fixes | [session-18.md](handoff/sessions/session-18.md) |

---

## Technical Architecture

### Core Components

**1. EDW Analysis Module (`edw_reporter.py`)**
- PDF text extraction using `PyPDF2.PdfReader`
- Trip identification by "Trip Id" markers
- EDW detection: any duty day touching 02:30-05:00 local time (function at `edw_reporter.py:69`)
- Multi-format support: 757, MD-11, single-line, multi-line PDFs
- Fallback duty day detection for PDFs without Briefing/Debriefing keywords

**2. Streamlit UI (`app.py`)**
- File upload and parameter input
- Interactive visualizations (charts, tables, filters)
- Trip details viewer with formatted HTML display
- Download buttons for Excel and PDF reports
- Session state management for persistent results

**3. Trip Parsing (`parse_trip_for_table()` in `edw_reporter.py:176-341`)**
- Marker-based parsing (searches for keywords, not fixed line positions)
- Handles DH (deadhead), GT (ground transport), and regular flights
- Extracts duty times, block times, credit, TAFB, rest periods
- Per-duty-day EDW detection and metrics

**4. Duty Day Analysis (`parse_duty_day_details()` in `edw_reporter.py:396-545`)**
- Analyzes each duty day individually
- Counts legs per duty day
- Calculates duty day duration
- Detects EDW status for individual duty days
- Supports complex filtering criteria

### Key Algorithms

**EDW Detection Logic:**
```python
def is_edw_trip(trip_text):
    """A trip is EDW if any duty day touches 02:30-05:00 local time (inclusive)"""
    # Local time extracted from pattern: (HH)MM:SS where HH is local hour
    # Check all departure and arrival times in the trip
```

**Metrics Calculation:**
- **Trip-weighted:** Simple ratio of EDW trips to total trips
- **TAFB-weighted:** EDW trip hours / total TAFB hours
- **Duty-day-weighted:** EDW duty days / total duty days

---

## File Structure

```
.
├── app.py                          # Main Streamlit application (3-tab interface)
├── edw_reporter.py                 # EDW analysis module
├── safte_model.py                  # SAFTE fatigue model core (NEW - Session 15)
├── safte_integration.py            # SAFTE data bridge (NEW - Session 15)
├── bid_parser.py                   # Bid line parsing module
├── report_builder.py               # Bid line PDF report generator
├── requirements.txt                # Python dependencies
├── .python-version                 # Python version (3.9.6)
├── .env.example                    # Supabase credentials template
├── .gitignore                      # Git ignore rules (updated)
├── HANDOFF.md                      # This file (main index)
├── HANDOFF.md.backup               # Backup of original monolithic file
├── CLAUDE.md                       # Project instructions for Claude Code
├── docs/                           # Documentation
│   ├── IMPLEMENTATION_PLAN.md      # 6-phase Supabase integration plan
│   └── SUPABASE_SETUP.md           # Database setup guide
├── handoff/
│   └── sessions/
│       ├── session-01.md           # Session 1 details
│       ├── session-02.md           # Session 2 details
│       ├── ...                     # Sessions 3-14
│       └── session-15.md           # Session 15 details (latest - SAFTE)
└── debug/                          # Debug and test scripts (not in git)
    ├── test_safte_model.py         # Basic SAFTE unit tests
    ├── test_safte_validation.py    # Scientific validation tests
    └── test_safte_integration.py   # Integration tests with trip data
└── test_data/                      # Test PDFs and data (not in git)
```

---

## Excel Output Structure

Generated files follow pattern: `{domicile}_{aircraft}_Bid{bid_period}_EDW_Report_Data.xlsx`

**Sheets included:**
1. **Summary:** Trip-weighted, TAFB-weighted, duty-day-weighted EDW percentages
2. **EDW Trips:** All EDW trips with details (Trip ID, Frequency, TAFB, Duty Days, etc.)
3. **Day Trips:** All non-EDW (day) trips
4. **Hot Standby:** Hot standby pairings (ONT-ONT, SDF-SDF, etc.)
5. **All Trips:** Complete trip list with all metrics

---

## Known Issues and Future Improvements

### Current Limitations
1. **No multi-file upload:** App processes one PDF at a time
2. **No comparison mode:** Can't compare multiple bid periods
3. **Basic error handling:** Limited validation of PDF format
4. **No authentication:** Anyone with link can use the app
5. **Temporary file cleanup:** Relies on OS to clean up temp directories
6. **No bulk export of trip details:** Can only view one trip at a time

### Potential Enhancements
- Multi-file upload and comparison
- Historical trend analysis across bid periods
- Export all trip details to CSV
- User authentication and saved preferences
- Better error messages for malformed PDFs
- PDF format auto-detection with warnings

---

## Development Notes

### Testing Changes
Since this is a Streamlit app without formal unit tests:

1. Run the app and test with sample PDFs (BID2601, BID2507, BID2501)
2. Verify EDW detection logic by checking trips that touch 02:30-05:00 local time
3. Confirm all chart generation works
4. Validate Excel output structure (check all sheets present)
5. Test trip details viewer with various trip types
6. Verify all filters work correctly

### Common Issues
- **Unicode handling:** Always use `clean_text()` when preparing text for ReportLab or Excel
- **Chart memory management:** Charts saved to BytesIO, converted to PIL Image before PDF embedding
- **Parser robustness:** Use marker-based parsing, not fixed line positions

### PDF Format Support
- **757 Format:** Multi-line with Briefing/Debriefing keywords
- **MD-11 Format:** No Briefing/Debriefing keywords, requires fallback detection
- **Single-line Format:** All duty day info on one line
- **Handles:** DH flights, GT transport, route suffixes (catering), bare flight numbers

---

## Recent Commits (Last 5)

```
4ed9aa3 Update HANDOFF.md with Session 8 documentation
fe2cea6 Update app title to 'Pairing Analyzer Tool 1.0'
fec864f Fix MD-11 multi-day duty parsing and duty/block time extraction
dea34d6 Fix fallback duty day detection creating phantom duty days
3ec026f Add duty day statistics display and 1-day trip filter
```

Full commit history available in individual session files.

---

## Contact and Resources

**GitHub Repository:** https://github.com/Kibutznik1978/edw_streamlit_starter
**Streamlit Docs:** https://docs.streamlit.io
**PyPDF2 Docs:** https://pypdf2.readthedocs.io

For questions or issues, please open an issue on GitHub.

---

**Last Updated:** October 24, 2025
**Status:** ✅ SAFTE Model Critical Bugs Fixed - Time parsing, AutoSleep, and date advancement corrected. PDF exports enhanced with hot standby metrics and interactive tooltips.
**Next Session:** Test with real multi-day trips, commit critical bug fixes, consider SAFTE PDF export integration, deep validation of transmeridian adjustments
