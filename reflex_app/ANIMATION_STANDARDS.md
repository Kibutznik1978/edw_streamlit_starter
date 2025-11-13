# Animation Standards Guide

**Quick Reference for Reflex Development**

This guide provides animation standards and best practices for the Aero Crew Data Analyzer Reflex application.

---

## Standard Timing

Use these standard durations for consistency:

```python
# Snappy interactions (150ms)
transition="all 150ms ease"
# Use for: Buttons, nav items, badges, quick hover effects

# Standard interactions (200ms)
transition="all 200ms ease"
# Use for: Cards, containers, tooltips, dropdowns, accordions

# Smooth panels (300ms)
transition="left 300ms ease"
# Use for: Sidebars, drawers, large panels
```

---

## Button Animations

### Standard Button
```python
rx.button(
    "Click Me",
    on_click=handler,
    cursor="pointer",
    style={
        "transition": "all 150ms ease",
        "_hover": {
            "transform": "translateY(-1px)",
        },
    },
)
```

### Icon Button
```python
rx.icon_button(
    rx.icon("settings", size=20),
    on_click=handler,
    cursor="pointer",
    # CSS handles hover: scale(1.1)
)
```

---

## Card Animations

### Stat Card / Info Card
```python
rx.box(
    # ... card content ...,
    padding="4",
    border_radius="8px",
    border=f"1px solid {rx.color('gray', 6)}",
    background=rx.color("gray", 2),
    transition="all 200ms ease",
    _hover={
        "box_shadow": "0 4px 12px rgba(0, 0, 0, 0.1)",
        "transform": "translateY(-2px)",
        "border_color": rx.color('gray', 7),
    },
)
```

### Colored Stat Card
```python
rx.box(
    # ... card content ...,
    border=f"1px solid {rx.color(color, 6)}",
    background=rx.color(color, 2),
    transition="all 200ms ease",
    _hover={
        "box_shadow": f"0 4px 12px {rx.color(color, 4)}",
        "transform": "translateY(-2px)",
        "border_color": rx.color(color, 7),
    },
)
```

---

## Upload Zone Animation

```python
rx.upload(
    # ... upload content ...,
    border="2px dashed",
    border_color=Colors.gray_300,
    cursor="pointer",
    transition="all 200ms ease",
    _hover={
        "border_color": Colors.navy_500,
        "background": Colors.navy_50,
        "box_shadow": Shadows.glow_blue,
        "transform": "scale(1.01)",
    },
)
```

---

## Navigation Items

```python
rx.box(
    # ... nav item content ...,
    cursor="pointer",
    transition="all 150ms ease",
    _hover={
        "background": Colors.gray_100,
    },
)
```

---

## Table Rows

Table rows are handled by global CSS, but if you need custom styling:

```python
rx.table.row(
    # ... table cells ...,
    cursor="pointer",
    style={
        "transition": "background-color 150ms ease",
        "_hover": {
            "background": Colors.gray_50,
        },
    },
)
```

---

## Badge Micro-Interactions

Badges automatically scale on hover via global CSS:
```python
rx.badge("Status", color_scheme="blue")
# CSS handles hover: scale(1.05)
```

---

## Content Entrance Animations

### Fade In (using CSS animation)
```python
rx.box(
    # ... content ...,
    animation="fadeIn 300ms ease",
)
```

### Conditional Content
```python
rx.cond(
    condition,
    rx.box(
        # ... content that appears ...,
        animation="fadeIn 200ms ease",
    ),
    rx.fragment(),
)
```

---

## CSS Animation Classes

### Available Keyframes (in theme_overrides.css)

**fadeIn** - Smooth content entrance
```css
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}
```

**slideInLeft** - Slide from left
```css
@keyframes slideInLeft {
    from { transform: translateX(-10px); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
}
```

**scaleIn** - Scale up entrance
```css
@keyframes scaleIn {
    from { transform: scale(0.95); opacity: 0; }
    to { transform: scale(1); opacity: 1; }
}
```

**pulse** - Loading indicator
```css
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}
```

---

## Performance Best Practices

### DO ✅
- Use `transform` for movement (GPU accelerated)
- Use `opacity` for fading (GPU accelerated)
- Use `box-shadow` for elevation changes
- Keep transitions under 300ms
- Use `ease` easing for natural feel

### DON'T ❌
- Don't animate `width`, `height`, `top`, `left` (causes layout shifts)
- Don't use `linear` easing (feels robotic)
- Don't make transitions too slow (>500ms)
- Don't animate too many properties at once
- Don't forget accessibility (reduced motion)

---

## Accessibility

**Always respect reduced motion preferences.**

The global CSS automatically handles this:
```css
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation-duration: 0.01ms !important;
        transition-duration: 0.01ms !important;
    }
}
```

No additional code needed - all animations automatically become instant for users who prefer reduced motion.

---

## Common Patterns

### Loading State
```python
rx.button(
    rx.cond(
        is_loading,
        rx.hstack(
            rx.spinner(size="3"),  # Spinner has built-in animation
            rx.text("Loading..."),
            spacing="2",
        ),
        rx.text("Submit"),
    ),
    disabled=is_loading,
    cursor="pointer",
)
```

### Hover Elevation
```python
style={
    "transition": "all 200ms ease",
    "_hover": {
        "transform": "translateY(-2px)",
        "box_shadow": "0 4px 12px rgba(0, 0, 0, 0.1)",
    },
}
```

### Hover Scale
```python
style={
    "transition": "transform 150ms ease",
    "_hover": {
        "transform": "scale(1.05)",
    },
}
```

### Active Press
```python
style={
    "transition": "transform 150ms ease",
    "_hover": {
        "transform": "translateY(-1px)",
    },
    "_active": {
        "transform": "translateY(0)",
    },
}
```

---

## Global CSS Enhancements

These elements automatically have smooth transitions:
- All buttons (`.rt-Button`)
- All cards (`.rt-Card`)
- All badges (`.rt-Badge`)
- All icon buttons (`.rt-IconButton`)
- All table rows (`.rt-TableRow`)
- All accordion triggers (`.rt-AccordionTrigger`)
- All select triggers (`.rt-SelectTrigger`)
- All slider thumbs (`.rt-SliderThumb`)

**No additional code needed** - they just work!

---

## Testing Checklist

When adding new components, verify:

- [ ] Hover states are responsive (no delay)
- [ ] Transitions are smooth (no jank)
- [ ] Timing matches similar elements (150/200/300ms)
- [ ] Works in dark mode
- [ ] Works on mobile/tablet
- [ ] Respects reduced motion preference

---

## Examples from the Codebase

### Sidebar Navigation
```python
# /reflex_app/reflex_app/components/layout/sidebar.py
transition="left 300ms ease"  # Smooth slide
```

### Upload Component
```python
# /reflex_app/reflex_app/edw/components/upload.py
transition="all 200ms ease"
_hover={
    "transform": "scale(1.01)",
}
```

### Stat Cards
```python
# /reflex_app/reflex_app/edw/components/summary.py
transition="all 200ms ease"
_hover={
    "transform": "translateY(-2px)",
    "box_shadow": "0 4px 12px rgba(0, 0, 0, 0.1)",
}
```

### Download Buttons
```python
# /reflex_app/reflex_app/edw/components/downloads.py
style={
    "transition": "all 150ms ease",
    "_hover": {
        "transform": "translateY(-2px)",
    },
}
```

---

## Quick Copy-Paste Templates

### Generic Button
```python
rx.button(
    "Action",
    on_click=handler,
    cursor="pointer",
    style={
        "transition": "all 150ms ease",
        "_hover": {"transform": "translateY(-1px)"},
    },
)
```

### Generic Card
```python
rx.box(
    # content,
    padding="4",
    border_radius="8px",
    border=f"1px solid {rx.color('gray', 6)}",
    transition="all 200ms ease",
    _hover={
        "box_shadow": "0 4px 12px rgba(0, 0, 0, 0.1)",
        "transform": "translateY(-2px)",
    },
)
```

### Generic Badge
```python
rx.badge("Label", color_scheme="blue")
# Hover scale handled by CSS automatically
```

---

## Resources

- **Main CSS File**: `/reflex_app/assets/theme_overrides.css`
- **Animation Examples**: See any component in `/reflex_app/reflex_app/edw/components/`
- **Theme Config**: `/reflex_app/reflex_app/theme.py`
- **Completion Report**: `/reflex_app/FINAL_COMPLETION_REPORT.md`

---

**Last Updated:** December 12, 2024
**Version:** 1.0
**Status:** Production Ready
