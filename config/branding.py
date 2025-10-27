"""
Aero Crew Data brand identity and styling configuration.

This module centralizes all brand colors, logo paths, and styling constants
used throughout PDF reports and visualizations.
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class BrandColors:
    """
    Brand color palette for Aero Crew Data.

    All colors are in hex format (#RRGGBB).
    """

    # Primary brand color - Navy blue for headers and primary backgrounds
    primary_hex: str = "#0C1E36"

    # Accent color - Teal for highlights, CTAs, and interactive elements
    accent_hex: str = "#1BB3A4"

    # Rule/border color - Gray for dividers and borders
    rule_hex: str = "#5B6168"

    # Muted text color - Gray for secondary typography
    muted_hex: str = "#5B6168"

    # Alternate background - Light slate for zebra striping (high contrast)
    bg_alt_hex: str = "#F8FAFC"

    # Supporting accent - Sky blue for data visualization
    sky_hex: str = "#2E9BE8"

    def to_dict(self) -> Dict[str, str]:
        """
        Convert brand colors to dictionary format.

        Provides backward compatibility with code expecting dict format.

        Returns:
            Dictionary with color names as keys and hex values as strings
        """
        return {
            "primary_hex": self.primary_hex,
            "accent_hex": self.accent_hex,
            "rule_hex": self.rule_hex,
            "muted_hex": self.muted_hex,
            "bg_alt_hex": self.bg_alt_hex,
            "sky_hex": self.sky_hex,
        }


# Default brand instance
DEFAULT_BRAND = BrandColors()

# Logo and Report Configuration
LOGO_PATH = "logo-full.svg"
DEFAULT_REPORT_TITLE = "Analysis Report"
