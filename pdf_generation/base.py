"""
pdf_generation/base.py
Shared base components for PDF report generation (EDW and Bid Line).

Contains:
- Brand colors and default branding
- Color conversion utilities
- Header and footer rendering
- KPI badge flowables
- Common table styling
"""

import os
from datetime import datetime
from typing import Dict, Any, List

# ReportLab imports
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Table, TableStyle, Flowable
from reportlab.pdfgen import canvas as pdf_canvas

# Import brand configuration
from config.branding import DEFAULT_BRAND, LOGO_PATH, DEFAULT_REPORT_TITLE


# Default branding - Aero Crew Data brand palette
# Built from config.branding for backward compatibility with dict-based code
DEFAULT_BRANDING = {
    **DEFAULT_BRAND.to_dict(),
    "logo_path": LOGO_PATH,
    "title_left": DEFAULT_REPORT_TITLE
}


def hex_to_reportlab_color(hex_str: str) -> colors.Color:
    """
    Convert hex color string to ReportLab Color object.

    Args:
        hex_str: Hex color string (e.g., "#1BB3A4" or "1BB3A4")

    Returns:
        ReportLab Color object
    """
    hex_str = hex_str.lstrip('#')
    r, g, b = int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16)
    return colors.Color(r/255.0, g/255.0, b/255.0)


def draw_header(canvas: pdf_canvas.Canvas, doc, branding: Dict[str, Any]) -> None:
    """
    Draw professional header bar on each page.

    Args:
        canvas: ReportLab canvas object
        doc: Document object
        branding: Branding dictionary with colors and logo
    """
    canvas.saveState()

    # Draw header bar
    primary_color = hex_to_reportlab_color(branding["primary_hex"])
    canvas.setFillColor(primary_color)
    canvas.rect(0, letter[1] - 40, letter[0], 40, fill=1, stroke=0)

    # Draw title text
    canvas.setFillColor(colors.white)
    canvas.setFont('Helvetica-Bold', 11)
    canvas.drawString(36, letter[1] - 25, branding["title_left"])

    # Draw logo if provided
    if branding.get("logo_path") and os.path.exists(branding["logo_path"]):
        try:
            canvas.drawImage(
                branding["logo_path"],
                letter[0] - 100, letter[1] - 35,
                width=60, height=30,
                preserveAspectRatio=True,
                mask='auto'
            )
        except Exception:
            pass  # Silently skip if logo can't be loaded

    canvas.restoreState()


def draw_footer(canvas: pdf_canvas.Canvas, doc) -> None:
    """
    Draw professional footer on each page with timestamp and page number.

    Args:
        canvas: ReportLab canvas object
        doc: Document object
    """
    canvas.saveState()

    # Footer text styling
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(colors.HexColor("#6B7280"))

    # Left: timestamp with app name
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    canvas.drawString(36, 30, f"Generated: {timestamp} by Aero Crew Data App")

    # Right: page number
    page_num = canvas.getPageNumber()
    canvas.drawRightString(letter[0] - 36, 30, f"Page {page_num}")

    canvas.restoreState()


class KPIBadge(Flowable):
    """
    Custom flowable for KPI card display with optional range indicator.

    Features:
    - Rounded rectangle background with brand color
    - Label text at top
    - Large value in center
    - Optional range text at bottom (e.g., "↑ Range 65.8-85.7")
    """

    def __init__(
        self,
        label: str,
        value: str,
        branding: Dict[str, Any],
        width: float = 120,
        range_text: str = None
    ):
        """
        Initialize KPI badge.

        Args:
            label: Label text displayed at top
            value: Main value displayed in center
            branding: Branding dictionary with colors
            width: Badge width in points
            range_text: Optional range text displayed at bottom
        """
        Flowable.__init__(self)
        self.label = label
        self.value = value
        self.range_text = range_text
        self.branding = branding
        self.width = width
        self.height = 70 if range_text else 60  # Taller if showing range

    def draw(self):
        """Draw the KPI badge on the canvas."""
        canvas = self.canv

        # Background rectangle with rounded corners
        accent_color = hex_to_reportlab_color(self.branding["accent_hex"])
        canvas.setFillColor(accent_color)
        canvas.setStrokeColor(accent_color)
        canvas.roundRect(0, 0, self.width, self.height, 4, fill=1, stroke=1)

        # Label (small, muted)
        muted_color = hex_to_reportlab_color(self.branding["muted_hex"])
        canvas.setFillColor(muted_color)
        canvas.setFont('Helvetica', 9)
        canvas.drawCentredString(self.width / 2, self.height - 16, self.label)

        # Value (bold, dark)
        canvas.setFillColor(colors.HexColor("#111827"))
        canvas.setFont('Helvetica-Bold', 16)
        value_y = self.height - 38 if self.range_text else self.height - 45
        canvas.drawCentredString(self.width / 2, value_y, str(self.value))

        # Range text (small, green) if provided
        if self.range_text:
            canvas.setFillColor(colors.HexColor("#10B981"))  # Green color
            canvas.setFont('Helvetica', 8)
            canvas.drawCentredString(self.width / 2, self.height - 58, self.range_text)


def make_kpi_row(metrics: Dict[str, Any], branding: Dict[str, Any]) -> Table:
    """
    Create a row of KPI badges from metrics dictionary.

    Args:
        metrics: Dictionary where values can be either:
            - Simple value (str/number)
            - Dict with 'value' and optional 'range' keys
        branding: Branding dictionary with colors

    Returns:
        ReportLab Table containing KPI badges

    Examples:
        Simple values:
        >>> make_kpi_row({"Total Trips": 522, "EDW Trips": 242}, branding)

        With ranges:
        >>> make_kpi_row({
        ...     "Avg Credit": {"value": "75.3", "range": "↑ Range 65.8-85.7"},
        ...     "Avg Block": {"value": "62.1", "range": "↑ Range 55.0-70.5"}
        ... }, branding)
    """
    badges = []
    for label, metric_data in metrics.items():
        if isinstance(metric_data, dict):
            value = str(metric_data.get('value', ''))
            range_text = metric_data.get('range')
            badges.append(KPIBadge(label, value, branding, width=120, range_text=range_text))
        else:
            badges.append(KPIBadge(label, str(metric_data), branding, width=120))

    # Create table to hold badges
    table_data = [[badge for badge in badges]]
    table = Table(table_data, colWidths=[130] * len(badges))
    table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))

    return table


def make_styled_table(
    data: List[List[str]],
    col_widths: List[float],
    branding: Dict[str, Any]
) -> Table:
    """
    Create a professionally styled table with zebra striping.

    Features:
    - Header row with brand accent color background
    - Grid borders with brand rule color
    - Zebra striping for data rows
    - Centered alignment
    - Consistent padding

    Args:
        data: 2D list of table data (first row is header)
        col_widths: List of column widths in points
        branding: Branding dictionary with colors

    Returns:
        ReportLab Table with professional styling
    """
    table = Table(data, colWidths=col_widths)

    accent_color = hex_to_reportlab_color(branding["accent_hex"])
    rule_color = hex_to_reportlab_color(branding["rule_hex"])
    bg_alt_color = hex_to_reportlab_color(branding["bg_alt_hex"])

    style = TableStyle([
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), accent_color),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#111827")),
        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 10),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

        # Grid
        ('GRID', (0, 0), (-1, -1), 0.5, rule_color),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ])

    # Add zebra striping to data rows (every other row after header)
    for i in range(2, len(data), 2):
        style.add('BACKGROUND', (0, i), (-1, i), bg_alt_color)

    table.setStyle(style)
    return table
