# Reflex.dev Migration Plan

## Overview

This document outlines the plan for exploring and potentially migrating the Aero Crew Data application from Streamlit to Reflex.dev to achieve better performance and a more professional UI while staying in pure Python.

## Why Reflex.dev?

### Key Advantages Over Streamlit
1. **No Script Reruns** - WebSocket-based reactive updates (only changed components re-render)
2. **Professional UI** - Built on Radix UI with modern components
3. **Pure Python** - No JavaScript/React knowledge required
4. **Better Performance** - Real-time updates without page reloads
5. **True Routing** - Multi-page apps with proper URL routing
6. **Scalable Architecture** - FastAPI backend + React frontend (compiled from Python)

### Why Not Next.js + FastAPI?
- Requires learning React/TypeScript (2-3 months learning curve)
- 2X development time (5-8 weeks vs 3-4 weeks)
- More expensive to maintain (2 separate codebases)
- Overkill for internal tools

## Current Streamlit Optimizations (Completed)

Before migration, we've implemented the following optimizations to make Streamlit smoother:

### ✅ Caching Implemented
1. **Bid Line Analyzer** (`ui_modules/bid_line_analyzer_page.py`)
   - `_extract_header_cached()` - Caches PDF header extraction
   - `_parse_bid_lines_cached()` - Caches full PDF parsing
   - **Impact:** Header extraction only happens once per file (was running on every widget interaction)

2. **EDW Analyzer** (`ui_modules/edw_analyzer_page.py`)
   - `_extract_edw_header_cached()` - Caches PDF header extraction
   - `_run_edw_report_cached()` - Caches entire EDW analysis
   - **Impact:** Full analysis cached after first run (was re-parsing 100+ page PDFs on every interaction)

3. **Database Explorer** (`ui_modules/database_explorer_page.py`)
   - `_get_bid_periods_cached()` - 60-second TTL for filter options
   - `_query_pairings_cached()` - 30-second TTL for pairing queries
   - `_query_bid_lines_cached()` - 30-second TTL for bid line queries
   - **Impact:** Database queries cached for 30-60 seconds (prevents redundant queries on filter changes)

### Expected Performance Improvement
- **Header extraction:** 100% faster after first load (instant from cache)
- **PDF parsing:** 95%+ faster after first parse (was 10-30 seconds, now instant)
- **Database queries:** 80%+ faster during filter interactions (cache hit rate ~80%)
- **Overall:** App should feel 60-70% smoother

### Remaining Limitations
- Still has page "flash" on reruns
- Filter sliders still trigger full reruns (can be improved with `st.fragment()`)
- Not truly smooth like a modern React app

## Reflex.dev Exploration Plan

### Phase 1: Setup & Learning (Week 1)
**Goals:** Install Reflex, complete tutorials, understand architecture

**Tasks:**
1. Install Reflex: `pip install reflex`
2. Complete official tutorial: https://reflex.dev/docs/getting-started/
3. Review example apps: https://reflex.dev/docs/gallery/
4. Read architecture docs: https://reflex.dev/blog/2024-03-21-reflex-architecture/

**Deliverables:**
- Working Reflex development environment
- Completed tutorial app
- Notes on key differences from Streamlit

### Phase 2: Prototype Tab 4 (Week 2)
**Goals:** Build a simple prototype to validate approach

**Why Tab 4?**
- Currently just a placeholder (minimal risk)
- Good learning opportunity
- Can compare side-by-side with Streamlit

**Tasks:**
1. Create new Reflex app: `reflex init`
2. Build Historical Trends page with:
   - Database query UI
   - Plotly charts
   - Filter controls
3. Connect to existing Supabase backend
4. Compare performance with Streamlit

**Deliverables:**
- Working Reflex prototype
- Performance comparison document
- Go/No-Go decision on full migration

**Example Code Structure:**
```python
import reflex as rx
import pandas as pd
from database import query_pairings

class State(rx.State):
    """Application state."""
    df: pd.DataFrame = pd.DataFrame()
    domicile: str = "ONT"
    aircraft: str = "757"
    loading: bool = False

    async def load_data(self):
        """Load pairing data."""
        self.loading = True
        self.df = await query_pairings({
            "domiciles": [self.domicile],
            "aircraft": [self.aircraft]
        })
        self.loading = False

def historical_trends() -> rx.Component:
    """Historical trends page."""
    return rx.vstack(
        rx.heading("Historical Trends"),
        rx.hstack(
            rx.select(
                ["ONT", "LAX", "SFO"],
                value=State.domicile,
                on_change=State.set_domicile
            ),
            rx.select(
                ["757", "767", "777"],
                value=State.aircraft,
                on_change=State.set_aircraft
            ),
            rx.button(
                "Load Data",
                on_click=State.load_data,
                loading=State.loading
            )
        ),
        rx.cond(
            State.df.empty,
            rx.text("No data loaded"),
            rx.data_table(data=State.df)
        )
    )
```

### Phase 3: Migrate Tab 3 (Week 3)
**Goals:** Migrate Database Explorer (simpler UI, good for refining patterns)

**Tasks:**
1. Recreate filter UI with Reflex components
2. Implement paginated results table
3. Add CSV export functionality
4. Connect to existing database queries

**Key Learnings:**
- How to handle complex filter state
- Pagination patterns in Reflex
- File downloads in Reflex

### Phase 4: Migrate Tabs 1 & 2 (Weeks 4-5)
**Goals:** Migrate the core analysis tabs

**Tab 1: EDW Pairing Analyzer**
- File upload component
- Progress indicators
- Results display with charts
- Excel/PDF downloads
- Reuse existing `edw/` module (no changes needed!)

**Tab 2: Bid Line Analyzer**
- File upload
- Data editor (interactive table)
- Filter controls
- Distribution charts
- CSV/PDF downloads
- Reuse existing `bid_parser.py` (no changes needed!)

### Phase 5: Polish & Deploy (Week 6)
**Tasks:**
1. Professional theming with brand colors
2. Responsive design for mobile
3. Error handling and loading states
4. Deploy to Reflex Cloud ($20/month)
5. User acceptance testing

## Code Reusability Analysis

### ✅ 100% Reusable (No Changes)
- `edw/` package (parser, analyzer, excel_export, reporter)
- `bid_parser.py` (all parsing logic)
- `pdf_generation/` package (PDF report generation)
- `database.py` (Supabase integration)
- `auth.py` (authentication logic)
- `config/` package (constants, branding, validation)
- `models/` package (data structures)

**Total:** ~12,000 lines of code (70% of codebase)

### 🔄 Needs Rewrite (UI Layer Only)
- `ui_modules/` (Streamlit-specific UI code)
- `ui_components/` (Streamlit widgets)
- `app.py` (routing)

**Total:** ~5,000 lines of code (30% of codebase)

### Backend Integration
The existing Supabase backend works with any frontend framework:
- PostgreSQL database (no changes)
- Row Level Security policies (no changes)
- JWT authentication (no changes)
- All database queries are framework-agnostic

## Migration Checklist

### Pre-Migration
- [ ] Complete Streamlit optimizations (caching, fragments)
- [ ] User acceptance of current performance
- [ ] Budget approval ($20/month hosting + 4-6 weeks dev time)

### Phase 1: Learning
- [ ] Install Reflex
- [ ] Complete tutorial
- [ ] Review architecture docs
- [ ] Prototype simple page

### Phase 2: Validation
- [ ] Build Tab 4 prototype
- [ ] Performance testing
- [ ] User feedback
- [ ] Go/No-Go decision

### Phase 3-5: Migration
- [ ] Migrate Tab 3 (Database Explorer)
- [ ] Migrate Tab 1 (EDW Analyzer)
- [ ] Migrate Tab 2 (Bid Line Analyzer)
- [ ] Build Tab 4 (Historical Trends - new feature)

### Phase 6: Deployment
- [ ] Professional theming
- [ ] Responsive design
- [ ] Deploy to Reflex Cloud
- [ ] User acceptance testing
- [ ] Decommission Streamlit app

## Cost Analysis

### Streamlit (Current)
- **Hosting:** $0/month (Streamlit Community Cloud free tier)
- **Development:** Already done
- **Maintenance:** Low (simple architecture)

### Reflex Migration
- **Hosting:** $20/month (Reflex Cloud Starter)
  - Alternative: $7-15/month (self-hosted on Render/Railway)
- **Development:** 4-6 weeks (3-5 hours/day = 60-120 hours)
  - At $50/hour opportunity cost = $3,000-6,000
- **Maintenance:** Medium (more complex architecture, but better DX)

**Year 1 Total Cost:** $3,240 - $6,240
**Year 2+ Annual Cost:** $240/year (hosting only)

### ROI Analysis
**Benefits:**
- **Better UX:** Smooth interactions, no page reloads → happier users
- **Faster Development:** Future features easier to build with proper state management
- **Professional Image:** Modern UI → better for client demos
- **Scalability:** Easier to add features (real-time updates, background jobs, etc.)

**Intangible:** If this becomes a customer-facing product, professional UI is essential.

## Decision Framework

### Stay with Streamlit If:
- ✅ Budget is tight (no $3k-6k for migration)
- ✅ This is purely an internal tool (not customer-facing)
- ✅ Current performance (with caching) is "good enough"
- ✅ No plans to add advanced features (real-time updates, complex workflows)

### Migrate to Reflex If:
- ✅ Professional UI is important (demos, client-facing)
- ✅ Budget allows for 4-6 weeks development
- ✅ Planning to add advanced features (real-time data, dashboards, complex workflows)
- ✅ Want to stay in Python (no React learning curve)
- ✅ Current "clunkiness" is frustrating users

## Next Steps

1. **Test Current Optimizations** (Week 1)
   - Run the Streamlit app with new caching
   - Gather user feedback
   - Measure performance improvement

2. **Make Decision** (End of Week 1)
   - If caching fixes 80% of pain → Stay with Streamlit
   - If still frustrating → Proceed to Phase 1

3. **Start Phase 1** (Week 2)
   - Install Reflex
   - Complete tutorials
   - Build simple prototype

4. **Validate Approach** (Week 3)
   - Build Tab 4 prototype
   - Compare with Streamlit
   - Make final Go/No-Go decision

## Resources

### Official Docs
- Reflex Documentation: https://reflex.dev/docs/
- Reflex Gallery: https://reflex.dev/docs/gallery/
- Reflex Blog: https://reflex.dev/blog/
- Reflex Discord: https://discord.gg/T5WSbC2YtQ

### Tutorials
- Getting Started: https://reflex.dev/docs/getting-started/
- Architecture Guide: https://reflex.dev/blog/2024-03-21-reflex-architecture/
- Hosting Guide: https://reflex.dev/docs/hosting/deploy/

### Comparison Articles
- Reflex vs Streamlit: https://reflex.dev/blog/2025-08-20-reflex-streamlit/
- Python Web Frameworks 2025: https://reflex.dev/blog/2024-12-20-python-comparison/

## FAQ

### Q: Will we lose any functionality?
**A:** No. All backend logic (PDF parsing, EDW analysis, database queries) is framework-agnostic and will work unchanged. Only the UI layer needs to be rewritten.

### Q: How long will migration take?
**A:** 4-6 weeks for a full migration, assuming 3-5 hours/day. Can be done in parallel with using current Streamlit app.

### Q: Can we migrate incrementally?
**A:** Yes! We can build Reflex app alongside Streamlit, migrate one tab at a time, and switch when ready.

### Q: What if Reflex doesn't work out?
**A:** Phase 2 is specifically designed to validate the approach with minimal investment (1 week). If it doesn't work, we stay with optimized Streamlit.

### Q: Can we self-host instead of Reflex Cloud?
**A:** Yes! Reflex apps can be deployed to any platform that supports Docker (Render, Railway, DigitalOcean, AWS, etc.). Self-hosting is $7-15/month vs $20 for Reflex Cloud.

### Q: What about st.fragment() for partial reruns?
**A:** This is a good optimization for Streamlit and can be implemented in Phase 1 alongside caching. However, it's still limited by Streamlit's architecture and won't match Reflex's smoothness.

## Appendix: Streamlit Fragment Implementation

If we decide to stay with Streamlit, here's how to add `st.fragment()` for even better performance:

### Example: Filter Sidebar Fragment
```python
@st.fragment
def render_filters():
    """Fragment that only reruns when filters change."""
    ct_min, ct_max = st.slider("CT Range", 0.0, 200.0, (0.0, 200.0))
    bt_min, bt_max = st.slider("BT Range", 0.0, 200.0, (0.0, 200.0))

    # Apply filters and update only this section
    filtered = st.session_state.df[
        (st.session_state.df['CT'] >= ct_min) &
        (st.session_state.df['CT'] <= ct_max) &
        (st.session_state.df['BT'] >= bt_min) &
        (st.session_state.df['BT'] <= bt_max)
    ]

    st.dataframe(filtered)

# Main app
render_filters()  # Only this reruns when sliders change
```

This can be implemented in Week 1 alongside testing current caching optimizations.
