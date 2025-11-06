# Phase 3: EDW Pairing Analyzer - Implementation Plan

**Phase Duration:** 80 hours (budgeted)
**Timeline:** Weeks 5-6
**Risk Level:** 🟡 MEDIUM
**Priority:** 🔴 HIGH
**Status:** 🚧 IN PROGRESS

---

## Overview

Phase 3 implements the EDW (Early/Day/Window) Pairing Analyzer tab, migrating the functionality from Streamlit Tab 1. This phase builds on the authentication and infrastructure foundation established in Phase 1.

**Key Deliverables:**
- PDF upload with progress tracking
- EDW trip analysis and statistics
- Interactive filtering UI
- Plotly visualizations
- Trip details viewer
- Excel and PDF report generation
- Database save functionality

---

## Implementation Progress

### Task 3.1: EDW State Management (3 days) ✅ COMPLETE

**Files Created:**
- `/reflex_app/edw/edw_state.py` (370 lines)
- `/reflex_app/edw/__init__.py`

**Features Implemented:**
- [x] Upload state management (file name, progress, errors)
- [x] Header information storage (domicile, aircraft, bid period, etc.)
- [x] Results state (trip counts, weighted metrics, detailed data)
- [x] Filter state (duty day, trip length, legs, EDW status)
- [x] Computed variables (`filtered_trips`, `has_results`, etc.)
- [x] Event handlers (`handle_upload`, `reset_filters`, `save_to_database`)
- [x] Progress callback integration
- [x] Duty day criteria matching logic

**Testing Status:** ⏳ Pending (requires UI components)

---

### Task 3.2: PDF Upload Component (2 days) 🚧 IN PROGRESS

**Target File:** `/reflex_app/edw/components/upload.py`

**Features to Implement:**
- [ ] File upload with drag-and-drop support
- [ ] File type validation (PDF only)
- [ ] Progress bar during processing
- [ ] Error message display
- [ ] Success confirmation

**Dependencies:**
- EDW State (✅ Complete)
- POC 2 file upload patterns (✅ Validated)

**Estimated Completion:** Session 25

---

### Task 3.3: Header Information Display (1 day) ⏳ PENDING

**Target File:** `/reflex_app/edw/components/header.py`

**Features to Implement:**
- [ ] Info card showing extracted metadata
- [ ] Bid period, domicile, fleet type display
- [ ] Date range and report date
- [ ] Responsive layout

**Dependencies:**
- EDW State (✅ Complete)

**Estimated Completion:** Session 25

---

### Task 3.4: Results Display Components (3 days) ⏳ PENDING

**Target Files:**
- `/reflex_app/edw/components/summary.py`
- `/reflex_app/edw/components/weighted_metrics.py`
- `/reflex_app/edw/components/duty_day_stats.py`

**Features to Implement:**
- [ ] Trip summary statistics cards (unique, total, EDW, day, hot standby)
- [ ] Weighted metrics display (trip-weighted, TAFB-weighted, duty-day-weighted)
- [ ] Duty day statistics table
- [ ] Hot standby summary
- [ ] Responsive grid layout

**Dependencies:**
- EDW State (✅ Complete)

**Estimated Completion:** Session 25-26

---

### Task 3.5: Duty Day Distribution Charts (2 days) ⏳ PENDING

**Target File:** `/reflex_app/edw/components/charts.py`

**Features to Implement:**
- [ ] Plotly bar chart for duty days vs trips
- [ ] Plotly bar chart for duty days vs percentage
- [ ] Toggle to exclude 1-day trips (turns)
- [ ] Chart responsiveness
- [ ] Interactive hover tooltips

**Dependencies:**
- EDW State (✅ Complete)
- POC 3 Plotly integration (✅ Validated)

**Estimated Completion:** Session 26

---

### Task 3.6: Filtering UI (2 days) ⏳ PENDING

**Target Files:**
- `/reflex_app/edw/components/filters.py`

**Features to Implement:**
- [ ] Max duty day length slider
- [ ] Max legs per duty slider
- [ ] Duty day criteria filters (duration, legs, EDW status)
- [ ] Match mode selector (Any/All duty days)
- [ ] EDW status filter (All/EDW Only/Day Only)
- [ ] Hot Standby filter
- [ ] Sort by selector
- [ ] Reset filters button
- [ ] Active filter count display

**Dependencies:**
- EDW State (✅ Complete)

**Estimated Completion:** Session 26

---

### Task 3.7: Trip Details Viewer (2 days) ⏳ PENDING

**Target File:** `/reflex_app/edw/components/trip_details.py`

**Features to Implement:**
- [ ] Trip ID selector dropdown
- [ ] Duty day breakdown table (HTML/styled)
- [ ] Flight details (day, flight, route, times)
- [ ] Subtotal rows per duty day
- [ ] Trip summary section
- [ ] Raw text toggle
- [ ] Responsive width constraint (50%/80%/100%)

**Dependencies:**
- EDW State (✅ Complete)
- Filtered trips list

**Estimated Completion:** Session 27

---

### Task 3.8: Trip Records Table (1 day) ⏳ PENDING

**Target File:** `/reflex_app/edw/components/trip_table.py`

**Features to Implement:**
- [ ] Data table with filtered trips
- [ ] Columns: Trip ID, Frequency, TAFB, Duty Days, Max Duty, Max Legs, EDW, Hot Standby
- [ ] Sortable columns
- [ ] Row count display
- [ ] Responsive design

**Dependencies:**
- EDW State (✅ Complete)
- Filtered trips computed var

**Estimated Completion:** Session 27

---

### Task 3.9: Export Functionality (3 days) ⏳ PENDING

**Target Files:**
- `/reflex_app/edw/components/exports.py`
- Integration with existing `edw_reporter.py` and `export_pdf.py`

**Features to Implement:**
- [ ] Excel download button
- [ ] PDF download button
- [ ] File generation using existing logic
- [ ] Download file naming (domicile_aircraft_bidXXXX_EDW_Report.xlsx/pdf)
- [ ] Loading states during generation

**Dependencies:**
- EDW State (✅ Complete)
- Results data available

**Estimated Completion:** Session 28

---

### Task 3.10: Database Save Feature (2 days) ⏳ PENDING

**Target File:** `/reflex_app/edw/components/save.py`

**Features to Implement:**
- [ ] "Save to Database" button
- [ ] Duplicate detection warning
- [ ] Overwrite confirmation dialog
- [ ] Success/error message display
- [ ] Save progress indicator
- [ ] Integration with database state

**Dependencies:**
- EDW State (✅ Complete)
- Database schema ready
- Authentication working (✅ Complete)

**Estimated Completion:** Session 28

---

### Task 3.11: Main EDW Page Integration (2 days) ⏳ PENDING

**Target File:** `/reflex_app/edw/page.py`

**Features to Implement:**
- [ ] Compose all components into main page
- [ ] Tab navigation integration
- [ ] Page routing
- [ ] Layout and spacing
- [ ] Protected route decorator
- [ ] Loading states
- [ ] Error boundaries

**Dependencies:**
- All EDW components (Tasks 3.2-3.10)

**Estimated Completion:** Session 29

---

### Task 3.12: Integration Testing (2 days) ⏳ PENDING

**Test Scenarios:**
- [ ] Upload valid pairing PDF → Analysis succeeds
- [ ] Upload invalid PDF → Error displayed
- [ ] Apply filters → Trip count updates correctly
- [ ] Select trip ID → Details display correctly
- [ ] Download Excel → File generates successfully
- [ ] Download PDF → File generates successfully
- [ ] Save to database → Data persists correctly
- [ ] Reset filters → All filters clear
- [ ] Responsive design → Works on mobile/tablet
- [ ] Cross-browser → Chrome, Firefox, Safari

**Deliverable:** Test report with screenshots

**Estimated Completion:** Session 29

---

## Acceptance Criteria

### Functional Requirements
- [x] State management handles all EDW data
- [ ] PDF upload works with progress tracking
- [ ] Header extraction displays correct metadata
- [ ] All statistics calculate correctly (trip-weighted, TAFB-weighted, duty-day-weighted)
- [ ] Plotly charts render and are interactive
- [ ] All filters work correctly (duty day, trip length, legs, EDW status)
- [ ] Trip details table displays correctly with responsive width
- [ ] Excel export generates correct workbook
- [ ] PDF export generates correct report
- [ ] Database save works with duplicate detection
- [ ] Error handling displays user-friendly messages

### Non-Functional Requirements
- [ ] Page load time < 2 seconds
- [ ] PDF processing time ≤ Streamlit version
- [ ] Interaction response < 500ms
- [ ] Mobile responsive design
- [ ] Accessible (keyboard navigation, screen readers)

---

## Dependencies

### Completed
- ✅ Phase 0: POC Testing (All POCs passed)
- ✅ Phase 1: Authentication & Infrastructure
- ✅ POC 2: File Upload (PyPDF2 integration validated)
- ✅ POC 3: Plotly Charts (All chart types working)

### External
- `/edw_reporter.py` (Streamlit version, reusable)
- `/export_pdf.py` (PDF generation logic, reusable)
- `PyPDF2` library (PDF parsing)
- `reportlab` library (PDF generation)
- `openpyxl` library (Excel generation)

---

## Risks & Mitigation

### Risk 1: PyPDF2 Async Compatibility
**Status:** 🟢 LOW
**Mitigation:** Wrap synchronous PDF processing in async handler (established pattern)

### Risk 2: Large PDF Processing Time
**Status:** 🟡 MEDIUM
**Mitigation:**
- Show progress bar during processing
- Implement background task if needed
- POC 2 validated performance is acceptable

### Risk 3: Chart Responsiveness
**Status:** 🟢 LOW
**Mitigation:** Use Plotly's responsive layout options (validated in POC 3)

### Risk 4: Trip Details Table Complexity
**Status:** 🟡 MEDIUM
**Mitigation:**
- Reuse Streamlit HTML table structure
- Use rx.html() for custom HTML rendering
- Test on multiple screen sizes

---

## Timeline

| Week | Task | Status |
|------|------|--------|
| Session 24 | Task 3.1: EDW State | ✅ Complete |
| Session 25 | Tasks 3.2-3.4: Upload, Header, Results | 🚧 In Progress |
| Session 26 | Tasks 3.5-3.6: Charts, Filters | ⏳ Pending |
| Session 27 | Tasks 3.7-3.8: Trip Details, Trip Table | ⏳ Pending |
| Session 28 | Tasks 3.9-3.10: Exports, Database Save | ⏳ Pending |
| Session 29 | Tasks 3.11-3.12: Integration, Testing | ⏳ Pending |

**Total Estimated Time:** 80 hours (6 sessions @ ~13 hours each)

---

## Success Metrics

### Code Quality
- [ ] All components have type hints
- [ ] Comprehensive error handling
- [ ] Clear documentation/docstrings
- [ ] No circular import issues

### Performance
- [ ] PDF processing < 5 seconds for typical PDF (50 pages)
- [ ] Chart rendering < 1 second
- [ ] Filter application < 500ms
- [ ] Page load < 2 seconds

### User Experience
- [ ] Clear loading states
- [ ] Helpful error messages
- [ ] Intuitive navigation
- [ ] Responsive on all devices

---

## Next Steps

**Current Session (24):**
1. ✅ Create EDW State management class
2. 🚧 Begin Task 3.2: PDF Upload Component

**Next Session (25):**
1. Complete Tasks 3.2-3.4 (Upload, Header, Results Display)
2. Begin Task 3.5 (Charts)

---

**Last Updated:** 2025-11-05, Session 24
**Phase Owner:** Claude Code
**Status:** 🚧 IN PROGRESS (10% complete)
