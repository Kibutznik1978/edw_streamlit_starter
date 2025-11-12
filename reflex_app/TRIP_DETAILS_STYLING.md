# Trip Details Styling Update

**Date:** November 12, 2025
**File Modified:** `reflex_app/reflex_app/edw/components/details.py`
**Goal:** Match Reflex trip details table to Streamlit version styling

---

## Changes Made

### 1. Table Container Styling

**Added responsive width constraints:**
- Max-width: 60% on desktop
- Max-width: 100% on mobile (< 768px)
- Centered with `margin: 0 auto`
- Horizontal overflow scrolling enabled

```python
rx.box(
    # ... table content ...
    overflow_x="auto",
    width="100%",
    max_width="60%",
    margin="0 auto",
    css={
        "@media (max-width: 768px)": {
            "max-width": "100%",
        }
    },
)
```

### 2. Table Root Styling

**Added monospace font and borders:**
- Font: `'Courier New', monospace`
- Font size: `11px`
- Min-width: `650px` (horizontal scroll on small screens)
- Border collapse: `collapse`

```python
rx.table.root(
    # ... content ...
    width="100%",
    min_width="650px",
    border_collapse="collapse",
    font_family="'Courier New', monospace",
    font_size="11px",
)
```

### 3. Table Header Cells

**Styled to match Streamlit:**
- Background: `#e0e0e0` (light gray)
- Border: `1px solid #999`
- Padding: `6px 4px`
- Font size: `10px`
- Font weight: `bold`
- White space: `nowrap`

### 4. Table Body Cells

**Four row types, each with specific styling:**

#### Briefing Row
- Background: `#f9f9f9` (very light gray)
- Border: `1px solid #ccc`
- Font: Italic "Briefing" text
- Padding: `4px`
- Font size: `11px`

#### Flight Row
- Standard white background
- Border: `1px solid #ccc`
- Padding: `4px`
- Font size: `11px`

#### Debriefing Row
- Background: `#f9f9f9` (very light gray)
- Border: `1px solid #ccc`
- Font: Italic "Debriefing" text
- Padding: `4px`
- Font size: `11px`

#### Subtotal Row
- Background: `#f5f5f5` (light gray)
- Border: `1px solid #ccc` (sides)
- Border top: `2px solid #666` (thick separator)
- Font weight: `bold`
- Padding: `4px`
- Font size: `11px`

### 5. Trip Summary Section

**Styled to match Streamlit embedded table:**

#### Header
- Background: `#d6eaf8` (light blue)
- Border: `3px solid #333`
- Padding: `6px`
- Text: "TRIP SUMMARY" (bold, centered)

#### Content Box
- Background: `#f0f8ff` (very light blue)
- Border: `1px solid #ccc`
- Padding: `10px`
- Font: `'Courier New', monospace`
- Font size: `11px`

#### Layout
- Two rows of metrics
- Row 1: Credit, Blk, Duty Time, TAFB, Duty Days
- Row 2: Prem, PDiem, LDGS, Crew, Domicile
- Labels are bold, values are regular weight
- Horizontal spacing with margins

---

## Visual Comparison

### Before (Basic Reflex styling)
- Modern Radix UI theme colors
- Sans-serif font
- Minimal borders
- Full width table
- Separate summary section

### After (Matches Streamlit)
- Monospace Courier New font
- Explicit gray/blue backgrounds
- Strong borders and separators
- 60% width (centered)
- Integrated summary with table styling

---

## Key Differences from Streamlit

1. **No rowspan support** - Reflex tables don't support rowspan well, so Duty/Cr/L/O columns remain empty for flight rows (not spanned from first row)

2. **Separate summary rendering** - In Streamlit, the trip summary is embedded as special table rows. In Reflex, it's rendered separately but styled to look like it's part of the table.

3. **Border consistency** - Some border combinations (like `border` + `border-top`) may render slightly differently in Reflex vs HTML.

---

## Testing Checklist

- [ ] Upload a pairing PDF
- [ ] Select a trip from dropdown
- [ ] Verify monospace font in table
- [ ] Check header cell styling (gray background, bold)
- [ ] Check briefing/debriefing rows (light gray, italic)
- [ ] Check flight rows (white background)
- [ ] Check subtotal rows (gray background, thick top border, bold)
- [ ] Verify trip summary styling (blue header, light blue content)
- [ ] Test responsive behavior (60% desktop, 100% mobile)
- [ ] Test horizontal scrolling on narrow screens

---

## Files Modified

1. `reflex_app/reflex_app/edw/components/details.py` (lines 125-507)
   - Updated table container with width constraints
   - Added monospace font and borders to table root
   - Updated all header cells with Streamlit styling
   - Updated `_render_table_row()` with cell styling for all row types
   - Updated `_render_trip_summary()` with table-like layout

---

## Performance Notes

The styling changes are purely CSS-based and should not impact performance. The table rendering logic remains the same - only visual presentation changed.

---

## Maintenance Notes

If the Streamlit version styling changes in the future, update these properties:
- Colors: `#e0e0e0`, `#f9f9f9`, `#f5f5f5`, `#d6eaf8`, `#f0f8ff`
- Borders: `1px solid #ccc`, `2px solid #666`, `3px solid #333`
- Font sizes: `10px` (headers), `11px` (body)
- Padding: `4px` (cells), `6px` (headers)
