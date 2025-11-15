# CLAUDE.md Content Migration Map

**Purpose:** This document maps where every section of the current CLAUDE.md will be relocated. Nothing is deleted - all information is preserved.

**Current CLAUDE.md:** 716 lines, 4,485 words, ~5,830 tokens

---

## Migration Destinations

### ✅ NEW: Minimal CLAUDE.md (~500 tokens)
**Content:**
- Project overview (1-sentence description)
- Current session pointer → "Session 46"
- Quick run command
- Architecture tree (condensed to module names only)
- Clear navigation to detailed docs
- Python 3.11 requirement (critical, must stay)
- Status: "Phases 1-5 complete, Phase 6 next"

**Lines:** Lines 1-13, 41-55, 93-141 (condensed), 667-716 (condensed)

---

### 📘 NEW: docs/QUICK_REF.md (~800 tokens)
**Purpose:** Operational guide - setup, running, testing, troubleshooting

**Content from CLAUDE.md:**
- **Python Requirements** (Lines 14-40)
  - Python 3.11 requirement details
  - Version checking commands
  - Installation instructions

- **Running the Application** (Lines 41-55)
  - Activate venv
  - Install dependencies
  - Run command
  - Port information

- **Development Setup** (Lines 57-91)
  - Prerequisites
  - Setup steps 1-5
  - Supabase setup pointer

- **Testing Changes** (Lines 498-540)
  - All 4 tabs testing procedures
  - Cross-tab testing
  - Authentication testing

- **Common Issues** (Lines 542-555)
  - Python version issues
  - Virtual environment
  - Port conflicts
  - Wrong PDF uploads
  - Chart memory management
  - Unicode handling
  - Session state conflicts
  - Database errors

- **File Naming Convention** (Lines 460-475)
  - EDW report naming
  - Bid line report naming

---

### 🏗️ NEW: docs/ARCHITECTURE.md (~2,500 tokens)
**Purpose:** Deep technical documentation - module structure, functions, data flow

**Content from CLAUDE.md:**
- **Application Structure** (Lines 95-141) - FULL DETAIL
  - Complete file tree with line counts
  - Preserve all module descriptions

- **app.py** (Lines 143-149)

- **Configuration & Models** (Lines 151-188)
  - config/ package details
  - models/ package details
  - Benefits explanation

- **ui_modules/** (Lines 190-262)
  - edw_analyzer_page.py (full description)
  - bid_line_analyzer_page.py (full description)
  - database_explorer_page.py (full description)
  - historical_trends_page.py (full description)
  - shared_components.py (full description)

- **ui_components/** (Lines 264-305)
  - filters.py (full description)
  - data_editor.py (full description)
  - exports.py (full description)
  - statistics.py (full description)

- **Core Analysis Modules** (Lines 307-450)
  - EDW Analysis Module (edw/)
  - Bid Line Parser (bid_parser.py)
  - PDF Generation Package (pdf_generation/)
  - Database Module (database.py)
  - Authentication Module (auth.py)

- **Text Handling** (Lines 443-450)
  - clean_text() function explanation

- **PDF Libraries** (Lines 452-458)
  - PyPDF2 vs pdfplumber distinction

- **Database Schema Overview** (Lines 477-496)
  - 7 tables + 1 materialized view
  - Key features
  - Link to detailed schema docs

- **Manual Data Editing Feature** (Lines 557-586)
  - Full technical description
  - Session state management
  - Change tracking
  - Validation warnings

---

### 📚 NEW: docs/SESSIONS_INDEX.md (~1,500 tokens)
**Purpose:** Session history with topic-based lookup + sequential continuity

**Content from CLAUDE.md:**
- **Latest Session Pointer** (NEW)
  - "Session 46 - Context optimization"
  - "Next: Implement minimal CLAUDE.md"
  - "Read: handoff/sessions/session-46.md"

- **Recent Sessions Rolling Window** (Lines 590-627)
  - Last 5 sessions with detailed summaries
  - Session 32: SDF bid line parser bug fixes
  - Session 31: Older PDF format compatibility
  - Session 30: UI fixes & critical bugs
  - Session 29: Duplicate trip parsing fix
  - Session 28-27: [from Recent Milestones]

- **Recent Milestones** (Lines 629-642)
  - Phase 2 Complete
  - Phase 1 Complete

- **Older Sessions Summary** (Lines 644-656)
  - Sessions 18-25 refactoring summaries

- **Topic-Based Lookup Index** (NEW)
  - Parsing & Bug Fixes: Sessions 29-32
  - Database & Auth: Sessions 27-28
  - Refactoring: Sessions 18-25
  - UI/UX: Sessions 18, 22, 25, 30

- **Current Status & Next Steps** (Lines 667-716)
  - All phase completion status
  - Future phases roadmap

---

### 📋 STAYS IN PLACE (Already in separate docs)
**No changes needed:**
- `docs/IMPLEMENTATION_PLAN.md` - Database integration roadmap
- `docs/SUPABASE_SETUP.md` - Supabase setup instructions
- `docs/migrations/` - SQL migration files
- `.env.example` - Environment template
- `HANDOFF.md` - Project overview

---

## Verification Checklist

After migration, verify all content is accessible:

- [ ] Python 3.11 requirement clearly stated
- [ ] Run commands easily found
- [ ] All module descriptions preserved
- [ ] All session summaries preserved
- [ ] All testing procedures preserved
- [ ] All common issues preserved
- [ ] All technical details preserved
- [ ] Navigation between docs is clear
- [ ] Nothing deleted, only moved

---

## Token Savings

**Current:**
- CLAUDE.md: 5,830 tokens (auto-loaded every session)

**After Migration:**
- Minimal CLAUDE.md: ~500 tokens (auto-loaded)
- docs/QUICK_REF.md: ~800 tokens (on-demand)
- docs/ARCHITECTURE.md: ~2,500 tokens (on-demand)
- docs/SESSIONS_INDEX.md: ~1,500 tokens (on-demand)

**Total if all loaded:** 5,300 tokens (still a savings)
**Typical session:** 500 tokens (91% savings)
**Session with context needs:** 1,500-3,000 tokens (50-75% savings)
