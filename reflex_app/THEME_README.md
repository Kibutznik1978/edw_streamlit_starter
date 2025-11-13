# Aero Crew Data Analyzer - Design System Theme

This document describes how to use the custom design system theme in the Reflex application.

## Overview

The theme is defined in `/reflex_app/reflex_app/theme.py` and provides:

- **Color Palette**: Navy (primary), Teal (accent), Sky (highlight), Gray (text)
- **Typography**: Inter for UI, JetBrains Mono for data/code
- **Spacing Scale**: 8px base unit (4px, 8px, 12px, 16px, 24px, 32px, 48px, 64px)
- **Border Radius**: sm (6px), md (8px), lg (12px), xl (16px)
- **Shadows**: Multiple depth levels + glow effects
- **Component Presets**: Reusable styles for cards, buttons, inputs, tables

## Theme Integration

The theme is automatically applied in `/reflex_app/reflex_app/reflex_app.py`:

```python
from .theme import get_theme_config, get_global_styles

app = rx.App(
    theme=rx.theme(**get_theme_config()),
    stylesheets=[
        "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap",
        "https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap",
    ],
    style=get_global_styles(),
)
```

## Usage Examples

### Importing Theme Elements

```python
from reflex_app.theme import Colors, Typography, Spacing, BorderRadius, Shadows, ComponentStyles
```

### Using Colors

```python
import reflex as rx

# Primary colors
rx.box(background=Colors.navy_800, color="#ffffff")

# Accent colors
rx.button("Click Me", background=Colors.teal_600)

# Semantic colors
rx.callout(background=Colors.success_light, color=Colors.success_dark)
```

### Using Component Presets

```python
# Standard card
rx.box(**ComponentStyles.card())

# Interactive card with hover
rx.box(**ComponentStyles.card_interactive())

# Primary button
rx.button("Submit", **ComponentStyles.button_primary())

# Input field
rx.input(**ComponentStyles.input_field())

# Table header
rx.table.header(**ComponentStyles.table_header())
```

### Using Spacing

```python
# Padding
rx.box(padding=Spacing.lg)  # 24px

# Margin
rx.text("Hello", margin_top=Spacing.base)  # 16px

# Gap in stack
rx.vstack(spacing=Spacing.md)  # 12px
```

### Using Shadows

```python
# Card with shadow
rx.box(box_shadow=Shadows.md)

# Button with glow on hover
rx.button(
    "Click",
    _hover={"box_shadow": Shadows.glow_blue}
)
```

## Brand Colors

### Navy (Primary) - Professional, Trustworthy
- **Primary**: `Colors.navy_800` (#1e3a8a)
- Use for: Primary buttons, headings, important text

### Teal (Accent) - Fresh, Modern
- **Accent**: `Colors.teal_600` (#0d9488)
- Use for: Secondary actions, highlights, badges

### Sky (Highlight) - Aviation, Clarity
- **Highlight**: `Colors.sky_500` (#0ea5e9)
- Use for: Links, interactive elements, info callouts

### Gray (Text & Backgrounds)
- **Body Text**: `Colors.gray_600` (#475569)
- **Backgrounds**: `Colors.gray_50` to `Colors.gray_200`
- Use for: Text hierarchy, neutral backgrounds

## Typography

### Font Families
- **UI Text**: `Typography.font_ui` (Inter)
- **Code/Data**: `Typography.font_mono` (JetBrains Mono)

### Example
```python
# Data table with monospace numbers
rx.text("123.45", font_family=Typography.font_mono)

# UI heading
rx.heading("Welcome", font_family=Typography.font_ui)
```

## Complete Component Example

```python
import reflex as rx
from reflex_app.theme import Colors, Spacing, BorderRadius, Shadows

def my_card() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.heading(
                "Card Title",
                color=Colors.navy_800,
                margin_bottom=Spacing.md,
            ),
            rx.text(
                "Card content goes here",
                color=Colors.gray_600,
            ),
            rx.button(
                "Action",
                background=Colors.teal_600,
                color="#ffffff",
                border_radius=BorderRadius.md,
                _hover={
                    "background": Colors.teal_700,
                    "box_shadow": Shadows.glow_teal,
                },
            ),
            spacing=Spacing.md,
        ),
        background=Colors.bg_primary,
        padding=Spacing.lg,
        border_radius=BorderRadius.lg,
        box_shadow=Shadows.base,
    )
```

## Next Steps

After Priority 1 (Theme) is complete, the following priorities will enhance the UI:

- **Priority 2**: Improve Upload Component Styling
- **Priority 3**: Enhance Navbar with User Menu
- **Priority 4**: Add Sidebar Navigation
- **Priority 5**: Polish Card Layouts
- **Priority 6**: Improve Table Styling

Each priority will use the design system to maintain visual consistency.
