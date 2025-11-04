# Aero Crew Data Analyzer - Reflex Edition

This is the **Reflex version** of the Aero Crew Data Analyzer application, currently under development as part of the Streamlit → Reflex migration.

## Status

🚧 **UNDER CONSTRUCTION** - Phase 0 (Week 1)

**Current Phase:** Phase 0 - Proof of Concept Testing
**Progress:** 30% - Infrastructure complete, POC testing ready to begin
**Branch:** `reflex-migration`
**Last Updated:** November 4, 2025

This application is being developed in parallel with the existing Streamlit version on the `reflex-migration` branch.

## Quick Start

### Prerequisites

**IMPORTANT:** Python 3.11+ is required for Reflex

1. **Python 3.11+** (Reflex requires Python 3.10+, project uses 3.11.1)
   ```bash
   python --version  # Should show Python 3.11.x
   ```

2. **Git** (for cloning and branch management)

3. **Virtual environment** (recommended)

### First-Time Setup

```bash
# 1. Ensure you're on the reflex-migration branch
git checkout reflex-migration

# 2. Create virtual environment with Python 3.11 (if not already created)
python3.11 -m venv .venv

# 3. Activate virtual environment
source .venv/bin/activate  # macOS/Linux
# OR
.venv\Scripts\activate  # Windows

# 4. Verify Python version
python --version  # Should show Python 3.11.x

# 5. Upgrade pip
pip install --upgrade pip

# 6. Install Streamlit dependencies (shared backend modules)
pip install -r requirements.txt

# 7. Install Reflex and dev dependencies
pip install -r requirements_reflex.txt

# 8. Navigate to Reflex app directory
cd reflex_app

# 9. Initialize Reflex (first time only)
reflex init
```

### Installation Complete! ✅

You should now have:
- ✅ Python 3.11.1 virtual environment
- ✅ All Streamlit dependencies installed
- ✅ Reflex 0.8.18 installed
- ✅ Reflex app initialized

### Running the App

```bash
# From reflex_app directory
reflex run
```

The app will be available at `http://localhost:3000` (default Reflex port).

## Project Structure

```
reflex_app/
├── rxconfig.py                 # Reflex configuration
├── reflex_app/                 # Main application package
│   ├── __init__.py
│   └── reflex_app.py          # Main app entry point (4-tab navigation)
├── assets/                     # Static assets (images, CSS)
└── README.md                   # This file
```

## Shared Backend Modules

The Reflex app uses the **same backend modules** as the Streamlit version:
- `/edw/` - EDW pairing analysis
- `/bid_parser.py` - Bid line parsing
- `/pdf_generation/` - PDF report generation
- `/database.py` - Supabase integration
- `/auth.py` - Authentication (being adapted for Reflex)
- `/config/` - Centralized configuration
- `/models/` - Data models

This ensures consistency between both versions and reduces code duplication.

## Current Features

### Implemented (Phase 0)
- [x] Basic 4-tab navigation structure
- [x] Tab 1: EDW Pairing Analyzer (placeholder)
- [x] Tab 2: Bid Line Analyzer (placeholder)
- [x] Tab 3: Database Explorer (placeholder)
- [x] Tab 4: Historical Trends (placeholder)
- [x] Authentication UI skeleton
- [x] Navbar with user info

### In Progress (Phase 0 POCs)
- [ ] POC: Interactive data editor (critical)
- [ ] POC: PDF file upload and processing
- [ ] POC: Plotly chart integration
- [ ] POC: JWT/Supabase authentication

### Planned (Phases 1-6)
See `/REFLEX_MIGRATION_STATUS.md` for detailed phase-by-phase plan.

## Configuration

### Environment Variables

Create a `.env` file in the project root (not in `reflex_app/`):

```bash
# Supabase configuration (shared with Streamlit version)
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
```

### Reflex Configuration

Edit `rxconfig.py` to customize:
- App name
- Database URL (currently SQLite for dev, will use Supabase)
- Environment (DEV/PROD)

## Development Workflow

### Making Changes

1. Ensure you're on the `reflex-migration` branch
2. Make changes to files in `reflex_app/`
3. Test with `reflex run`
4. Commit changes with descriptive messages

### Testing POCs

Phase 0 POCs are in `/phase0_pocs/` directory:

```bash
# Test data editor POC
cd phase0_pocs/data_editor
reflex run poc_data_editor.py

# Test file upload POC
cd phase0_pocs/file_upload
reflex run poc_file_upload.py

# Test Plotly charts POC
cd phase0_pocs/plotly_charts
reflex run poc_plotly_charts.py

# Test JWT auth POC
cd phase0_pocs/jwt_auth
reflex run poc_jwt_auth.py
```

### Hot Reload

Reflex supports hot reload - changes to Python files will automatically reload the app in the browser.

## Comparison: Streamlit vs Reflex

| Feature | Streamlit | Reflex |
|---------|-----------|--------|
| **Port** | 8501 | 3000 |
| **State Model** | Session state with reruns | Reactive state with events |
| **Routing** | Tabs with `st.tabs()` | Radix UI tabs component |
| **File Upload** | `st.file_uploader()` | `rx.upload()` |
| **Data Editor** | `st.data_editor()` | Custom component (TBD) |
| **Charts** | `st.plotly_chart()` | `rx.plotly()` |
| **Authentication** | Custom with session state | Custom with reactive state |

## Key Differences

### State Management

**Streamlit:**
```python
if 'data' not in st.session_state:
    st.session_state.data = []

st.session_state.data.append(new_item)
```

**Reflex:**
```python
class State(rx.State):
    data: List[str] = []

    def add_item(self, item: str):
        self.data.append(item)
```

### Event Handling

**Streamlit:** Re-runs entire script on widget interaction

**Reflex:** Updates only affected components via reactive state

## Known Issues & Limitations

### Phase 0 Blockers (Under Investigation)
1. **Data Editor** - No direct equivalent to `st.data_editor()`
   - Exploring: Custom component, third-party libraries, modal editing
2. **JWT/RLS** - Need to validate JWT session handling with Supabase RLS
   - Exploring: Custom JWT middleware, cookie-based sessions

### Future Enhancements
- Mobile-optimized responsive design
- Better performance with large datasets
- Enhanced accessibility (WCAG 2.1 Level AA)

## Documentation

**Migration Planning:**
- `/docs/REFLEX_MIGRATION_SUMMARY.md` - Executive overview and cost-benefit analysis
- `/docs/REFLEX_COMPONENT_MAPPING.md` - Detailed Streamlit → Reflex mappings
- `/docs/REFLEX_MIGRATION_PHASES.md` - Week-by-week implementation plan
- `/docs/REFLEX_MIGRATION_RISKS.md` - Risk assessment and mitigation

**Migration Tracking:**
- `/REFLEX_MIGRATION_STATUS.md` - Current phase status and decision log

**POC Testing:**
- `/phase0_pocs/README.md` - POC testing instructions

## Contributing

### Code Style
- Use Black for formatting
- Follow PEP 8 guidelines
- Add type hints for all functions
- Document complex logic with comments

### Testing
- Test all changes manually before committing
- Validate responsive behavior on mobile (< 768px)
- Check browser console for errors

## Support

**Questions?** See `/docs/REFLEX_MIGRATION_SUMMARY.md` or create an issue on GitHub.

**Streamlit Version:** Still maintained on `main` branch at `/app.py`
