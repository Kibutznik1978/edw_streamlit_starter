# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## 🎯 Continue From Last Session

**Latest session and status:** See `docs/SESSIONS_INDEX.md` (always up-to-date)

👉 **To continue sequentially:** Check SESSIONS_INDEX.md for the most recent session number, then read `handoff/sessions/session-XX.md`

---

## Project Overview

**EDW Streamlit Analyzer** - Unified Streamlit application for analyzing airline bid packet data for pilots.

**Stack:** Python 3.11+ | Streamlit | Supabase
**Status:** Phases 1-5 complete (Database, Auth, Query Interface) | Phase 6 next (Historical Trends)

### 4-Tab Interface
1. **EDW Pairing Analyzer** - Analyzes pairings PDF to identify Early/Day/Window (EDW) trips
2. **Bid Line Analyzer** - Parses bid line PDFs for scheduling metrics (CT, BT, DO, DD)
3. **Database Explorer** - Query historical data with multi-dimensional filters
4. **Historical Trends** - Database-powered trend analysis (Phase 6 planned)

---

## Quick Start

### ⚠️ Python 3.11+ Required

```bash
python --version  # Must be 3.11.x

# If not, install Python 3.11:
# macOS: brew install python@3.11
# Ubuntu: sudo apt install python3.11
```

### Run the App

```bash
source .venv/bin/activate
streamlit run app.py
```

Available at `http://localhost:8501` (or `8502` if port in use).

---

## Architecture (High-Level)

```
edw_streamlit_starter/
├── app.py                    # Entry point (56 lines)
├── config/                   # Configuration (constants, branding, validation)
├── models/                   # Data structures (pdf_models, bid_models, edw_models)
├── ui_modules/               # Tab pages (4 analyzers)
├── ui_components/            # Reusable UI (filters, data_editor, exports, statistics)
├── edw/                      # EDW analysis (parser, analyzer, excel_export, reporter)
├── bid_parser.py             # Bid line PDF parsing
├── pdf_generation/           # PDF reports (base, charts, edw_pdf, bid_line_pdf)
├── database.py               # Supabase integration
└── auth.py                   # Authentication
```

---

## Documentation & References

### 📖 For Sequential Work (Continue from last session)
- **Latest session:** `handoff/sessions/session-51.md` ← **START HERE**
- **Session history:** `docs/SESSIONS_INDEX.md`

### 🔧 For Development Help
- **Quick help:** `docs/QUICK_REF.md` (setup, testing, troubleshooting, common issues)
- **Architecture:** `docs/ARCHITECTURE.md` (module structure, functions, technical details)

### 💾 For Database Work
- **Database setup:** `docs/SUPABASE_SETUP.md`
- **Implementation plan:** `docs/IMPLEMENTATION_PLAN.md`
- **Migrations:** `docs/migrations/`

---

## Key Technical Details

### PDF Libraries
- **PyPDF2**: EDW pairing analysis (Tab 1 → `edw/parser.py`)
- **pdfplumber**: Bid line analysis (Tab 2 → `bid_parser.py`)

Don't assume these are interchangeable.

### Text Handling
Always use `clean_text()` from `edw/parser.py` when preparing text for ReportLab or Excel (handles Unicode normalization).

### Session State
All widgets have unique keys to prevent conflicts:
- Tab 1: `key="edw_pdf_uploader"`
- Tab 2: `key="bid_line_pdf_uploader"`

---

## Current Status

### ✅ Completed (Phases 1-5)
- Phase 1: Database schema deployed (7 tables, 32 RLS policies, 30+ indexes)
- Phase 2: Authentication & database save functionality
- Phase 3: Testing & optimization (audit fields, error handling)
- Phase 4: Admin upload interface (both analyzers)
- Phase 5: User query interface (Database Explorer - Tab 3)

### 🚧 Next Up (Phase 6)
- Historical Trends Tab - Trend visualizations and comparative analysis

See `docs/SESSIONS_INDEX.md` for detailed roadmap.

---

## Testing

Quick sanity checks:
- **Tab 1:** Upload pairing PDF → verify EDW analysis → download Excel/PDF
- **Tab 2:** Upload bid line PDF → verify parsing → test filters → save to DB
- **Tab 3:** Query database → test filters → export CSV
- **Auth:** Login → verify JWT claims in sidebar

Full testing procedures in `docs/QUICK_REF.md`.

---

## Common Issues (Quick Fixes)

- **Python version errors:** Check `python --version` (must be 3.11+)
- **Import errors:** Activate `.venv` → reinstall: `pip install -r requirements.txt`
- **Wrong PDF uploaded:** App now shows helpful error messages
- **Database errors:** Check JWT claims in sidebar debug tools
- **Port conflicts:** Streamlit auto-increments (8502, 8503, etc.)

Full troubleshooting in `docs/QUICK_REF.md`.

---

**For detailed information, see the documentation references above. This file is kept minimal to reduce context usage.**
