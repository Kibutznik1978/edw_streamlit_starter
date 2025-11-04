# Reserve Line Exclusion Logic

## Overview
Reserve lines are now **excluded from the main DataFrame** to prevent them from being included in average calculations. They are still tracked separately in `diagnostics.reserve_lines` for display in the Summary tab.

## How the Parser Works

The bid line parser (`bid_parser.py`) has two main parsing paths:

### Path 1: Pay Period Parsing (lines 472-540)
For modern PDF format with **PP1 (2513)** and **PP2 (2601)** markers.

**Flow:**
1. Extract pay periods → creates `period_records` list
2. Check for **split VTO lines** (one period regular, one VTO)
   - If split → include in data with `VTOType` and `VTOPeriod` metadata
3. Check for **full VTO lines** (both periods VTO)
   - If full VTO → `return [], []` (excluded)
4. **NEW: Check for reserve lines**
   - If reserve → `return [], []` (excluded)
5. If regular line → include in data

### Path 2: Fallback Parsing (lines 542-580)
For legacy PDF format without pay period markers.

**Flow:**
1. Check for **VTO lines**
   - If VTO → `return [], []` (excluded)
2. **NEW: Check for reserve lines**
   - If reserve → `return [], []` (excluded)
3. If regular line → parse CT, BT, DO, DD and include in data

## The Exclusion Pattern

**What does `return [], []` mean?**
- First `[]` = empty records list (no data to add to main DataFrame)
- Second `[]` = empty warnings list (no parsing warnings)
- This tells the parser: "We found a line, but don't include it in the final data"

**Code added at line 531-534 (Pay Period Path):**
```python
else:
    # Check if this is a reserve line - skip it
    is_reserve, _, _, _ = _detect_reserve_line(block)
    if is_reserve:
        return [], []  # Exclude from main data

    # Regular line - include in data
    for record in period_records:
        record["VTOType"] = None
        record["VTOPeriod"] = None
    return period_records, warnings
```

**Code added at line 548-551 (Fallback Path):**
```python
# Skip VTO/VTOR/VOR lines in fallback
if _VTO_PATTERN_RE.search(block):
    return [], []

# Skip reserve lines in fallback
is_reserve, _, _, _ = _detect_reserve_line(block)
if is_reserve:
    return [], []  # Exclude from main data

# Continue parsing regular line...
ct_value = _extract_time_field(block, "CT")
```

## Reserve Line Detection

Reserve lines are detected by `_detect_reserve_line()` (line 251-292), which checks for:

1. **Reserve day keywords:** RA, SA, RB, SB, RC, SC, RD, SD
2. **Shiftable reserve keyword:** SHIFTABLE RESERVE
3. **Zero credit/block pattern:** CT:0:00 AND BT:0:00 (with or without DD:14)
4. **Hot Standby pattern:** HSBY, HOT STANDBY

**Returns:** `(is_reserve, is_hot_standby, captain_slots, fo_slots)`
- `is_reserve`: True if any reserve indicator found
- `is_hot_standby`: True if HSBY pattern found
- `captain_slots`, `fo_slots`: Extracted from availability pattern (e.g., 1/1/0)

## Why This Matters

**Before the fix:**
- Reserve lines were included in main DataFrame
- Averages included reserve line values (CT=0-80, BT=0, DO=14-17, DD=14)
- This skewed statistics (especially BT average)

**After the fix:**
- Reserve lines excluded from main DataFrame
- Averages only include regular flying lines
- Reserve statistics shown separately in Summary tab

**Example from SDF bid packet:**
- **Total lines:** 379
  - Lines 1-263: Regular flying lines (258 after excluding 5 reserve lines)
  - Lines 264-346: VTO/VOR lines (83 excluded)
  - Lines 347-379: Reserve lines (33 excluded)
- **Main DataFrame:** 258 regular flying lines only
- **Diagnostics:** Reserve line info tracked separately for Summary display

## Impact on UI

The UI already handles this correctly:

**`ui_modules/bid_line_analyzer_page.py` (line 484-493):**
```python
if diagnostics and diagnostics.reserve_lines is not None:
    reserve_df = diagnostics.reserve_lines
    if 'IsReserve' in reserve_df.columns and 'IsHotStandby' in reserve_df.columns:
        # Regular reserve lines (not HSBY): exclude from everything
        regular_reserve_mask = (reserve_df['IsReserve'] == True) & (reserve_df['IsHotStandby'] == False)
        reserve_line_numbers = set(reserve_df[regular_reserve_mask]['Line'].tolist())

        # HSBY lines: exclude only from BT
        hsby_mask = reserve_df['IsHotStandby'] == True
        hsby_line_numbers = set(reserve_df[hsby_mask]['Line'].tolist())
```

**This code is now redundant** because reserve lines are already excluded from the main DataFrame. However, it provides a safety net and will work correctly either way.
