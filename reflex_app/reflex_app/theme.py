"""Design System Theme for Aero Crew Data Analyzer.

This module provides a comprehensive design system including:
- Color palette (Navy primary, Teal accent, Sky highlight)
- Typography system (Inter for UI, JetBrains Mono for data)
- Spacing constants (8px base scale)
- Border radius values
- Shadow definitions
- Semantic colors
- Radix UI theme configuration
"""

import reflex as rx
from typing import Dict, Any

# ============================================================================
# COLOR PALETTE
# ============================================================================

class Colors:
    """Brand color scales and semantic colors."""

    # Navy (Primary) - Professional, trustworthy
    navy_50 = "#eff6ff"
    navy_100 = "#dbeafe"
    navy_200 = "#bfdbfe"
    navy_300 = "#93c5fd"
    navy_400 = "#60a5fa"
    navy_500 = "#3b82f6"
    navy_600 = "#2563eb"
    navy_700 = "#1d4ed8"
    navy_800 = "#1e3a8a"  # Primary brand color
    navy_900 = "#1e293b"

    # Teal (Accent) - Fresh, modern
    teal_50 = "#f0fdfa"
    teal_100 = "#ccfbf1"
    teal_200 = "#99f6e4"
    teal_300 = "#5eead4"
    teal_400 = "#2dd4bf"
    teal_500 = "#14b8a6"
    teal_600 = "#0d9488"  # Accent color
    teal_700 = "#0f766e"
    teal_800 = "#115e59"
    teal_900 = "#134e4a"

    # Sky (Highlight) - Aviation, clarity
    sky_50 = "#f0f9ff"
    sky_100 = "#e0f2fe"
    sky_200 = "#bae6fd"
    sky_300 = "#7dd3fc"
    sky_400 = "#38bdf8"
    sky_500 = "#0ea5e9"  # Highlight color
    sky_600 = "#0284c7"
    sky_700 = "#0369a1"
    sky_800 = "#075985"
    sky_900 = "#0c4a6e"

    # Gray (Text and backgrounds)
    gray_50 = "#f8fafc"
    gray_100 = "#f1f5f9"
    gray_200 = "#e2e8f0"
    gray_300 = "#cbd5e1"
    gray_400 = "#94a3b8"
    gray_500 = "#64748b"
    gray_600 = "#475569"  # Body text
    gray_700 = "#334155"
    gray_800 = "#1e293b"
    gray_900 = "#0f172a"

    # Semantic colors
    success_light = "#d1fae5"
    success = "#10b981"
    success_dark = "#047857"

    warning_light = "#fef3c7"
    warning = "#f59e0b"
    warning_dark = "#d97706"

    error_light = "#fee2e2"
    error = "#ef4444"
    error_dark = "#dc2626"

    info_light = "#dbeafe"
    info = "#3b82f6"
    info_dark = "#2563eb"

    # Backgrounds
    bg_primary = "#ffffff"
    bg_secondary = "#f8fafc"
    bg_tertiary = "#f1f5f9"


class DarkColors:
    """Dark mode color palette."""

    # Dark backgrounds
    bg_primary = "#0f172a"     # Very dark navy
    bg_secondary = "#1e293b"   # Dark navy (cards, elevated surfaces)
    bg_tertiary = "#334155"    # Lighter dark navy (hover states)

    # Dark text
    text_primary = "#f1f5f9"   # Light gray (high contrast)
    text_secondary = "#cbd5e1" # Medium gray (body text)
    text_tertiary = "#94a3b8"  # Darker gray (captions)

    # Dark borders
    border = "#334155"         # Subtle dividers
    border_hover = "#475569"   # Hover state borders

    # Brand colors (adjusted for dark backgrounds)
    navy_accent = "#3b82f6"    # Brighter blue for visibility
    teal_accent = "#14b8a6"    # Bright teal
    sky_accent = "#38bdf8"     # Bright sky blue

    # Semantic colors for dark mode
    success = "#10b981"        # Green
    success_bg = "#064e3b"     # Dark green bg
    warning = "#f59e0b"        # Amber
    warning_bg = "#78350f"     # Dark amber bg
    error = "#ef4444"          # Red
    error_bg = "#7f1d1d"       # Dark red bg


# ============================================================================
# TYPOGRAPHY
# ============================================================================

class Typography:
    """Typography system with font families and scales."""

    # Font families
    font_ui = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
    font_mono = "'JetBrains Mono', 'Monaco', 'Consolas', monospace"

    # Font sizes (in rem units)
    text_xs = "0.75rem"    # 12px
    text_sm = "0.875rem"   # 14px
    text_base = "1rem"     # 16px
    text_lg = "1.125rem"   # 18px
    text_xl = "1.25rem"    # 20px
    text_2xl = "1.5rem"    # 24px
    text_3xl = "1.875rem"  # 30px
    text_4xl = "2.25rem"   # 36px

    # Font weights
    weight_normal = "400"
    weight_medium = "500"
    weight_semibold = "600"
    weight_bold = "700"

    # Line heights
    leading_tight = "1.25"
    leading_normal = "1.5"
    leading_relaxed = "1.75"


# ============================================================================
# SPACING
# ============================================================================

class Spacing:
    """Spacing scale based on 8px base unit."""

    xs = "4px"      # 0.5 × base
    sm = "8px"      # 1 × base
    md = "12px"     # 1.5 × base
    base = "16px"   # 2 × base
    lg = "24px"     # 3 × base
    xl = "32px"     # 4 × base
    xxl = "48px"    # 6 × base
    xxxl = "64px"   # 8 × base


# ============================================================================
# BORDER RADIUS
# ============================================================================

class BorderRadius:
    """Border radius values for different component sizes."""

    sm = "6px"
    md = "8px"
    lg = "12px"
    xl = "16px"
    full = "9999px"


# ============================================================================
# SHADOWS
# ============================================================================

class Shadows:
    """Box shadow definitions for depth."""

    sm = "0 1px 2px 0 rgba(0, 0, 0, 0.05)"
    base = "0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)"
    md = "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)"
    lg = "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)"
    xl = "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)"

    # Blue glow for interactive elements
    glow_blue = "0 0 0 3px rgba(59, 130, 246, 0.15)"
    glow_teal = "0 0 0 3px rgba(13, 148, 136, 0.15)"


# ============================================================================
# RADIX UI THEME CONFIGURATION
# ============================================================================

def get_theme_config() -> Dict[str, Any]:
    """Get Radix UI theme configuration.

    Custom color overrides are applied via /assets/theme_overrides.css which maps
    Radix color scales to our Navy/Teal/Sky brand palette:
    - Blue/Indigo/Accent -> Navy (primary brand color)
    - Green/Teal -> Teal (accent color)
    - Cyan -> Sky (highlight color)

    Returns:
        Dictionary of theme configuration options
    """
    return {
        "appearance": "light",
        "has_background": True,
        "radius": "medium",
        "accent_color": "blue",  # Maps to Navy via CSS overrides
        "gray_color": "slate",
        "panel_background": "solid",
        "scaling": "100%",
    }


# ============================================================================
# GLOBAL STYLES
# ============================================================================

def get_global_styles() -> Dict[str, Any]:
    """Get global CSS styles for the application.

    Returns:
        Dictionary of global style rules
    """
    return {
        # Body styles
        "body": {
            "font_family": Typography.font_ui,
            "color": Colors.gray_800,
            "background": Colors.bg_secondary,
        },

        # Headings
        "h1, h2, h3, h4, h5, h6": {
            "color": Colors.navy_800,
            "font_weight": Typography.weight_bold,
        },

        # Links
        "a": {
            "color": Colors.sky_500,
            "text_decoration": "none",
            "transition": "color 0.2s ease",
        },
        "a:hover": {
            "color": Colors.sky_600,
        },

        # Code blocks (monospace)
        "code, pre": {
            "font_family": Typography.font_mono,
        },
    }


# ============================================================================
# COMPONENT STYLE PRESETS
# ============================================================================

class ComponentStyles:
    """Reusable style presets for common components."""

    @staticmethod
    def card() -> Dict[str, Any]:
        """Standard card styling."""
        return {
            "background": Colors.bg_primary,
            "border_radius": BorderRadius.lg,
            "box_shadow": Shadows.base,
            "padding": Spacing.lg,
        }

    @staticmethod
    def card_interactive() -> Dict[str, Any]:
        """Interactive card with hover effect."""
        return {
            **ComponentStyles.card(),
            "cursor": "pointer",
            "transition": "all 0.2s ease",
            "_hover": {
                "box_shadow": Shadows.md,
                "transform": "translateY(-2px)",
            },
        }

    @staticmethod
    def button_primary() -> Dict[str, Any]:
        """Primary button styling."""
        return {
            "background": Colors.navy_800,
            "color": "#ffffff",
            "border_radius": BorderRadius.md,
            "padding": f"{Spacing.md} {Spacing.lg}",
            "font_weight": Typography.weight_semibold,
            "cursor": "pointer",
            "transition": "all 0.2s ease",
            "_hover": {
                "background": Colors.navy_900,
                "box_shadow": Shadows.glow_blue,
            },
        }

    @staticmethod
    def button_secondary() -> Dict[str, Any]:
        """Secondary button styling."""
        return {
            "background": Colors.teal_600,
            "color": "#ffffff",
            "border_radius": BorderRadius.md,
            "padding": f"{Spacing.md} {Spacing.lg}",
            "font_weight": Typography.weight_semibold,
            "cursor": "pointer",
            "transition": "all 0.2s ease",
            "_hover": {
                "background": Colors.teal_700,
                "box_shadow": Shadows.glow_teal,
            },
        }

    @staticmethod
    def input_field() -> Dict[str, Any]:
        """Input field styling."""
        return {
            "border": f"1px solid {Colors.gray_300}",
            "border_radius": BorderRadius.md,
            "padding": f"{Spacing.md} {Spacing.base}",
            "background": Colors.bg_primary,
            "transition": "all 0.2s ease",
            "_focus": {
                "border_color": Colors.sky_500,
                "box_shadow": Shadows.glow_blue,
                "outline": "none",
            },
        }

    @staticmethod
    def table_header() -> Dict[str, Any]:
        """Table header styling."""
        return {
            "background": Colors.gray_100,
            "color": Colors.gray_700,
            "font_weight": Typography.weight_semibold,
            "font_size": Typography.text_sm,
            "padding": f"{Spacing.md} {Spacing.base}",
            "border_bottom": f"2px solid {Colors.gray_300}",
            "position": "sticky",
            "top": "0",
            "z_index": "10",
        }

    @staticmethod
    def table_cell() -> Dict[str, Any]:
        """Table cell styling."""
        return {
            "padding": f"{Spacing.md} {Spacing.base}",
            "border_bottom": f"1px solid {Colors.gray_200}",
            "font_size": Typography.text_sm,
        }

    @staticmethod
    def table_row_hover() -> Dict[str, Any]:
        """Table row hover effect."""
        return {
            "transition": "background-color 0.15s ease",
            "_hover": {
                "background": Colors.gray_50,
            },
        }


# ============================================================================
# THEME EXPORT
# ============================================================================

# Export main theme object for easy import
theme = {
    "colors": Colors,
    "dark_colors": DarkColors,
    "typography": Typography,
    "spacing": Spacing,
    "border_radius": BorderRadius,
    "shadows": Shadows,
    "component_styles": ComponentStyles,
}
