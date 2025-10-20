# Implementation Plan: Supabase Integration + UI Enhancements

**Date Created:** 2025-10-19
**Status:** Planning Complete - Ready for Implementation
**Estimated Timeline:** 6-10 hours development time

---

## Table of Contents

1. [Architecture Decision](#architecture-decision)
2. [Database Design](#database-design)
3. [Implementation Phases](#implementation-phases)
4. [UI/UX Improvements](#uiux-improvements)
5. [Testing Strategy](#testing-strategy)
6. [Deployment Considerations](#deployment-considerations)

---

## Architecture Decision

### Decision: Streamlit + Supabase

**Rationale:**
- **Perfect fit for use case:** Data analysis, reporting, and trend visualization
- **Rapid development:** Build features in hours instead of weeks
- **Existing investment:** 80% of UI already complete
- **Easy maintenance:** Python-only stack, no frontend/backend separation needed
- **Deployment simplicity:** Streamlit Cloud + Supabase cloud = minimal DevOps

### Why NOT Migrate to Standalone Web App

**Not needed because:**
- Target audience: Internal pilot group/union tool
- Expected usage: <100 concurrent users
- Primary use: Desktop/laptop analysis
- Focus: Data over complex UI interactions

**When to reconsider:**
- Need to support thousands of concurrent users
- Require highly custom/mobile-first UI
- Need real-time collaboration features
- Want to build a public SaaS product

### Technology Stack

**Current:**
- Frontend/Backend: Streamlit
- PDF Parsing: PyPDF2, pdfplumber
- Data Viz: matplotlib, pandas
- File Generation: openpyxl, reportlab

**Adding:**
- Database: Supabase (PostgreSQL)
- Python Client: supabase-py
- Environment: python-dotenv
- Enhanced Charts: plotly
- (Optional) UI Components: streamlit-extras, streamlit-aggrid

---

## Database Design

### Schema Overview

**6 Tables Total:**
1. `bid_periods` - Master table for bid period metadata
2. `trips` - Granular pairing/trip data
3. `edw_summary_stats` - Aggregated EDW metrics
4. `bid_lines` - Granular line data
5. `bid_line_summary_stats` - Aggregated line metrics
6. (Optional) `uploads` - Track PDF upload history

### Table Schemas

#### 1. bid_periods

Master reference table for all bid periods.

```sql
CREATE TABLE bid_periods (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  domicile VARCHAR(10) NOT NULL,
  aircraft VARCHAR(10) NOT NULL,
  bid_period VARCHAR(10) NOT NULL,
  upload_date TIMESTAMP DEFAULT NOW(),
  created_at TIMESTAMP DEFAULT NOW(),

  -- Ensure no duplicate bid periods
  UNIQUE(domicile, aircraft, bid_period)
);

CREATE INDEX idx_bid_periods_lookup ON bid_periods(domicile, aircraft, bid_period);
```

#### 2. trips

Individual pairing/trip details from EDW Pairing Analyzer.

```sql
CREATE TABLE trips (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  bid_period_id UUID REFERENCES bid_periods(id) ON DELETE CASCADE,

  -- Trip identification
  trip_id VARCHAR(50) NOT NULL,

  -- EDW analysis
  is_edw BOOLEAN NOT NULL,
  edw_reason TEXT, -- Which duty day(s) triggered EDW flag

  -- Metrics
  tafb_hours DECIMAL(6,2),
  duty_days INTEGER,
  credit_time_hours DECIMAL(6,2),

  -- Raw trip text (for debugging/audit)
  raw_text TEXT,

  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_trips_bid_period ON trips(bid_period_id);
CREATE INDEX idx_trips_edw ON trips(is_edw);
```

#### 3. edw_summary_stats

Aggregated EDW statistics per bid period.

```sql
CREATE TABLE edw_summary_stats (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  bid_period_id UUID REFERENCES bid_periods(id) ON DELETE CASCADE UNIQUE,

  -- Trip counts
  total_trips INTEGER NOT NULL,
  edw_trips INTEGER NOT NULL,
  non_edw_trips INTEGER NOT NULL,

  -- Trip-weighted percentage
  trip_weighted_pct DECIMAL(5,2),

  -- TAFB-weighted
  total_tafb_hours DECIMAL(8,2),
  edw_tafb_hours DECIMAL(8,2),
  tafb_weighted_pct DECIMAL(5,2),

  -- Duty-day-weighted
  total_duty_days INTEGER,
  edw_duty_days INTEGER,
  duty_day_weighted_pct DECIMAL(5,2),

  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_edw_summary_bid_period ON edw_summary_stats(bid_period_id);
```

#### 4. bid_lines

Individual line details from Bid Line Analyzer.

```sql
CREATE TABLE bid_lines (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  bid_period_id UUID REFERENCES bid_periods(id) ON DELETE CASCADE,

  -- Line identification
  line_number INTEGER NOT NULL,

  -- Metrics
  credit_time_minutes INTEGER NOT NULL,
  block_time_minutes INTEGER NOT NULL,
  days_off INTEGER NOT NULL,
  duty_days INTEGER NOT NULL,

  -- Analysis
  is_buy_up BOOLEAN, -- CT < 75 hours

  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_bid_lines_bid_period ON bid_lines(bid_period_id);
CREATE INDEX idx_bid_lines_buy_up ON bid_lines(is_buy_up);
```

#### 5. bid_line_summary_stats

Aggregated line statistics per bid period.

```sql
CREATE TABLE bid_line_summary_stats (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  bid_period_id UUID REFERENCES bid_periods(id) ON DELETE CASCADE UNIQUE,

  -- Counts
  total_lines INTEGER NOT NULL,
  buy_up_lines INTEGER NOT NULL,

  -- Credit Time stats (in minutes)
  ct_min INTEGER,
  ct_max INTEGER,
  ct_avg DECIMAL(8,2),
  ct_median DECIMAL(8,2),
  ct_stddev DECIMAL(8,2),

  -- Block Time stats (in minutes)
  bt_min INTEGER,
  bt_max INTEGER,
  bt_avg DECIMAL(8,2),
  bt_median DECIMAL(8,2),
  bt_stddev DECIMAL(8,2),

  -- Days Off stats
  do_min INTEGER,
  do_max INTEGER,
  do_avg DECIMAL(5,2),
  do_median DECIMAL(5,2),

  -- Duty Days stats
  dd_min INTEGER,
  dd_max INTEGER,
  dd_avg DECIMAL(5,2),
  dd_median DECIMAL(5,2),

  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_bid_line_summary_bid_period ON bid_line_summary_stats(bid_period_id);
```

### Row-Level Security (RLS)

Initially, we'll start with simple authentication. Future enhancement could add RLS:

```sql
-- Enable RLS (future)
ALTER TABLE bid_periods ENABLE ROW LEVEL SECURITY;
ALTER TABLE trips ENABLE ROW LEVEL SECURITY;
-- etc.

-- Example policy: Allow authenticated users to read all data
CREATE POLICY "Allow read access to authenticated users"
  ON bid_periods FOR SELECT
  USING (auth.role() = 'authenticated');
```

---

## Implementation Phases

### Phase 1: Supabase Setup & Database Schema ✓

**Tasks:**
1. Create new Supabase project (via dashboard)
2. Note project URL and anon/service keys
3. Run SQL migrations to create all 6 tables
4. Create `.env` file with credentials
5. Create `.env.example` template
6. Update `.gitignore` to exclude `.env`
7. Create `docs/SUPABASE_SETUP.md` guide

**Deliverables:**
- Working Supabase database with schema
- Environment configuration files
- Setup documentation

**Time Estimate:** 1-2 hours

---

### Phase 2: Database Integration Module

**Tasks:**
1. Add dependencies to `requirements.txt`:
   ```
   supabase==2.3.4
   python-dotenv==1.0.0
   plotly==5.18.0
   ```
2. Create `database.py` module with functions:
   - `init_supabase()` - Initialize client
   - `save_edw_data()` - Save trips + summary stats
   - `save_bid_line_data()` - Save lines + summary stats
   - `get_historical_data()` - Query with filters
   - `check_bid_period_exists()` - Duplicate prevention
3. Add error handling and logging
4. Test connection with simple query

**File:** `database.py`

**Key Functions:**
```python
from supabase import create_client
from dotenv import load_dotenv
import os

def init_supabase():
    """Initialize Supabase client from environment variables."""
    load_dotenv()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")
    return create_client(url, key)

def save_edw_data(domicile, aircraft, bid_period, trips_data, summary_stats):
    """Save EDW analysis data to database."""
    # Implementation details...

def save_bid_line_data(domicile, aircraft, bid_period, lines_data, summary_stats):
    """Save bid line data to database."""
    # Implementation details...

def get_historical_data(domicile=None, aircraft=None, start_date=None, end_date=None):
    """Query historical data with optional filters."""
    # Implementation details...
```

**Deliverables:**
- Working database module
- Updated requirements.txt
- Connection tested

**Time Estimate:** 2-3 hours

---

### Phase 3: UI Theme & Styling Improvements

**Tasks:**
1. Create `.streamlit/config.toml` with professional theme
2. Create `styles.py` module for custom CSS injection
3. Update all pages to use consistent styling
4. Replace matplotlib charts with Plotly (interactive)
5. Add professional metric cards
6. Improve layout spacing and typography

**Files:**
- `.streamlit/config.toml` (new)
- `styles.py` (new)
- `app.py` (update)
- `pages/2_Bid_Line_Analyzer.py` (update)

**Theme Configuration Example:**
```toml
[theme]
primaryColor = "#0066cc"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"
```

**Custom CSS Module:**
```python
import streamlit as st

def apply_custom_css():
    st.markdown("""
        <style>
        /* Hide Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}

        /* Professional metric cards */
        div[data-testid="metric-container"] {
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 1rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }

        /* Button styling */
        .stButton>button {
            border-radius: 6px;
            font-weight: 500;
        }
        </style>
    """, unsafe_allow_html=True)
```

**Deliverables:**
- Professional theme applied
- Consistent styling across all pages
- Interactive Plotly charts
- Cleaner UI appearance

**Time Estimate:** 1-2 hours

---

### Phase 4: Add Save Functionality to Existing Pages

#### 4A: EDW Pairing Analyzer (`app.py`)

**Tasks:**
1. Import database module
2. Store parsed trip data in `st.session_state` after analysis
3. Add "💾 Save to Database" button below download buttons
4. On save:
   - Check if bid period already exists
   - If exists, show warning and ask for confirmation
   - Save trips + summary stats to database
   - Show success message with record counts
5. Add error handling for database failures

**UI Flow:**
```python
if st.button("💾 Save to Database"):
    if database.check_bid_period_exists(domicile, aircraft, bid_period):
        st.warning(f"⚠️ Data for {domicile} {aircraft} Bid {bid_period} already exists!")
        if st.button("Overwrite existing data"):
            # Save logic
    else:
        # Save logic
        st.success(f"✅ Saved {len(trips)} trips to database!")
```

**Deliverables:**
- Working save functionality on EDW analyzer
- Duplicate detection
- User-friendly messages

**Time Estimate:** 1 hour

#### 4B: Bid Line Analyzer (`pages/2_Bid_Line_Analyzer.py`)

**Tasks:**
1. Import database module
2. Store parsed line data in session state
3. Add save button with same duplicate checking
4. Improve layout with tabs (Results | Raw Data)
5. Add database save functionality

**Deliverables:**
- Working save functionality on Bid Line analyzer
- Improved layout with tabs
- Consistent UX with EDW analyzer

**Time Estimate:** 1 hour

---

### Phase 5: Historical Trends Viewer (New Page)

**Tasks:**
1. Create `pages/3_Historical_Trends.py`
2. Add sidebar filters:
   - Domicile multi-select
   - Aircraft multi-select
   - Date range picker
3. Query database based on filters
4. Create interactive visualizations:
   - EDW trends over time (line chart with all 3 metrics)
   - Average credit/block time trends (line chart)
   - Days off trends (line chart)
   - Summary statistics table
5. Add export to Excel button for filtered data
6. Handle empty state (no data in database yet)

**Page Structure:**
```
Sidebar:
  - Filters (domicile, aircraft, date range)
  - Apply Filters button

Main Area:
  - Page title and description
  - Summary metrics (total bid periods, date range)

  Tab 1: EDW Trends
    - Line chart: EDW percentages over time
    - Data table: Detailed EDW stats

  Tab 2: Bid Line Trends
    - Line charts: CT, BT, DO trends
    - Data table: Detailed line stats

  Tab 3: Comparisons
    - Side-by-side bid period comparison
    - Year-over-year analysis
```

**Visualizations:**
```python
import plotly.express as px

# EDW trends
fig = px.line(df, x='bid_period', y=['trip_weighted_pct', 'tafb_weighted_pct', 'duty_day_weighted_pct'],
              title='EDW Percentages Over Time',
              labels={'value': 'EDW %', 'variable': 'Metric Type'})
st.plotly_chart(fig, use_container_width=True)
```

**Deliverables:**
- Working historical trends page
- Interactive charts with filters
- Export functionality
- Professional layout

**Time Estimate:** 2-3 hours

---

### Phase 6: Documentation Updates

**Tasks:**
1. Create `docs/SUPABASE_SETUP.md`:
   - Step-by-step Supabase project creation
   - SQL migration instructions
   - Environment variable setup
   - Testing connection
2. Update `CLAUDE.md`:
   - Add database architecture section
   - Document new modules (database.py, styles.py)
   - Update file structure
3. Update `README.md`:
   - Add new features (database integration, trends viewer)
   - Add setup instructions for Supabase
   - Add screenshots of new pages
4. Create `.env.example`:
   ```
   SUPABASE_URL=your-project-url.supabase.co
   SUPABASE_ANON_KEY=your-anon-key
   ```

**Deliverables:**
- Complete setup guide
- Updated project documentation
- Easy onboarding for new developers

**Time Estimate:** 1 hour

---

## UI/UX Improvements

### Theme & Styling

**Professional Color Scheme:**
- Primary: `#0066cc` (Professional blue)
- Secondary background: `#f0f2f6` (Light gray)
- Success: `#28a745` (Green)
- Warning: `#ffc107` (Amber)
- Error: `#dc3545` (Red)

**Typography:**
- Headers: Clear hierarchy (H1 > H2 > H3)
- Body: Sans-serif, comfortable reading size
- Code/Data: Monospace font

**Layout Improvements:**
1. Consistent spacing between sections
2. Card-based metric displays
3. Tabbed interfaces for complex data
4. Professional buttons with icons
5. Loading spinners for long operations

### Interactive Elements

**Charts:**
- Replace all matplotlib → Plotly
- Add hover tooltips
- Enable zoom/pan
- Export chart as PNG option

**Tables:**
- Sortable columns
- Search/filter within table
- Pagination for large datasets
- Highlight important rows

**Forms:**
- Better input grouping
- Clear labels and help text
- Validation messages
- Default values

### Responsive Design

While Streamlit is desktop-first, we'll ensure:
- Columns stack nicely on smaller screens
- Charts resize appropriately
- Sidebar collapsible on mobile
- Touch-friendly buttons

---

## Testing Strategy

### Manual Testing Checklist

**Phase 2: Database Integration**
- [ ] Supabase connection successful
- [ ] Can insert bid period
- [ ] Can insert trips
- [ ] Can insert summary stats
- [ ] Duplicate detection works
- [ ] Query functions return correct data
- [ ] Error handling catches bad credentials

**Phase 3: UI Improvements**
- [ ] Theme colors applied correctly
- [ ] Custom CSS renders properly
- [ ] Plotly charts are interactive
- [ ] Layout looks professional on different screen sizes
- [ ] No console errors in browser

**Phase 4: Save Functionality**
- [ ] EDW analyzer save button works
- [ ] Bid Line analyzer save button works
- [ ] Duplicate warning shows correctly
- [ ] Success/error messages display
- [ ] Data persists in database correctly
- [ ] Can save multiple bid periods

**Phase 5: Historical Trends**
- [ ] Page loads without errors
- [ ] Filters work correctly
- [ ] Charts render with correct data
- [ ] Empty state handled gracefully
- [ ] Export to Excel works
- [ ] Comparison features work

**Integration Testing:**
- [ ] Upload PDF → Analyze → Save → View in Trends (end-to-end)
- [ ] Multiple domiciles/aircraft can be tracked
- [ ] Date range filtering works across years
- [ ] Can delete and re-upload same bid period

### Test Data

**Create test PDFs for:**
- ONT 757 Bid 2507 (current)
- ONT 757 Bid 2506 (previous month)
- LAX 777 Bid 2507 (different domicile/aircraft)

**Verify:**
- Different EDW percentages
- Different line counts
- Trends show correctly across months

---

## Deployment Considerations

### Local Development

**Requirements:**
- Python 3.9+
- Virtual environment
- Supabase account (free tier sufficient for testing)

**Setup:**
```bash
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your Supabase credentials
streamlit run app.py
```

### Production Deployment

**Option 1: Streamlit Cloud (Recommended)**
- Connect GitHub repo
- Add Supabase credentials as secrets
- Automatic deployments on git push
- Free tier: 1 app, unlimited viewers

**Option 2: Self-Hosted**
- Docker container with Streamlit
- Environment variables for Supabase
- Nginx reverse proxy
- SSL certificate (Let's Encrypt)

**Supabase:**
- Free tier: 500MB database, 2GB bandwidth/month
- Upgrade to Pro ($25/mo) if needed for:
  - 8GB database
  - 250GB bandwidth
  - Better performance

### Environment Variables

**Production secrets (never commit):**
```
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Streamlit Cloud:**
Add via dashboard Settings → Secrets:
```toml
SUPABASE_URL = "https://xxxxx.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Performance Optimization

**Database:**
- Indexes on commonly queried fields (already in schema)
- Limit query results (pagination)
- Cache frequently accessed data

**Streamlit:**
- Use `@st.cache_data` for expensive operations
- Cache database queries with TTL
- Lazy load historical data
- Optimize chart rendering

**Example caching:**
```python
@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_historical_trends(domicile, aircraft, start_date, end_date):
    return database.get_historical_data(domicile, aircraft, start_date, end_date)
```

---

## Future Enhancements (Post-MVP)

### Phase 7: Advanced Features (Optional)

1. **User Authentication**
   - Supabase Auth integration
   - User-specific dashboards
   - Row-level security

2. **Advanced Analytics**
   - Predictive modeling (next month's EDW forecast)
   - Anomaly detection (unusual bid periods)
   - Statistical significance testing

3. **Enhanced UI**
   - Dark mode toggle
   - Custom airline branding
   - streamlit-aggrid for better tables
   - Download charts as images

4. **Bulk Operations**
   - Bulk PDF upload page
   - Batch processing of historical data
   - CSV import for legacy data

5. **Notifications**
   - Email alerts when new data uploaded
   - Slack integration for team updates
   - Scheduled report generation

6. **Export Options**
   - PowerPoint slide generation
   - Custom PDF reports with branding
   - API endpoint for external tools

### Technical Debt to Address

1. Add unit tests (pytest)
2. Add integration tests
3. CI/CD pipeline (GitHub Actions)
4. Error logging (Sentry)
5. Performance monitoring
6. Automated backups

---

## Success Criteria

**Phase 1-6 Complete When:**
- ✅ All 6 database tables created and tested
- ✅ Data can be saved from both analyzer pages
- ✅ Historical trends page shows visualizations
- ✅ UI looks professional with consistent theming
- ✅ Documentation complete and accurate
- ✅ End-to-end workflow tested (upload → analyze → save → view trends)

**User Acceptance:**
- Can upload and analyze PDFs as before (no regression)
- Can save analyzed data to database with one click
- Can view historical trends across multiple bid periods
- Can filter and export historical data
- UI is more polished and professional

---

## Timeline Summary

| Phase | Description | Time Estimate |
|-------|-------------|---------------|
| 1 | Supabase Setup & Schema | 1-2 hours |
| 2 | Database Integration Module | 2-3 hours |
| 3 | UI Theme & Styling | 1-2 hours |
| 4 | Save Functionality | 2 hours |
| 5 | Historical Trends Page | 2-3 hours |
| 6 | Documentation | 1 hour |
| **Total** | **End-to-End Implementation** | **9-13 hours** |

**Recommended Approach:**
- Week 1: Phases 1-2 (database foundation)
- Week 2: Phases 3-4 (UI + save)
- Week 3: Phases 5-6 (trends + docs)

Or do it all in one focused day! 🚀

---

## Questions & Decisions Log

**Q: Should we use Streamlit or migrate to standalone web app?**
A: Stick with Streamlit - perfect fit for this use case, faster delivery.

**Q: What granularity of data to store?**
A: Both detailed (trip/line level) and summary stats for flexibility.

**Q: How to handle duplicate uploads?**
A: Detect duplicates, show warning, allow manual overwrite.

**Q: Theme improvements?**
A: Yes - add basic professional styling via config + custom CSS.

**Q: When to save data?**
A: Manual save button (not automatic) for user control.

---

## Contact & Support

**For implementation questions:**
- Refer to `docs/SUPABASE_SETUP.md` for database setup
- Check `CLAUDE.md` for codebase architecture
- Review this document for overall plan

**Need help?**
- Supabase docs: https://supabase.com/docs
- Streamlit docs: https://docs.streamlit.io
- Plotly docs: https://plotly.com/python/

---

**End of Implementation Plan**
