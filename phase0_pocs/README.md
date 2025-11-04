# Phase 0: Proof of Concept Testing

This directory contains critical POCs to validate the feasibility of migrating from Streamlit to Reflex.

## Purpose

Phase 0 POCs test the **highest-risk technical challenges** before committing to the full migration:

1. **Data Editor** - Can we replicate Streamlit's `st.data_editor()` functionality?
2. **File Upload** - How does Reflex handle PDF file uploads and processing?
3. **Plotly Charts** - Can we embed Plotly visualizations in Reflex?
4. **JWT/Supabase** - Does JWT session handling work with Supabase RLS policies?

## Decision Gate

**Week 1 Decision**: After completing these POCs, we will decide:
- ✅ **PROCEED** - All POCs successful, continue to Phase 1
- ⚠️ **PAUSE** - Some blockers found, reassess approach
- ❌ **ABORT** - Critical blockers, migration not feasible

## POC Directories

### 1. `data_editor/` - Interactive Data Editing
**Goal**: Validate inline data editing with validation
**Success Criteria**:
- Editable table with CT, BT, DO, DD columns
- Column validation (ranges, CT < BT)
- Change tracking (original vs edited)
- Responsive on mobile

**Risk Level**: 🔴 **CRITICAL** (No direct Reflex equivalent)

### 2. `file_upload/` - PDF File Processing
**Goal**: Validate PDF upload and text extraction
**Success Criteria**:
- Upload PDF files (PyPDF2, pdfplumber)
- Display upload progress
- Extract and display text
- Handle large files (5-10 MB)

**Risk Level**: 🟡 **MEDIUM** (Reflex has file upload, need to test with PDF libraries)

### 3. `plotly_charts/` - Chart Visualization
**Goal**: Validate Plotly chart embedding and interactivity
**Success Criteria**:
- Render Plotly bar, pie, and radar charts
- Interactive hover/zoom
- Responsive sizing
- Export as images

**Risk Level**: 🟢 **LOW** (Plotly officially supported in Reflex)

### 4. `jwt_auth/` - Supabase Authentication
**Goal**: Validate JWT session handling with Supabase RLS
**Success Criteria**:
- Login with Supabase Auth
- JWT custom claims propagation
- RLS policy enforcement
- Session persistence

**Risk Level**: 🔴 **CRITICAL** (Complex JWT/RLS requirements)

## Running POCs

Each POC directory contains:
- `poc_<name>.py` - Standalone Reflex app
- `README.md` - Specific testing instructions
- `test_cases.md` - Test scenarios and acceptance criteria

To run a POC:

```bash
cd phase0_pocs/<poc_name>
reflex run poc_<name>.py
```

## Timeline

- **Days 1-2**: Data editor POC
- **Day 3**: File upload POC
- **Day 4**: Plotly charts POC
- **Day 5**: JWT/Supabase POC
- **Day 5 EOD**: GO/NO-GO decision

## Next Steps After Phase 0

If all POCs pass:
1. Review findings with stakeholders
2. Update risk assessment in `/docs/REFLEX_MIGRATION_RISKS.md`
3. Proceed to **Phase 1: Authentication & Infrastructure**

If blockers found:
1. Document blockers in `/docs/phase0_findings.md`
2. Assess mitigation options
3. Decide: pause, pivot, or abort
