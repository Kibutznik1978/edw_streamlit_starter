# Session 15 - Reserve Line Logic & Distribution Enhancements

**Date:** October 26, 2025
**Focus:** Smart reserve line filtering, distribution charts, and accurate average calculations
**Branch:** `main`

---

## Overview

This session focused on implementing intelligent reserve line filtering and adding comprehensive distribution charts to the Bid Line Analyzer. The key improvement was distinguishing between regular reserve lines (which should be excluded from all calculations) and Hot Standby (HSBY) lines (which have valid CT/DO/DD values but should be excluded from BT calculations).

---

## Changes Made

### 1. **Reserve Line Detection & Filtering Logic**

**Problem:** Average Block Time (BT) was being distorted by reserve lines with BT=0.

**Solution:** Implemented smart filtering that distinguishes between:
- **Regular Reserve Lines (RA, SA, RB, SB, etc.):** Exclude from ALL averages (CT, BT, DO, DD)
- **Hot Standby (HSBY) Lines:** Exclude from BT only, include in CT/DO/DD
- **Regular Lines:** Include in ALL calculations

#### Files Modified:
- `bid_parser.py` (lines 37, 218-259)
  - Added `_HOT_STANDBY_RE` regex pattern
  - Updated `_detect_reserve_line()` to return `(is_reserve, is_hot_standby, captain_slots, fo_slots)`
  - Added `IsHotStandby` column to reserve_lines DataFrame
  - Updated all 3 call sites to handle new return signature

- `app.py` - `_render_summary_tab()` (lines 1168-1239)
  - Separate filtering logic: `reserve_line_numbers` (regular reserve) and `hsby_line_numbers` (HSBY)
  - For CT/DO/DD: Use `filtered_df_non_reserve` (excludes regular reserve, keeps HSBY)
  - For BT: Use `filtered_df_for_bt` (excludes both regular reserve AND HSBY)
  - Added clear captions: "*Reserve lines excluded" / "*Reserve/HSBY excluded"

- `report_builder.py` (lines 382-402, 469-475, 509-517, 538-577, 790-823)
  - Same filtering logic for all PDF sections
  - KPI Cards, Summary Statistics, Pay Period Averages, Buy-up Analysis all use smart filtering

#### Logic Summary:
| Metric | Regular Lines | HSBY Lines | Reserve Lines |
|--------|---------------|------------|---------------|
| **CT** | ✅ Included | ✅ Included | ❌ Excluded |
| **BT** | ✅ Included | ❌ Excluded | ❌ Excluded |
| **DO** | ✅ Included | ✅ Included | ❌ Excluded |
| **DD** | ✅ Included | ✅ Included | ❌ Excluded |

---

### 2. **Enhanced Distribution Charts (Visuals Tab)**

**Added 4 comprehensive distribution charts:**

#### A. **Credit Time (CT) Distribution**
- Color: Teal (#1BB3A4)
- Bins: 5-hour intervals, smart binning (starts from actual min, ends at actual max)
- Excludes: CT=0 (reserve lines automatically filtered out)
- Labels: Angled at -45° (e.g., "65-70 hrs", "70-75 hrs")
- Data: Uses `filtered_df_non_reserve` (excludes regular reserve, keeps HSBY)

#### B. **Block Time (BT) Distribution**
- Color: Sky Blue (#2E9BE8)
- Bins: 5-hour intervals, smart binning
- Excludes: BT=0 (reserve + HSBY lines automatically filtered out)
- Labels: Angled at -45° (e.g., "55-60 hrs", "60-65 hrs")
- Data: Uses `filtered_df_for_bt` (excludes regular reserve AND HSBY)

#### C. **Duty Days (DD) Distribution**
- Color: Dark Teal (#0C7C73)
- Bins: Discrete values (10, 11, 12, etc.)
- Data: Uses `filtered_df_non_reserve` (excludes regular reserve, keeps HSBY)

#### D. **Days Off (DO) Distribution**
- Color: Blue (#457B9D)
- Bins: Discrete values (9, 10, 11, etc.)
- Data: Uses `filtered_df_non_reserve` (excludes regular reserve, keeps HSBY)

#### Implementation:
- `app.py` - `_render_visuals_tab()` (lines 1213-1377)
- All charts use Altair for interactivity
- Tooltips show range/value and line count
- Consistent brand colors with PDF reports

---

### 3. **UI Improvements**

**Summary Tab KPI Cards:**
```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ Avg Credit  │  │ Avg Block   │  │ Avg Days Off│  │ Avg Duty    │
│    82.3     │  │    67.5     │  │    11.2     │  │    13.8     │
│ Range 70-95 │  │ Range 55-80 │  │ Range 9-13  │  │ Range 11-16 │
└─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘
*Reserve lines   *Reserve/HSBY   *Reserve lines  *Reserve lines
  excluded         excluded         excluded        excluded
```

**Chart Label Improvements:**
- Before: `(65.0, 70.0]` ❌
- After: `65-70 hrs` ✅
- Angled at -45° for readability

---

## Additional Enhancements (Completed in Same Session)

### 1. **Exclude Reserve Lines from "Credit and Block by Line" Chart** ✅
- Location: Visuals tab, top line chart
- Updated: Now filters out regular reserve lines (keeps HSBY)
- Implementation: Added reserve line detection before creating line chart
- File: `app.py` lines 1247-1264

### 2. **Add Percentage Charts to Distributions** ✅
- Location: Visuals tab, alongside existing count charts
- Added: Percentage view (% of total lines) for all 4 distributions
- Layout: Side-by-side two-column layout (Count | Percentage)
- Features: Both charts share same tooltips showing count, percentage, and range
- File: `app.py` lines 1295-1483

---

## Files Modified

| File | Lines Modified | Purpose |
|------|----------------|---------|
| `bid_parser.py` | 37, 218-259, 290-297, 349, 398 | HSBY detection and filtering |
| `app.py` | 1163-1239, 1213-1377, 1017 | Summary tab averages, Visuals tab charts |
| `report_builder.py` | 382-823 | PDF report filtering (all sections) |
| `HANDOFF.md` | 1-151 | Session 15 documentation |

---

## Testing Notes

**Syntax Validation:**
- ✅ `app.py` compiles
- ✅ `bid_parser.py` compiles
- ✅ `report_builder.py` compiles

**Functional Testing:**
- ✅ Reserve line detection works
- ✅ HSBY detection works
- ✅ CT/BT/DO/DD averages accurate
- ✅ Distribution charts display correctly
- ✅ Angled labels readable
- ✅ PDF reports match UI logic

---

## User Flow

1. **Upload bid line PDF** (Tab 2)
2. **Parse PDF** → Reserve lines automatically detected
3. **Summary Tab:**
   - KPI cards show averages with clear exclusion captions
   - Pay Period Averages table uses same logic
4. **Visuals Tab:**
   - "Credit and Block by Line" chart (currently includes reserve lines - pending fix)
   - 4 distribution charts with smart filtering
5. **Download PDF:**
   - All sections use consistent reserve line filtering

---

## Technical Details

### Reserve Line Detection (`bid_parser.py`)

```python
# Regular expression for HSBY detection
_HOT_STANDBY_RE = re.compile(r"\b(HSBY|HOT\s*STANDBY|HOTSTANDBY)\b", re.IGNORECASE)

# Detection function returns 4 values
def _detect_reserve_line(block: str) -> Tuple[bool, bool, int, int]:
    is_hot_standby = bool(_HOT_STANDBY_RE.search(block))
    # ... other detection logic
    return is_reserve, is_hot_standby, captain_slots, fo_slots
```

### Filtering Logic (UI and PDF)

```python
# Regular reserve lines (RA, SA, RB, etc.) - exclude from everything
regular_reserve_mask = (reserve_lines['IsReserve'] == True) & (reserve_lines['IsHotStandby'] == False)
reserve_line_numbers = set(reserve_lines[regular_reserve_mask]['Line'].tolist())

# HSBY lines - exclude only from BT
hsby_mask = reserve_lines['IsHotStandby'] == True
hsby_line_numbers = set(reserve_lines[hsby_mask]['Line'].tolist())

# For CT, DO, DD: exclude regular reserve (keep HSBY)
df_non_reserve = df[~df['Line'].isin(reserve_line_numbers)]

# For BT: exclude both regular reserve AND HSBY
all_exclude_for_bt = reserve_line_numbers | hsby_line_numbers
df_for_bt = df[~df['Line'].isin(all_exclude_for_bt)]
```

---

## Key Takeaways

1. **Smart Filtering:** Distinguishing between regular reserve and HSBY provides accurate averages without losing valid data
2. **Consistency:** Same logic applied across UI (Summary/Visuals) and PDF reports
3. **Clarity:** Clear captions inform users which lines are excluded
4. **Visualization:** Distribution charts provide comprehensive view of line characteristics
5. **Usability:** Angled labels and smart binning improve chart readability

---

## Next Steps

1. Exclude reserve lines from "Credit and Block by Line" line chart (Visuals tab)
2. Add percentage charts alongside count charts in distributions
3. (Optional) Consider adding distribution charts to PDF report

---

**Session Duration:** ~3 hours
**Commits:** Pending (changes ready for commit)
**Status:** ✅ All features working, pending enhancements documented
