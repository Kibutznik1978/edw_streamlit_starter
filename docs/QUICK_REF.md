# EDW Streamlit Analyzer - Quick Reference

**Purpose:** Quick operational guide for setup, running, testing, and troubleshooting.

For detailed architecture, see [ARCHITECTURE.md](ARCHITECTURE.md).

---

## Python Requirements

**Required Python Version:** **3.11+** (Project uses Python 3.11.1)

**Important:** This project requires Python 3.11 or higher. Python 3.10 may work but is not tested.

The Python 3.11 requirement applies to:
- Streamlit application (main branch)
- Reflex migration development (reflex-migration branch)

### Why Python 3.11?

- Reflex framework requires Python 3.10+ (discovered during migration)
- Python 3.9 reaches EOL October 2025
- Modern typing support and performance improvements
- Full compatibility with all project dependencies

### Checking Your Python Version

```bash
python --version  # Should show Python 3.11.x
python3.11 --version  # Check if Python 3.11 is available
```

### Installing Python 3.11

- **macOS**: `brew install python@3.11`
- **Ubuntu**: `sudo apt install python3.11`
- **Windows**: Download from python.org

---

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

---

## Development Setup

### Prerequisites

- Python 3.11+ installed (check with `python --version`)
- Git

### Setup Steps

**1. Create virtual environment** (first time only):
```bash
# Ensure you're using Python 3.11
python3.11 -m venv .venv
```

**2. Activate virtual environment:**
```bash
source .venv/bin/activate
```

**3. Verify Python version:**
```bash
python --version  # Should show Python 3.11.x
```

**4. Install dependencies:**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**5. (Optional) For database integration:**
- Create Supabase project at https://supabase.com
- Copy `.env.example` to `.env`
- Fill in `SUPABASE_URL` and `SUPABASE_ANON_KEY`
- See `SUPABASE_SETUP.md` for detailed setup instructions

---

## File Naming Convention

### EDW Reports

Generated files follow the pattern:
```
{domicile}_{aircraft}_Bid{bid_period}_EDW_Report_Data.xlsx
{domicile}_{aircraft}_Bid{bid_period}_EDW_Report.pdf
```

**Example:** `ONT_757_Bid2507_EDW_Report_Data.xlsx`

### Bid Line Reports

```
Bid_Lines_Analysis_Report.pdf
bid_lines_filtered.csv
```

---

## Testing Changes

Since this is a Streamlit app without formal tests:

### Tab 1 (EDW Pairing Analyzer)

- Upload a pairing PDF and verify automatic header extraction
- Run analysis and check all weighted EDW metrics
- Test duty day criteria filtering (match modes: Any/All)
- View trip details and verify table width constraint (60% on desktop)
- Download Excel and PDF reports
- Test "Save to Database" with duplicate detection

### Tab 2 (Bid Line Analyzer)

- Upload a bid line PDF and verify parsing completes
- Apply filters (CT, BT, DO, DD ranges)
- Check all three sub-tabs (Overview, Summary, Visuals)
- Verify pay period analysis displays correctly
- Test manual data editing and change tracking
- Test CSV and PDF export
- Test "Save to Database" with duplicate detection

### Tab 3 (Database Explorer)

- Select filters (domicile, aircraft, seat, bid periods)
- Test quick date filters and custom date range
- Run queries for both Pairings and Bid Lines
- Verify pagination works correctly
- Test CSV export functionality
- View record details in expandable JSON viewer
- Test with no filters (should show all data)

### Tab 4 (Historical Trends)

- Verify placeholder content displays
- (After Phase 6 implementation) Test trend visualizations

### Cross-tab Testing

- Verify session state isolation (no bleeding between tabs)
- Test switching between tabs multiple times
- Upload different PDFs in different tabs

### Authentication

- Test login/signup flow
- Verify JWT claims are set correctly
- Test admin vs regular user permissions

---

## Common Issues

### Python Version

**Issue:** Typing errors or import issues
**Solution:** Check `python --version`. Python 3.9 is NOT supported (EOL October 2025). See "Python Requirements" section above for details.

### Virtual Environment

**Issue:** Packages not found or version conflicts
**Solution:** Always activate `.venv` before running app or installing dependencies. Recreate with Python 3.11 if needed:
```bash
rm -rf .venv && python3.11 -m venv .venv
```

### Port Conflicts

**Issue:** Port 8501 already in use
**Solution:** Streamlit will auto-increment (8502, 8503, etc.)

### Wrong PDF Upload

Both analyzers now provide helpful error messages if the wrong PDF type is uploaded:

- **Tab 1 (EDW Pairing Analyzer)**: Detects bid line PDFs and suggests uploading to Tab 2
- **Tab 2 (Bid Line Analyzer)**: Detects pairing PDFs and suggests uploading to Tab 1

### Chart Memory Management

**Issue:** Memory errors with charts
**Solution:** Charts are saved to BytesIO, converted to PIL Image before PDF embedding

### Unicode Handling

**Issue:** Special characters display incorrectly
**Solution:** Always use `clean_text()` when preparing text for ReportLab or Excel

### Session State Conflicts

**Issue:** Widgets interfere with each other
**Solution:** Ensure all widget keys are unique across tabs

### Table Width

**Issue:** Pairing detail table too wide/narrow
**Solution:** Pairing detail table uses responsive CSS (50%/80%/100% based on screen width)

### Database Errors

**Issue:** Database operations fail
**Solution:** Check JWT claims are set (use debug tools in sidebar)

### RLS Violations

**Issue:** Row Level Security policy violations
**Solution:** Ensure user is authenticated and JWT session is set in `get_supabase_client()`

---

## Quick Commands Reference

### Start Development

```bash
source .venv/bin/activate
streamlit run app.py
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Check Python Version

```bash
python --version  # Should be 3.11.x
```

### Recreate Virtual Environment

```bash
rm -rf .venv
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Database Setup

See `SUPABASE_SETUP.md` for detailed instructions.

---

## Getting Help

- **Architecture questions**: See [ARCHITECTURE.md](ARCHITECTURE.md)
- **Session history**: See [SESSIONS_INDEX.md](SESSIONS_INDEX.md)
- **Database setup**: See `SUPABASE_SETUP.md`
- **Implementation plan**: See `IMPLEMENTATION_PLAN.md`
