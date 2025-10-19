# Session 2: Advanced Filtering and Trip Details

**Session 2**

[← Back to Main Handoff](../../HANDOFF.md)

---

## Session 2 Accomplishments (October 17, 2025)

### Major Features Implemented

#### 12. **Advanced Duty Day Length Filtering** ✅
- **What:** Filter pairings by maximum duty day length threshold
- **Implementation:**
  - New function `parse_max_duty_day_length()` in `edw_reporter.py:105-123`
  - Extracts all duty day lengths from trip text
  - Returns maximum duty day length in hours
  - Added "Max Duty Length" column to trip records
- **UI:**
  - Slider control: 0.0 to max hours, 0.5-hour increments
  - Shows only pairings where longest duty day ≥ threshold
  - Located in "Advanced Filters" section
- **Files:** `edw_reporter.py:105-123, 247-259`, `app.py:120-168`

#### 13. **Legs Per Duty Day Filtering** ✅
- **What:** Filter pairings by maximum number of flight legs in any single duty day
- **Implementation:**
  - New function `parse_max_legs_per_duty_day()` in `edw_reporter.py:126-165`
  - Counts flight legs between Briefing/Debriefing markers
  - Handles variations in flight number format (with/without spaces)
  - Returns maximum legs per duty day across all duty days
  - Added "Max Legs/Duty" column to trip records
- **UI:**
  - Slider control: 0 to max legs, 1-leg increments
  - Shows only pairings where any duty day has ≥ threshold legs
  - Located in "Advanced Filters" section
- **Files:** `edw_reporter.py:126-165, 247-259`, `app.py:136-168`
- **Bug Fix:** Changed regex from `r'\bUPS\s*\d+\s+[A-Z]{3}-[A-Z]{3}\b'` to `r'^\s*UPS\s*\d+\s*$'` to match flight numbers on their own lines

#### 14. **Interactive Trip Details Viewer** ✅
- **What:** Click-to-view detailed pairing information for any trip
- **Approach:** Selectbox dropdown + expandable details panel
- **Implementation:**
  - Modified `run_edw_report()` to return `trip_text_map` dictionary (edw_reporter.py:477)
  - Stores raw trip text indexed by Trip ID
  - Trip text map saved to session state for persistence
- **UI Flow:**
  1. User applies filters to trip records table
  2. Selectbox shows available Trip IDs from filtered results
  3. Select a Trip ID to view full pairing details
  4. Details displayed in expandable panel with formatted table
  5. Optional raw text viewer in nested expander
- **Files:** `edw_reporter.py:176-341, 477`, `app.py:187-361`

#### 15. **Structured Trip Details Parser** ✅
- **What:** Parse raw trip text into structured table format for display
- **Function:** `parse_trip_for_table()` in `edw_reporter.py:176-341`
- **Data Structure:**
  ```python
  {
      'trip_id': int,
      'date_freq': str,  # "(5 trips)" or "Only on Fri 16Jan2026"
      'duty_days': [
          {
              'flights': [
                  {
                      'day': str,        # "1 (Fr)Fr" format
                      'flight': str,     # "UPS 986"
                      'route': str,      # "ONT-BFI"
                      'depart': str,     # "(00)08:40"
                      'arrive': str,     # "(03)11:06"
                      'block': str,      # "2h26"
                      'connection': str  # "1h39"
                  }
              ],
              'duty_time': str,    # "7h44"
              'block_total': str,  # "4h50"
              'credit': str,       # "5h09D"
              'rest': str          # "16h31 S1" or None
          }
      ],
      'trip_summary': {
          'Duty Days': int,
          'Credit': str,
          'Blk': str,
          'TAFB': str,
          ...
      }
  }
  ```
- **Parsing Logic:**
  - Splits text into duty days using "Briefing" markers
  - Extracts flights with day, flight number, route, times, block, connection
  - Captures duty summaries from separate lines (label on one line, value on next)
  - Handles both single-day and multi-day trips
  - Captures layover/rest periods between duty days
- **Files:** `edw_reporter.py:176-341`

#### 16. **HTML Table Display for Trip Details** ✅
- **What:** Renders trip details as formatted HTML table matching PDF bid pack style
- **Table Structure:**
  - Headers: Day | Flight | Dep-Arr | Depart (L) Z | Arrive (L) Z | Blk | Cxn | Duty | Cr | L/O
  - Flight rows grouped by duty day
  - Duty day subtotal rows (grey background)
  - Trip summary footer (blue background)
- **Styling:**
  - Monospace font (Courier New)
  - Bordered cells
  - Color-coded rows (subtotal: #f5f5f5, summary: #d6eaf8)
  - Responsive width
- **Features:**
  - Rowspan for Duty/Cr/L/O columns (one value per duty day)
  - Date/frequency caption at top
  - Collapsible raw text viewer
- **Files:** `app.py:207-355`

#### 17. **Parsing Bug Fixes** ✅

**Bug 1: Flight Numbers Without Spaces**
- **Issue:** "UPS2985" not captured by regex `r'^(UPS|GT)\s'` which required space after UPS
- **Fix:** Changed to `r'^(UPS|GT)'` (removed space requirement)
- **Location:** `edw_reporter.py:227, 255`

**Bug 2: Duplicate Flight Captures**
- **Issue:** Same flight captured twice, insufficient line skipping
- **Fix:** Changed from `i += 1` to `i += 9` to skip past complete flight data block
- **Location:** `edw_reporter.py:251`

**Bug 3: Duty Summary Values Not Captured**
- **Issue:** Labels like "Duty", "Block", "Credit" appear on separate lines from their values
  ```
  Duty
  7h44
  ```
- **Fix:** Modified to check if line equals label exactly, then grab next line's value
- **Code Pattern:**
  ```python
  if line == 'Duty' and i + 1 < len(lines):
      next_line = lines[i + 1].strip()
      if re.match(r'\d+h\d+', next_line):
          current_duty['duty_time'] = next_line
  ```
- **Location:** `edw_reporter.py:280-302`

**Bug 4: Date/Frequency Not Captured for Date-Specific Trips**
- **Issue:** Pattern only matched "(N trips)" but not "Only on Fri 16Jan2026"
- **Fix:** Enhanced regex to also match date patterns
  ```python
  if (re.search(r'\d+\s+trips?\)', line, re.IGNORECASE) or
      re.search(r'Only on|^\d{2}\w{3}\d{4}', line, re.IGNORECASE)):
  ```
- **Location:** `edw_reporter.py:188-191`

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
- `parse_max_duty_day_length()` - Extract maximum duty day length in hours _(New in Session 2)_
- `parse_max_legs_per_duty_day()` - Count maximum flight legs in any duty day _(New in Session 2)_
- `parse_trip_for_table()` - Parse trip into structured format for table display _(New in Session 2)_
- `run_edw_report()` - Main orchestration function (now returns trip_text_map)

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
  - **Advanced filters:** _(New in Session 2)_
    - Max duty day length slider (hours)
    - Max legs per duty day slider
  - **Trip details viewer:** _(New in Session 2)_
    - Selectbox to choose Trip ID
    - Formatted HTML table with all flight details
    - Duty day subtotals and trip summary
    - Raw text viewer in collapsible section
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

## Session 2 Testing Results

### Automated Test Suite
Created comprehensive test scripts to validate parsing:

**Test Files Created:**
- `test_parse_trip.py` - Single-day trip validation (Trip 1/100)
- `test_trip_197.py` - Multi-day trip validation (Trip 197)
- `final_test.py` - Comprehensive test suite
- `find_multiday.py` - Utility to find multi-day trip examples
- `check_all_trips.py` - Duty day distribution analyzer

### Test Results

**Trip 1 (Single Duty Day) - PASS ✅**
- Trip ID: 100
- Date/Frequency: "02Dec2025-10Dec2025 .234... (5 trips)"
- Duty Days: 1
- Flights: 2 (UPS 986, UPS2985)
- All fields populated correctly:
  - Duty time: 7h44
  - Block total: 4h50
  - Credit: 5h09D
  - Flight details: Day, Flight, Route, Depart, Arrive, Block, Connection

**Trip 197 (Multi Duty Day) - PASS ✅**
- Trip ID: 197
- Date/Frequency: "Only on Fri 16Jan2026"
- Duty Days: 2
- Flights: 1 in Day 1, 2 in Day 2
- Day 1 Summary:
  - Duty time: 4h55
  - Block total: 3h40
  - Credit: 4h00M
  - Rest: 16h31 S1 (layover captured correctly)
- Day 2 Summary:
  - Duty time: 8h26
  - Block total: 5h56
  - Credit: 5h56L
  - Rest: None (final day)

**Overall: ALL TESTS PASSED ✅**

Parser correctly handles:
- Single-day trips with multiple flights
- Multi-day trips with layovers
- Date/frequency patterns (both frequency counts and specific dates)
- Duty summaries (duty time, block, credit, rest)
- Flight details (day, flight number, route, times, connections)

### Duty Day Distribution Validation
- Total trips: 272
- Duty day breakdown:
  - 1 day: 100 trips (37%)
  - 2 days: 1 trip (0.4%)
  - 3 days: 4 trips (1.5%)
  - 4 days: 15 trips (5.5%)
  - 5 days: 34 trips (12.5%)
  - 6 days: 53 trips (19.5%)
  - 7 days: 56 trips (20.6%)
  - 8 days: 8 trips (2.9%)
  - 9 days: 1 trip (0.4%)
- Multi-day trips: 172 (63% of all pairings)

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
6. **Trip detail parsing assumptions:** Assumes consistent PDF formatting
   - Flight data must be in specific order (day, flight number, route, times, etc.)
   - May fail on non-standard pairing formats
7. **No bulk export of trip details:** Can only view one trip at a time
   - Cannot export all trip details to Excel/CSV

### Session 2 Accomplishments ✅
- ~~**Advanced Filters:** Filter by TAFB range, specific duty day counts, etc.~~
  - ✅ **Implemented:** Max duty day length filter (hours)
  - ✅ **Implemented:** Max legs per duty day filter
- ~~**Trip Detail View:** Click to see full pairing information~~
  - ✅ **Implemented:** Interactive trip details viewer with selectbox
  - ✅ **Implemented:** Formatted HTML table display
  - ✅ **Implemented:** Raw text viewer

### Session 4 Accomplishments ✅
- ~~**Trip Summary Display:** Show complete trip summary data in pairing details~~
  - ✅ **Implemented:** All 10 trip summary fields parsed and displayed
  - ✅ **Implemented:** Structured 2-row table format
  - ✅ **Implemented:** Crew, Domicile, Credit Time, Block Time, Duty Time, TAFB, Premium, Per Diem, LDGS, Duty Days

### Future Enhancement Ideas
1. **Batch Processing:** Upload multiple PDFs and compare results
2. **Historical Tracking:** Store and track EDW percentages over time
3. **Custom EDW Window:** Allow users to define custom time windows
4. **Export to CSV:** Individual downloadable CSV files for each sheet
5. **Email Reports:** Send generated reports via email
6. **API Integration:** Connect to airline scheduling systems
7. **User Accounts:** Save preferences and history
8. **Enhanced Trip Details:**
   - Bulk export all trip details to Excel with formatted tables
   - Side-by-side comparison of multiple trips
   - Search/filter within trip details (e.g., find all ONT-BFI flights)
9. **Chart Customization:** Allow users to choose chart types and colors
10. **Mobile Optimization:** Improve responsive design for tablets/phones
11. **Advanced Filtering:**
   - Filter by specific airports (origin/destination)
   - Filter by time of day (early morning, late night, etc.)
   - Filter by credit range
   - Filter by TAFB range
   - Combine multiple filters with AND/OR logic

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

### Trip Detail Parsing Logic (Session 2)
- **Entry Point:** `parse_trip_for_table()` function
- **Input:** Raw trip text string from PDF
- **Output:** Structured dictionary with duty days, flights, and summaries
- **Algorithm:**
  1. Split text into lines
  2. Find date/frequency line (matches "(N trips)" or "Only on..." patterns)
  3. Iterate through lines looking for "Briefing" markers (start of duty day)
  4. Within each duty day:
     - Look for day indicator pattern: `\d+\s+\(` (e.g., "1 (Fr)Fr")
     - Next line should be flight number: `^(UPS|GT)` (e.g., "UPS 986")
     - Extract flight details from following lines (route, times, block, connection)
     - Skip 9 lines to avoid duplicate captures
  5. Capture duty summary values from separate lines:
     - Line equals "Duty" → next line is duty time (e.g., "7h44")
     - Line equals "Block" → next line is block total
     - Line equals "Credit" → next line is credit value
     - Line equals "Rest" → next line is rest/layover time
  6. Parse trip summary at end for TAFB, total credit, etc.
- **Critical Details:**
  - Flight numbers may or may not have spaces (UPS 986 vs UPS2985)
  - Labels and values often on separate lines
  - Rest/layover only appears between duty days, not on final day
  - Day indicators show both local and Zulu days: "(local)zulu" format

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

### Commit 3 (Session 2): "Add advanced filtering and trip details viewer"
- Added max duty day length filtering
- Added max legs per duty day filtering
- Implemented interactive trip details viewer with selectbox
- Created structured trip parsing (`parse_trip_for_table()`)
- Built HTML table display for pairing details
- Fixed multiple parsing bugs:
  - Flight numbers without spaces
  - Duplicate flight captures
  - Duty summary values on separate lines
  - Date/frequency pattern matching
- Added comprehensive test suite

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
- **Max duty length:** `parse_max_duty_day_length(trip_text)` _(New in Session 2)_
- **Max legs per duty:** `parse_max_legs_per_duty_day(trip_text)` _(New in Session 2)_
- **Parse for table:** `parse_trip_for_table(trip_text)` _(New in Session 2, enhanced in Session 4 with trip summary parsing)_

### Testing
- **Test PDF:** `BID2601_757_ONT_TRIPS_CAROL.pdf` (not in repo)
- **Expected results:** 272 pairings, 522 trips, 46.4% EDW
- **Test scripts:** _(Session 2)_
  - `final_test.py` - Comprehensive validation (single + multi-day trips)
  - `test_parse_trip.py` - Trip 1 validation
  - `test_trip_197.py` - Multi-day trip validation
  - `check_all_trips.py` - Duty day distribution
  - `find_multiday.py` - Find multi-day examples

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

---

## Session 2 Summary

### What Was Accomplished
This session focused on **advanced filtering and interactive trip exploration**:

1. **Advanced Filtering Capabilities:**
   - Filter by maximum duty day length (hours)
   - Filter by maximum legs per duty day
   - Both filters work seamlessly with existing EDW and Hot Standby filters

2. **Interactive Trip Details Viewer:**
   - Click any Trip ID to view complete pairing information
   - Formatted HTML table matching PDF bid pack style
   - Shows all flights, duty summaries, layovers, and trip totals
   - Optional raw text viewer for debugging

3. **Robust Parsing Engine:**
   - Created `parse_trip_for_table()` function with comprehensive parsing logic
   - Handles both single-day and multi-day trips
   - Captures layover/rest periods between duty days
   - Supports multiple date/frequency formats

4. **Quality Assurance:**
   - Built comprehensive test suite (5 test scripts)
   - Validated parsing with both simple and complex trips
   - All tests passing (single-day, multi-day, layovers, summaries)

### Files Modified
- `edw_reporter.py` - Added 3 new functions, 4 bug fixes
- `app.py` - Added advanced filters and trip details viewer
- `HANDOFF.md` - Updated with Session 2 documentation

### Files Created
- `test_parse_trip.py` - Single-day trip test
- `test_trip_197.py` - Multi-day trip test
- `final_test.py` - Comprehensive test suite
- `check_all_trips.py` - Duty day distribution analyzer
- `find_multiday.py` - Multi-day trip finder

### Next Session Recommendations

**Potential Enhancements:**
1. **Export trip details to Excel** - Add ability to export all trip details to formatted Excel sheets
2. **Airport-based filtering** - Filter by specific origin/destination airports
3. **Time-based filtering** - Filter by departure/arrival time ranges
4. **Trip comparison** - Side-by-side comparison of multiple trips
5. **Search functionality** - Search across all trips for specific routes or patterns

**Code Cleanup:**
1. Consider removing test scripts before production deployment (or move to `tests/` directory)
2. Add error handling for malformed trip text
3. Consider caching parsed trip details to improve performance

**Testing:**
1. Test with different bid pack PDFs to ensure parsing robustness
2. Validate with extremely long trips (9+ duty days)
3. Test with non-standard pairing formats (if they exist)

---