# Theme Usage Guide: Navy/Teal/Sky Brand Colors

## Quick Reference

### Brand Color Palette

| Color | Usage | Hex Value | Python Constant |
|-------|-------|-----------|-----------------|
| **Navy** | Primary brand, buttons, navigation | `#1e3a8a` | `Colors.navy_800` |
| **Teal** | Accent, success, downloads | `#0d9488` | `Colors.teal_600` |
| **Sky** | Highlight, info, links | `#0ea5e9` | `Colors.sky_500` |
| **Gray** | Text, borders, backgrounds | `#475569` | `Colors.gray_600` |

## Two Ways to Use Brand Colors

### Method 1: Direct Color References (Recommended)
Use the `Colors` class for precise control:

```python
from reflex_app.theme import Colors

# Text with custom color
rx.text("Hello", color=Colors.navy_800)

# Button with custom background
rx.button("Click", background=Colors.teal_600)

# Icon with custom color
rx.icon("plane", color=Colors.sky_500)
```

**Pros:**
- Explicit and predictable
- Type-safe with IDE autocomplete
- Clear intent in code

**Use when:**
- You need precise control over colors
- Building reusable components
- Setting backgrounds, borders, or icon colors

### Method 2: Radix Color Names (Now Brand Colors!)
Use generic Radix color names that automatically map to brand colors:

```python
# These now use Navy colors via CSS overrides
rx.button("Primary", color="blue")  # Navy
rx.badge("Status", color_scheme="indigo")  # Navy
rx.callout("Info", color="blue")  # Navy

# These now use Teal colors via CSS overrides
rx.button("Success", color="green")  # Teal
rx.badge("Active", color_scheme="teal")  # Teal

# These now use Sky colors via CSS overrides
rx.text("Highlight", color="cyan")  # Sky
```

**Pros:**
- Cleaner syntax for Radix components
- Semantic meaning (blue = primary, green = success)
- Works with all Radix UI component color properties

**Use when:**
- Working with Radix UI components (`rx.button`, `rx.badge`, `rx.callout`, etc.)
- You want semantic color names
- Building forms and interactive elements

## Color Mapping Reference

### Components Using `color` Property

| Component | Property | Maps To | Example |
|-----------|----------|---------|---------|
| `rx.button()` | `color="blue"` | Navy | Primary actions |
| `rx.button()` | `color="green"` | Teal | Success actions |
| `rx.callout()` | `color="blue"` | Navy | Info messages |
| `rx.callout()` | `color="green"` | Teal | Success messages |
| `rx.text()` | `color="blue"` | Navy | Emphasized text |

### Components Using `color_scheme` Property

| Component | Property | Maps To | Example |
|-----------|----------|---------|---------|
| `rx.badge()` | `color_scheme="blue"` | Navy | Status badges |
| `rx.badge()` | `color_scheme="green"` | Teal | Active badges |
| `rx.icon_button()` | `color_scheme="blue"` | Navy | Icon buttons |

## Complete Color Scale Usage

Each brand color has a full scale from 50 (lightest) to 900 (darkest):

### Navy Scale (Primary)
```python
Colors.navy_50   # #eff6ff - Lightest background
Colors.navy_100  # #dbeafe - Light background
Colors.navy_200  # #bfdbfe - Subtle borders
Colors.navy_300  # #93c5fd - Soft borders
Colors.navy_400  # #60a5fa - Hover states
Colors.navy_500  # #3b82f6 - Active states
Colors.navy_600  # #2563eb - Solid colors
Colors.navy_700  # #1d4ed8 - Interactive elements
Colors.navy_800  # #1e3a8a - PRIMARY BRAND COLOR ⭐
Colors.navy_900  # #1e293b - Darkest text
```

### Teal Scale (Accent)
```python
Colors.teal_50   # #f0fdfa - Lightest background
Colors.teal_100  # #ccfbf1 - Light background
Colors.teal_200  # #99f6e4 - Subtle borders
Colors.teal_300  # #5eead4 - Soft borders
Colors.teal_400  # #2dd4bf - Hover states
Colors.teal_500  # #14b8a6 - Active states
Colors.teal_600  # #0d9488 - ACCENT COLOR ⭐
Colors.teal_700  # #0f766e - Pressed states
Colors.teal_800  # #115e59 - Dark text
Colors.teal_900  # #134e4a - Darkest text
```

### Sky Scale (Highlight)
```python
Colors.sky_50    # #f0f9ff - Lightest background
Colors.sky_100   # #e0f2fe - Light background
Colors.sky_200   # #bae6fd - Subtle borders
Colors.sky_300   # #7dd3fc - Soft borders
Colors.sky_400   # #38bdf8 - Hover states
Colors.sky_500   # #0ea5e9 - HIGHLIGHT COLOR ⭐
Colors.sky_600   # #0284c7 - Pressed states
Colors.sky_700   # #0369a1 - Dark states
Colors.sky_800   # #075985 - Dark text
Colors.sky_900   # #0c4a6e - Darkest text
```

### Gray Scale (Neutral)
```python
Colors.gray_50   # #f8fafc - Page background
Colors.gray_100  # #f1f5f9 - Card background
Colors.gray_200  # #e2e8f0 - Borders
Colors.gray_300  # #cbd5e1 - Dividers
Colors.gray_400  # #94a3b8 - Disabled text
Colors.gray_500  # #64748b - Subtle text
Colors.gray_600  # #475569 - BODY TEXT ⭐
Colors.gray_700  # #334155 - Headings
Colors.gray_800  # #1e293b - Strong text
Colors.gray_900  # #0f172a - Darkest text
```

## Common Patterns

### Primary Button
```python
rx.button(
    "Save",
    color="blue",  # Navy via CSS override
    variant="solid",
    size="3",
)
```

### Success Button
```python
rx.button(
    "Download",
    color="green",  # Teal via CSS override
    variant="soft",
    size="3",
)
```

### Custom Background Button
```python
rx.button(
    "Custom",
    background=Colors.navy_700,
    color="white",
    _hover={"background": Colors.navy_800},
)
```

### Status Badge
```python
rx.badge(
    "Active",
    color_scheme="blue",  # Navy via CSS override
    variant="soft",
    size="2",
)
```

### Callout/Alert
```python
rx.callout.root(
    rx.callout.text("Important info"),
    icon="info",
    color="blue",  # Navy via CSS override
)
```

### Card with Brand Colors
```python
rx.card(
    rx.vstack(
        rx.heading("Title", color=Colors.navy_800),
        rx.text("Content", color=Colors.gray_600),
        rx.button("Action", color="green"),  # Teal
    ),
    background=Colors.gray_50,
    border=f"1px solid {Colors.gray_200}",
)
```

### Navigation Item
```python
rx.box(
    rx.hstack(
        rx.icon("home", color=Colors.navy_700),
        rx.text("Home", color=Colors.navy_800),
    ),
    background=Colors.navy_100,
    border_left=f"3px solid {Colors.navy_600}",
    _hover={"background": Colors.navy_200},
)
```

## Semantic Color Usage

### Status Colors (Keep Radix Defaults)
For semantic status colors, use Radix defaults:

```python
# ✅ Success - Use Teal
rx.callout("Success!", color="green")  # Maps to Teal

# ⚠️ Warning - Use Radix amber/orange
rx.callout("Warning!", color="amber")  # Keeps Radix amber

# ❌ Error - Use Radix red
rx.callout("Error!", color="red")  # Keeps Radix red

# ℹ️ Info - Use Navy
rx.callout("Info", color="blue")  # Maps to Navy
```

## Typography with Brand Colors

```python
from reflex_app.theme import Colors, Typography

# Heading with Navy
rx.heading(
    "Page Title",
    size="8",
    weight="bold",
    color=Colors.navy_800,
)

# Body text with Gray
rx.text(
    "Description text",
    size="4",
    color=Colors.gray_600,
    font_family=Typography.font_ui,
)

# Code/monospace text
rx.code(
    "def hello():",
    font_family=Typography.font_mono,
    color=Colors.gray_700,
)
```

## Backgrounds and Borders

```python
# Light background
rx.box(
    "Content",
    background=Colors.gray_50,
    border=f"1px solid {Colors.gray_200}",
)

# Navy accent background
rx.box(
    "Highlighted",
    background=Colors.navy_100,
    border_left=f"3px solid {Colors.navy_600}",
)

# Teal accent background
rx.box(
    "Success state",
    background=Colors.teal_50,
    border=f"1px solid {Colors.teal_200}",
)
```

## Interactive States

```python
# Button with hover/active states
rx.button(
    "Interactive",
    background=Colors.navy_700,
    color="white",
    _hover={
        "background": Colors.navy_800,
        "transform": "translateY(-2px)",
    },
    _active={
        "background": Colors.navy_900,
        "transform": "translateY(0)",
    },
)
```

## Best Practices

### DO ✅
- Use `Colors.navy_800` for primary brand color
- Use `Colors.teal_600` for success/accent actions
- Use `Colors.gray_600` for body text
- Use `color="blue"` for Radix components (maps to Navy)
- Use `color="green"` for success actions (maps to Teal)
- Keep semantic colors (red, amber) for errors/warnings

### DON'T ❌
- Don't hardcode hex values like `color="#1e3a8a"`
- Don't use random color values
- Don't override semantic warning/error colors
- Don't use Navy/Teal for error states
- Don't use too many different shades in one component

## Testing Your Colors

To verify your colors are working:

1. **Run the app:**
   ```bash
   cd reflex_app
   source .venv_reflex/bin/activate
   reflex run
   ```

2. **Check these elements:**
   - Sidebar navigation should show Navy accents
   - Primary buttons should be Navy
   - Success buttons should be Teal
   - Badges should use brand colors
   - Text should be Gray 600-700

3. **Browser DevTools:**
   - Inspect elements
   - Check computed styles
   - Look for `--blue-9`, `--green-7`, etc. CSS variables
   - Verify they match Navy/Teal hex values

## Need Help?

- **Theme definition:** `/reflex_app/reflex_app/theme.py`
- **CSS overrides:** `/reflex_app/assets/theme_overrides.css`
- **Fix summary:** `/reflex_app/THEME_FIX_SUMMARY.md`
- **Design system:** `/reflex_app/DESIGN_SYSTEM.md`
