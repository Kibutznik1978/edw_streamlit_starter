# Reflex Migration Implementation Phases

## Overview

This document outlines a 6-phase approach to migrating the Streamlit application to Reflex.dev. Each phase builds on the previous, with clearly defined deliverables and acceptance criteria.

**Estimated Total Duration**: 8-12 weeks (1 developer)

---

## Phase 0: Project Setup & Architecture (Week 1)

### Goals
- Initialize Reflex project structure
- Configure shared backend modules
- Set up development environment
- Create proof-of-concept for critical components

### Tasks

#### 0.1 - Reflex Project Initialization (2 days)
```bash
# Create Reflex project
cd edw_streamlit_starter
reflex init

# Reorganize directory structure
mkdir -p reflex_app/{pages,components,state}
mkdir -p shared
mv edw/ shared/
mv pdf_generation/ shared/
mv config/ shared/
mv models/ shared/
mv database.py auth.py bid_parser.py shared/
```

**Deliverable**: Working Reflex "Hello World" app

#### 0.2 - Backend Module Integration (2 days)
- Update import paths in shared modules
- Test that backend modules work independently (unit tests)
- Verify PDF parsing, Excel generation, Plotly chart generation

**Deliverable**: All backend modules importable from Reflex context

#### 0.3 - Critical Component Prototypes (3 days)
Build proof-of-concept for high-risk components:
1. **Data Editor POC**: Test `rx.data_editor()` or build custom editable table
2. **File Upload POC**: Test async PDF upload and processing
3. **Plotly Integration POC**: Verify `rx.plotly()` works with existing charts
4. **JWT Auth POC**: Test Supabase auth with Reflex State classes

**Deliverable**: Working prototypes demonstrating feasibility

**Decision Point**: If data editor POC fails, plan custom implementation before proceeding.

#### 0.4 - Development Environment (1 day)
- Configure hot reload for Reflex
- Set up debugging tools
- Create development `.env` file
- Document development workflow

**Deliverable**: Developer documentation for running Reflex app

### Acceptance Criteria
- [ ] Reflex app starts without errors
- [ ] All backend modules import successfully
- [ ] Critical component POCs demonstrate viability
- [ ] Development environment documented

### Risks & Mitigation
- **Risk**: Data editor doesn't meet requirements
  - **Mitigation**: Budget 1 week for custom implementation
- **Risk**: PDF processing is too slow in async context
  - **Mitigation**: Implement background task queue

---

## Phase 1: Authentication & Database Foundation (Week 2)

### Goals
- Implement Supabase authentication in Reflex
- Create base State classes for app-wide state
- Establish JWT session handling pattern
- Build reusable auth UI components

### Tasks

#### 1.1 - Auth State Class (2 days)
```python
# reflex_app/state/auth.py
class AuthState(rx.State):
    jwt_token: str = ""
    user_email: str = ""
    user_id: str = ""
    is_authenticated: bool = False
    is_admin: bool = False

    def get_supabase_client(self):
        """Returns Supabase client with JWT session"""
        # Reuse logic from shared/database.py
        pass

    async def login(self, email: str, password: str):
        """Handle login with Supabase Auth"""
        pass

    async def signup(self, email: str, password: str):
        """Handle user registration"""
        pass

    def logout(self):
        """Clear session and redirect"""
        pass

    @rx.var
    def jwt_claims(self) -> dict:
        """Decode JWT for debugging"""
        pass
```

**Deliverable**: Working auth State class with Supabase integration

#### 1.2 - Auth UI Components (2 days)
Build reusable components:
- `LoginForm` - Email/password login
- `SignupForm` - New user registration
- `AuthHeader` - User info display with logout button
- `ProtectedRoute` - Wrapper for authenticated pages

**Deliverable**: Reusable auth components

#### 1.3 - Database Query Helpers (2 days)
Create State methods for common database operations:
```python
class DatabaseState(AuthState):
    """Extends AuthState to access JWT token"""

    async def save_pairing_data(self, data: dict):
        client = self.get_supabase_client()
        # Use existing save_pairing_data_to_db logic
        pass

    async def query_pairings(self, filters: dict):
        client = self.get_supabase_client()
        # Use existing query logic
        pass
```

**Deliverable**: Database State class with save/query methods

#### 1.4 - Testing & Validation (1 day)
- Test login/logout flow
- Verify JWT claims are set correctly
- Test RLS policy enforcement
- Validate admin vs regular user permissions

**Deliverable**: Passing test suite for auth and database operations

### Acceptance Criteria
- [ ] Users can log in and log out
- [ ] JWT token is correctly set and persists across page navigation
- [ ] Supabase RLS policies enforce access control
- [ ] Admin users can be identified
- [ ] Database save operations work with audit fields

### Dependencies
- Phase 0 complete
- Supabase project configured (already done)

### Risks & Mitigation
- **Risk**: JWT session handling differs from Streamlit
  - **Mitigation**: Extensive testing with mock scenarios
- **Risk**: RLS policies fail with Reflex-generated tokens
  - **Mitigation**: Debug with JWT claims viewer component

---

## Phase 2: Database Explorer Tab (Weeks 3-4)

### Goals
- Migrate simplest tab first to establish patterns
- Implement multi-dimensional filtering
- Build paginated data table
- Create export functionality

**Rationale**: Database Explorer is the simplest tab (no PDF upload, minimal state complexity). Success here validates the architecture before tackling harder tabs.

### Tasks

#### 2.1 - Filter State Management (3 days)
```python
class QueryState(rx.State):
    # Filter state
    selected_domiciles: list[str] = []
    selected_aircraft: list[str] = []
    selected_seats: list[str] = []
    selected_bid_periods: list[str] = []
    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None
    data_type: str = "Pairings"  # or "Bid Lines"

    # Results state
    results: list[dict] = []
    total_records: int = 0
    current_page: int = 1
    page_size: int = 50
    is_loading: bool = False

    # Computed vars
    @rx.var
    def total_pages(self) -> int:
        return (self.total_records + self.page_size - 1) // self.page_size

    @rx.var
    def paginated_results(self) -> list[dict]:
        start = (self.current_page - 1) * self.page_size
        end = start + self.page_size
        return self.results[start:end]

    # Event handlers
    async def execute_query(self):
        self.is_loading = True
        # Use shared/database.py query functions
        pass

    def set_page(self, page: int):
        self.current_page = page

    def reset_filters(self):
        # Reset all filters to defaults
        pass
```

**Deliverable**: Filter State class with query logic

#### 2.2 - Filter UI Components (3 days)
Build filter sidebar:
- Multi-select for domiciles, aircraft, seats, bid periods
- Date range picker
- Quick date filter buttons (Last 3 months, Last 6 months, etc.)
- Data type selector (Pairings / Bid Lines)
- "Reset Filters" button
- Filter summary display ("X filters active")

**Deliverable**: Complete filter sidebar component

#### 2.3 - Results Table & Pagination (3 days)
- Build data table with dynamic columns based on data type
- Implement pagination controls (prev/next, page selector)
- Add row selection for detail view
- Show loading spinner during queries

**Deliverable**: Working paginated results table

#### 2.4 - Record Detail Viewer (2 days)
- Modal or expandable panel for record details
- JSON display with syntax highlighting
- Copy to clipboard button

**Deliverable**: Record detail viewer component

#### 2.5 - Export Functionality (2 days)
- CSV export button (reuse existing logic)
- Excel export button (future)
- PDF export button (future)

**Deliverable**: CSV export working

#### 2.6 - Integration & Testing (2 days)
- Test with various filter combinations
- Verify pagination with large result sets
- Test export with filtered data
- Responsive design testing

**Deliverable**: Fully functional Database Explorer page

### Acceptance Criteria
- [ ] All filters work correctly
- [ ] Queries return correct results based on filters
- [ ] Pagination works with large datasets (1000+ records)
- [ ] Record detail viewer displays all fields
- [ ] CSV export includes filtered data
- [ ] Page is responsive on mobile devices
- [ ] Loading states are clear to users

### Dependencies
- Phase 1 complete (auth and database state)

### Risks & Mitigation
- **Risk**: Query performance with complex filters
  - **Mitigation**: Database indexes already in place, test with large datasets
- **Risk**: Data table performance with 1000+ rows
  - **Mitigation**: Implement pagination (already planned)

---

## Phase 3: EDW Pairing Analyzer Tab (Weeks 5-6)

### Goals
- Migrate Tab 1 (EDW Pairing Analyzer)
- Implement PDF upload and processing
- Build filtering UI (duty day criteria, trip length, legs)
- Create visualizations (Plotly charts)
- Add Excel and PDF export

### Tasks

#### 3.1 - EDW State Management (3 days)
```python
class EDWState(AuthState):
    # Upload state
    uploaded_file_name: str = ""
    is_processing: bool = False
    processing_progress: int = 0

    # Header info
    domicile: str = ""
    aircraft: str = ""
    bid_period: str = ""

    # Results state
    trips: list[dict] = []
    edw_statistics: dict = {}
    duty_day_stats: dict = {}

    # Filter state
    filter_duty_day_min: Optional[float] = None
    filter_duty_day_max: Optional[float] = None
    filter_trip_length_min: Optional[int] = None
    filter_trip_length_max: Optional[int] = None
    filter_legs_min: Optional[int] = None
    filter_legs_max: Optional[int] = None

    # Computed vars
    @rx.var
    def filtered_trips(self) -> list[dict]:
        # Apply filters to trips
        pass

    @rx.var
    def total_edw_trips(self) -> int:
        return len([t for t in self.filtered_trips if t['is_edw']])

    # Event handlers
    async def process_pdf(self, files: list[rx.UploadFile]):
        self.is_processing = True
        try:
            for file in files:
                data = await file.read()
                # Use shared/edw/reporter.py
                from shared.edw import run_edw_report
                results = run_edw_report(data, progress_callback=self.update_progress)
                self.trips = results['trips']
                self.edw_statistics = results['statistics']
                # ... populate other fields
        finally:
            self.is_processing = False

    def update_progress(self, progress: int):
        self.processing_progress = progress

    async def generate_excel(self):
        # Use shared/edw/excel_export.py
        pass

    async def generate_pdf(self):
        # Use shared/pdf_generation/edw_pdf.py
        pass

    async def save_to_database(self):
        # Use save_pairing_data_to_db from DatabaseState
        pass
```

**Deliverable**: EDW State class with full workflow

#### 3.2 - PDF Upload Component (2 days)
- File upload with drag-and-drop
- Progress bar during processing
- Automatic header extraction display
- Error handling for wrong PDF type

**Deliverable**: Working PDF upload component

#### 3.3 - Results Display Components (3 days)
- EDW statistics cards (total trips, EDW trips, percentages)
- Weighted metrics display (trip-weighted, TAFB-weighted, duty-day-weighted)
- Duty day distribution table
- Trip length distribution chart (Plotly bar chart)

**Deliverable**: Results visualization components

#### 3.4 - Filtering UI (2 days)
- Duty day criteria sliders (min/max hours, match mode)
- Trip length filter (number of days)
- Legs filter (number of segments)
- "Reset Filters" button
- Active filter summary

**Deliverable**: Filter sidebar for EDW tab

#### 3.5 - Trip Details Viewer (2 days)
- Expandable trip details table
- Duty day breakdown
- Responsive width constraint (60% on desktop)

**Deliverable**: Trip details component

#### 3.6 - Export & Database Save (3 days)
- Excel download button (uses existing excel_export.py)
- PDF download button (uses existing edw_pdf.py)
- "Save to Database" button with success/error messages
- Duplicate detection and replace workflow

**Deliverable**: All export and save functionality working

#### 3.7 - Integration & Testing (2 days)
- Test with various PDF formats (modern and older)
- Verify all charts render correctly
- Test filters with edge cases
- Test database save with duplicates
- Responsive design testing

**Deliverable**: Fully functional EDW Pairing Analyzer page

### Acceptance Criteria
- [ ] PDF upload works with progress indicator
- [ ] Header extraction displays correct metadata
- [ ] All EDW statistics calculate correctly
- [ ] Weighted metrics match Streamlit version
- [ ] Plotly charts render and are interactive
- [ ] Filters work correctly (duty day, trip length, legs)
- [ ] Trip details table is responsive
- [ ] Excel export generates correct workbook
- [ ] PDF export generates correct report
- [ ] Database save works with duplicate detection
- [ ] Error handling works for invalid PDFs

### Dependencies
- Phase 1 complete (auth and database)
- Phase 2 complete (establishes UI patterns)

### Risks & Mitigation
- **Risk**: PyPDF2 async compatibility issues
  - **Mitigation**: Wrap synchronous PDF processing in async handler
- **Risk**: Chart generation is slow
  - **Mitigation**: Show spinner during chart creation
- **Risk**: Large PDFs cause timeout
  - **Mitigation**: Implement background task processing with status polling

---

## Phase 4: Bid Line Analyzer Tab (Weeks 7-9)

### Goals
- Migrate Tab 2 (Bid Line Analyzer)
- Implement interactive data editor (critical challenge)
- Build pay period analysis
- Create distribution charts
- Add validation and change tracking

**Note**: This is the most complex tab due to the data editor requirement.

### Tasks

#### 4.1 - Bid Line State Management (4 days)
```python
class BidLineState(AuthState):
    # Upload state
    uploaded_file_name: str = ""
    is_processing: bool = False

    # Header info
    domicile: str = ""
    aircraft: str = ""
    bid_period: str = ""
    date_range: str = ""

    # Data state
    original_data: pd.DataFrame = pd.DataFrame()  # Never modified
    edited_data: pd.DataFrame = pd.DataFrame()    # Contains user edits
    reserve_lines: list[dict] = []

    # Filter state
    filter_ct_min: float = 0.0
    filter_ct_max: float = 200.0
    filter_bt_min: float = 0.0
    filter_bt_max: float = 200.0
    filter_do_min: int = 0
    filter_do_max: int = 31
    filter_dd_min: int = 0
    filter_dd_max: int = 31

    # Edit tracking
    edited_cells: list[dict] = []  # Track changes
    validation_errors: list[str] = []

    # Computed vars
    @rx.var
    def filtered_data(self) -> pd.DataFrame:
        # Apply filters to edited_data
        pass

    @rx.var
    def has_edits(self) -> bool:
        return len(self.edited_cells) > 0

    @rx.var
    def statistics(self) -> dict:
        # Calculate CT/BT/DO/DD statistics from filtered_data
        pass

    # Event handlers
    async def process_pdf(self, files: list[rx.UploadFile]):
        # Use shared/bid_parser.py
        pass

    def update_cell(self, row_idx: int, col_name: str, new_value: Any):
        """Handle inline cell edit"""
        old_value = self.edited_data.at[row_idx, col_name]
        self.edited_data.at[row_idx, col_name] = new_value

        # Track change
        self.edited_cells.append({
            'row': row_idx,
            'column': col_name,
            'old': old_value,
            'new': new_value
        })

        # Validate
        self.validate_edits()

    def validate_edits(self):
        """Validate edited data against rules"""
        errors = []
        # Check: BT > CT
        # Check: DO + DD > 31
        # Check: Values in valid ranges
        self.validation_errors = errors

    def reset_edits(self):
        """Revert to original data"""
        self.edited_data = self.original_data.copy()
        self.edited_cells = []
        self.validation_errors = []
```

**Deliverable**: Bid Line State class with edit tracking

#### 4.2 - Interactive Data Editor Component (5 days)

**Critical Decision**: Choose implementation approach based on Phase 0 POC.

**Option A: Use rx.data_editor() (if available)**
```python
rx.data_editor(
    data=BidLineState.edited_data,
    columns=["Line", "CT", "BT", "DO", "DD"],
    editable_columns=["CT", "BT", "DO", "DD"],
    on_cell_edit=BidLineState.update_cell
)
```

**Option B: Custom Implementation with rx.data_table()**
```python
# Use rx.data_table() with click handlers
# Open modal dialog for cell editing
# More work but full control

def editable_table():
    return rx.data_table(
        data=BidLineState.edited_data,
        columns=[
            {"field": "Line", "editable": False},
            {"field": "CT", "editable": True},
            # ...
        ],
        on_cell_click=lambda row, col: open_edit_modal(row, col)
    )

def edit_modal():
    return rx.dialog(
        rx.input(value=BidLineState.edit_modal_value),
        rx.button("Save", on_click=BidLineState.save_edit),
        is_open=BidLineState.is_edit_modal_open
    )
```

**Deliverable**: Working interactive data editor

#### 4.3 - Change Tracking UI (2 days)
- Visual indicator when data is edited ("✏️ X changes")
- "View edited cells" expander with before/after comparison
- Validation warning display
- "Reset to Original" button

**Deliverable**: Change tracking components

#### 4.4 - Filter Sidebar (2 days)
- CT, BT, DO, DD range sliders
- "Filters active" detection
- Filter summary display
- "Reset Filters" button

**Deliverable**: Filter sidebar matching Streamlit version

#### 4.5 - Statistics Display (3 days)
- Basic statistics grid (CT, BT, DO, DD min/max/mean/median)
- Pay period comparison (PP1 vs PP2)
- Reserve line summary (Captain/FO slots)
- Smart reserve line filtering for charts

**Deliverable**: Statistics components

#### 4.6 - Distribution Charts (3 days)
- CT distribution (5-hour buckets)
- BT distribution (5-hour buckets)
- DO distribution (day buckets)
- DD distribution (day buckets)
- Pay period breakdown (PP1 vs PP2 individual distributions)
- All charts use Plotly with consistent styling

**Deliverable**: All distribution charts working

#### 4.7 - Export & Database Save (3 days)
- CSV download (includes manual edits)
- PDF download (uses existing bid_line_pdf.py)
- Excel download (future)
- "Save to Database" with duplicate detection

**Deliverable**: All export and save functionality

#### 4.8 - Integration & Testing (3 days)
- Test data editor with various edit scenarios
- Verify validation rules work correctly
- Test filters with edge cases
- Verify pay period analysis
- Test exports include edited data
- Responsive design testing

**Deliverable**: Fully functional Bid Line Analyzer page

### Acceptance Criteria
- [ ] PDF upload and parsing works with pdfplumber
- [ ] Data editor allows inline cell editing
- [ ] Edited values are validated (BT>CT, DO+DD≤31, etc.)
- [ ] Change tracking displays edited cells
- [ ] Filters work correctly (CT, BT, DO, DD ranges)
- [ ] Statistics calculate correctly (exclude reserve lines appropriately)
- [ ] Pay period comparison displays correctly
- [ ] All distribution charts render (with 5-hour buckets for CT/BT)
- [ ] Pay period breakdown shows individual PP1/PP2 distributions
- [ ] CSV export includes manual edits
- [ ] PDF export generates correct report
- [ ] Database save works with audit fields
- [ ] Split VTO lines handled correctly (one period regular, one VTO)

### Dependencies
- Phase 1 complete (auth and database)
- Phase 3 complete (PDF upload patterns established)

### Risks & Mitigation
- **Risk**: Data editor is too complex to implement in Reflex
  - **Mitigation**: Fallback to modal-based editing if inline editing fails
- **Risk**: Change tracking breaks with large datasets
  - **Mitigation**: Optimize comparison logic, use diffing library
- **Risk**: pdfplumber async compatibility issues
  - **Mitigation**: Same as Phase 3 - wrap in async handler

---

## Phase 5: Historical Trends Tab (Week 10)

### Goals
- Create placeholder Historical Trends tab
- Establish framework for future visualizations
- Plan Phase 6 enhancements

### Tasks

#### 5.1 - Placeholder Page (2 days)
- Create tab structure
- Add "Coming Soon" messaging
- Outline planned features:
  - Trend charts (EDW percentage over time)
  - Multi-bid-period comparisons
  - Anomaly detection
  - Forecasting

**Deliverable**: Placeholder page with planned feature list

#### 5.2 - Framework Planning (2 days)
- Design State structure for trend analysis
- Plan query patterns for time-series data
- Select visualization libraries (Plotly time series)
- Document future implementation plan

**Deliverable**: Design document for Phase 6 implementation

### Acceptance Criteria
- [ ] Tab exists and displays placeholder content
- [ ] Design document outlines implementation plan

### Dependencies
- Phase 1-4 complete

---

## Phase 6: Polish & Performance (Weeks 11-12)

### Goals
- Responsive design optimization
- Performance tuning
- Error handling improvements
- User experience polish
- Documentation

### Tasks

#### 6.1 - Responsive Design (3 days)
- Test all pages on mobile devices (iPhone, Android)
- Adjust layouts for small screens
- Optimize data tables for mobile
- Test touch interactions

**Deliverable**: Fully responsive app

#### 6.2 - Performance Optimization (3 days)
- Profile slow operations
- Optimize large DataFrame rendering
- Implement lazy loading for charts
- Cache expensive computations with `@rx.cached_var`
- Optimize WebSocket payload size

**Deliverable**: Performance report with benchmarks

#### 6.3 - Error Handling & UX (3 days)
- Comprehensive error messages
- Loading states for all async operations
- Toast notifications for success/error
- Empty state components (no results, no data)
- Keyboard shortcuts (future)

**Deliverable**: Polished user experience

#### 6.4 - Testing & QA (3 days)
- End-to-end testing with Playwright
- Cross-browser testing (Chrome, Firefox, Safari)
- Load testing with concurrent users
- Security audit (JWT handling, SQL injection, XSS)

**Deliverable**: Passing E2E test suite

#### 6.5 - Documentation (2 days)
- User guide for Reflex app
- Developer documentation
- Deployment guide
- Migration comparison document (Streamlit vs Reflex)

**Deliverable**: Complete documentation

### Acceptance Criteria
- [ ] App is fully responsive on mobile devices
- [ ] Performance benchmarks meet targets (page load <2s, interactions <500ms)
- [ ] All error states are handled gracefully
- [ ] E2E tests cover critical workflows
- [ ] Documentation is complete and accurate

### Dependencies
- Phase 1-5 complete

---

## Summary Timeline

| Phase | Duration | Key Deliverables |
|-------|----------|-----------------|
| Phase 0 | Week 1 | Project setup, POCs |
| Phase 1 | Week 2 | Auth & database foundation |
| Phase 2 | Weeks 3-4 | Database Explorer tab |
| Phase 3 | Weeks 5-6 | EDW Pairing Analyzer tab |
| Phase 4 | Weeks 7-9 | Bid Line Analyzer tab (most complex) |
| Phase 5 | Week 10 | Historical Trends placeholder |
| Phase 6 | Weeks 11-12 | Polish & performance |

**Total**: 12 weeks (3 months)

---

## Critical Path

The following tasks are on the critical path and cannot be parallelized:
1. Phase 0: Project setup (blocks all other work)
2. Phase 1: Auth implementation (required for all tabs)
3. Phase 4: Data editor implementation (highest risk, longest duration)

**Parallelization Opportunities**:
- Phase 3 and Phase 4 could partially overlap if multiple developers available
- Phase 5 can be done anytime after Phase 2 (minimal dependencies)

---

## Resource Requirements

### Developer Skills Required
- **Python**: Advanced (backend logic, State management)
- **Reflex**: Intermediate (component composition, event handlers)
- **React/Frontend**: Basic (understanding Reflex's rendering model)
- **Database**: Intermediate (Supabase, PostgreSQL, RLS policies)
- **PDF Processing**: Intermediate (PyPDF2, pdfplumber)
- **Data Visualization**: Intermediate (Plotly)

### Infrastructure
- Development machine (local Reflex server)
- Supabase project (already configured)
- Staging environment for testing
- Production deployment (Reflex Cloud or self-hosted)

### Tools
- Reflex CLI
- Python 3.10+
- Git (feature branch workflow)
- Code editor (VS Code recommended)
- Browser DevTools
- Playwright (for E2E testing)

---

## Success Metrics

### Functional Parity
- [ ] All Streamlit features replicated in Reflex
- [ ] Database operations work identically
- [ ] PDF parsing produces same results
- [ ] Charts display same data

### Performance Targets
- [ ] Page load time < 2 seconds
- [ ] Interaction response < 500ms
- [ ] PDF processing time ≤ Streamlit version
- [ ] Support 50+ concurrent users

### User Experience
- [ ] Mobile-friendly design
- [ ] Intuitive navigation
- [ ] Clear error messages
- [ ] Consistent styling

### Code Quality
- [ ] 80%+ test coverage
- [ ] Type hints on all State vars
- [ ] Comprehensive documentation
- [ ] No security vulnerabilities

---

## Decision Log

Track key architectural decisions during migration:

| Date | Decision | Rationale | Alternatives Considered |
|------|----------|-----------|------------------------|
| TBD | Data editor approach | TBD after Phase 0 POC | rx.data_editor() vs custom modal editor |
| TBD | Styling framework | TBD | Inline styles vs Tailwind vs CSS modules |
| TBD | Deployment target | TBD | Reflex Cloud vs self-hosted vs hybrid |

---

## Future Enhancements (Post-Migration)

After migration is complete, consider:
1. **Real-time Collaboration**: Multiple users editing same data
2. **Offline Mode**: Service worker for offline capability
3. **Advanced Analytics**: ML-powered insights
4. **Mobile App**: React Native wrapper for native mobile
5. **API Endpoints**: REST API for external integrations
6. **Webhooks**: Notifications for new bid packets
7. **Scheduled Jobs**: Automated PDF processing pipeline
