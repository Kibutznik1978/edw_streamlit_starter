# EDW Pairing Analyzer - Handoff Document

**Last Updated:** October 16, 2025
**Project:** EDW Streamlit Starter
**Repository:** https://github.com/Kibutznik1978/edw_streamlit_starter

---

## Project Overview

The **EDW Pairing Analyzer** is a single-page Streamlit application designed for airline pilots to analyze bid packet PDFs. It identifies Early/Day/Window (EDW) trips and provides comprehensive statistics, visualizations, and downloadable reports.

### Key Purpose
- Parse airline pairings PDF documents
- Identify EDW trips (any duty day touching 02:30-05:00 local time)
- Track trip frequencies and Hot Standby assignments
- Generate Excel workbooks and PDF reports
- Provide interactive web-based data exploration

---

## Session Accomplishments

### Major Features Implemented

#### 1. **Fixed PDF Parsing Bug** ✅
- **Issue:** PDF header was being captured as Trip 1, causing incorrect counts
- **Solution:** Added `in_trip` flag to only start collecting after first "Trip Id" marker
- **Files:** `edw_reporter.py:39-61`
- **Result:** Correctly parses 272 trips instead of 273

#### 2. **Trip ID and Frequency Tracking** ✅
- **What:** Extract actual Trip IDs (100-371) instead of sequential numbering
- **What:** Parse frequency from patterns like "(5 trips)" or "(40 trips)"
- **Impact:**
  - 272 unique pairings
  - 522 total trips when accounting for frequency
  - Accurate weighted statistics
- **Files:** `edw_reporter.py:97-112`

#### 3. **Hot Standby Detection** ✅
- **What:** Identify Hot Standby pairings (e.g., ONT-ONT, SDF-SDF)
- **Logic:** Single-segment trips where departure == arrival
- **Exclusion:** Trips with positioning legs (ONT-DFW-DFW-ONT) are NOT Hot Standby
- **Found:** 3 Hot Standby pairings (361, 362, 363) totaling 112 occurrences
- **Files:** `edw_reporter.py:115-136`

#### 4. **Frequency-Weighted Calculations** ✅
- **What:** All statistics now account for trip frequency
- **Metrics:**
  - Trip-weighted EDW %
  - TAFB-weighted EDW %
  - Duty-day-weighted EDW %
- **Impact:** More accurate representation of actual flying exposure
- **Files:** `edw_reporter.py:176-197`

#### 5. **Hot Standby Exclusion from Distribution** ✅
- **What:** Exclude Hot Standby pairings from duty day distribution charts
- **Reason:** Hot Standby assignments aren't traditional "trips"
- **Result:** Distribution shows 410 regular trips (522 - 112 Hot Standby)
- **Files:** `edw_reporter.py:203-206`

#### 6. **Granular Progress Bar** ✅
- **What:** Page-by-page and trip-by-trip progress updates
- **Stages:**
  - 5-40%: PDF Parsing (updates every 10 pages)
  - 45-55%: Analyzing pairings (updates every 25 trips)
  - 60%: Calculating statistics
  - 65%: Generating Excel
  - 70%: Creating charts
  - 85%: Building PDF report
  - 100%: Complete
- **Files:** `edw_reporter.py:39-49, 164-196`, `app.py:32-37`

#### 7. **Session State for Persistent Downloads** ✅
- **Issue:** Download buttons disappeared after clicking
- **Solution:** Store results in `st.session_state`
- **Result:** Buttons remain visible after interaction
- **Files:** `app.py:22-23, 59-68, 71-173`

#### 8. **Interactive Data Visualizations** ✅
- **What:** Added web-based data exploration
- **Features:**
  - Summary tables (Trip, Weighted, Hot Standby)
  - Bar charts (Duty Days vs Trips, Duty Days vs Percent)
  - Interactive trip records table with filters:
    - Filter by EDW: All / EDW Only / Day Only
    - Filter by Hot Standby: All / Hot Standby Only / Exclude Hot Standby
    - Sort by: Trip ID / Frequency / TAFB Hours / Duty Days
- **Files:** `app.py:79-143`

#### 9. **Chart Labels and Descriptions** ✅
- **What:** Added proper axis labels to visualizations
- **Labels:**
  - X-axis: "Duty Days"
  - Y-axis: "Trips" or "Percent"
  - Titles: "Duty Days vs Trips", "Duty Days vs Percentage"
- **Files:** `app.py:107-111`

#### 10. **Streamlit Cloud Compatibility** ✅
- **What:** Fixed deployment issues for headless server environments
- **Changes:**
  - Added `matplotlib.use('Agg')` for headless rendering
  - Removed `pdfplumber` dependency (unused)
  - Added version constraints to requirements.txt
  - Created `.python-version` file
- **Files:** `edw_reporter.py:6-7`, `requirements.txt`, `.python-version`

#### 11. **Removed Bid Line Analyzer Page** ✅
- **What:** Deleted secondary page to focus on pairing analysis
- **Reason:** Simplify app and focus on core functionality
- **Files:** Deleted `pages/pages:2_Bid_Line_Analyzer.py`

---

## Technical Architecture

### File Structure
```
edw_streamlit_starter/
├── app.py                          # Main Streamlit application
├── edw_reporter.py                 # Core business logic and PDF parsing
├── requirements.txt                # Python dependencies
├── .python-version                 # Python version specification (3.9)
├── CLAUDE.md                       # Claude Code project instructions
├── HANDOFF.md                      # This file
└── BID2601_757_ONT_TRIPS_CAROL.pdf # Test PDF (not committed)
```

### Key Modules

#### `edw_reporter.py`
**Core Functions:**
- `parse_pairings()` - Extract trips from PDF with progress callbacks
- `parse_trip_id()` - Extract actual Trip ID (100-371)
- `parse_trip_frequency()` - Extract frequency from "(N trips)" notation
- `is_hot_standby()` - Detect Hot Standby pairings (XXX-XXX single segment)
- `is_edw_trip()` - Detect EDW trips (02:30-05:00 local time window)
- `parse_tafb()` - Extract TAFB hours
- `parse_duty_days()` - Count duty day blocks
- `run_edw_report()` - Main orchestration function

**Progress Tracking:**
- Accepts optional `progress_callback(progress, message)` parameter
- Updates at key stages with percentage and status message

**Output:**
- Excel workbook with 5 sheets:
  - Trip Records (Trip ID, Frequency, Hot Standby, TAFB, Duty Days, EDW)
  - Duty Distribution
  - Trip Summary
  - Weighted Summary
  - Hot Standby Summary
- Multi-page PDF report with charts and tables

#### `app.py`
**Streamlit Interface:**
- File uploader for PDF
- Optional labels (domicile, aircraft, bid period)
- Progress bar with status text
- Session state management for persistent results
- Interactive visualizations:
  - Summary tables in 3 columns
  - Bar charts for duty day distribution
  - Filterable/sortable trip records table
- Download buttons for Excel and PDF reports

### EDW Detection Logic

**EDW Definition:** Any duty day that touches 02:30-05:00 local time (inclusive)

**Time Extraction:**
- Pattern: `(HH)MM:SS` where HH is local hour
- Example: `(03)11:06` means 11:06 Zulu, 03:00 local

**Detection:**
```python
if (hour == 2 and minute >= 30) or (hour in [3, 4]) or (hour == 5 and minute == 0):
    return True  # EDW trip
```

### Hot Standby Detection Logic

**Definition:** Single-segment pairings where departure == arrival

**Algorithm:**
1. Extract all route segments (XXX-XXX patterns)
2. If exactly 1 segment found
3. AND departure == arrival
4. THEN Hot Standby

**Exclusions:**
- Multi-segment trips with positioning legs
- Example: ONT-DFW, DFW-DFW, DFW-ONT = NOT Hot Standby (has positioning)

---

## Excel Output Structure

### Sheet 1: Trip Records
| Trip ID | Frequency | Hot Standby | TAFB Hours | TAFB Days | Duty Days | EDW   |
|---------|-----------|-------------|------------|-----------|-----------|-------|
| 100     | 5         | False       | 7.73       | 0.32      | 1         | True  |
| 361     | 40        | True        | 8.00       | 0.33      | 1         | False |

### Sheet 2: Duty Distribution
| Duty Days | Trips | Percent |
|-----------|-------|---------|
| 1         | 238   | 58.0    |
| 5         | 34    | 8.3     |

**Note:** Excludes Hot Standby pairings

### Sheet 3: Trip Summary
| Metric           | Value |
|------------------|-------|
| Unique Pairings  | 272   |
| Total Trips      | 522   |
| EDW Trips        | 242   |
| Day Trips        | 280   |
| Pct EDW          | 46.4% |

### Sheet 4: Weighted Summary
| Metric                         | Value  |
|--------------------------------|--------|
| Trip-weighted EDW trip %       | 46.4%  |
| TAFB-weighted EDW trip %       | 73.3%  |
| Duty-day-weighted EDW trip %   | 66.2%  |

### Sheet 5: Hot Standby Summary
| Metric                | Value |
|-----------------------|-------|
| Hot Standby Pairings  | 3     |
| Hot Standby Trips     | 112   |

---

## Test Results (BID2601_757_ONT_TRIPS_CAROL.pdf)

### Statistics
- **PDF:** 292 pages
- **Unique Pairings:** 272 (Trip IDs 100-371)
- **Total Trip Occurrences:** 522
- **EDW Trips:** 242 (46.4%)
- **Hot Standby:** 3 pairings, 112 occurrences
  - Trip 361: ONT-ONT, frequency 40 (Mon-Fri)
  - Trip 362: ONT-ONT, frequency 32 (Tue-Fri)
  - Trip 363: ONT-ONT, frequency 40 (Tue-Sat)

### Frequency Distribution
- 1 occurrence: 215 pairings
- 2-6 occurrences: 50 pairings
- 9-10 occurrences: 2 pairings
- 32 occurrences: 1 pairing
- 40 occurrences: 2 pairings (Hot Standby)

---

## Running the Application

### Local Development
```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run Streamlit app
streamlit run app.py

# Access at http://localhost:8501
```

### Streamlit Cloud Deployment
1. Push changes to GitHub
2. Connect repository to Streamlit Cloud
3. Streamlit Cloud will auto-detect:
   - Python version from `.python-version`
   - Dependencies from `requirements.txt`
   - Entry point: `app.py`
4. App URL: Your Streamlit Cloud URL

---

## Known Issues and Future Improvements

### Current Limitations
1. **No multi-file upload:** App processes one PDF at a time
2. **No comparison mode:** Can't compare multiple bid periods
3. **Basic error handling:** Limited validation of PDF format
4. **No authentication:** Anyone with link can use the app
5. **Temporary file cleanup:** Relies on OS to clean up temp directories

### Future Enhancement Ideas
1. **Batch Processing:** Upload multiple PDFs and compare results
2. **Historical Tracking:** Store and track EDW percentages over time
3. **Custom EDW Window:** Allow users to define custom time windows
4. **Export to CSV:** Individual downloadable CSV files for each sheet
5. **Email Reports:** Send generated reports via email
6. **API Integration:** Connect to airline scheduling systems
7. **User Accounts:** Save preferences and history
8. **Advanced Filters:** Filter by TAFB range, specific duty day counts, etc.
9. **Chart Customization:** Allow users to choose chart types and colors
10. **Mobile Optimization:** Improve responsive design for tablets/phones

---

## Important Notes

### EDW Time Window
- **Window:** 02:30 - 05:00 local time (inclusive)
- **Critical Hours:** If ANY duty day touches this window, entire trip is EDW
- **Local Time Extraction:** Uses `(HH)` pattern from PDF text

### Hot Standby Identification
- **Must be single segment:** XXX-XXX with no other flight legs
- **Positioning flights excluded:** If trip has ONT-DFW-DFW-ONT, only the DFW-DFW is Hot Standby, but the trip is NOT marked as Hot Standby overall
- **Common patterns:** ONT-ONT, SDF-SDF, DFW-DFW

### Frequency Weighting
- **Source:** Extracted from text like "(5 trips)" or "(40 trips)"
- **Default:** If no frequency found, assumes 1
- **Impact:** All percentages and distributions are frequency-weighted

### PDF Parsing
- **Library:** PyPDF2 (NOT pdfplumber)
- **Trip Delimiter:** "Trip Id:" marker
- **Critical Fix:** Only collect text after first Trip Id marker to avoid header pollution

### Matplotlib Backend
- **Headless Mode:** Uses 'Agg' backend for Streamlit Cloud
- **Must be set BEFORE:** Importing pyplot
- **Location:** `edw_reporter.py:6-7`

---

## Git Commits Summary

### Commit 1: "Add comprehensive EDW pairing analysis features"
- Fixed PDF parsing bug (excluded header)
- Added Trip ID and frequency tracking
- Implemented Hot Standby detection
- Added frequency-weighted calculations
- Created granular progress bar
- Added session state for persistent downloads
- Built interactive visualizations
- Updated chart labels

### Commit 2: "Fix Streamlit Cloud deployment compatibility"
- Added matplotlib Agg backend
- Updated requirements.txt (removed pdfplumber, added versions)
- Created .python-version file
- Fixed headless server compatibility

---

## Quick Reference

### File Locations
- **Main app:** `app.py`
- **Business logic:** `edw_reporter.py`
- **Project docs:** `CLAUDE.md`
- **This handoff:** `HANDOFF.md`

### Key Functions
- **Parse PDF:** `parse_pairings(pdf_path, progress_callback=None)`
- **Generate report:** `run_edw_report(pdf_path, output_dir, domicile, aircraft, bid_period, progress_callback=None)`
- **EDW detection:** `is_edw_trip(trip_text)`
- **Hot Standby detection:** `is_hot_standby(trip_text)`

### Testing
- **Test PDF:** `BID2601_757_ONT_TRIPS_CAROL.pdf` (not in repo)
- **Expected results:** 272 pairings, 522 trips, 46.4% EDW

### Deployment
- **Production:** Streamlit Cloud (auto-deploy from GitHub)
- **Local:** `streamlit run app.py`
- **Port:** 8501 (default)

---

## Contact and Resources

- **Repository:** https://github.com/Kibutznik1978/edw_streamlit_starter
- **Streamlit Docs:** https://docs.streamlit.io
- **PyPDF2 Docs:** https://pypdf2.readthedocs.io
- **ReportLab Docs:** https://www.reportlab.com/docs/reportlab-userguide.pdf

---

**End of Handoff Document**

*Generated: October 16, 2025*
*Next session: Continue from this point with all context preserved*
