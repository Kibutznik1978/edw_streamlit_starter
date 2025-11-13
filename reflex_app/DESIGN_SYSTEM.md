# Aero Crew Data Analyzer - Design System Reference

## Color Palette

### Navy (Primary) - Professional & Trustworthy
```
navy_50:  #eff6ff  ░░░░░░░░░
navy_100: #dbeafe  ▒▒▒▒▒▒▒▒▒
navy_200: #bfdbfe  ▓▓▓▓▓▓▓▓▓
navy_300: #93c5fd  ████████
navy_400: #60a5fa  ████████
navy_500: #3b82f6  ████████
navy_600: #2563eb  ████████
navy_700: #1d4ed8  ████████
navy_800: #1e3a8a  █████████  ← PRIMARY BRAND COLOR
navy_900: #1e293b  █████████
```
**Use for**: Primary buttons, headings, navigation, important UI elements

---

### Teal (Accent) - Fresh & Modern
```
teal_50:  #f0fdfa  ░░░░░░░░░
teal_100: #ccfbf1  ▒▒▒▒▒▒▒▒▒
teal_200: #99f6e4  ▓▓▓▓▓▓▓▓▓
teal_300: #5eead4  ████████
teal_400: #2dd4bf  ████████
teal_500: #14b8a6  ████████
teal_600: #0d9488  █████████  ← ACCENT COLOR
teal_700: #0f766e  █████████
teal_800: #115e59  █████████
teal_900: #134e4a  █████████
```
**Use for**: Secondary actions, badges, highlights, success states

---

### Sky (Highlight) - Aviation & Clarity
```
sky_50:  #f0f9ff  ░░░░░░░░░
sky_100: #e0f2fe  ▒▒▒▒▒▒▒▒▒
sky_200: #bae6fd  ▓▓▓▓▓▓▓▓▓
sky_300: #7dd3fc  ████████
sky_400: #38bdf8  ████████
sky_500: #0ea5e9  █████████  ← HIGHLIGHT COLOR
sky_600: #0284c7  █████████
sky_700: #0369a1  █████████
sky_800: #075985  █████████
sky_900: #0c4a6e  █████████
```
**Use for**: Links, interactive elements, info callouts, hover states

---

### Gray (Text & Backgrounds)
```
gray_50:  #f8fafc  ░░░░░░░░░  ← Light backgrounds
gray_100: #f1f5f9  ▒▒▒▒▒▒▒▒▒
gray_200: #e2e8f0  ▓▓▓▓▓▓▓▓▓  ← Borders
gray_300: #cbd5e1  ████████
gray_400: #94a3b8  ████████
gray_500: #64748b  ████████
gray_600: #475569  █████████  ← BODY TEXT
gray_700: #334155  █████████  ← Headings (alt)
gray_800: #1e293b  █████████
gray_900: #0f172a  █████████
```
**Use for**: Text, borders, neutral backgrounds, disabled states

---

## Semantic Colors

### Success (Green)
```
Light:  #d1fae5  ▒▒▒▒▒▒▒▒▒
Base:   #10b981  █████████
Dark:   #047857  █████████
```

### Warning (Amber)
```
Light:  #fef3c7  ▒▒▒▒▒▒▒▒▒
Base:   #f59e0b  █████████
Dark:   #d97706  █████████
```

### Error (Red)
```
Light:  #fee2e2  ▒▒▒▒▒▒▒▒▒
Base:   #ef4444  █████████
Dark:   #dc2626  █████████
```

### Info (Blue)
```
Light:  #dbeafe  ▒▒▒▒▒▒▒▒▒
Base:   #3b82f6  █████████
Dark:   #2563eb  █████████
```

---

## Typography

### Font Families
- **UI Text**: `Inter` (400, 500, 600, 700)
- **Code/Data**: `JetBrains Mono` (400, 500, 600)

### Font Sizes
```
text_xs:   12px  (0.75rem)   ← Small labels
text_sm:   14px  (0.875rem)  ← Table text
text_base: 16px  (1rem)      ← Body text
text_lg:   18px  (1.125rem)  ← Subheadings
text_xl:   20px  (1.25rem)
text_2xl:  24px  (1.5rem)
text_3xl:  30px  (1.875rem)
text_4xl:  36px  (2.25rem)   ← Main headings
```

### Font Weights
```
Normal:    400
Medium:    500
Semibold:  600
Bold:      700
```

---

## Spacing Scale (8px Base)

```
xs:    4px   (0.5 × base)  ← Tight spacing
sm:    8px   (1 × base)    ← Component padding
md:    12px  (1.5 × base)  ← Default gap
base:  16px  (2 × base)    ← Section spacing
lg:    24px  (3 × base)    ← Card padding
xl:    32px  (4 × base)    ← Large sections
xxl:   48px  (6 × base)    ← Page sections
xxxl:  64px  (8 × base)    ← Hero spacing
```

---

## Border Radius

```
sm:   6px   ← Buttons, badges
md:   8px   ← Inputs, cards
lg:   12px  ← Larger cards
xl:   16px  ← Modals
full: 9999px ← Pills, avatars
```

---

## Shadows

### Standard Shadows
```
sm:   Subtle depth (1px)
base: Default cards (3px)
md:   Elevated elements (6px)
lg:   Modals, dropdowns (15px)
xl:   Hero sections (25px)
```

### Glow Effects (for hover/focus)
```
glow_blue: rgba(59, 130, 246, 0.15)  ← Primary actions
glow_teal: rgba(13, 148, 136, 0.15)  ← Secondary actions
```

---

## Component Patterns

### Cards
```python
# Standard card
background: #ffffff
border_radius: 12px (lg)
box_shadow: 0 1px 3px rgba(0,0,0,0.1)
padding: 24px (lg)

# Interactive card (hover)
box_shadow: 0 4px 6px rgba(0,0,0,0.1)
transform: translateY(-2px)
```

### Buttons
```python
# Primary button
background: #1e3a8a (navy_800)
color: #ffffff
border_radius: 8px (md)
padding: 12px 24px (md lg)
font_weight: 600 (semibold)

# Hover state
background: #1e293b (navy_900)
box_shadow: glow_blue
```

### Inputs
```python
border: 1px solid #cbd5e1 (gray_300)
border_radius: 8px (md)
padding: 12px 16px (md base)
background: #ffffff

# Focus state
border_color: #0ea5e9 (sky_500)
box_shadow: glow_blue
```

### Tables
```python
# Header
background: #f1f5f9 (gray_100)
color: #334155 (gray_700)
font_weight: 600 (semibold)
padding: 12px 16px (md base)
position: sticky
top: 0

# Cell
padding: 12px 16px (md base)
border_bottom: 1px solid #e2e8f0 (gray_200)

# Row hover
background: #f8fafc (gray_50)
```

---

## Accessibility

### Color Contrast
- All text meets WCAG AA standards (4.5:1 minimum)
- Interactive elements have 3:1 contrast with backgrounds
- Focus states are clearly visible

### Interactive States
- Hover: Visual feedback (shadow/background change)
- Focus: Blue glow outline
- Active: Slightly darker background
- Disabled: Reduced opacity + no cursor pointer

---

## Usage Guidelines

### DO:
✅ Use Navy for primary actions and navigation
✅ Use Teal for secondary actions and highlights
✅ Use Sky for links and interactive elements
✅ Maintain consistent spacing using the 8px scale
✅ Use semantic colors for status messages
✅ Apply shadows for depth and hierarchy

### DON'T:
❌ Mix random hex colors - always use design system
❌ Use arbitrary spacing values
❌ Create custom shadows without reason
❌ Ignore hover/focus states
❌ Use colors with poor contrast

---

## Implementation Status

### ✅ Completed (Priority 1)
- [x] Color palette defined
- [x] Typography system created
- [x] Spacing scale established
- [x] Component presets built
- [x] Theme integrated into app

### 🔄 In Progress
- [ ] Priority 2: Upload Component Styling
- [ ] Priority 3: Navbar Enhancement
- [ ] Priority 4: Sidebar Navigation
- [ ] Priority 5: Card Layouts
- [ ] Priority 6: Table Styling

---

## Quick Reference - Most Used Values

```python
# Colors
primary:    Colors.navy_800   (#1e3a8a)
accent:     Colors.teal_600   (#0d9488)
highlight:  Colors.sky_500    (#0ea5e9)
text:       Colors.gray_600   (#475569)

# Spacing
card_padding:     Spacing.lg    (24px)
section_gap:      Spacing.base  (16px)
component_gap:    Spacing.md    (12px)

# Borders
card_radius:      BorderRadius.lg   (12px)
button_radius:    BorderRadius.md   (8px)

# Shadows
card_shadow:      Shadows.base
hover_shadow:     Shadows.md
```

---

**Last Updated**: 2025-11-12
**Version**: 1.0.0
**Status**: Priority 1 Complete ✅
