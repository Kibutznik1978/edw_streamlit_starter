# IPA Operations Dashboard Enhancement

**Document Version:** 1.0
**Created:** 2025-10-31
**Status:** Future Enhancement (Not Yet Started)
**Dependencies:** Requires completion of `SUPABASE_INTEGRATION_ROADMAP.md` Phases 1-5

---

## Overview

This document outlines a major enhancement to transform the current single-bid-period analysis app into a comprehensive **IPA-style Operations Dashboard** with multi-bid-period trending, fleet-level aggregation, and professional operations reporting.

**Reference Document:** `docs/IPA BID PACKAGE REPORT, 25-07.pdf`

---

## Current State vs. IPA Report

### What We Currently Have

- **Single bid period analysis** - Analyze one PDF at a time
- **Individual line/trip data** - Granular pairing and bid line records
- **Basic statistics** - CT, BT, DO, DD averages and distributions
- **Reserve detection** - Identifies reserve lines
- **PDF export** - 3-page analysis reports
- **Database storage** - Individual records in Supabase (Phases 1-5)

### What IPA Report Provides (That We Lack)

1. **Multi-bid-period time series** - Track 8+ bid periods over time
2. **Fleet-level aggregation** - Total crew block hours, line counts by domicile/aircraft
3. **Period-over-period comparison** - Current vs. previous bid period with % change
4. **Schedule type distribution** - REG/RES/VTO/HOT/RDG percentages
5. **Reserve line trending** - Reserve percentage over time
6. **No-Bidders tracking** - Training, military, LOA, medical
7. **Line credit distribution** - Histogram with 5 buckets (<70, 70-74, 75-80, 80-85, >85)
8. **Fleet small multiples** - Sparkline charts for each fleet
9. **Aggregated statistics** - System-wide averages (PP credit, block hours, days off/duty days)
10. **Professional dashboard layout** - Multi-chart, data-dense single-page view

---

## IPA Report Detailed Analysis

### Page Layout Structure

The IPA report is a **single-page, data-dense dashboard** with:

#### Section 1: Fleet Comparison Table (Top Left)
**Crew Block Hours** and **Number Regular Lines** by fleet:
- Current bid period (25-07) vs. previous (24-07)
- Change (+/- absolute) and % change
- Color coding (red for negative, green/black for positive)
- Total row at bottom
- 8 fleets tracked: ANC 747, MIA, ONT, SDF 747, SDF 757, A300, SDF MD11, SDFZ

#### Section 2: Time Series Charts (6 Large Charts)
1. **Scheduled Flying Hours of Work (Crew Block Hours)** - Stacked area chart, 8 bid periods
2. **Available Flying Schedules (Regular Lines)** - Stacked area chart, 8 bid periods
3. **Scheduled Duty Days** - Stacked area chart, 8 bid periods
4. **Average Scheduled Block Hours per Reg Line** - Line chart, 8 bid periods
5. **Reserve Lines as % of Bid Package** - Area chart with trend line, 8 bid periods
6. **No-Bidders (Training, Military, LOA, Medical)** - Stacked area chart, 5 bid periods

#### Section 3: Fleet Small Multiples (9 Small Charts - Top Right)
- Grid layout: 3 columns × 3 rows
- One chart per fleet showing crew block hours trend
- 4 bid periods per chart (22-07, 23-07, 24-07, 25-07)
- Consistent y-axis scaling for comparison
- Simple line charts in small format

#### Section 4: Current Period Analysis (Bottom Row - 3 Columns)

**Left Column: Regular Line Stats**
- % of PP Credit Below Guarantee: 39%
- PP Credit Range: 60.0 - 89.6
- Average PP Credit: 77.0
- Average PP Pay Credit: 78.3
- Average PP Block Hours: 48.9
- Average BP Calendar Days Off / Duty Days: 14.1 / 12.9

**Middle Column: Composition Charts**
- **Schedules Pie Chart**: REG 69%, RES 14%, VTO 15%, HOT 2%, RDG 0%
- **Fleet Pie Chart**: 757 (75), A30 (52), 767 (96), M1F (27), 747 (43), TOT 293
- **Line Credit Distribute Histogram**: 5 buckets with percentages

**Right Column: Average Line Credit Trends**
- **Average Line Credit (per Pay Period)**: Line chart, 5 bid periods (21-07 to 25-07)

### Key Metrics Tracked

**Operational Metrics:**
- Total Crew Block Hours (by fleet and aggregate)
- Number Regular Lines (by fleet and aggregate)
- Scheduled Duty Days (aggregate)
- Average Block Hours per Regular Line (system-wide)
- Reserve Line Percentage (system-wide)

**Line Quality Metrics:**
- Average PP Credit (pay period credit time)
- Average PP Pay Credit (includes premiums)
- Average PP Block Hours (actual flying time)
- Average Days Off / Duty Days (quality of life)
- % Below Guarantee (lines under minimum credit)
- Credit Range (min-max spread)

**Composition Metrics:**
- Schedule types: REG, RES, VTO, HOT, RDG (percentages)
- Fleet distribution (by aircraft type)
- Line credit distribution (5 buckets with counts and percentages)
- No-Bidders count (by category: training, military, LOA, medical)

---

## Database Schema Enhancements

### New Table: `bid_period_summary`

Aggregated metrics for each bid period, calculated during data save.

```sql
CREATE TABLE bid_period_summary (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  bid_period_id UUID NOT NULL REFERENCES bid_periods(id) ON DELETE CASCADE,

  -- Operational Metrics (from pairings)
  total_crew_block_hours DECIMAL(10,2),  -- Sum of all pairing block hours
  total_tafb_hours DECIMAL(10,2),        -- Sum of all TAFB hours
  total_duty_days INTEGER,                -- Sum across all pairings
  total_trips INTEGER,                    -- Count of pairings
  edw_trips INTEGER,                      -- Count of EDW pairings
  hot_standby_trips INTEGER,              -- Count of hot standby pairings

  -- Line Metrics (from bid_lines)
  total_regular_lines INTEGER,            -- Count of non-reserve lines
  total_reserve_lines INTEGER,            -- Count of reserve lines
  total_vto_lines INTEGER,                -- Count of VTO lines
  total_hot_standby_lines INTEGER,        -- Count of hot standby lines
  total_rdg_lines INTEGER,                -- Count of RDG (redeye guarantee) lines

  -- Average Line Quality Metrics
  avg_pp_credit DECIMAL(5,2),             -- Average pay period credit time
  avg_pp_pay_credit DECIMAL(5,2),         -- Average pay period pay credit (with premiums)
  avg_pp_block_hours DECIMAL(5,2),        -- Average pay period block hours
  avg_days_off DECIMAL(4,2),              -- Average days off per line
  avg_duty_days DECIMAL(4,2),             -- Average duty days per line

  -- Distribution Metrics
  pp_credit_range_min DECIMAL(5,2),       -- Minimum PP credit in bid package
  pp_credit_range_max DECIMAL(5,2),       -- Maximum PP credit in bid package
  pct_below_guarantee DECIMAL(5,2),       -- % of lines below 75 hours (or custom threshold)
  reserve_line_pct DECIMAL(5,2),          -- Reserve lines as % of total lines

  -- Line Credit Distribution (5 buckets)
  credit_bucket_below_70_count INTEGER,
  credit_bucket_70_74_count INTEGER,
  credit_bucket_75_80_count INTEGER,
  credit_bucket_80_85_count INTEGER,
  credit_bucket_above_85_count INTEGER,
  credit_bucket_below_70_pct DECIMAL(5,2),
  credit_bucket_70_74_pct DECIMAL(5,2),
  credit_bucket_75_80_pct DECIMAL(5,2),
  credit_bucket_80_85_pct DECIMAL(5,2),
  credit_bucket_above_85_pct DECIMAL(5,2),

  -- No-Bidders Tracking (future enhancement - requires manual input)
  no_bidders_training INTEGER DEFAULT 0,
  no_bidders_military INTEGER DEFAULT 0,
  no_bidders_loa INTEGER DEFAULT 0,
  no_bidders_medical INTEGER DEFAULT 0,

  -- Audit
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  UNIQUE(bid_period_id)
);

-- Indexes
CREATE INDEX idx_summary_bid_period ON bid_period_summary(bid_period_id);
CREATE INDEX idx_summary_metrics ON bid_period_summary(
  total_crew_block_hours,
  total_regular_lines,
  reserve_line_pct
);
```

### Updated Materialized View: `bid_period_trends`

Enhance existing view to include summary data:

```sql
CREATE MATERIALIZED VIEW bid_period_trends AS
SELECT
  bp.id AS bid_period_id,
  bp.period,
  bp.domicile,
  bp.aircraft,
  bp.seat,
  bp.start_date,
  bp.end_date,

  -- Summary metrics (if summary exists)
  s.total_crew_block_hours,
  s.total_regular_lines,
  s.total_reserve_lines,
  s.reserve_line_pct,
  s.avg_pp_credit,
  s.avg_pp_block_hours,
  s.avg_days_off,
  s.avg_duty_days,

  -- Pairing metrics (if EDW data exists)
  COUNT(DISTINCT p.id) AS total_trips_detail,
  COUNT(DISTINCT p.id) FILTER (WHERE p.is_edw) AS edw_trips,
  ROUND(100.0 * COUNT(p.id) FILTER (WHERE p.is_edw) / NULLIF(COUNT(p.id), 0), 2) AS edw_trip_pct,

  -- Bid line metrics (if bid line data exists)
  COUNT(DISTINCT bl.id) AS total_lines_detail,
  ROUND(AVG(bl.total_ct), 2) AS ct_avg,
  ROUND(AVG(bl.total_bt), 2) AS bt_avg,
  ROUND(AVG(bl.total_do::numeric), 1) AS do_avg,
  ROUND(AVG(bl.total_dd::numeric), 1) AS dd_avg

FROM bid_periods bp
LEFT JOIN bid_period_summary s ON s.bid_period_id = bp.id
LEFT JOIN pairings p ON p.bid_period_id = bp.id AND p.deleted_at IS NULL
LEFT JOIN bid_lines bl ON bl.bid_period_id = bp.id AND bl.deleted_at IS NULL AND bl.is_reserve = false
WHERE bp.deleted_at IS NULL
GROUP BY bp.id, bp.period, bp.domicile, bp.aircraft, bp.seat, bp.start_date, bp.end_date,
  s.total_crew_block_hours, s.total_regular_lines, s.total_reserve_lines, s.reserve_line_pct,
  s.avg_pp_credit, s.avg_pp_block_hours, s.avg_days_off, s.avg_duty_days
ORDER BY bp.start_date DESC;

-- Indexes
CREATE INDEX idx_trends_v2_domicile ON bid_period_trends(domicile, start_date DESC);
CREATE INDEX idx_trends_v2_aircraft ON bid_period_trends(aircraft, start_date DESC);
CREATE INDEX idx_trends_v2_period ON bid_period_trends(period DESC);
```

---

## Enhanced Data Capture

### Tab 1: EDW Pairing Analyzer - New Aggregations

**Current:** Saves individual pairing records to `pairings` table

**Enhancement:** Calculate and save to `bid_period_summary`:
- `total_crew_block_hours` - Sum of all `block_hours` from pairings
- `total_tafb_hours` - Sum of all `tafb_hours` from pairings
- `total_duty_days` - Sum of `num_duty_days` across all pairings
- `total_trips` - Count of all pairings
- `edw_trips` - Count where `is_edw = true`
- `hot_standby_trips` - Count where detected as hot standby

**Implementation Location:** `database.py` - `save_pairing_data_to_db()`

### Tab 2: Bid Line Analyzer - New Aggregations

**Current:** Saves individual bid line records to `bid_lines` table

**Enhancement:** Calculate and save to `bid_period_summary`:

**Line Counts:**
- `total_regular_lines` - Count where `is_reserve = false`
- `total_reserve_lines` - Count where `is_reserve = true`
- `total_vto_lines` - Count where `vto_type IS NOT NULL`
- `total_hot_standby_lines` - Count where `is_hot_standby = true`
- `total_rdg_lines` - Count where line contains "RDG" keyword (future)

**Averages (exclude reserve lines):**
- `avg_pp_credit` - AVG(total_ct / 2) for non-reserve lines
- `avg_pp_pay_credit` - Same as avg_pp_credit (premiums not currently tracked)
- `avg_pp_block_hours` - AVG(total_bt / 2) for non-reserve lines
- `avg_days_off` - AVG(total_do) for non-reserve lines
- `avg_duty_days` - AVG(total_dd) for non-reserve lines

**Distribution Metrics:**
- `pp_credit_range_min` - MIN(total_ct / 2) for non-reserve lines
- `pp_credit_range_max` - MAX(total_ct / 2) for non-reserve lines
- `pct_below_guarantee` - % of lines where (total_ct / 2) < 75
- `reserve_line_pct` - (reserve_lines / total_lines) * 100

**Line Credit Distribution (5 buckets based on PP credit):**
```python
pp_credit = df['total_ct'] / 2  # Pay period credit

buckets = {
    'below_70': pp_credit < 70,
    '70_74': (pp_credit >= 70) & (pp_credit < 75),
    '75_80': (pp_credit >= 75) & (pp_credit < 80),
    '80_85': (pp_credit >= 80) & (pp_credit < 85),
    'above_85': pp_credit >= 85
}

# Count and percentage for each bucket
for bucket_name, condition in buckets.items():
    count = condition.sum()
    pct = (count / len(df)) * 100
    summary[f'credit_bucket_{bucket_name}_count'] = count
    summary[f'credit_bucket_{bucket_name}_pct'] = pct
```

**Implementation Location:** `database.py` - `save_bid_line_data_to_db()`

---

## Historical Trends Tab (Tab 3) - IPA Dashboard

### Layout Overview

Transform the placeholder Tab 3 into a comprehensive IPA-style dashboard with 4 main sections:

```
┌─────────────────────────────────────────────────────────────────┐
│ IPA OPERATIONS DASHBOARD - BID PERIOD {current}                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ SECTION 1: FLEET COMPARISON TABLE                              │
│ [Current vs Previous Period - Crew Block Hours & Line Counts]  │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ SECTION 2: TIME SERIES CHARTS (6 Large Charts)                 │
│                                                                 │
│ Row 1: [Crew Block Hours]     [Regular Lines]                  │
│ Row 2: [Scheduled Duty Days]  [Avg Block/Line]                 │
│ Row 3: [Reserve %]            [No-Bidders]                      │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ SECTION 3: FLEET SMALL MULTIPLES                               │
│ [Grid of 8 sparkline charts showing crew block hours by fleet] │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ SECTION 4: CURRENT PERIOD ANALYSIS (3 Columns)                 │
│                                                                 │
│ Column 1:          Column 2:           Column 3:               │
│ Regular Line Stats Composition Pie     Line Credit Distribution│
│ - % Below Guar.    - Schedules (REG/   - Histogram (5 buckets) │
│ - Credit Range       RES/VTO/HOT)      - Counts & %            │
│ - Avg PP Credit    - Fleet Distribution                        │
│ - Avg PP Pay                                                    │
│ - Avg Block                                                     │
│ - Days Off/Duty                                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Section 1: Fleet Comparison Table

**Component:** Styled Streamlit DataFrame

**Data Source:** Query `bid_period_summary` for current and previous bid periods

**Columns:**
- Fleet (domicile + aircraft, e.g., "ONT 757")
- Crew Block Hours (current)
- Chg (absolute change)
- % Chg (percentage change)
- Number Regular Lines (current)
- Chg (absolute change)
- % Chg (percentage change)

**Styling:**
- Highlight negative changes in red
- Highlight positive changes in green
- Bold row for TOTAL
- Professional table formatting

**Code Location:** `ui_modules/historical_trends_page.py` - `render_fleet_comparison_table()`

### Section 2: Time Series Charts (6 Charts)

**Component:** Plotly line/area charts

**Chart 1: Scheduled Flying Hours of Work**
- X-axis: Bid period (8 periods)
- Y-axis: Crew block hours (stacked by fleet)
- Chart type: Stacked area chart
- Data: `total_crew_block_hours` from summary

**Chart 2: Available Flying Schedules**
- X-axis: Bid period (8 periods)
- Y-axis: Regular line count (stacked by fleet)
- Chart type: Stacked area chart
- Data: `total_regular_lines` from summary

**Chart 3: Scheduled Duty Days**
- X-axis: Bid period (8 periods)
- Y-axis: Total duty days (stacked by fleet)
- Chart type: Stacked area chart
- Data: `total_duty_days` from summary

**Chart 4: Average Scheduled Block Hours per Reg Line**
- X-axis: Bid period (8 periods)
- Y-axis: Average block hours
- Chart type: Line chart
- Data: `avg_pp_block_hours` from summary

**Chart 5: Reserve Lines as % of Bid Package**
- X-axis: Bid period (8 periods)
- Y-axis: Reserve percentage
- Chart type: Area chart with trend line
- Data: `reserve_line_pct` from summary
- Show target zone (e.g., 10-15% shaded region)

**Chart 6: No-Bidders**
- X-axis: Bid period (5 periods)
- Y-axis: No-bidders count (stacked by category)
- Chart type: Stacked area chart
- Data: `no_bidders_*` fields from summary
- **Note:** Requires manual data entry (future enhancement)

**Code Location:** `ui_components/trend_charts.py`

### Section 3: Fleet Small Multiples

**Component:** Grid of small Plotly charts

**Layout:** 2 rows × 4 columns (8 charts for 8 fleets)

**Per Chart:**
- Title: Fleet name (e.g., "ANC 747")
- X-axis: 4 recent bid periods (e.g., 22-07, 23-07, 24-07, 25-07)
- Y-axis: Crew block hours
- Chart type: Simple line chart
- Size: ~200px height

**Y-axis Scaling:** Consistent across all charts for visual comparison

**Data Source:** Query `bid_period_summary` filtered by domicile+aircraft, last 4 periods

**Code Location:** `ui_components/trend_charts.py` - `create_fleet_small_multiples()`

### Section 4: Current Period Analysis

**Layout:** 3-column layout using `st.columns([1, 1, 1])`

#### Column 1: Regular Line Stats

**Component:** Metrics cards

**Metrics:**
- % of PP Credit Below Guarantee (e.g., "39%")
- PP Credit Range (e.g., "60.0 - 89.6")
- Average PP Credit (e.g., "77.0")
- Average PP Pay Credit (e.g., "78.3")
- Average PP Block Hours (e.g., "48.9")
- Average BP Calendar Days Off / Duty Days (e.g., "14.1 / 12.9")

**Data Source:** Latest `bid_period_summary` record

**Code Location:** `ui_components/kpi_cards.py` - `render_line_stats_card()`

#### Column 2: Composition Pie Charts

**Component:** Two Plotly pie charts stacked vertically

**Pie Chart 1: Schedule Types**
- Slices: REG, RES, VTO, HOT, RDG
- Data: Count of each type from summary
- Show percentages

**Pie Chart 2: Fleet Distribution**
- Slices: Each fleet (domicile + aircraft)
- Data: Total regular lines per fleet
- Show counts

**Code Location:** `ui_components/trend_charts.py` - `create_composition_pie_charts()`

#### Column 3: Line Credit Distribution Histogram

**Component:** Plotly bar chart

**X-axis:** 5 buckets (<70, 70-74, 75-80, 80-85, >85)

**Y-axis:** Count of lines

**Data Labels:** Show count and percentage per bucket

**Data Source:** `credit_bucket_*` fields from summary

**Code Location:** `ui_components/trend_charts.py` - `create_credit_distribution_histogram()`

### Filters (Sidebar)

**Filter Controls:**

1. **Fleet/Domicile Multi-Select**
   - Options: All fleets from database
   - Default: All selected
   - Affects: All charts and tables

2. **Bid Period Range Slider**
   - Options: "Last 4 periods", "Last 8 periods", "Last 12 periods", "All time"
   - Default: "Last 8 periods"
   - Affects: Time series charts and small multiples

3. **Seat Position Toggle**
   - Options: CA, FO, Both
   - Default: Both
   - Affects: All data

4. **Date Range Picker** (Optional)
   - Start Date / End Date
   - Overrides bid period range if set

**Implementation:** Standard Streamlit sidebar components

---

## New Visualization Components

### File: `ui_components/trend_charts.py`

**New Functions:**

```python
def create_time_series_chart(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    title: str,
    y_label: str,
    chart_type: str = 'line',  # 'line', 'area', 'stacked_area'
    color_by: Optional[str] = None,
    height: int = 400
) -> go.Figure:
    """Create professional time series chart matching IPA styling."""
    pass

def create_fleet_small_multiples(
    df: pd.DataFrame,
    fleets: List[str],
    metric: str,
    num_periods: int = 4,
    height: int = 200
) -> List[go.Figure]:
    """Create grid of small sparkline charts for each fleet."""
    pass

def create_composition_pie_charts(
    schedule_data: Dict[str, int],
    fleet_data: Dict[str, int],
    height: int = 300
) -> Tuple[go.Figure, go.Figure]:
    """Create schedule type and fleet distribution pie charts."""
    pass

def create_credit_distribution_histogram(
    bucket_data: Dict[str, Dict[str, float]],
    height: int = 400
) -> go.Figure:
    """Create line credit distribution histogram with counts and percentages."""
    pass

def create_comparison_table(
    current_df: pd.DataFrame,
    previous_df: pd.DataFrame,
    metric_cols: List[str]
) -> pd.DataFrame:
    """Create styled period-over-period comparison table."""
    pass
```

### File: `ui_components/kpi_cards.py`

**New Functions:**

```python
def render_kpi_grid(
    metrics: Dict[str, Any],
    columns: int = 3,
    height: str = "100px"
):
    """Render grid of KPI cards with delta indicators."""
    pass

def render_stat_card(
    label: str,
    value: Any,
    delta: Optional[float] = None,
    delta_label: str = "vs. previous",
    format_string: str = "{:.1f}"
):
    """Render individual stat card with optional delta."""
    pass

def render_line_stats_card(summary_data: Dict):
    """Render the Regular Line Stats section from summary data."""
    pass
```

---

## Database Module Enhancements

### File: `database.py`

**New Functions:**

```python
def calculate_bid_period_summary(
    bid_period_id: str,
    pairings_df: Optional[pd.DataFrame] = None,
    bid_lines_df: Optional[pd.DataFrame] = None
) -> Dict:
    """
    Calculate all aggregated metrics for bid_period_summary table.

    Args:
        bid_period_id: UUID of bid period
        pairings_df: DataFrame of pairings (optional)
        bid_lines_df: DataFrame of bid lines (optional)

    Returns:
        Dictionary with all summary fields
    """
    pass

def save_bid_period_summary(
    bid_period_id: str,
    summary_data: Dict
) -> str:
    """Save aggregated summary data to bid_period_summary table."""
    pass

def get_bid_period_comparison(
    current_period: str,
    domicile: str,
    aircraft: str,
    seat: str
) -> Tuple[Dict, Dict]:
    """
    Get current and previous bid period summaries for comparison.

    Returns:
        (current_summary, previous_summary) tuple
    """
    pass

def get_fleet_trends(
    fleets: List[str],
    num_periods: int = 8,
    seat: Optional[str] = None
) -> pd.DataFrame:
    """
    Get trend data for multiple fleets over N periods.

    Returns:
        DataFrame with columns: period, domicile, aircraft, metric_name, metric_value
    """
    pass

@st.cache_data(ttl=timedelta(hours=1))
def get_historical_summaries(
    domicile: Optional[str] = None,
    aircraft: Optional[str] = None,
    seat: Optional[str] = None,
    num_periods: int = 8
) -> pd.DataFrame:
    """
    Get historical summary data with optional filters (cached 1 hour).

    Returns:
        DataFrame from bid_period_trends materialized view
    """
    pass
```

**Enhanced Functions:**

```python
def save_pairing_data_to_db(
    header_info: Dict,
    pairings_df: pd.DataFrame,
    duty_days_df: pd.DataFrame,
    user_id: Optional[str] = None
) -> str:
    """
    Save EDW pairing data to database.

    ENHANCEMENT: Now also calculates and saves bid_period_summary
    """
    # ... existing code ...

    # NEW: Calculate and save summary
    summary_data = calculate_bid_period_summary(
        bid_period_id=bid_period_id,
        pairings_df=pairings_df
    )
    save_bid_period_summary(bid_period_id, summary_data)

    # Refresh materialized view
    refresh_trends()

    return bid_period_id

def save_bid_line_data_to_db(
    header_info: Dict,
    bid_lines_df: pd.DataFrame,
    user_id: Optional[str] = None
) -> str:
    """
    Save bid line data to database.

    ENHANCEMENT: Now also calculates and saves bid_period_summary
    """
    # ... existing code ...

    # NEW: Calculate and save summary
    summary_data = calculate_bid_period_summary(
        bid_period_id=bid_period_id,
        bid_lines_df=bid_lines_df
    )
    save_bid_period_summary(bid_period_id, summary_data)

    # Refresh materialized view
    refresh_trends()

    return bid_period_id
```

---

## Implementation Roadmap

### Prerequisites

**MUST BE COMPLETED FIRST:**
- ✅ Supabase Integration Roadmap Phases 1-5
  - Phase 1: Database Schema ✅
  - Phase 2: Authentication Setup ✅
  - Phase 3: Database Module (in progress)
  - Phase 4: Admin Upload Interface (pending)
  - Phase 5: User Query Interface (pending)

### Phase IPA-1: Database Schema Enhancements (2-3 days)

**Tasks:**
1. Create `bid_period_summary` table migration
2. Update `bid_period_trends` materialized view
3. Add RLS policies for new table
4. Create indexes
5. Test with sample data

**Deliverables:**
- Migration file: `003_add_bid_period_summary.sql`
- Updated materialized view with summary data
- RLS policies tested

### Phase IPA-2: Enhanced Data Capture (3-4 days)

**Tasks:**
1. Implement `calculate_bid_period_summary()` in `database.py`
2. Implement `save_bid_period_summary()` in `database.py`
3. Update `save_pairing_data_to_db()` to calculate summary
4. Update `save_bid_line_data_to_db()` to calculate summary
5. Test with real PDF data
6. Verify summary data accuracy

**Deliverables:**
- Updated `database.py` with summary calculation
- Both analyzer tabs save summary data
- Unit tests for summary calculation

**Testing:**
- Upload EDW pairing PDF → verify summary saved
- Upload bid line PDF → verify summary saved
- Check `bid_period_summary` table in Supabase
- Verify all fields populated correctly

### Phase IPA-3: Trend Visualization Components (4-5 days)

**Tasks:**
1. Create `ui_components/trend_charts.py`
2. Implement time series chart function
3. Implement small multiples function
4. Implement composition pie charts
5. Implement credit distribution histogram
6. Implement comparison table function
7. Create `ui_components/kpi_cards.py`
8. Implement KPI card components

**Deliverables:**
- `ui_components/trend_charts.py` (complete)
- `ui_components/kpi_cards.py` (complete)
- All chart functions tested with sample data
- Professional styling matching IPA report

### Phase IPA-4: Historical Trends Tab Implementation (5-7 days)

**Tasks:**
1. Create `ui_modules/historical_trends_page.py` (replace placeholder)
2. Implement Section 1: Fleet Comparison Table
3. Implement Section 2: Time Series Charts (6 charts)
4. Implement Section 3: Fleet Small Multiples
5. Implement Section 4: Current Period Analysis (3 columns)
6. Add sidebar filters
7. Wire up data queries
8. Test with multiple bid periods

**Deliverables:**
- Fully functional Historical Trends tab
- All 4 sections rendering
- Filters working correctly
- Performance optimized (<3s load time)

**Testing:**
- Upload 8+ bid periods (mixed domiciles/aircraft)
- Verify all charts populate
- Test filters (should update all charts)
- Test with missing data (graceful degradation)
- Performance test with large datasets

### Phase IPA-5: Database Query Enhancements (2-3 days)

**Tasks:**
1. Implement `get_bid_period_comparison()` in `database.py`
2. Implement `get_fleet_trends()` in `database.py`
3. Implement `get_historical_summaries()` in `database.py`
4. Add caching decorators
5. Optimize queries for performance
6. Test pagination for large datasets

**Deliverables:**
- Enhanced `database.py` with new query functions
- Query performance < 3 seconds
- Caching working correctly

### Phase IPA-6: Polish & Documentation (2-3 days)

**Tasks:**
1. Professional styling (match IPA colors and fonts)
2. Responsive layout testing
3. Error handling for missing data
4. Loading states and progress indicators
5. Update `CLAUDE.md` with IPA dashboard documentation
6. Create user guide with screenshots
7. Test edge cases (single bid period, no data, etc.)

**Deliverables:**
- Professional UI matching IPA quality
- Complete documentation
- User guide with examples

### Phase IPA-7: Testing & QA (3-4 days)

**Tasks:**
1. End-to-end testing workflow:
   - Upload 12 bid periods across multiple fleets
   - Verify all summaries calculated correctly
   - Check all charts render correctly
   - Test filters comprehensively
2. Cross-browser testing
3. Performance benchmarking
4. User acceptance testing
5. Bug fixes

**Deliverables:**
- All test scenarios passing
- Performance benchmarks met
- Bug list cleared

---

## Total Timeline

**Prerequisites:** Supabase Roadmap Phases 1-5 (3-4 weeks)

**IPA Enhancement Phases:**
- Phase IPA-1: Database Schema (2-3 days)
- Phase IPA-2: Enhanced Data Capture (3-4 days)
- Phase IPA-3: Visualization Components (4-5 days)
- Phase IPA-4: Historical Trends Tab (5-7 days)
- Phase IPA-5: Query Enhancements (2-3 days)
- Phase IPA-6: Polish & Documentation (2-3 days)
- Phase IPA-7: Testing & QA (3-4 days)

**Total IPA Enhancement Time:** 21-29 days (4-6 weeks)

**Combined Total (Prerequisites + Enhancement):** 7-10 weeks

---

## Key Benefits

### 1. Multi-Bid-Period Intelligence
- Track operational metrics over time (currently impossible)
- Identify trends and patterns across 8+ bid periods
- Period-over-period comparison with % change highlighting

### 2. Fleet-Level Insights
- Compare performance across domiciles and aircraft types
- Identify operational imbalances
- Track crew block hours and line counts by fleet

### 3. Professional Operations Reporting
- Match industry-standard IPA report quality
- Data-dense single-page dashboard
- Executive-ready visualizations

### 4. Data-Driven Decision Making
- Historical context for bidding strategies
- Reserve line percentage trending
- Line quality metrics (days off, duty days, credit distribution)

### 5. System-Wide Visibility
- Aggregate statistics across all fleets
- Schedule type composition (REG/RES/VTO/HOT)
- Buy-up analysis (% below guarantee)

---

## Success Metrics

### Data Completeness
- ✅ 100% of uploaded bid periods have summary data
- ✅ All 20+ summary fields populated correctly
- ✅ Line credit distribution buckets sum to 100%

### Performance
- ✅ Historical Trends tab loads in < 3 seconds
- ✅ Charts render smoothly with 8+ bid periods
- ✅ Filters update dashboard in < 1 second
- ✅ Query performance meets SLA

### User Experience
- ✅ Dashboard matches IPA report quality
- ✅ All charts and tables render correctly
- ✅ Responsive layout works on different screen sizes
- ✅ Intuitive filter controls

### Accuracy
- ✅ Summary calculations match manual verification
- ✅ Period-over-period % change correct
- ✅ Fleet aggregations correct
- ✅ No data loss or corruption

---

## Future Enhancements (Beyond IPA Report)

### 1. No-Bidders Manual Entry UI
- Admin interface to enter no-bidders counts
- Categories: Training, Military, LOA, Medical
- Historical tracking

### 2. RDG (Redeye Guarantee) Detection
- Automatic detection of RDG lines
- Add to schedule type composition
- Track RDG percentage over time

### 3. Premium Pay Tracking
- Parse premium pay from PDFs
- Separate `avg_pp_credit` from `avg_pp_pay_credit`
- Track premium distribution

### 4. Custom Dashboard Builder
- Allow users to create custom dashboard layouts
- Drag-and-drop chart configuration
- Save custom views

### 5. Alerts & Notifications
- Email alerts for significant metric changes
- Threshold-based warnings (e.g., reserve % > 20%)
- Automated weekly reports

### 6. Export to PowerPoint
- One-click export of dashboard to PPTX
- Professional template matching IPA style
- Shareable executive reports

---

## Migration Path

### Retroactive Summary Calculation

For bid periods already in the database (from Phases 4-5), run migration script:

```python
# scripts/backfill_summaries.py

from database import (
    get_bid_periods,
    calculate_bid_period_summary,
    save_bid_period_summary
)
import pandas as pd

def backfill_all_summaries():
    """Calculate summaries for all existing bid periods."""

    bid_periods = get_bid_periods()

    for _, bp in bid_periods.iterrows():
        print(f"Processing {bp['period']} {bp['domicile']} {bp['aircraft']}...")

        # Query pairings and bid lines for this period
        pairings_df = query_pairings({'bid_period_id': bp['id']})
        bid_lines_df = query_bid_lines({'bid_period_id': bp['id']})

        # Calculate summary
        summary_data = calculate_bid_period_summary(
            bid_period_id=bp['id'],
            pairings_df=pairings_df,
            bid_lines_df=bid_lines_df
        )

        # Save summary
        save_bid_period_summary(bp['id'], summary_data)

        print(f"  ✅ Summary saved")

    # Refresh materialized view
    refresh_trends()

    print("\n✅ All summaries backfilled successfully")

if __name__ == "__main__":
    backfill_all_summaries()
```

**Run After:**
- Database schema migration (Phase IPA-1)
- Enhanced data capture code deployed (Phase IPA-2)

---

## Appendix: IPA Report Metrics Reference

### Crew Block Hours
**Definition:** Total scheduled flying time across all pairings
**Source:** Sum of block hours from all trips in bid package
**Use Case:** Measure operational capacity and utilization

### Number Regular Lines
**Definition:** Count of non-reserve bid lines
**Source:** Total lines minus reserve lines
**Use Case:** Track scheduling headcount

### Reserve Lines as % of Bid Package
**Definition:** Reserve lines divided by total lines
**Formula:** `(reserve_lines / total_lines) * 100`
**Target Range:** Typically 10-15% (industry standard)

### Average PP Credit
**Definition:** Average pay period credit time per line
**Formula:** `AVG(total_ct / 2)` for non-reserve lines
**Typical Range:** 70-85 hours

### % Below Guarantee
**Definition:** Percentage of lines below minimum credit threshold
**Formula:** `COUNT(lines WHERE pp_credit < 75) / total_lines * 100`
**Threshold:** Usually 75 hours (configurable)

### Line Credit Distribution
**Definition:** Histogram of lines grouped by PP credit ranges
**Buckets:** <70, 70-74, 75-80, 80-85, >85
**Use Case:** Visualize line quality distribution

### Schedule Types
**REG:** Regular lines (normal flying)
**RES:** Reserve lines (on-call)
**VTO:** Voluntary time off
**HOT:** Hot standby (ready reserve)
**RDG:** Redeye guarantee (future)

---

**Document End**
