# Supabase Integration Roadmap

## Project Overview

This document outlines the complete implementation plan for integrating Supabase as the database backend for the Aero Crew Data analysis application. The integration will enable:

- **Multi-user access** with role-based authentication (admin vs. user roles)
- **Historical data storage** for both EDW pairing analysis and bid line analysis
- **Advanced querying** across multiple dimensions (bid period, domicile, aircraft, seat)
- **Trend analysis** with interactive visualizations
- **Customizable PDF exports** with admin-managed templates
- **Data backfill** capabilities for historical analysis

---

## Database Architecture

### Core Tables

#### 1. `bid_periods`
Master table containing metadata for each bid period.

```sql
CREATE TABLE bid_periods (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  period TEXT NOT NULL,  -- e.g., "2507", "2508"
  domicile TEXT NOT NULL,  -- e.g., "ONT", "LAX", "SFO"
  aircraft TEXT NOT NULL,  -- e.g., "757", "737", "A320"
  seat TEXT NOT NULL,  -- "CA" (Captain) or "FO" (First Officer)
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  created_by UUID REFERENCES auth.users(id),

  -- Ensure uniqueness
  UNIQUE(period, domicile, aircraft, seat)
);

CREATE INDEX idx_bid_periods_lookup ON bid_periods(period, domicile, aircraft, seat);
CREATE INDEX idx_bid_periods_dates ON bid_periods(start_date, end_date);
```

#### 2. `pairings`
Individual trip records from EDW pairing analysis.

```sql
CREATE TABLE pairings (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  bid_period_id UUID NOT NULL REFERENCES bid_periods(id) ON DELETE CASCADE,
  trip_id TEXT NOT NULL,

  -- EDW Classification
  is_edw BOOLEAN NOT NULL,
  edw_reason TEXT,  -- Which duty days triggered EDW

  -- Trip Metrics
  total_credit_time DECIMAL(5,2),  -- In hours
  tafb_hours DECIMAL(5,2),  -- Time Away From Base
  num_duty_days INTEGER,
  num_legs INTEGER,

  -- Timestamps
  departure_time TIMESTAMP WITH TIME ZONE,
  arrival_time TIMESTAMP WITH TIME ZONE,

  -- Trip Details (optional, for full text search)
  trip_details TEXT,  -- Full parsed trip text

  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  UNIQUE(bid_period_id, trip_id)
);

CREATE INDEX idx_pairings_bid_period ON pairings(bid_period_id);
CREATE INDEX idx_pairings_edw ON pairings(is_edw);
CREATE INDEX idx_pairings_metrics ON pairings(total_credit_time, tafb_hours, num_duty_days);
```

#### 3. `pairing_duty_days`
Detailed duty day records for each pairing (one-to-many with pairings).

```sql
CREATE TABLE pairing_duty_days (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  pairing_id UUID NOT NULL REFERENCES pairings(id) ON DELETE CASCADE,
  duty_day_number INTEGER NOT NULL,  -- 1, 2, 3, etc.

  -- Duty Day Metrics
  num_legs INTEGER,
  duty_duration DECIMAL(5,2),  -- In hours
  credit_time DECIMAL(5,2),
  is_edw BOOLEAN NOT NULL,

  -- Times (local time at departure city)
  report_time TIME,
  release_time TIME,

  -- Duty day details
  duty_day_text TEXT,  -- Full parsed duty day text

  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  UNIQUE(pairing_id, duty_day_number)
);

CREATE INDEX idx_duty_days_pairing ON pairing_duty_days(pairing_id);
CREATE INDEX idx_duty_days_edw ON pairing_duty_days(is_edw);
```

#### 4. `bid_lines`
Individual bid line records from bid line analysis.

```sql
CREATE TABLE bid_lines (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  bid_period_id UUID NOT NULL REFERENCES bid_periods(id) ON DELETE CASCADE,
  line_number INTEGER NOT NULL,

  -- Line Metrics (Pay Period 1)
  pp1_ct DECIMAL(5,2),  -- Credit Time
  pp1_bt DECIMAL(5,2),  -- Block Time
  pp1_do INTEGER,       -- Days Off
  pp1_dd INTEGER,       -- Duty Days

  -- Line Metrics (Pay Period 2)
  pp2_ct DECIMAL(5,2),
  pp2_bt DECIMAL(5,2),
  pp2_do INTEGER,
  pp2_dd INTEGER,

  -- Combined Metrics
  total_ct DECIMAL(5,2),
  total_bt DECIMAL(5,2),
  total_do INTEGER,
  total_dd INTEGER,

  -- Reserve Line Data (if applicable)
  is_reserve BOOLEAN DEFAULT FALSE,
  reserve_slots_ca INTEGER,  -- Captain reserve slots
  reserve_slots_fo INTEGER,  -- First Officer reserve slots

  -- Line Details
  line_details TEXT,  -- Full parsed line text (optional)

  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  UNIQUE(bid_period_id, line_number)
);

CREATE INDEX idx_bid_lines_bid_period ON bid_lines(bid_period_id);
CREATE INDEX idx_bid_lines_reserve ON bid_lines(is_reserve);
CREATE INDEX idx_bid_lines_metrics ON bid_lines(total_ct, total_bt, total_do, total_dd);
```

### Authentication & User Management Tables

#### 5. `profiles`
Extended user profile information (linked to Supabase Auth).

```sql
CREATE TABLE profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  display_name TEXT,
  role TEXT NOT NULL DEFAULT 'user',  -- 'admin' or 'user'
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  CHECK (role IN ('admin', 'user'))
);

CREATE INDEX idx_profiles_role ON profiles(role);

-- Trigger to create profile on user signup
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id, display_name, role)
  VALUES (NEW.id, NEW.email, 'user');
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION handle_new_user();
```

#### 6. `pdf_export_templates`
Admin-managed PDF export templates.

```sql
CREATE TABLE pdf_export_templates (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  description TEXT,

  -- Template Configuration (JSON)
  config_json JSONB NOT NULL,
  -- Example config structure:
  -- {
  --   "sections": ["filters", "data_table", "summary_stats"],
  --   "charts": ["time_series", "distribution"],
  --   "chart_layout": "compact",
  --   "color_scheme": "color"
  -- }

  -- Metadata
  created_by UUID REFERENCES auth.users(id),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  -- Visibility
  is_public BOOLEAN DEFAULT TRUE,
  is_default BOOLEAN DEFAULT FALSE,

  UNIQUE(name)
);

CREATE INDEX idx_pdf_templates_public ON pdf_export_templates(is_public);
CREATE INDEX idx_pdf_templates_default ON pdf_export_templates(is_default);
```

### Row-Level Security (RLS) Policies

```sql
-- Enable RLS on all tables
ALTER TABLE bid_periods ENABLE ROW LEVEL SECURITY;
ALTER TABLE pairings ENABLE ROW LEVEL SECURITY;
ALTER TABLE pairing_duty_days ENABLE ROW LEVEL SECURITY;
ALTER TABLE bid_lines ENABLE ROW LEVEL SECURITY;
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE pdf_export_templates ENABLE ROW LEVEL SECURITY;

-- bid_periods policies
CREATE POLICY "Anyone can view bid periods" ON bid_periods FOR SELECT USING (true);
CREATE POLICY "Admins can insert bid periods" ON bid_periods FOR INSERT
  WITH CHECK (EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role = 'admin'));
CREATE POLICY "Admins can update bid periods" ON bid_periods FOR UPDATE
  USING (EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role = 'admin'));
CREATE POLICY "Admins can delete bid periods" ON bid_periods FOR DELETE
  USING (EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role = 'admin'));

-- pairings policies (same pattern)
CREATE POLICY "Anyone can view pairings" ON pairings FOR SELECT USING (true);
CREATE POLICY "Admins can insert pairings" ON pairings FOR INSERT
  WITH CHECK (EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role = 'admin'));
CREATE POLICY "Admins can update pairings" ON pairings FOR UPDATE
  USING (EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role = 'admin'));
CREATE POLICY "Admins can delete pairings" ON pairings FOR DELETE
  USING (EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role = 'admin'));

-- pairing_duty_days policies
CREATE POLICY "Anyone can view duty days" ON pairing_duty_days FOR SELECT USING (true);
CREATE POLICY "Admins can insert duty days" ON pairing_duty_days FOR INSERT
  WITH CHECK (EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role = 'admin'));
CREATE POLICY "Admins can update duty days" ON pairing_duty_days FOR UPDATE
  USING (EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role = 'admin'));
CREATE POLICY "Admins can delete duty days" ON pairing_duty_days FOR DELETE
  USING (EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role = 'admin'));

-- bid_lines policies
CREATE POLICY "Anyone can view bid lines" ON bid_lines FOR SELECT USING (true);
CREATE POLICY "Admins can insert bid lines" ON bid_lines FOR INSERT
  WITH CHECK (EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role = 'admin'));
CREATE POLICY "Admins can update bid lines" ON bid_lines FOR UPDATE
  USING (EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role = 'admin'));
CREATE POLICY "Admins can delete bid lines" ON bid_lines FOR DELETE
  USING (EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role = 'admin'));

-- profiles policies
CREATE POLICY "Users can view their own profile" ON profiles FOR SELECT
  USING (auth.uid() = id);
CREATE POLICY "Admins can view all profiles" ON profiles FOR SELECT
  USING (EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role = 'admin'));
CREATE POLICY "Users can update their own profile" ON profiles FOR UPDATE
  USING (auth.uid() = id);
CREATE POLICY "Admins can update all profiles" ON profiles FOR UPDATE
  USING (EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role = 'admin'));

-- pdf_export_templates policies
CREATE POLICY "Anyone can view public templates" ON pdf_export_templates FOR SELECT
  USING (is_public = true);
CREATE POLICY "Admins can view all templates" ON pdf_export_templates FOR SELECT
  USING (EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role = 'admin'));
CREATE POLICY "Admins can insert templates" ON pdf_export_templates FOR INSERT
  WITH CHECK (EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role = 'admin'));
CREATE POLICY "Admins can update templates" ON pdf_export_templates FOR UPDATE
  USING (EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role = 'admin'));
CREATE POLICY "Admins can delete templates" ON pdf_export_templates FOR DELETE
  USING (EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role = 'admin'));
```

---

## Implementation Phases

### Phase 1: Database Schema & Supabase Setup (2-3 days)

**Objective:** Set up Supabase project and create database schema.

**Tasks:**
1. Create Supabase project at https://supabase.com
2. Copy project URL and anon key to `.env` file
3. Run SQL migrations to create all 6 tables
4. Set up indexes and constraints
5. Configure Row-Level Security (RLS) policies
6. Test authentication (create test admin and user accounts)
7. Verify RLS policies work correctly

**Deliverables:**
- Supabase project configured
- All tables created with proper indexes
- RLS policies active and tested
- `.env` file with credentials (not committed to git)

**Testing:**
- Create test user accounts (1 admin, 1 regular user)
- Verify admins can insert data, users cannot
- Verify both can read data

---

### Phase 2: Database Module (`database.py`) (2-3 days)

**Objective:** Create Python module for all database interactions.

**Module Structure:**

```python
# database.py

from supabase import create_client, Client
import os
from dotenv import load_dotenv
from typing import List, Dict, Optional, Tuple
import pandas as pd

class SupabaseClient:
    """Singleton Supabase client."""
    def __init__(self):
        load_dotenv()
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")
        self.client: Client = create_client(url, key)

    # Admin Operations (Upload/Save)
    def save_bid_period(self, period_data: Dict) -> str:
        """Create or update bid period. Returns bid_period_id."""
        pass

    def save_pairings(self, bid_period_id: str, pairings_df: pd.DataFrame) -> int:
        """Bulk insert pairings. Returns count of records inserted."""
        pass

    def save_pairing_duty_days(self, pairing_id: str, duty_days: List[Dict]) -> int:
        """Insert duty day records for a pairing."""
        pass

    def save_bid_lines(self, bid_period_id: str, lines_df: pd.DataFrame) -> int:
        """Bulk insert bid lines. Returns count of records inserted."""
        pass

    def update_pairing(self, pairing_id: str, updates: Dict) -> bool:
        """Update a single pairing record."""
        pass

    def delete_pairing(self, pairing_id: str) -> bool:
        """Delete a pairing and its duty days (cascade)."""
        pass

    def delete_bid_period(self, bid_period_id: str) -> bool:
        """Delete bid period and all related data (cascade)."""
        pass

    # Query Operations (User-facing)
    def get_bid_periods(self, filters: Optional[Dict] = None) -> pd.DataFrame:
        """List available bid periods with optional filters.

        Filters:
        - domicile: List[str]
        - aircraft: List[str]
        - seat: List[str]
        - start_date: str (YYYY-MM-DD)
        - end_date: str (YYYY-MM-DD)
        """
        pass

    def query_pairings(self, filters: Dict) -> pd.DataFrame:
        """Query pairings with multi-dimensional filters."""
        pass

    def query_bid_lines(self, filters: Dict) -> pd.DataFrame:
        """Query bid lines with multi-dimensional filters."""
        pass

    def get_pairing_details(self, pairing_id: str) -> Tuple[Dict, List[Dict]]:
        """Get full pairing details including duty days."""
        pass

    def get_trend_data(self, metric: str, filters: Dict) -> pd.DataFrame:
        """Get time series data for trend analysis.

        Metrics: 'ct', 'bt', 'do', 'dd', 'edw_percentage', etc.
        Returns DataFrame with columns: period, date, value
        """
        pass

    # Analytics Functions
    def calculate_period_stats(self, bid_period_id: str) -> Dict:
        """Calculate aggregate statistics for a bid period."""
        pass

    def compare_periods(self, bid_period_ids: List[str]) -> pd.DataFrame:
        """Side-by-side comparison of multiple bid periods."""
        pass

    def detect_anomalies(self, filters: Dict, threshold: float = 2.0) -> pd.DataFrame:
        """Detect statistical outliers (z-score > threshold)."""
        pass

    # PDF Template Operations
    def save_pdf_template(self, template_data: Dict) -> str:
        """Create or update PDF export template. Returns template_id."""
        pass

    def get_pdf_templates(self, public_only: bool = True) -> List[Dict]:
        """List available PDF templates."""
        pass

    def get_pdf_template(self, template_id: str) -> Dict:
        """Get a specific template configuration."""
        pass

    def delete_pdf_template(self, template_id: str) -> bool:
        """Delete a PDF template."""
        pass

    def set_default_template(self, template_id: str) -> bool:
        """Set a template as the default."""
        pass

    # User Management (Admin only)
    def get_users(self) -> List[Dict]:
        """List all users (admin only)."""
        pass

    def update_user_role(self, user_id: str, role: str) -> bool:
        """Update user role (admin only)."""
        pass
```

**Error Handling:**
- All functions should handle Supabase exceptions gracefully
- Return `None` or empty DataFrame on errors
- Log errors to console/file for debugging

**Testing:**
- Unit tests for each function with mock data
- Integration tests with real Supabase connection
- Test error handling (invalid IDs, missing data, etc.)

**Deliverables:**
- `database.py` module with all functions implemented
- Unit tests in `tests/test_database.py`
- Documentation for each function

---

### Phase 3: Admin Upload Interface (1-2 days)

**Objective:** Add "Save to Database" functionality to existing analyzer tabs.

#### 3.1 EDW Pairing Analyzer Enhancement

**Location:** `app.py`, Tab 1 (after analysis results are displayed)

**UI Changes:**
1. Add expandable section: "💾 Save to Database"
2. Form inputs (pre-filled from PDF header extraction):
   - Bid Period (text input, e.g., "2507")
   - Domicile (text input, e.g., "ONT")
   - Aircraft (text input, e.g., "757")
   - Seat (radio button: Captain / First Officer)
   - Start Date (date picker)
   - End Date (date picker)
3. Preview section showing:
   - Total trips: X
   - EDW trips: Y (Z%)
   - Trip-weighted EDW: X%
   - TAFB-weighted EDW: X%
   - Duty-day-weighted EDW: X%
4. Conflict handling dropdown:
   - "Overwrite existing data" (if bid period exists)
   - "Skip (don't save)"
5. "Save to Database" button

**Implementation:**
```python
# In app.py, Tab 1, after analysis results
if st.session_state.get('edw_analysis_complete'):
    with st.expander("💾 Save to Database"):
        st.markdown("### Bid Period Metadata")

        col1, col2 = st.columns(2)
        with col1:
            period = st.text_input("Bid Period", value=st.session_state.get('bid_period', ''), key='edw_save_period')
            domicile = st.text_input("Domicile", value=st.session_state.get('domicile', ''), key='edw_save_domicile')
            aircraft = st.text_input("Aircraft", value=st.session_state.get('aircraft', ''), key='edw_save_aircraft')

        with col2:
            seat = st.radio("Seat", ["Captain", "First Officer"], key='edw_save_seat')
            start_date = st.date_input("Start Date", key='edw_save_start_date')
            end_date = st.date_input("End Date", key='edw_save_end_date')

        st.markdown("### Preview")
        stats = st.session_state.get('edw_stats', {})
        st.write(f"Total trips: {stats.get('total_trips', 0)}")
        st.write(f"EDW trips: {stats.get('edw_trips', 0)} ({stats.get('edw_percentage', 0):.1f}%)")

        # Check if bid period exists
        db = SupabaseClient()
        existing = db.get_bid_periods({
            'period': period,
            'domicile': domicile,
            'aircraft': aircraft,
            'seat': seat
        })

        if not existing.empty:
            st.warning("⚠️ This bid period already exists in the database.")
            conflict_action = st.selectbox("Action", ["Overwrite", "Skip"], key='edw_conflict_action')
        else:
            conflict_action = "Insert"

        if st.button("Save to Database", key='edw_save_button'):
            try:
                # Save bid period
                bid_period_id = db.save_bid_period({
                    'period': period,
                    'domicile': domicile,
                    'aircraft': aircraft,
                    'seat': 'CA' if seat == 'Captain' else 'FO',
                    'start_date': start_date,
                    'end_date': end_date
                })

                # Save pairings
                pairings_df = st.session_state.get('pairings_df')
                count = db.save_pairings(bid_period_id, pairings_df)

                st.success(f"✅ Saved {count} pairings to database!")
                st.info(f"Bid Period ID: {bid_period_id}")

            except Exception as e:
                st.error(f"❌ Error saving to database: {str(e)}")
```

#### 3.2 Bid Line Analyzer Enhancement

**Location:** `app.py`, Tab 2 (after parsing completes)

**UI Changes:** (Similar pattern to EDW Pairing Analyzer)
1. Add "💾 Save to Database" expander
2. Same metadata form
3. Preview showing:
   - Total lines: X
   - Reserve lines: Y
   - CT range: X - Y
   - Average CT: X
4. Save button with conflict handling

**Implementation:** (Follow same pattern as 3.1)

#### 3.3 Bulk Upload Tool (New Admin Tab)

**Location:** `app.py`, new Tab 4 (admin only, shown after authentication)

**Features:**
1. File uploader (CSV or Excel)
2. Data type selector: "Pairings" or "Bid Lines"
3. Column mapping interface:
   - Dropdown for each required field
   - Auto-detect common column names
4. Validation preview:
   - Show first 10 rows
   - Highlight any errors (missing required fields, invalid values)
5. Progress bar during upload
6. Results summary:
   - Records inserted: X
   - Records skipped: Y
   - Errors: Z (with downloadable error log)

**Implementation:**
```python
# In app.py, new tab
if user_role == 'admin':
    tab4 = st.tabs(["EDW Pairing Analyzer", "Bid Line Analyzer", "Historical Trends", "Bulk Upload"])

    with tab4[3]:  # Bulk Upload tab
        st.header("🗂️ Bulk Data Upload")
        st.markdown("Upload historical data from CSV or Excel files.")

        data_type = st.radio("Data Type", ["Pairings", "Bid Lines"], key='bulk_data_type')
        uploaded_file = st.file_uploader("Upload File", type=['csv', 'xlsx'], key='bulk_file_uploader')

        if uploaded_file:
            # Read file
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)

            st.markdown("### Column Mapping")
            st.write(f"Detected {len(df)} rows")

            # Column mapping interface
            required_fields = get_required_fields(data_type)
            col_map = {}

            cols = st.columns(2)
            for i, field in enumerate(required_fields):
                with cols[i % 2]:
                    col_map[field] = st.selectbox(
                        f"{field}:",
                        options=['-- Select --'] + list(df.columns),
                        key=f'bulk_map_{field}'
                    )

            # Validation preview
            st.markdown("### Preview (First 10 rows)")
            preview_df = df.head(10)
            st.dataframe(preview_df)

            # Upload button
            if st.button("Start Upload", key='bulk_upload_button'):
                progress_bar = st.progress(0)
                status_text = st.empty()

                # Process in batches
                batch_size = 100
                total_rows = len(df)
                results = {'inserted': 0, 'skipped': 0, 'errors': []}

                db = SupabaseClient()

                for i in range(0, total_rows, batch_size):
                    batch = df.iloc[i:i+batch_size]

                    try:
                        # Save batch
                        if data_type == 'Pairings':
                            count = db.save_pairings_batch(batch, col_map)
                        else:
                            count = db.save_bid_lines_batch(batch, col_map)

                        results['inserted'] += count
                    except Exception as e:
                        results['errors'].append(f"Row {i}: {str(e)}")
                        results['skipped'] += len(batch)

                    # Update progress
                    progress = (i + batch_size) / total_rows
                    progress_bar.progress(min(progress, 1.0))
                    status_text.text(f"Processing rows {i+1}-{min(i+batch_size, total_rows)} of {total_rows}...")

                # Results
                st.success(f"✅ Upload complete!")
                st.write(f"Inserted: {results['inserted']}")
                st.write(f"Skipped: {results['skipped']}")

                if results['errors']:
                    st.error(f"Errors: {len(results['errors'])}")
                    error_log = '\n'.join(results['errors'])
                    st.download_button("Download Error Log", error_log, "error_log.txt")
```

**Deliverables:**
- "Save to Database" functionality in both analyzer tabs
- Bulk upload tool with validation and progress tracking
- CSV templates for historical data import

---

### Phase 4: User Query Interface (2-3 days)

**Objective:** Create "Database Explorer" tab for querying and filtering historical data.

**Location:** `app.py`, new Tab 3 (replace "Historical Trends" placeholder)

#### 4.1 Filter Panel (Sidebar)

**UI Components:**
```python
# In app.py, Database Explorer tab
st.sidebar.header("🔍 Query Filters")

# Multi-select filters
domiciles = st.sidebar.multiselect(
    "Domicile",
    options=get_all_domiciles(),  # Query from database
    key='query_domiciles'
)

aircraft = st.sidebar.multiselect(
    "Aircraft",
    options=get_all_aircraft(),
    key='query_aircraft'
)

seats = st.sidebar.multiselect(
    "Seat Position",
    options=["Captain", "First Officer"],
    key='query_seats'
)

# Date range picker
st.sidebar.markdown("### Bid Period Range")
date_range = st.sidebar.date_input(
    "Date Range",
    value=(datetime.now() - timedelta(days=180), datetime.now()),
    key='query_date_range'
)

# Quick filters
quick_filter = st.sidebar.selectbox(
    "Quick Filter",
    ["Custom", "Last 6 months", "Last year", "All time"],
    key='query_quick_filter'
)

# Data type toggle
data_type = st.sidebar.radio(
    "Data Type",
    ["Pairings", "Bid Lines", "Both"],
    key='query_data_type'
)

# Query button
if st.sidebar.button("Run Query", key='query_run_button'):
    st.session_state['query_results'] = run_query(filters)
```

#### 4.2 Query Results View

**Main Content Area:**
```python
# Display query results
if 'query_results' in st.session_state:
    results = st.session_state['query_results']

    st.markdown(f"### Query Results ({len(results)} records)")

    # Export options
    col1, col2, col3 = st.columns(3)
    with col1:
        csv = results.to_csv(index=False)
        st.download_button("📥 Export CSV", csv, "query_results.csv")

    with col2:
        excel_buffer = io.BytesIO()
        results.to_excel(excel_buffer, index=False)
        st.download_button("📥 Export Excel", excel_buffer.getvalue(), "query_results.xlsx")

    with col3:
        if st.button("📄 Export PDF", key='query_export_pdf'):
            st.session_state['show_pdf_config'] = True

    # Paginated data table
    page_size = 50
    total_pages = (len(results) - 1) // page_size + 1
    page = st.number_input("Page", min_value=1, max_value=total_pages, value=1, key='query_page')

    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size

    st.dataframe(
        results.iloc[start_idx:end_idx],
        use_container_width=True,
        height=600
    )

    # Row detail expander
    st.markdown("### Details")
    selected_id = st.selectbox("Select record to view details:", results['id'].tolist(), key='query_detail_select')

    if selected_id:
        with st.expander("View Details"):
            if data_type == 'Pairings':
                pairing, duty_days = db.get_pairing_details(selected_id)
                st.json(pairing)
                st.markdown("#### Duty Days")
                st.dataframe(pd.DataFrame(duty_days))
            else:
                line = db.get_bid_line_details(selected_id)
                st.json(line)
```

#### 4.3 Saved Queries

**Feature:**
```python
# Save current query
if st.button("💾 Save Query", key='query_save_button'):
    query_name = st.text_input("Query Name", key='query_name_input')
    if query_name:
        save_query(query_name, filters)
        st.success(f"Saved query: {query_name}")

# Load saved query
saved_queries = get_saved_queries()
if saved_queries:
    selected_query = st.selectbox("Load Saved Query", saved_queries, key='query_load_select')
    if st.button("Load", key='query_load_button'):
        load_query(selected_query)
        st.experimental_rerun()

# Share query link
query_url = generate_query_url(filters)
st.text_input("Shareable Link", value=query_url, key='query_share_link')
```

#### 4.4 Custom PDF Export

**Export Configuration Dialog:**
```python
if st.session_state.get('show_pdf_config'):
    st.markdown("### PDF Export Configuration")

    # Template selection
    templates = db.get_pdf_templates()
    template_names = [t['name'] for t in templates] + ["Custom"]
    selected_template = st.selectbox("Use Template", template_names, key='pdf_template_select')

    if selected_template == "Custom":
        st.markdown("#### Select Sections to Include")

        # Checkboxes for sections
        include_filters = st.checkbox("Query Filters Summary", value=True, key='pdf_include_filters')
        include_data_table = st.checkbox("Data Table", value=True, key='pdf_include_data_table')
        include_summary_stats = st.checkbox("Summary Statistics", value=True, key='pdf_include_summary_stats')
        include_pp_breakdown = st.checkbox("Pay Period Breakdown", value=False, key='pdf_include_pp_breakdown')
        include_reserve_stats = st.checkbox("Reserve Statistics", value=False, key='pdf_include_reserve_stats')

        # Save as template option (admin only)
        if user_role == 'admin':
            if st.checkbox("Save as Template", key='pdf_save_template_checkbox'):
                template_name = st.text_input("Template Name", key='pdf_template_name')
                is_public = st.checkbox("Make Public", value=True, key='pdf_template_public')

        # Generate PDF
        if st.button("Generate PDF", key='pdf_generate_button'):
            config = {
                'sections': [],
                'filters': filters
            }
            if include_filters: config['sections'].append('filters')
            if include_data_table: config['sections'].append('data_table')
            if include_summary_stats: config['sections'].append('summary_stats')
            if include_pp_breakdown: config['sections'].append('pp_breakdown')
            if include_reserve_stats: config['sections'].append('reserve_stats')

            # Generate PDF using pdf_templates.py
            pdf_engine = PDFExportEngine()
            pdf_bytes = pdf_engine.generate_query_pdf(results, config)

            st.download_button(
                "📥 Download PDF",
                pdf_bytes,
                f"query_results_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf"
            )

            # Save template if requested
            if user_role == 'admin' and st.session_state.get('pdf_save_template_checkbox'):
                db.save_pdf_template({
                    'name': template_name,
                    'config_json': config,
                    'is_public': is_public
                })
                st.success(f"Template '{template_name}' saved!")

    else:
        # Load template and generate
        template = db.get_pdf_template(selected_template)
        config = template['config_json']

        if st.button("Generate PDF", key='pdf_generate_from_template_button'):
            pdf_engine = PDFExportEngine()
            pdf_bytes = pdf_engine.generate_query_pdf(results, config)

            st.download_button(
                "📥 Download PDF",
                pdf_bytes,
                f"query_results_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf"
            )
```

**Deliverables:**
- Database Explorer tab with multi-dimensional filtering
- Paginated query results with row details
- Saved query functionality
- Custom PDF export with section selection
- Template-based PDF export

---

### Phase 5: Analysis & Visualization (3-4 days)

**Objective:** Create "Trends" tab with interactive charts and statistical analysis.

**Location:** `app.py`, new Tab 4 (or Tab 5 if Bulk Upload is separate)

#### 5.1 Time Series Charts

**Implementation:**
```python
import altair as alt

# In Trends tab
st.header("📊 Trend Analysis")

# Filter panel (reuse from Database Explorer)
# ... filters ...

# Metric selector
metric = st.selectbox(
    "Metric",
    ["Average CT", "Average BT", "Average DO", "Average DD",
     "EDW Trip %", "EDW TAFB %", "EDW Duty Day %"],
    key='trend_metric_select'
)

# Get trend data
trend_data = db.get_trend_data(metric, filters)

# Time series chart
chart = alt.Chart(trend_data).mark_line(point=True).encode(
    x=alt.X('date:T', title='Bid Period'),
    y=alt.Y('value:Q', title=metric),
    color=alt.Color('domicile:N', legend=alt.Legend(title="Domicile")),
    tooltip=['date:T', 'domicile:N', 'aircraft:N', 'value:Q']
).properties(
    width=800,
    height=400,
    title=f"{metric} Over Time"
).interactive()

st.altair_chart(chart, use_container_width=True)

# Multi-series comparison
st.markdown("### Compare Multiple Series")
compare_by = st.radio("Compare By", ["Domicile", "Aircraft", "Seat"], key='trend_compare_by')

# Generate multi-series chart
# ...
```

#### 5.2 Comparative Analysis

**Side-by-Side Comparison:**
```python
st.markdown("### Comparative Analysis")

# Select periods to compare
periods = db.get_bid_periods(filters)
selected_periods = st.multiselect(
    "Select Bid Periods to Compare",
    options=periods['id'].tolist(),
    format_func=lambda x: format_period_name(x),
    key='compare_periods_select'
)

if len(selected_periods) >= 2:
    comparison_data = db.compare_periods(selected_periods)

    # Side-by-side bar chart
    chart = alt.Chart(comparison_data).mark_bar().encode(
        x=alt.X('metric:N', title='Metric'),
        y=alt.Y('value:Q', title='Value'),
        color=alt.Color('period:N', legend=alt.Legend(title="Bid Period")),
        xOffset='period:N',
        tooltip=['period:N', 'metric:N', 'value:Q']
    ).properties(
        width=800,
        height=400,
        title="Bid Period Comparison"
    )

    st.altair_chart(chart, use_container_width=True)

    # Heatmap (Domicile × Aircraft × Metric)
    st.markdown("### Heatmap")

    heatmap_metric = st.selectbox("Metric", ["CT", "BT", "DO", "DD"], key='heatmap_metric_select')
    heatmap_data = db.get_heatmap_data(heatmap_metric, filters)

    chart = alt.Chart(heatmap_data).mark_rect().encode(
        x=alt.X('domicile:N', title='Domicile'),
        y=alt.Y('aircraft:N', title='Aircraft'),
        color=alt.Color('value:Q', scale=alt.Scale(scheme='viridis'), title=heatmap_metric),
        tooltip=['domicile:N', 'aircraft:N', 'value:Q']
    ).properties(
        width=600,
        height=400,
        title=f"{heatmap_metric} by Domicile and Aircraft"
    )

    st.altair_chart(chart, use_container_width=True)
```

#### 5.3 Distribution Analysis

**Histograms and Box Plots:**
```python
st.markdown("### Distribution Analysis")

# Metric selector
dist_metric = st.selectbox("Metric", ["CT", "BT", "DO", "DD"], key='dist_metric_select')

# Get distribution data
dist_data = db.get_distribution_data(dist_metric, filters)

# Histogram
hist_chart = alt.Chart(dist_data).mark_bar().encode(
    x=alt.X(f'{dist_metric}:Q', bin=alt.Bin(maxbins=30), title=dist_metric),
    y=alt.Y('count()', title='Frequency'),
    tooltip=['count()']
).properties(
    width=800,
    height=300,
    title=f"{dist_metric} Distribution"
)

st.altair_chart(hist_chart, use_container_width=True)

# Box plot
box_chart = alt.Chart(dist_data).mark_boxplot().encode(
    x=alt.X('domicile:N', title='Domicile'),
    y=alt.Y(f'{dist_metric}:Q', title=dist_metric),
    color='domicile:N'
).properties(
    width=800,
    height=300,
    title=f"{dist_metric} Box Plot by Domicile"
)

st.altair_chart(box_chart, use_container_width=True)

# Cumulative distribution
cumulative_data = dist_data.sort_values(dist_metric)
cumulative_data['cumulative'] = cumulative_data.index / len(cumulative_data)

cum_chart = alt.Chart(cumulative_data).mark_line().encode(
    x=alt.X(f'{dist_metric}:Q', title=dist_metric),
    y=alt.Y('cumulative:Q', title='Cumulative %', axis=alt.Axis(format='%')),
    tooltip=[f'{dist_metric}:Q', 'cumulative:Q']
).properties(
    width=800,
    height=300,
    title=f"{dist_metric} Cumulative Distribution"
)

st.altair_chart(cum_chart, use_container_width=True)
```

#### 5.4 Anomaly Detection

**Statistical Outlier Detection:**
```python
st.markdown("### Anomaly Detection")

# Threshold selector
threshold = st.slider("Z-Score Threshold", min_value=1.0, max_value=3.0, value=2.0, step=0.1, key='anomaly_threshold')

# Detect anomalies
anomalies = db.detect_anomalies(filters, threshold)

if not anomalies.empty:
    st.warning(f"⚠️ Found {len(anomalies)} anomalies (z-score > {threshold})")

    # Anomaly table
    st.dataframe(
        anomalies[['period', 'domicile', 'aircraft', 'metric', 'value', 'z_score']],
        use_container_width=True
    )

    # Scatter plot with anomalies highlighted
    all_data = db.query_bid_lines(filters)
    all_data['is_anomaly'] = all_data['id'].isin(anomalies['id'])

    scatter_chart = alt.Chart(all_data).mark_circle(size=60).encode(
        x=alt.X('total_ct:Q', title='Total CT'),
        y=alt.Y('total_bt:Q', title='Total BT'),
        color=alt.condition(
            alt.datum.is_anomaly,
            alt.value('red'),
            alt.value('steelblue')
        ),
        tooltip=['line_number:N', 'total_ct:Q', 'total_bt:Q', 'is_anomaly:N']
    ).properties(
        width=800,
        height=400,
        title="CT vs BT (Anomalies in Red)"
    ).interactive()

    st.altair_chart(scatter_chart, use_container_width=True)

    # Drill-down
    st.markdown("### Anomaly Details")
    selected_anomaly = st.selectbox("Select Anomaly", anomalies['id'].tolist(), key='anomaly_detail_select')
    if selected_anomaly:
        anomaly_detail = db.get_bid_line_details(selected_anomaly)
        st.json(anomaly_detail)
else:
    st.success(f"✅ No anomalies detected with z-score > {threshold}")
```

#### 5.5 Trend Analysis PDF Export

**Export Configuration:**
```python
st.markdown("### Export Trend Analysis")

if st.button("📄 Export PDF", key='trend_export_pdf_button'):
    st.session_state['show_trend_pdf_config'] = True

if st.session_state.get('show_trend_pdf_config'):
    st.markdown("#### PDF Configuration")

    # Template selection
    templates = db.get_pdf_templates()
    template_names = [t['name'] for t in templates if 'trend' in t['name'].lower()] + ["Custom"]
    selected_template = st.selectbox("Use Template", template_names, key='trend_pdf_template_select')

    if selected_template == "Custom":
        st.markdown("##### Select Visualizations to Include")

        include_time_series = st.checkbox("Time Series Charts", value=True, key='trend_pdf_time_series')
        include_comparison = st.checkbox("Comparative Bar Charts", value=True, key='trend_pdf_comparison')
        include_heatmap = st.checkbox("Heatmap", value=False, key='trend_pdf_heatmap')
        include_distribution = st.checkbox("Distribution Charts", value=True, key='trend_pdf_distribution')
        include_anomalies = st.checkbox("Anomaly Detection", value=True, key='trend_pdf_anomalies')
        include_summary_table = st.checkbox("Statistical Summary Table", value=True, key='trend_pdf_summary_table')

        # Chart options
        st.markdown("##### Chart Options")
        chart_layout = st.radio("Chart Layout", ["Compact (2 per page)", "Full Page (1 per page)"], key='trend_pdf_layout')
        color_scheme = st.radio("Color Scheme", ["Color", "Grayscale"], key='trend_pdf_color_scheme')

        # Generate PDF
        if st.button("Generate PDF", key='trend_pdf_generate_button'):
            config = {
                'charts': [],
                'layout': 'compact' if 'Compact' in chart_layout else 'full_page',
                'color_scheme': color_scheme.lower(),
                'filters': filters
            }

            if include_time_series: config['charts'].append('time_series')
            if include_comparison: config['charts'].append('comparison')
            if include_heatmap: config['charts'].append('heatmap')
            if include_distribution: config['charts'].append('distribution')
            if include_anomalies: config['charts'].append('anomalies')
            if include_summary_table: config['charts'].append('summary_table')

            # Generate PDF
            pdf_engine = PDFExportEngine()
            pdf_bytes = pdf_engine.generate_trend_pdf(trend_data, config)

            st.download_button(
                "📥 Download PDF",
                pdf_bytes,
                f"trend_analysis_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf"
            )
```

**Deliverables:**
- Interactive time series charts (Altair)
- Comparative analysis (bar charts, heatmaps, scatter plots)
- Distribution analysis (histograms, box plots, cumulative curves)
- Anomaly detection with configurable threshold
- Custom PDF export for trend analysis

---

### Phase 6: Authentication & PDF Template Management (2-3 days)

**Objective:** Implement multi-user authentication and admin template editor.

#### 6.1 Supabase Auth Integration

**Login Page:**
```python
# auth.py

import streamlit as st
from supabase import Client

def login_page(supabase_client: Client):
    """Display login page and handle authentication."""
    st.title("🔐 Login")

    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:
        email = st.text_input("Email", key='login_email')
        password = st.text_input("Password", type='password', key='login_password')

        if st.button("Login", key='login_button'):
            try:
                response = supabase_client.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })

                # Store session in st.session_state
                st.session_state['user'] = response.user
                st.session_state['session'] = response.session

                # Get user profile to check role
                profile = supabase_client.table('profiles').select('*').eq('id', response.user.id).single().execute()
                st.session_state['user_role'] = profile.data['role']

                st.success(f"Welcome, {email}!")
                st.experimental_rerun()

            except Exception as e:
                st.error(f"Login failed: {str(e)}")

    with tab2:
        email = st.text_input("Email", key='signup_email')
        password = st.text_input("Password", type='password', key='signup_password')
        confirm_password = st.text_input("Confirm Password", type='password', key='signup_confirm_password')

        if st.button("Sign Up", key='signup_button'):
            if password != confirm_password:
                st.error("Passwords don't match")
            else:
                try:
                    response = supabase_client.auth.sign_up({
                        "email": email,
                        "password": password
                    })
                    st.success("Account created! Please log in.")
                except Exception as e:
                    st.error(f"Sign up failed: {str(e)}")

def logout():
    """Clear session and log out user."""
    st.session_state.clear()
    st.experimental_rerun()

def check_auth():
    """Check if user is authenticated."""
    return 'user' in st.session_state and st.session_state['user'] is not None

def get_user_role():
    """Get current user's role."""
    return st.session_state.get('user_role', 'user')
```

**App Integration:**
```python
# In app.py

from database import SupabaseClient
from auth import login_page, logout, check_auth, get_user_role

# Initialize Supabase
db = SupabaseClient()

# Check authentication
if not check_auth():
    login_page(db.client)
    st.stop()

# User is authenticated
user_role = get_user_role()

# Show user profile in sidebar
st.sidebar.markdown("---")
st.sidebar.markdown(f"👤 {st.session_state['user'].email}")
st.sidebar.markdown(f"Role: {user_role}")
if st.sidebar.button("Logout"):
    logout()

# Show/hide tabs based on role
if user_role == 'admin':
    tabs = st.tabs(["EDW Pairing Analyzer", "Bid Line Analyzer", "Database Explorer", "Trends", "Bulk Upload", "Admin Tools"])
else:
    tabs = st.tabs(["Database Explorer", "Trends"])

# ... rest of app ...
```

#### 6.2 Role-Based UI

**Admin-Only Features:**
- Tab 1 (EDW Pairing Analyzer) - Admin only
- Tab 2 (Bid Line Analyzer) - Admin only
- "Save to Database" buttons - Admin only
- Bulk Upload tab - Admin only
- Admin Tools tab - Admin only
- PDF template creation - Admin only

**User Features:**
- Database Explorer tab
- Trends tab
- PDF export using public templates

#### 6.3 Admin Tools Tab

**User Management:**
```python
# In Admin Tools tab
st.header("👥 User Management")

# List all users
users = db.get_users()
users_df = pd.DataFrame(users)

st.dataframe(users_df[['email', 'role', 'created_at']], use_container_width=True)

# Update user role
st.markdown("### Update User Role")
selected_user = st.selectbox("Select User", users_df['email'].tolist(), key='admin_user_select')
new_role = st.radio("New Role", ["user", "admin"], key='admin_new_role')

if st.button("Update Role", key='admin_update_role_button'):
    user_id = users_df[users_df['email'] == selected_user]['id'].values[0]
    success = db.update_user_role(user_id, new_role)
    if success:
        st.success(f"Updated {selected_user} to {new_role}")
    else:
        st.error("Failed to update role")
```

**PDF Template Editor:**
```python
st.markdown("---")
st.header("📄 PDF Template Editor")

# List existing templates
templates = db.get_pdf_templates(public_only=False)
templates_df = pd.DataFrame(templates)

st.dataframe(templates_df[['name', 'description', 'is_public', 'is_default']], use_container_width=True)

# Create/Edit template
st.markdown("### Create/Edit Template")

# Template selector
template_mode = st.radio("Mode", ["Create New", "Edit Existing"], key='template_mode')

if template_mode == "Edit Existing":
    selected_template_id = st.selectbox(
        "Select Template",
        templates_df['id'].tolist(),
        format_func=lambda x: templates_df[templates_df['id'] == x]['name'].values[0],
        key='template_edit_select'
    )
    template = db.get_pdf_template(selected_template_id)

    # Pre-fill form with existing values
    template_name = st.text_input("Template Name", value=template['name'], key='template_name')
    template_description = st.text_area("Description", value=template['description'], key='template_description')

    # Load config
    config = template['config_json']
else:
    template_name = st.text_input("Template Name", key='template_name')
    template_description = st.text_area("Description", key='template_description')
    config = {'sections': [], 'charts': []}

# Template configuration
st.markdown("#### Template Configuration")

# Sections (for query exports)
st.markdown("##### Query Export Sections")
sections = {
    'filters': st.checkbox("Query Filters Summary", value='filters' in config.get('sections', []), key='template_section_filters'),
    'data_table': st.checkbox("Data Table", value='data_table' in config.get('sections', []), key='template_section_data_table'),
    'summary_stats': st.checkbox("Summary Statistics", value='summary_stats' in config.get('sections', []), key='template_section_summary_stats'),
    'pp_breakdown': st.checkbox("Pay Period Breakdown", value='pp_breakdown' in config.get('sections', []), key='template_section_pp_breakdown'),
    'reserve_stats': st.checkbox("Reserve Statistics", value='reserve_stats' in config.get('sections', []), key='template_section_reserve_stats')
}

# Charts (for trend exports)
st.markdown("##### Trend Analysis Charts")
charts = {
    'time_series': st.checkbox("Time Series Charts", value='time_series' in config.get('charts', []), key='template_chart_time_series'),
    'comparison': st.checkbox("Comparative Bar Charts", value='comparison' in config.get('charts', []), key='template_chart_comparison'),
    'heatmap': st.checkbox("Heatmap", value='heatmap' in config.get('charts', []), key='template_chart_heatmap'),
    'distribution': st.checkbox("Distribution Charts", value='distribution' in config.get('charts', []), key='template_chart_distribution'),
    'anomalies': st.checkbox("Anomaly Detection", value='anomalies' in config.get('charts', []), key='template_chart_anomalies'),
    'summary_table': st.checkbox("Statistical Summary Table", value='summary_table' in config.get('charts', []), key='template_chart_summary_table')
}

# Chart options
st.markdown("##### Chart Options")
chart_layout = st.radio(
    "Chart Layout",
    ["compact", "full_page"],
    index=0 if config.get('layout', 'compact') == 'compact' else 1,
    key='template_chart_layout'
)
color_scheme = st.radio(
    "Color Scheme",
    ["color", "grayscale"],
    index=0 if config.get('color_scheme', 'color') == 'color' else 1,
    key='template_color_scheme'
)

# Visibility
st.markdown("##### Visibility")
is_public = st.checkbox("Make Public (visible to all users)", value=template.get('is_public', True) if template_mode == "Edit Existing" else True, key='template_is_public')
is_default = st.checkbox("Set as Default Template", value=template.get('is_default', False) if template_mode == "Edit Existing" else False, key='template_is_default')

# Preview button
if st.button("👁️ Preview Template", key='template_preview_button'):
    st.markdown("#### Preview")
    st.write("**Sections:**", [k for k, v in sections.items() if v])
    st.write("**Charts:**", [k for k, v in charts.items() if v])
    st.write("**Layout:**", chart_layout)
    st.write("**Color Scheme:**", color_scheme)
    st.write("**Public:**", is_public)
    st.write("**Default:**", is_default)

# Save button
if st.button("💾 Save Template", key='template_save_button'):
    new_config = {
        'sections': [k for k, v in sections.items() if v],
        'charts': [k for k, v in charts.items() if v],
        'layout': chart_layout,
        'color_scheme': color_scheme
    }

    template_data = {
        'name': template_name,
        'description': template_description,
        'config_json': new_config,
        'is_public': is_public,
        'is_default': is_default
    }

    if template_mode == "Edit Existing":
        template_data['id'] = selected_template_id

    try:
        template_id = db.save_pdf_template(template_data)
        st.success(f"✅ Template saved! (ID: {template_id})")
        st.experimental_rerun()
    except Exception as e:
        st.error(f"❌ Error saving template: {str(e)}")

# Delete button (for existing templates)
if template_mode == "Edit Existing":
    if st.button("🗑️ Delete Template", key='template_delete_button'):
        if st.checkbox("Confirm deletion", key='template_delete_confirm'):
            success = db.delete_pdf_template(selected_template_id)
            if success:
                st.success("✅ Template deleted")
                st.experimental_rerun()
            else:
                st.error("❌ Failed to delete template")
```

**Deliverables:**
- Login/signup pages with Supabase Auth
- Session management in Streamlit
- Role-based UI (admin vs. user tabs)
- Admin Tools tab with user management
- PDF template editor with drag-drop ordering (optional enhancement)
- Preview functionality for templates

---

### Phase 7: Data Migration & Testing (1-2 days)

**Objective:** Backfill historical data and thoroughly test all features.

#### 7.1 Historical Data Backfill

**Preparation:**
1. Create CSV templates for historical data:
   - `pairings_template.csv`
   - `bid_lines_template.csv`

2. Convert historical PDFs to CSV format:
   - Parse old PDFs using existing analyzers
   - Export to CSV
   - Manually review for accuracy

3. Use Bulk Upload tool to import data

**Validation:**
```python
# Validation script: validate_backfill.py

from database import SupabaseClient

db = SupabaseClient()

# Check row counts
print("Bid Periods:", db.client.table('bid_periods').select('count', count='exact').execute().count)
print("Pairings:", db.client.table('pairings').select('count', count='exact').execute().count)
print("Bid Lines:", db.client.table('bid_lines').select('count', count='exact').execute().count)

# Check for duplicates
duplicates = db.client.rpc('check_duplicates').execute()
if duplicates.data:
    print("⚠️ Duplicates found:", duplicates.data)
else:
    print("✅ No duplicates found")

# Validate aggregates
for bid_period_id in db.client.table('bid_periods').select('id').execute().data:
    stats = db.calculate_period_stats(bid_period_id['id'])
    print(f"Bid Period {bid_period_id['id']}:", stats)
```

#### 7.2 Testing Scenarios

**Admin Workflows:**

1. **Upload New Pairing Data**
   - Parse pairing PDF in Tab 1
   - Click "Save to Database"
   - Verify data appears in Database Explorer

2. **Upload New Bid Line Data**
   - Parse bid line PDF in Tab 2
   - Click "Save to Database"
   - Verify data appears in Database Explorer

3. **Bulk Upload Historical Data**
   - Upload CSV file in Bulk Upload tab
   - Map columns
   - Verify data appears in Database Explorer

4. **Edit/Delete Data**
   - Query data in Database Explorer
   - Edit a record
   - Delete a record
   - Verify changes persist

5. **Create PDF Template**
   - Go to Admin Tools tab
   - Create new PDF template
   - Preview template
   - Save template
   - Verify template appears in export dialogs

6. **Manage User Roles**
   - Go to Admin Tools tab
   - Change user role from 'user' to 'admin'
   - Log in as that user and verify admin features appear

**User Workflows:**

1. **Query Data**
   - Go to Database Explorer tab
   - Select filters (domicile, aircraft, seat, date range)
   - Run query
   - Verify results are accurate

2. **View Trends**
   - Go to Trends tab
   - Select metric (e.g., Average CT)
   - View time series chart
   - Verify chart shows correct data

3. **Export Data**
   - Query data in Database Explorer
   - Export to CSV
   - Export to Excel
   - Export to PDF (using template)
   - Verify exports are correct

4. **Comparative Analysis**
   - Go to Trends tab
   - Select multiple bid periods
   - View side-by-side comparison
   - Verify comparison is accurate

5. **Anomaly Detection**
   - Go to Trends tab
   - Set z-score threshold
   - View anomaly table
   - Drill down into anomaly details
   - Verify anomalies are statistically valid

**Performance Testing:**

1. **Query Performance**
   - Query with 10K+ records
   - Measure response time (should be < 3 seconds)
   - Test pagination performance

2. **Chart Rendering**
   - Load Trends tab with multiple charts
   - Measure render time (should be < 5 seconds)
   - Test interactivity (zoom, pan)

3. **PDF Generation**
   - Generate PDF with all sections
   - Measure generation time (should be < 30 seconds)
   - Verify PDF quality

**Authentication Testing:**

1. **Login/Logout**
   - Log in with valid credentials
   - Verify session persists across page refreshes
   - Log out and verify session cleared

2. **Role Restrictions**
   - Log in as 'user'
   - Verify upload tabs are hidden
   - Verify read-only access to data

3. **Sign Up**
   - Create new account
   - Verify default role is 'user'
   - Verify profile is created

#### 7.3 Documentation

**User Guide** (`docs/USER_GUIDE.md`):
- How to log in
- How to query data
- How to view trends
- How to export data
- How to use PDF templates

**Admin Guide** (`docs/ADMIN_GUIDE.md`):
- How to upload new data
- How to use bulk upload tool
- How to manage users
- How to create PDF templates
- How to edit/delete data

**Database Schema Documentation** (`docs/DATABASE_SCHEMA.md`):
- Table descriptions
- Column definitions
- Relationships
- Indexes
- RLS policies

**Deliverables:**
- 6-12 months of historical data in database
- Validation script confirming data integrity
- Complete test coverage (admin + user workflows)
- Performance benchmarks documented
- User and admin guides published

---

## Technology Stack Summary

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Database** | Supabase (PostgreSQL) | Data storage, authentication, RLS |
| **Backend** | Python 3.x | Data processing, analysis |
| **Frontend** | Streamlit | Web UI framework |
| **Charts** | Altair | Interactive visualizations |
| **PDF Generation** | ReportLab | Custom PDF reports |
| **PDF Parsing** | PyPDF2, pdfplumber | Extract data from PDFs |
| **Auth** | Supabase Auth | User authentication |
| **Deployment** | Streamlit Cloud / Docker | Hosting |

---

## Development Dependencies

Update `requirements.txt`:

```txt
streamlit>=1.28.0
pandas>=2.0.0
numpy>=1.24.0
PyPDF2>=3.0.0
pdfplumber>=0.10.0
reportlab>=4.0.0
fpdf2>=2.7.0
altair>=5.0.0
supabase>=1.0.0
python-dotenv>=1.0.0
plotly>=5.17.0
openpyxl>=3.1.0
```

---

## Environment Variables

`.env` file structure:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here

# Optional: Service Role Key (for admin operations)
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here

# Optional: Custom Configuration
APP_ENV=production
DEBUG=false
```

---

## Deployment Considerations

### Option 1: Streamlit Cloud

**Pros:**
- Easy deployment (connect GitHub repo)
- Free tier available
- Automatic updates on git push

**Cons:**
- Limited resources on free tier
- Public URL (not private by default)

**Steps:**
1. Push code to GitHub (excluding `.env`)
2. Connect repo to Streamlit Cloud
3. Add environment variables in Streamlit Cloud dashboard
4. Deploy

### Option 2: Docker + Cloud Run / AWS ECS

**Pros:**
- Full control over resources
- Can be deployed privately
- Scalable

**Cons:**
- More complex setup
- Costs for hosting

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

---

## Timeline Summary

| Phase | Duration | Description |
|-------|----------|-------------|
| **Phase 1** | 2-3 days | Database schema & Supabase setup |
| **Phase 2** | 2-3 days | Database module (`database.py`) |
| **Phase 3** | 1-2 days | Admin upload interface |
| **Phase 4** | 2-3 days | User query interface |
| **Phase 5** | 3-4 days | Analysis & visualization |
| **Phase 6** | 2-3 days | Authentication & templates |
| **Phase 7** | 1-2 days | Data migration & testing |
| **Total** | **~2.5 weeks** | Full implementation |

---

## Success Criteria

### Phase 1-2 (Database Foundation)
- [ ] Supabase project created
- [ ] All 6 tables created with indexes
- [ ] RLS policies active and tested
- [ ] `database.py` module complete with all functions
- [ ] Unit tests passing

### Phase 3 (Admin Upload)
- [ ] "Save to Database" buttons in Tabs 1 & 2
- [ ] Bulk upload tool functional
- [ ] Conflict handling works correctly
- [ ] Success/error messages display properly

### Phase 4 (User Query)
- [ ] Multi-dimensional filtering works
- [ ] Paginated results display correctly
- [ ] CSV/Excel export works
- [ ] Custom PDF export with section selection works
- [ ] Template-based PDF export works

### Phase 5 (Analysis)
- [ ] Time series charts render correctly
- [ ] Comparative analysis works (bar charts, heatmaps)
- [ ] Distribution analysis works (histograms, box plots)
- [ ] Anomaly detection identifies outliers correctly
- [ ] Trend PDF export works

### Phase 6 (Auth & Templates)
- [ ] Login/signup works
- [ ] Session persists across page refreshes
- [ ] Role-based UI works (admin vs. user tabs)
- [ ] Admin can create/edit/delete PDF templates
- [ ] Templates appear in export dialogs

### Phase 7 (Migration & Testing)
- [ ] 6-12 months of historical data imported
- [ ] All admin workflows tested and passing
- [ ] All user workflows tested and passing
- [ ] Performance benchmarks met (queries < 3s, PDFs < 30s)
- [ ] Documentation complete

---

## Future Enhancements (Post-Launch)

1. **Email Notifications**
   - Notify admins when new data is uploaded
   - Notify users when anomalies are detected

2. **Scheduled Reports**
   - Auto-generate monthly reports
   - Email PDFs to stakeholders

3. **Advanced Analytics**
   - Machine learning for trend prediction
   - Clustering analysis (group similar bid periods)

4. **Mobile Optimization**
   - Responsive design for tablets/phones
   - Mobile-friendly charts

5. **API Access**
   - REST API for programmatic access
   - API keys for external integrations

6. **Data Validation Rules**
   - Admin-configurable validation rules
   - Auto-reject invalid data during upload

7. **Audit Log**
   - Track all data changes (who, what, when)
   - Rollback capability

8. **Multi-Airline Support**
   - Support multiple airlines in same database
   - Airline-specific configurations

---

## Support & Maintenance

### Regular Maintenance Tasks

1. **Weekly:**
   - Monitor database size and performance
   - Check for failed uploads or errors
   - Review user feedback

2. **Monthly:**
   - Backup database
   - Review and optimize slow queries
   - Update dependencies

3. **Quarterly:**
   - Review user roles and permissions
   - Archive old data (if needed)
   - Performance audit

### Troubleshooting

**Issue: Slow Query Performance**
- Check indexes are being used (EXPLAIN ANALYZE)
- Consider adding composite indexes
- Optimize filter combinations

**Issue: PDF Generation Fails**
- Check reportlab version
- Verify chart images are valid
- Check template configuration

**Issue: Authentication Not Working**
- Verify Supabase credentials in `.env`
- Check RLS policies are enabled
- Verify user role in `profiles` table

**Issue: Data Not Saving**
- Check user has admin role
- Verify foreign key constraints
- Check for duplicate records

---

## Contact & Resources

- **Supabase Documentation:** https://supabase.com/docs
- **Streamlit Documentation:** https://docs.streamlit.io
- **Altair Gallery:** https://altair-viz.github.io/gallery/
- **ReportLab User Guide:** https://www.reportlab.com/docs/reportlab-userguide.pdf

---

**Document Version:** 1.0
**Last Updated:** 2025-10-27
**Author:** Claude Code
**Status:** Ready for Implementation
