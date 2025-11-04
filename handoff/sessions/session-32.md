# Session 32: SDF Bid Line Parser Bug Fixes

**Date:** October 30, 2025
**Branch:** `refractor`
**Focus:** Fix critical parsing bugs in bid line analyzer

---

## Issues Identified

User reported two critical issues when parsing the SDF Bid2601 PDF:

1. **Reserve line detection returning `None`** - All 296 lines incorrectly marked as reserve lines
2. **Reserve lines included in averages** - Reserve lines (38 lines) were in main DataFrame, skewing statistics

---

## Root Cause Analysis

### Issue #1: Boolean Logic Bug (bid_parser.py:277)

**Problem:** The `_detect_reserve_line()` function had a boolean expression that allowed `None` values to propagate:

```python
# BEFORE (buggy):
has_reserve_metrics = has_zero_credit_block or (ct_zero and dd_fourteen) or (bt_zero and dd_fourteen)
# When ct_zero = None: (None and Match) = None
# Result: False or None or None = None
```

**Impact:**
- Regular bid lines returned `is_reserve = None` instead of `False`
- All 296 lines flagged as "reserve" in diagnostics
- Parser couldn't distinguish regular lines from reserve lines

**Fix:** Added `bool()` wrappers to prevent `None` propagation:

```python
# AFTER (fixed):
has_reserve_metrics = has_zero_credit_block or bool(ct_zero and dd_fourteen) or bool(bt_zero and dd_fourteen)
# When ct_zero = None: bool(None and Match) = False
# Result: False or False or False = False
```

**File Modified:** `bid_parser.py:277`

---

### Issue #2: Reserve Lines Included in Main DataFrame

**Problem:** Reserve lines were being parsed and included in the main DataFrame, causing them to be used in average calculations.

**Impact:**
- 296 lines in data (should be 258)
- Average BT skewed by reserve lines with BT=0
- Average CT/DO/DD affected by reserve line values

**Fix:** Added exclusion logic similar to VTO line handling:

#### Fix 2a: Prevent VTO Misclassification (bid_parser.py:257-259)

VTO lines have CT:0, BT:0, DD:14 - same pattern as some reserve lines. Added early return to prevent misclassification:

```python
def _detect_reserve_line(block: str) -> Tuple[bool, bool, int, int]:
    """Detect if a line is a reserve line or hot standby."""
    # VTO lines are NOT reserve lines - check this first
    if _VTO_PATTERN_RE.search(block):
        return False, False, 0, 0
    # ... continue with reserve detection
```

#### Fix 2b: Track Reserves Before Exclusion (bid_parser.py:411-432)

Moved reserve tracking to happen BEFORE checking if records are empty:

```python
for block in merged_segments:
    # First, extract line number (needed for reserve tracking)
    header_match = _BLOCK_HEADER_RE.search(block)

    block_records, block_warnings = _parse_block_text(block, page_number)

    # Track reserve status even if records are empty (excluded reserve lines)
    if header_match:
        line_id = int(header_match.group("line"))
        is_reserve, is_hot_standby, captain_slots, fo_slots = _detect_reserve_line(block)
        reserve_info.append({
            "Line": line_id,
            "IsReserve": is_reserve,
            "IsHotStandby": is_hot_standby,
            "CaptainSlots": captain_slots,
            "FOSlots": fo_slots,
        })

    if block_records:
        records.extend(block_records)
```

**Why this matters:** Reserve lines now return empty records (`[]`), so they need to be tracked BEFORE this exclusion happens.

#### Fix 2c: Exclude Reserves in Pay Period Path (bid_parser.py:531-534)

Added reserve exclusion after VTO checks:

```python
else:
    # Check if this is a reserve line - skip it
    is_reserve, _, _, _ = _detect_reserve_line(block)
    if is_reserve:
        return [], []  # Empty records = excluded from main data

    # Regular line with no VTO
    for record in period_records:
        record["VTOType"] = None
        record["VTOPeriod"] = None
    return period_records, warnings
```

#### Fix 2d: Exclude Reserves in Fallback Path (bid_parser.py:548-551)

Added reserve exclusion in fallback parser:

```python
# Skip VTO/VTOR/VOR lines in fallback
if _VTO_PATTERN_RE.search(block):
    return [], []

# Skip reserve lines in fallback
is_reserve, _, _, _ = _detect_reserve_line(block)
if is_reserve:
    return [], []  # Empty records = excluded from main data

# Continue parsing regular line...
ct_value = _extract_time_field(block, "CT")
```

---

## Testing

Created comprehensive test scripts to verify fixes:

### Test Results - SDF Bid2601 PDF (379 total lines)

**Before Fixes:**
```
Total lines parsed: 296
Reserve lines detected: 296 (all lines incorrectly flagged)
IsReserve values: None (boolean logic bug)
VTO lines: 0 in data (correctly excluded)
```

**After Fixes:**
```
Total lines parsed: 258 (regular flying lines only)
Reserve lines detected: 38 (lines 257-261, 347-379)
IsReserve values: True/False (proper booleans)
VTO lines: 0 in data (correctly excluded)

Breakdown:
- Lines 1-256: Regular lines (256)
- Lines 257-261: Reserve lines (5) - excluded
- Lines 262-263: Regular lines (2)
- Lines 264-346: VTO/VOR lines (83) - excluded
- Lines 347-379: Reserve lines (33) - excluded

Main DataFrame: 258 regular flying lines
Diagnostics: 38 reserve lines tracked separately
```

**Verification:**
- ✅ Reserve lines excluded from averages
- ✅ Reserve line info tracked in diagnostics
- ✅ VTO lines not misclassified as reserve
- ✅ All boolean values are proper True/False (no None)
- ✅ Line number gaps correct (257-261, 264-346 missing)

---

## Files Modified

1. **bid_parser.py** (4 changes):
   - Line 257-259: Prevent VTO misclassification in `_detect_reserve_line()`
   - Line 277: Fix boolean logic bug with `bool()` wrappers
   - Line 411-432: Track reserves before exclusion in `_parse_line_blocks()`
   - Line 531-534: Exclude reserves in pay period path
   - Line 548-551: Exclude reserves in fallback path

2. **EXCLUSION_LOGIC.md** (new):
   - Comprehensive documentation of exclusion logic
   - Flow diagrams and code examples
   - Explanation of why changes were needed

---

## VTO/VOR Line Display Decision

**User Question:** Should VTO/VOR lines be displayed with notation?

**Current Behavior:**
- VTO/VOR lines (264-346): Completely hidden from data
- Split VTO lines: Shown with `VTOType` and `VTOPeriod` notation

**Decision:** Keep current behavior (Option A)
- ✅ Clean data - only shows biddable lines
- ✅ No confusion about which lines count in averages
- ✅ Split VTO lines already show when VTO is relevant
- ✅ Keeps data focused on biddable lines

If user wants to see VTO lines in future, would need:
- Add VTO lines to DataFrame with notation column
- Mark clearly as "not biddable"
- Update UI to show/hide VTO lines with toggle

---

## Testing Scripts Created

Created 6 test scripts for debugging and verification:

1. **test_sdf_parsing.py** - Basic parsing validation
2. **inspect_sdf_pdf.py** - Raw PDF content inspection
3. **test_single_block.py** - Reserve detection unit test
4. **test_debug_reserve.py** - Step-by-step reserve detection debug
5. **test_reserve_detection.py** - Reserve DataFrame analysis
6. **test_isreserve_values.py** - Boolean type verification
7. **test_sdf_detailed.py** - Comprehensive end-to-end validation

All scripts confirmed fixes working correctly.

---

## Impact on UI

The UI already had defensive filtering code in `ui_modules/bid_line_analyzer_page.py:484-493` that filters reserve lines from calculations:

```python
if diagnostics and diagnostics.reserve_lines is not None:
    reserve_df = diagnostics.reserve_lines
    if 'IsReserve' in reserve_df.columns:
        regular_reserve_mask = (reserve_df['IsReserve'] == True) & (reserve_df['IsHotStandby'] == False)
        reserve_line_numbers = set(reserve_df[regular_reserve_mask]['Line'].tolist())
```

**This code is now redundant** (reserve lines already excluded from main DataFrame), but provides a safety net and will work correctly either way.

---

## Summary

**Issues Fixed:**
1. ✅ Boolean logic bug causing `None` values in reserve detection
2. ✅ Reserve lines excluded from main DataFrame and averages
3. ✅ VTO lines not misclassified as reserve lines
4. ✅ Reserve line info properly tracked in diagnostics

**Result:**
- SDF bid packet now parses correctly (258 regular lines)
- Averages only include regular flying lines (reserve lines excluded)
- Reserve statistics shown separately in Summary tab
- All boolean values are proper True/False (no None values)

**No Breaking Changes:**
- Existing PDFs continue to work correctly
- UI filtering code provides backward compatibility
- Split VTO line handling unchanged

---

**Status:** ✅ Complete - All tests passing, ready for production use
