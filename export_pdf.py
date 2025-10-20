"""
export_pdf.py
Professional two-page analytics report generator using ReportLab and Matplotlib.

Usage:
    from export_pdf import create_pdf_report

    create_pdf_report(data, "/path/to/report.pdf", branding)
"""

import os
import tempfile
from datetime import datetime
from typing import Dict, List, Optional, Any

# ReportLab imports
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
    Image, PageBreak, Flowable, HRFlowable, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfgen import canvas

# Matplotlib imports
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt


# Default branding
DEFAULT_BRANDING = {
    "primary_hex": "#1E40AF",  # Pleasant blue instead of black
    "accent_hex": "#F3F4F6",
    "rule_hex": "#E5E7EB",
    "muted_hex": "#6B7280",
    "bg_alt_hex": "#FAFAFA",
    "logo_path": None,
    "title_left": "Pairing Analysis Report"
}


def _hex_to_reportlab_color(hex_str: str) -> colors.Color:
    """Convert hex color string to ReportLab Color object."""
    hex_str = hex_str.lstrip('#')
    r, g, b = int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16)
    return colors.Color(r/255.0, g/255.0, b/255.0)


def _draw_header(canvas: canvas.Canvas, doc, branding: Dict[str, Any]) -> None:
    """Draw header bar on each page."""
    canvas.saveState()

    # Draw header bar
    primary_color = _hex_to_reportlab_color(branding["primary_hex"])
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


def _draw_footer(canvas: canvas.Canvas, doc) -> None:
    """Draw footer on each page."""
    canvas.saveState()

    # Footer text
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(colors.HexColor("#6B7280"))

    # Left: timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    canvas.drawString(36, 30, f"Generated: {timestamp}")

    # Right: page number
    page_num = canvas.getPageNumber()
    canvas.drawRightString(letter[0] - 36, 30, f"Page {page_num}")

    canvas.restoreState()


class KPIBadge(Flowable):
    """Custom flowable for KPI card display."""

    def __init__(self, label: str, value: str, branding: Dict[str, Any], width: float = 120):
        Flowable.__init__(self)
        self.label = label
        self.value = value
        self.branding = branding
        self.width = width
        self.height = 60

    def draw(self):
        """Draw the KPI badge."""
        canvas = self.canv

        # Background rectangle with rounded corners
        accent_color = _hex_to_reportlab_color(self.branding["accent_hex"])
        canvas.setFillColor(accent_color)
        canvas.setStrokeColor(accent_color)
        canvas.roundRect(0, 0, self.width, self.height, 4, fill=1, stroke=1)

        # Label (small, muted)
        muted_color = _hex_to_reportlab_color(self.branding["muted_hex"])
        canvas.setFillColor(muted_color)
        canvas.setFont('Helvetica', 9)
        canvas.drawCentredString(self.width / 2, self.height - 20, self.label)

        # Value (bold, dark)
        canvas.setFillColor(colors.HexColor("#111827"))
        canvas.setFont('Helvetica-Bold', 16)
        canvas.drawCentredString(self.width / 2, self.height - 45, str(self.value))


def _make_kpi_row(trip_summary: Dict[str, Any], branding: Dict[str, Any]) -> Table:
    """Create a row of KPI badges."""
    # Extract KPI values (first 4 items)
    kpis = list(trip_summary.items())[:4]

    # Create KPI badges
    badges = [KPIBadge(label, str(value), branding, width=120) for label, value in kpis]

    # Create table to hold badges
    table_data = [[badge for badge in badges]]
    table = Table(table_data, colWidths=[130] * len(badges))
    table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))

    return table


def _make_weighted_summary_table(weighted_summary: Dict[str, str], branding: Dict[str, Any]) -> Table:
    """Create weighted summary table with zebra striping."""
    # Convert dict to list of lists
    data = [["Metric", "Value"]]
    for metric, value in weighted_summary.items():
        data.append([metric, value])

    # Create table
    table = Table(data, colWidths=[340, 100])

    # Style
    accent_color = _hex_to_reportlab_color(branding["accent_hex"])
    rule_color = _hex_to_reportlab_color(branding["rule_hex"])
    bg_alt_color = _hex_to_reportlab_color(branding["bg_alt_hex"])

    style = TableStyle([
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), accent_color),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#111827")),
        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 10),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),

        # Grid
        ('GRID', (0, 0), (-1, -1), 0.5, rule_color),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),

        # Zebra striping
        ('BACKGROUND', (0, 2), (-1, 2), bg_alt_color),
    ])

    table.setStyle(style)
    return table


def _make_duty_day_stats_table(duty_day_stats: List[List[str]], branding: Dict[str, Any]) -> Table:
    """Create duty day statistics table."""
    # Create table
    table = Table(duty_day_stats, colWidths=[160, 90, 90, 90])

    # Style
    accent_color = _hex_to_reportlab_color(branding["accent_hex"])
    rule_color = _hex_to_reportlab_color(branding["rule_hex"])
    bg_alt_color = _hex_to_reportlab_color(branding["bg_alt_hex"])

    style = TableStyle([
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), accent_color),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#111827")),
        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 10),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),

        # Grid
        ('GRID', (0, 0), (-1, -1), 0.5, rule_color),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),

        # Zebra striping (every other row after header)
        ('BACKGROUND', (0, 2), (-1, 2), bg_alt_color),
        ('BACKGROUND', (0, 4), (-1, 4), bg_alt_color),
    ])

    table.setStyle(style)
    return table


def _make_trip_length_table(
    trip_length_distribution: List[Dict[str, int]],
    total_trips: int,
    branding: Dict[str, Any]
) -> Table:
    """Create trip length distribution table with percentages."""
    # Build table data
    data = [["Duty Days", "Trips", "Percent"]]
    for item in trip_length_distribution:
        duty_days = item["duty_days"]
        trips = item["trips"]
        percent = f"{(trips / total_trips * 100):.1f}%" if total_trips > 0 else "0%"
        data.append([str(duty_days), str(trips), percent])

    # Create table
    table = Table(data, colWidths=[120, 120, 120])

    # Style
    accent_color = _hex_to_reportlab_color(branding["accent_hex"])
    rule_color = _hex_to_reportlab_color(branding["rule_hex"])
    bg_alt_color = _hex_to_reportlab_color(branding["bg_alt_hex"])

    style = TableStyle([
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), accent_color),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#111827")),
        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 10),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),

        # Grid
        ('GRID', (0, 0), (-1, -1), 0.5, rule_color),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ])

    # Add zebra striping
    for i in range(2, len(data), 2):
        style.add('BACKGROUND', (0, i), (-1, i), bg_alt_color)

    table.setStyle(style)
    return table


def _save_donut_png(edw_trips: int, non_edw_trips: int) -> str:
    """Create and save pie chart to temp file."""
    # Force square figure for perfect circles - exact size for consistent output
    fig, ax = plt.subplots(figsize=(4, 4), dpi=100)

    labels = ['EDW', 'Non-EDW']
    sizes = [edw_trips, non_edw_trips]
    colors_list = ['#EF4444', '#10B981']

    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=labels,
        autopct='%1.1f%%',
        startangle=90,
        colors=colors_list
        # Removed wedgeprops to make solid pie chart (not donut)
    )

    # Style text
    for text in texts:
        text.set_fontsize(11)
        text.set_weight('bold')
    for autotext in autotexts:
        autotext.set_color('#1F2937')  # Dark gray for visibility on all backgrounds
        autotext.set_fontsize(11)
        autotext.set_weight('bold')

    # Title with fixed position
    ax.set_title('EDW vs Non-EDW Trips', fontsize=12, weight='bold', pad=10)
    ax.axis('equal')  # Ensure perfect circle

    # Adjust subplot to ensure consistent margins with room for title at top
    plt.subplots_adjust(left=0.05, right=0.95, top=0.85, bottom=0.05)

    # Save to temp file with fixed bbox to prevent size variation
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    plt.savefig(temp_file.name, dpi=150, bbox_inches=None)  # Don't use tight layout
    plt.close(fig)

    return temp_file.name


def _save_triplen_bar_png(trip_length_distribution: List[Dict[str, int]], title: str = "Trip Length Distribution") -> str:
    """Create and save trip length bar chart to temp file."""
    fig, ax = plt.subplots(figsize=(5, 4))

    duty_days = [str(item["duty_days"]) for item in trip_length_distribution]
    trips = [item["trips"] for item in trip_length_distribution]

    bars = ax.bar(duty_days, trips, color='#3B82F6', alpha=0.8)

    ax.set_xlabel('Duty Days', fontsize=11, weight='bold')
    ax.set_ylabel('Number of Trips', fontsize=11, weight='bold')
    ax.set_title(title, fontsize=12, weight='bold', pad=15)
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width()/2., height,
            f'{int(height)}',
            ha='center', va='bottom', fontsize=9
        )

    plt.tight_layout()

    # Save to temp file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    plt.savefig(temp_file.name, dpi=150, bbox_inches='tight')
    plt.close(fig)

    return temp_file.name


def _save_triplen_percentage_bar_png(trip_length_distribution: List[Dict[str, int]], title: str = "Trip Length Distribution (%)") -> str:
    """Create and save trip length percentage bar chart to temp file."""
    fig, ax = plt.subplots(figsize=(5, 4))

    duty_days = [str(item["duty_days"]) for item in trip_length_distribution]
    trips = [item["trips"] for item in trip_length_distribution]

    # Calculate percentages
    total_trips = sum(trips)
    percentages = [(t / total_trips * 100) if total_trips > 0 else 0 for t in trips]

    bars = ax.bar(duty_days, percentages, color='#10B981', alpha=0.8)

    ax.set_xlabel('Duty Days', fontsize=11, weight='bold')
    ax.set_ylabel('Percentage of Trips (%)', fontsize=11, weight='bold')
    ax.set_title(title, fontsize=12, weight='bold', pad=15)
    ax.set_ylim(0, max(percentages) * 1.15 if percentages else 100)  # Add 15% headroom
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    # Add percentage labels on bars
    for bar, pct in zip(bars, percentages):
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width()/2., height,
            f'{pct:.1f}%',
            ha='center', va='bottom', fontsize=9, weight='bold'
        )

    plt.tight_layout()

    # Save to temp file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    plt.savefig(temp_file.name, dpi=150, bbox_inches='tight')
    plt.close(fig)

    return temp_file.name


def _save_edw_percentages_bar_png(weighted_summary: Dict[str, str]) -> str:
    """Create and save EDW percentages comparison bar chart to temp file."""
    fig, ax = plt.subplots(figsize=(6, 4))

    # Extract percentages (remove % sign and convert to float)
    methods = ['Trip-Weighted', 'TAFB-Weighted', 'Duty Day-Weighted']
    percentages = []

    for key in ["Trip-weighted EDW trip %", "TAFB-weighted EDW trip %", "Duty-day-weighted EDW trip %"]:
        value_str = weighted_summary.get(key, "0%")
        # Handle both "46.4%" and "46.4" formats
        value_str = value_str.replace('%', '').strip()
        try:
            percentages.append(float(value_str))
        except ValueError:
            percentages.append(0.0)

    colors_list = ['#3B82F6', '#10B981', '#F59E0B']
    bars = ax.bar(methods, percentages, color=colors_list, alpha=0.85)

    ax.set_ylabel('EDW Percentage (%)', fontsize=11, weight='bold')
    ax.set_title('EDW Percentages by Weighting Method', fontsize=12, weight='bold', pad=15)
    ax.set_ylim(0, 100)
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width()/2., height,
            f'{height:.1f}%',
            ha='center', va='bottom', fontsize=10, weight='bold'
        )

    # Rotate x-axis labels for better readability
    plt.xticks(rotation=15, ha='right')
    plt.tight_layout()

    # Save to temp file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    plt.savefig(temp_file.name, dpi=150, bbox_inches='tight')
    plt.close(fig)

    return temp_file.name


def _save_weighted_pie_png(edw_pct: float, method_name: str, color_scheme: str = 'default') -> str:
    """Create and save weighted method pie chart to temp file."""
    # Force square figure for perfect circles - exact size for consistent output
    fig, ax = plt.subplots(figsize=(4, 4), dpi=100)

    labels = ['EDW', 'Non-EDW']
    sizes = [edw_pct, 100 - edw_pct]

    # Color schemes for different methods
    color_schemes = {
        'trip': ['#3B82F6', '#93C5FD'],
        'tafb': ['#10B981', '#6EE7B7'],
        'duty': ['#F59E0B', '#FCD34D']
    }
    colors_list = color_schemes.get(color_scheme, ['#EF4444', '#FCA5A5'])

    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=labels,
        autopct='%1.1f%%',
        startangle=90,
        colors=colors_list
        # Removed wedgeprops to make solid pie chart (not donut)
    )

    # Style text
    for text in texts:
        text.set_fontsize(10)
        text.set_weight('bold')
    for autotext in autotexts:
        autotext.set_color('#1F2937')  # Dark gray for visibility on all backgrounds
        autotext.set_fontsize(10)
        autotext.set_weight('bold')

    # Title with fixed position to ensure consistent spacing
    ax.set_title(method_name, fontsize=11, weight='bold', pad=10)
    ax.axis('equal')  # Ensure perfect circle

    # Adjust subplot to ensure consistent margins with room for title at top
    plt.subplots_adjust(left=0.05, right=0.95, top=0.85, bottom=0.05)

    # Save to temp file with fixed bbox to prevent size variation
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    plt.savefig(temp_file.name, dpi=150, bbox_inches=None)  # Don't use tight layout
    plt.close(fig)

    return temp_file.name


def _save_duty_day_grouped_bar_png(duty_day_stats: List[List[str]]) -> str:
    """Create and save grouped bar chart for duty day statistics."""
    import numpy as np

    fig, ax = plt.subplots(figsize=(7, 4.5))

    # Extract metrics and values from the table (skip header row)
    metrics = []
    all_values = []
    edw_values = []
    non_edw_values = []

    for row in duty_day_stats[1:]:  # Skip header
        metric = row[0]
        all_val = row[1]
        edw_val = row[2]
        non_edw_val = row[3]

        # Parse values (handle "X.XX h" format)
        def parse_value(val_str):
            val_str = val_str.replace(' h', '').strip()
            try:
                return float(val_str)
            except ValueError:
                return 0.0

        metrics.append(metric)
        all_values.append(parse_value(all_val))
        edw_values.append(parse_value(edw_val))
        non_edw_values.append(parse_value(non_edw_val))

    # Set up bar positions
    x = np.arange(len(metrics))
    width = 0.25

    # Create bars
    bars1 = ax.bar(x - width, all_values, width, label='All Trips', color='#3B82F6', alpha=0.8)
    bars2 = ax.bar(x, edw_values, width, label='EDW Trips', color='#EF4444', alpha=0.8)
    bars3 = ax.bar(x + width, non_edw_values, width, label='Non-EDW Trips', color='#10B981', alpha=0.8)

    # Customize chart
    ax.set_ylabel('Value', fontsize=11, weight='bold')
    ax.set_title('Duty Day Statistics Comparison', fontsize=12, weight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(metrics, fontsize=9, rotation=15, ha='right')
    ax.legend(loc='upper left', fontsize=9)
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    # Add value labels on bars
    def add_labels(bars):
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.1f}',
                       ha='center', va='bottom', fontsize=7)

    add_labels(bars1)
    add_labels(bars2)
    add_labels(bars3)

    plt.tight_layout()

    # Save to temp file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    plt.savefig(temp_file.name, dpi=150, bbox_inches='tight')
    plt.close(fig)

    return temp_file.name


def _save_duty_day_radar_png(duty_day_stats: List[List[str]]) -> str:
    """Create and save radar/spider chart for duty day statistics."""
    import numpy as np

    fig, ax = plt.subplots(figsize=(5, 5), subplot_kw=dict(projection='polar'))

    # Extract metrics and values
    metrics = []
    edw_values = []
    non_edw_values = []

    for row in duty_day_stats[1:]:  # Skip header
        metric = row[0]
        edw_val = row[2]
        non_edw_val = row[3]

        # Parse values (handle "X.XX h" format)
        def parse_value(val_str):
            val_str = val_str.replace(' h', '').strip()
            try:
                return float(val_str)
            except ValueError:
                return 0.0

        metrics.append(metric.replace('Avg ', ''))
        edw_values.append(parse_value(edw_val))
        non_edw_values.append(parse_value(non_edw_val))

    # Normalize values to 0-10 scale for better visualization
    max_vals = [max(edw_values[i], non_edw_values[i]) for i in range(len(edw_values))]
    edw_normalized = [(edw_values[i] / max_vals[i] * 10) if max_vals[i] > 0 else 0 for i in range(len(edw_values))]
    non_edw_normalized = [(non_edw_values[i] / max_vals[i] * 10) if max_vals[i] > 0 else 0 for i in range(len(non_edw_values))]

    # Number of variables
    num_vars = len(metrics)

    # Compute angle for each axis
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()

    # Complete the circle
    edw_normalized += edw_normalized[:1]
    non_edw_normalized += non_edw_normalized[:1]
    angles += angles[:1]

    # Plot data
    ax.plot(angles, edw_normalized, 'o-', linewidth=2, label='EDW Trips', color='#EF4444', alpha=0.7)
    ax.fill(angles, edw_normalized, alpha=0.15, color='#EF4444')

    ax.plot(angles, non_edw_normalized, 'o-', linewidth=2, label='Non-EDW Trips', color='#10B981', alpha=0.7)
    ax.fill(angles, non_edw_normalized, alpha=0.15, color='#10B981')

    # Set labels
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(metrics, fontsize=9)
    ax.set_ylim(0, 10)
    ax.set_yticks([2.5, 5, 7.5, 10])
    ax.set_yticklabels(['', '', '', ''], fontsize=7)
    ax.grid(True, alpha=0.3)

    # Add legend and title
    ax.legend(loc='upper right', bbox_to_anchor=(1.2, 1.1), fontsize=9)
    ax.set_title('EDW vs Non-EDW Profile', fontsize=12, weight='bold', pad=20)

    plt.tight_layout()

    # Save to temp file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    plt.savefig(temp_file.name, dpi=150, bbox_inches='tight')
    plt.close(fig)

    return temp_file.name


def create_pdf_report(
    data: Dict[str, Any],
    output_path: str,
    branding: Optional[Dict[str, Any]] = None
) -> None:
    """
    Generate a professional two-page analytics report PDF.

    Args:
        data: Dictionary containing report data with keys:
            - title: Main report title
            - subtitle: Report subtitle
            - trip_summary: Dict of KPI metrics
            - weighted_summary: Dict of weighted metrics
            - duty_day_stats: List of lists for duty day statistics table
            - trip_length_distribution: List of dicts with duty_days and trips
            - notes: Optional notes text
            - generated_by: Optional attribution text
        output_path: Path where PDF will be saved
        branding: Optional dictionary with color scheme and branding elements

    Raises:
        ValueError: If required data keys are missing
        IOError: If output path is not writable
    """
    # Validate required data keys
    required_keys = ["title", "subtitle", "trip_summary", "weighted_summary",
                     "duty_day_stats", "trip_length_distribution"]
    missing_keys = [key for key in required_keys if key not in data]
    if missing_keys:
        raise ValueError(f"Missing required data keys: {missing_keys}")

    # Merge with default branding
    branding = {**DEFAULT_BRANDING, **(branding or {})}

    # Create document
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=60,  # Space for header
        bottomMargin=50  # Space for footer
    )

    # Prepare styles
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#111827"),
        spaceAfter=6,
        alignment=TA_CENTER
    )

    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=_hex_to_reportlab_color(branding["muted_hex"]),
        spaceAfter=20,
        alignment=TA_CENTER
    )

    heading2_style = ParagraphStyle(
        'CustomHeading2',
        parent=styles['Heading2'],
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#111827"),
        spaceAfter=6,
        spaceBefore=12
    )

    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=10,
        textColor=_hex_to_reportlab_color(branding["muted_hex"]),
        spaceAfter=12
    )

    # Build story (content flow)
    story = []
    temp_files = []  # Track temp files for cleanup

    try:
        # PAGE 1
        # Title and subtitle
        story.append(Paragraph(data["title"], title_style))
        story.append(Paragraph(data["subtitle"], subtitle_style))
        story.append(Spacer(1, 12))

        # KPI Cards
        kpi_table = _make_kpi_row(data["trip_summary"], branding)
        story.append(kpi_table)
        story.append(Spacer(1, 20))

        # Horizontal rule
        hr = HRFlowable(
            width="100%",
            thickness=1,
            color=_hex_to_reportlab_color(branding["rule_hex"]),
            spaceAfter=16,
            spaceBefore=4
        )
        story.append(hr)

        # Charts section
        story.append(Paragraph("Visual Analytics", heading2_style))
        story.append(Spacer(1, 8))

        # Create charts
        edw_trips = data["trip_summary"].get("EDW Trips", 0)
        total_trips = data["trip_summary"].get("Total Trips", 0)
        non_edw_trips = total_trips - edw_trips

        donut_path = _save_donut_png(edw_trips, non_edw_trips)
        temp_files.append(donut_path)

        bar_path = _save_triplen_bar_png(data["trip_length_distribution"], "Trip Length Distribution")
        temp_files.append(bar_path)

        # Place charts side by side
        donut_img = Image(donut_path, width=2.5*inch, height=2.5*inch)
        bar_img = Image(bar_path, width=3*inch, height=2.5*inch)

        chart_table = Table([[donut_img, bar_img]], colWidths=[2.75*inch, 3.25*inch])
        chart_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        story.append(chart_table)
        story.append(Spacer(1, 20))

        # Horizontal rule
        story.append(hr)

        # Weighted Summary
        story.append(Paragraph("Weighted EDW Metrics", heading2_style))
        story.append(Spacer(1, 8))
        weighted_table = _make_weighted_summary_table(data["weighted_summary"], branding)
        story.append(weighted_table)
        story.append(Spacer(1, 16))

        # Duty Day Statistics - Keep together to prevent page break
        duty_section = [
            Paragraph("Duty Day Statistics", heading2_style),
            Spacer(1, 8),
            _make_duty_day_stats_table(data["duty_day_stats"], branding)
        ]
        story.append(KeepTogether(duty_section))
        story.append(Spacer(1, 16))

        # Duty Day Statistics Visualizations
        # Generate both chart types for comparison
        grouped_bar_path = _save_duty_day_grouped_bar_png(data["duty_day_stats"])
        temp_files.append(grouped_bar_path)

        radar_chart_path = _save_duty_day_radar_png(data["duty_day_stats"])
        temp_files.append(radar_chart_path)

        # Place both charts side by side
        grouped_bar_img = Image(grouped_bar_path, width=4*inch, height=2.6*inch)
        radar_chart_img = Image(radar_chart_path, width=2.5*inch, height=2.5*inch)

        chart_comparison_table = Table(
            [[grouped_bar_img, radar_chart_img]],
            colWidths=[4.2*inch, 2.8*inch]
        )
        chart_comparison_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ]))
        story.append(chart_comparison_table)

        # Notes if provided
        if data.get("notes"):
            story.append(Spacer(1, 16))
            story.append(Paragraph(f"<i>Note: {data['notes']}</i>", body_style))

        # PAGE 2
        story.append(PageBreak())

        story.append(Paragraph("Trip Length Breakdown", heading2_style))
        story.append(Paragraph(
            "Distribution by Duty Days (Hot Standby excluded)",
            body_style
        ))
        story.append(Spacer(1, 12))

        # Trip length table
        trip_table = _make_trip_length_table(
            data["trip_length_distribution"],
            total_trips,
            branding
        )
        story.append(trip_table)
        story.append(Spacer(1, 20))

        # Trip length charts - both absolute numbers and percentages
        bar_path_large = _save_triplen_bar_png(
            data["trip_length_distribution"],
            "Trip Length Distribution (Absolute Numbers)"
        )
        temp_files.append(bar_path_large)

        bar_pct_path = _save_triplen_percentage_bar_png(
            data["trip_length_distribution"],
            "Trip Length Distribution (Percentage)"
        )
        temp_files.append(bar_pct_path)

        # Place charts side by side
        bar_img_large = Image(bar_path_large, width=3.5*inch, height=3*inch)
        bar_pct_img = Image(bar_pct_path, width=3.5*inch, height=3*inch)

        trip_charts_table = Table(
            [[bar_img_large, bar_pct_img]],
            colWidths=[3.6*inch, 3.6*inch]
        )
        trip_charts_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        story.append(trip_charts_table)
        story.append(Spacer(1, 24))

        # Horizontal rule
        story.append(hr)

        # Filter out single-day trips
        multi_day_trips = [item for item in data["trip_length_distribution"] if item["duty_days"] > 1]
        total_multi_day = sum(item["trips"] for item in multi_day_trips)

        if multi_day_trips:
            # Multi-day trip analysis section - keep together to prevent page breaks
            multi_day_section = []

            # Title and subtitle
            multi_day_section.append(Paragraph("Trip Length Analysis (Single-Day Trips Excluded)", heading2_style))
            multi_day_section.append(Paragraph(
                "Focus on multi-day pairings by removing 1-day trips",
                body_style
            ))
            multi_day_section.append(Spacer(1, 12))

            # Multi-day only table
            accent_color = _hex_to_reportlab_color(branding["accent_hex"])
            rule_color = _hex_to_reportlab_color(branding["rule_hex"])
            bg_alt_color = _hex_to_reportlab_color(branding["bg_alt_hex"])

            multi_day_data = [["Duty Days", "Trips", "Percentage"]]
            for item in multi_day_trips:
                duty_days = item["duty_days"]
                trips = item["trips"]
                percent = f"{(trips / total_multi_day * 100):.1f}%" if total_multi_day > 0 else "0%"
                multi_day_data.append([str(duty_days), str(trips), percent])

            multi_day_table = Table(multi_day_data, colWidths=[120, 120, 120])

            # Apply table style
            table_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), accent_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#111827")),
                ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 10),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, rule_color),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
            ])

            # Add zebra striping
            for i in range(2, len(multi_day_data), 2):
                table_style.add('BACKGROUND', (0, i), (-1, i), bg_alt_color)

            multi_day_table.setStyle(table_style)
            multi_day_section.append(multi_day_table)
            multi_day_section.append(Spacer(1, 20))

            # Charts for multi-day trips - both absolute and percentage
            multi_bar_path = _save_triplen_bar_png(
                multi_day_trips,
                "Multi-Day Trips (Absolute Numbers)"
            )
            temp_files.append(multi_bar_path)

            multi_bar_pct_path = _save_triplen_percentage_bar_png(
                multi_day_trips,
                "Multi-Day Trips (Percentage)"
            )
            temp_files.append(multi_bar_pct_path)

            # Place charts side by side
            multi_bar_img = Image(multi_bar_path, width=3.5*inch, height=3*inch)
            multi_bar_pct_img = Image(multi_bar_pct_path, width=3.5*inch, height=3*inch)

            multi_charts_table = Table(
                [[multi_bar_img, multi_bar_pct_img]],
                colWidths=[3.6*inch, 3.6*inch]
            )
            multi_charts_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ]))
            multi_day_section.append(multi_charts_table)

            # Add entire section as KeepTogether
            story.append(KeepTogether(multi_day_section))
            story.append(Spacer(1, 20))
        else:
            story.append(Paragraph("Trip Length Analysis (Single-Day Trips Excluded)", heading2_style))
            story.append(Paragraph("<i>No multi-day trips found in dataset.</i>", body_style))
            story.append(Spacer(1, 20))

        # PAGE 3 - EDW Percentages Analysis
        story.append(PageBreak())

        story.append(Paragraph("EDW Percentages Analysis", heading2_style))
        story.append(Paragraph(
            "Comparison of EDW metrics across different weighting methods",
            body_style
        ))
        story.append(Spacer(1, 12))

        # EDW Percentages comparison bar chart
        edw_pct_bar_path = _save_edw_percentages_bar_png(data["weighted_summary"])
        temp_files.append(edw_pct_bar_path)

        edw_pct_bar_img = Image(edw_pct_bar_path, width=5*inch, height=3.5*inch)
        story.append(edw_pct_bar_img)
        story.append(Spacer(1, 24))

        # Horizontal rule
        hr = HRFlowable(
            width="100%",
            thickness=1,
            color=_hex_to_reportlab_color(branding["rule_hex"]),
            spaceAfter=16,
            spaceBefore=4
        )
        story.append(hr)

        # Three pie charts showing each weighting method
        story.append(Paragraph("EDW Distribution by Weighting Method", heading2_style))
        story.append(Spacer(1, 12))

        # Extract percentages for pie charts
        percentages = {}
        for key in ["Trip-weighted EDW trip %", "TAFB-weighted EDW trip %", "Duty-day-weighted EDW trip %"]:
            value_str = data["weighted_summary"].get(key, "0%")
            value_str = value_str.replace('%', '').strip()
            try:
                percentages[key] = float(value_str)
            except ValueError:
                percentages[key] = 0.0

        # Create three pie charts
        trip_pie_path = _save_weighted_pie_png(
            percentages["Trip-weighted EDW trip %"],
            "Trip-Weighted",
            "trip"
        )
        temp_files.append(trip_pie_path)

        tafb_pie_path = _save_weighted_pie_png(
            percentages["TAFB-weighted EDW trip %"],
            "TAFB-Weighted",
            "tafb"
        )
        temp_files.append(tafb_pie_path)

        duty_pie_path = _save_weighted_pie_png(
            percentages["Duty-day-weighted EDW trip %"],
            "Duty Day-Weighted",
            "duty"
        )
        temp_files.append(duty_pie_path)

        # Place three pie charts in a row
        trip_pie_img = Image(trip_pie_path, width=2*inch, height=2*inch)
        tafb_pie_img = Image(tafb_pie_path, width=2*inch, height=2*inch)
        duty_pie_img = Image(duty_pie_path, width=2*inch, height=2*inch)

        pie_table = Table(
            [[trip_pie_img, tafb_pie_img, duty_pie_img]],
            colWidths=[2.1*inch, 2.1*inch, 2.1*inch]
        )
        pie_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        story.append(pie_table)
        story.append(Spacer(1, 20))

        # Footer line with data source
        footer_text = ""
        if data.get("notes"):
            footer_text += f"Data Source: {data['notes']}"
        if data.get("generated_by"):
            if footer_text:
                footer_text += " • "
            footer_text += f"Prepared by: {data['generated_by']}"

        if footer_text:
            footer_para = Paragraph(f"<i>{footer_text}</i>", body_style)
            story.append(footer_para)

        # Build PDF with header/footer
        def add_page_decorations(canvas, doc):
            _draw_header(canvas, doc, branding)
            _draw_footer(canvas, doc)

        doc.build(story, onFirstPage=add_page_decorations, onLaterPages=add_page_decorations)

    finally:
        # Clean up temporary image files
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except Exception:
                pass  # Silently ignore cleanup errors


if __name__ == "__main__":
    """Generate a sample PDF report for testing."""

    # Sample data
    sample_data = {
        "title": "ONT 757 – Bid 2601",
        "subtitle": "Executive Dashboard • Pairing Breakdown & Duty-Day Metrics",
        "trip_summary": {
            "Unique Pairings": 272,
            "Total Trips": 522,
            "EDW Trips": 242,
            "Day Trips": 280,
        },
        "weighted_summary": {
            "Trip-weighted EDW trip %": "46.4%",
            "TAFB-weighted EDW trip %": "73.3%",
            "Duty-day-weighted EDW trip %": "66.2%",
        },
        "duty_day_stats": [
            ["Metric", "All", "EDW", "Non-EDW"],
            ["Avg Legs/Duty Day", "1.81", "2.04", "1.63"],
            ["Avg Duty Day Length", "7.41 h", "8.22 h", "6.78 h"],
            ["Avg Block Time", "3.61 h", "4.33 h", "3.06 h"],
            ["Avg Credit Time", "5.05 h", "5.44 h", "4.75 h"],
        ],
        "trip_length_distribution": [
            {"duty_days": 1, "trips": 238},
            {"duty_days": 2, "trips": 1},
            {"duty_days": 3, "trips": 4},
            {"duty_days": 4, "trips": 15},
            {"duty_days": 5, "trips": 34},
            {"duty_days": 6, "trips": 53},
            {"duty_days": 7, "trips": 56},
            {"duty_days": 8, "trips": 8},
            {"duty_days": 9, "trips": 1},
        ],
        "notes": "Hot Standby pairings were excluded from trip-length distribution.",
        "generated_by": "Data Analysis App"
    }

    sample_branding = {
        "primary_hex": "#1E40AF",  # Pleasant blue header
        "accent_hex": "#F3F4F6",
        "rule_hex": "#E5E7EB",
        "muted_hex": "#6B7280",
        "bg_alt_hex": "#FAFAFA",
        "logo_path": None,
        "title_left": "ONT 757 – Bid 2601 | Pairing Analysis Report"
    }

    # Generate PDF
    output_path = "/tmp/sample_report.pdf"

    try:
        create_pdf_report(sample_data, output_path, sample_branding)
        print(f"✅ Sample PDF generated: {output_path}")
        print(f"   File size: {os.path.getsize(output_path) / 1024:.1f} KB")
        print(f"\nOpen with: open {output_path}")
    except Exception as e:
        print(f"❌ Error generating PDF: {e}")
        import traceback
        traceback.print_exc()
