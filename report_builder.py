"""
report_builder.py
Professional bid line analysis report generator using ReportLab and Matplotlib.
Enhanced to match the look and feel of the pairing analysis PDF export.
"""

import os
import tempfile
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, Iterable, Optional, Any, List
import math

import pandas as pd

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


# Default branding for bid line reports - Aero Crew Data brand palette
DEFAULT_BRANDING = {
    "primary_hex": "#0C1E36",  # Brand Navy - headers, primary background
    "accent_hex": "#1BB3A4",   # Brand Teal - accents, highlights, CTA
    "rule_hex": "#5B6168",     # Brand Gray - dividers, borders
    "muted_hex": "#5B6168",    # Brand Gray - secondary typography
    "bg_alt_hex": "#F8FAFC",   # Light slate for zebra rows (high contrast)
    "sky_hex": "#2E9BE8",      # Brand Sky - supporting data viz accent
    "logo_path": "logo-full.svg",  # Aero Crew Data logo
    "title_left": "Bid Line Analysis Report"
}


@dataclass
class ReportMetadata:
    """Metadata for bid line analysis report."""
    title: str = "Bid Line Analysis"
    subtitle: Optional[str] = None
    filters: Optional[Dict[str, Iterable]] = None


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

    # Left: timestamp with app name
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    canvas.drawString(36, 30, f"Generated: {timestamp} by Aero Crew Data App")

    # Right: page number
    page_num = canvas.getPageNumber()
    canvas.drawRightString(letter[0] - 36, 30, f"Page {page_num}")

    canvas.restoreState()


class KPIBadge(Flowable):
    """Custom flowable for KPI card display."""

    def __init__(self, label: str, value: str, branding: Dict[str, Any], width: float = 120, range_text: str = None):
        Flowable.__init__(self)
        self.label = label
        self.value = value
        self.range_text = range_text
        self.branding = branding
        self.width = width
        self.height = 70 if range_text else 60  # Taller if showing range

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


def _make_kpi_row(metrics: Dict[str, Any], branding: Dict[str, Any]) -> Table:
    """Create a row of KPI badges.

    Args:
        metrics: Dict where values can be either:
            - Simple value (str/number)
            - Dict with 'value' and 'range' keys
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


def _make_styled_table(data: List[List[str]], col_widths: List[float], branding: Dict[str, Any]) -> Table:
    """Create a professionally styled table with zebra striping."""
    table = Table(data, colWidths=col_widths)

    accent_color = _hex_to_reportlab_color(branding["accent_hex"])
    rule_color = _hex_to_reportlab_color(branding["rule_hex"])
    bg_alt_color = _hex_to_reportlab_color(branding["bg_alt_hex"])

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

    # Add zebra striping to data rows
    for i in range(2, len(data), 2):
        style.add('BACKGROUND', (0, i), (-1, i), bg_alt_color)

    table.setStyle(style)
    return table


def _save_bar_chart_png(
    data: pd.DataFrame,
    title: str,
    category_key: str,
    value_key: str,
    xlabel: str,
    ylabel: str,
    color: str = '#3B82F6'
) -> str:
    """Create and save bar chart to temp file with professional styling."""
    if data.empty:
        return None

    fig, ax = plt.subplots(figsize=(6, 4))

    labels = data[category_key].astype(str).tolist()
    values = data[value_key].astype(float).tolist()

    bars = ax.bar(labels, values, color=color, alpha=0.8)

    ax.set_xlabel(xlabel, fontsize=11, weight='bold')
    ax.set_ylabel(ylabel, fontsize=11, weight='bold')
    ax.set_title(title, fontsize=12, weight='bold', pad=15)
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        if height > 0:
            ax.text(
                bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}',
                ha='center', va='bottom', fontsize=9
            )

    # Rotate x-axis labels if many categories
    if len(labels) > 6:
        plt.xticks(rotation=45, ha='right')

    plt.tight_layout()

    # Save to temp file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    plt.savefig(temp_file.name, dpi=150, bbox_inches='tight')
    plt.close(fig)

    return temp_file.name


def _save_percentage_bar_chart_png(
    data: pd.DataFrame,
    title: str,
    category_key: str,
    percent_key: str,
    xlabel: str,
    color: str = '#3B82F6'
) -> str:
    """Create and save percentage bar chart to temp file with professional styling."""
    if data.empty:
        return None

    fig, ax = plt.subplots(figsize=(6, 4))

    labels = data[category_key].astype(str).tolist()
    # Extract percentage values (remove % sign and convert to float)
    percentages = [float(str(p).replace('%', '')) for p in data[percent_key].tolist()]

    bars = ax.bar(labels, percentages, color=color, alpha=0.8)

    ax.set_xlabel(xlabel, fontsize=11, weight='bold')
    ax.set_ylabel('Percentage (%)', fontsize=11, weight='bold')
    ax.set_title(title, fontsize=12, weight='bold', pad=15)
    ax.set_ylim(0, max(percentages) * 1.15 if percentages else 100)  # Add 15% headroom
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    # Add percentage labels on bars
    for bar, pct in zip(bars, percentages):
        height = bar.get_height()
        if height > 0:
            ax.text(
                bar.get_x() + bar.get_width()/2., height,
                f'{pct:.1f}%',
                ha='center', va='bottom', fontsize=9, weight='bold'
            )

    # Rotate x-axis labels if many categories
    if len(labels) > 6:
        plt.xticks(rotation=45, ha='right')

    plt.tight_layout()

    # Save to temp file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    plt.savefig(temp_file.name, dpi=150, bbox_inches='tight')
    plt.close(fig)

    return temp_file.name


def _save_pie_chart_png(title: str, labels: List[str], values: List[int], colors_list: List[str]) -> str:
    """Create and save pie chart to temp file with professional styling."""
    if not values or sum(values) == 0:
        return None

    # Very large square figure for long labels like "Buy-up (<75 CT)" and "Non Buy-up (≥75 CT)"
    fig, ax = plt.subplots(figsize=(7, 7), dpi=100)

    wedges, texts, autotexts = ax.pie(
        values,
        labels=labels,
        autopct='%1.1f%%',
        startangle=90,
        colors=colors_list,
        labeldistance=1.12  # Move labels even further outward for long text
    )

    # Style text
    for text in texts:
        text.set_fontsize(9)  # Smaller for long labels
        text.set_weight('bold')
    for autotext in autotexts:
        autotext.set_color('#1F2937')  # Dark gray for visibility
        autotext.set_fontsize(10)
        autotext.set_weight('bold')

    ax.set_title(title, fontsize=12, weight='bold', pad=15)
    ax.axis('equal')  # Ensure perfect circle

    # Much wider margins to accommodate long labels with special characters
    plt.subplots_adjust(left=0.22, right=0.78, top=0.78, bottom=0.22)

    # Save to temp file with fixed bbox to maintain square aspect ratio
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    plt.savefig(temp_file.name, dpi=150, bbox_inches=None)  # Keep square shape
    plt.close(fig)

    return temp_file.name


def build_analysis_pdf(
    df: pd.DataFrame,
    metadata: Optional[ReportMetadata] = None,
    pay_periods: Optional[pd.DataFrame] = None,
    reserve_lines: Optional[pd.DataFrame] = None,
    branding: Optional[Dict[str, Any]] = None
) -> bytes:
    """
    Create a professional PDF report for bid line analysis.

    Args:
        df: DataFrame with bid line data
        metadata: Report metadata (title, subtitle, filters)
        pay_periods: DataFrame with pay period data
        reserve_lines: DataFrame with reserve line data
        branding: Optional branding dictionary

    Returns:
        PDF bytes

    Raises:
        ValueError: If DataFrame is empty
        RuntimeError: If matplotlib is not available
    """
    if df.empty:
        raise ValueError("Cannot render PDF for empty dataset.")

    if plt is None:
        raise RuntimeError("Missing optional dependency 'matplotlib'. Install it with 'pip install matplotlib'.")

    metadata = metadata or ReportMetadata()
    branding = {**DEFAULT_BRANDING, **(branding or {})}

    # Create document
    doc = SimpleDocTemplate(
        tempfile.NamedTemporaryFile(delete=False, suffix='.pdf').name,
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
        story.append(Paragraph(metadata.title, title_style))
        if metadata.subtitle:
            story.append(Paragraph(metadata.subtitle, subtitle_style))
        else:
            story.append(Spacer(1, 12))

        story.append(Spacer(1, 12))

        # KPI Cards - Summary Statistics with ranges
        summary_stats = df[["CT", "BT", "DO", "DD"]].agg(['mean', 'min', 'max']).transpose()
        kpi_metrics = {
            "Avg Credit": {
                "value": f"{summary_stats.loc['CT', 'mean']:.1f}",
                "range": f"↑ Range {summary_stats.loc['CT', 'min']:.1f}-{summary_stats.loc['CT', 'max']:.1f}"
            },
            "Avg Block": {
                "value": f"{summary_stats.loc['BT', 'mean']:.1f}",
                "range": f"↑ Range {summary_stats.loc['BT', 'min']:.1f}-{summary_stats.loc['BT', 'max']:.1f}"
            },
            "Avg Days Off": {
                "value": f"{summary_stats.loc['DO', 'mean']:.1f}",
                "range": f"↑ Range {int(summary_stats.loc['DO', 'min'])}-{int(summary_stats.loc['DO', 'max'])}"
            },
            "Avg Duty Days": {
                "value": f"{summary_stats.loc['DD', 'mean']:.1f}",
                "range": f"↑ Range {int(summary_stats.loc['DD', 'min'])}-{int(summary_stats.loc['DD', 'max'])}"
            }
        }
        kpi_table = _make_kpi_row(kpi_metrics, branding)
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

        # Summary Statistics Table
        story.append(Paragraph("Summary Statistics", heading2_style))
        story.append(Spacer(1, 8))

        summary = df[["CT", "BT", "DO", "DD"]].agg(["min", "max", "mean", "median", "std"]).transpose()
        summary_data = [["Metric", "Min", "Max", "Average", "Median", "Std Dev"]]
        for metric in ["CT", "BT", "DO", "DD"]:
            row = summary.loc[metric]
            summary_data.append([
                metric,
                f"{row['min']:.2f}",
                f"{row['max']:.2f}",
                f"{row['mean']:.2f}",
                f"{row['median']:.2f}",
                f"{row['std']:.2f}"
            ])

        summary_table = _make_styled_table(summary_data, [80, 70, 70, 80, 70, 80], branding)
        story.append(summary_table)
        story.append(Spacer(1, 16))

        # Pay Period Averages
        if pay_periods is not None and not pay_periods.empty:
            subset = pay_periods[pay_periods["Line"].isin(df["Line"])].copy()

            if not subset.empty:
                story.append(Paragraph("Pay Period Averages", heading2_style))
                story.append(Spacer(1, 8))

                period_metrics = subset.groupby("Period")[["CT", "BT", "DO", "DD"]].mean().round(2)

                period_data = [["Pay Period", "Avg CT", "Avg BT", "Avg DO", "Avg DD"]]
                for period, row in period_metrics.iterrows():
                    period_data.append([
                        f"PP{int(period)}",
                        f"{row['CT']:.2f}",
                        f"{row['BT']:.2f}",
                        f"{row['DO']:.2f}",
                        f"{row['DD']:.2f}"
                    ])

                # Add overall row
                overall = subset[["CT", "BT", "DO", "DD"]].mean().round(2)
                period_data.append([
                    "Overall",
                    f"{overall['CT']:.2f}",
                    f"{overall['BT']:.2f}",
                    f"{overall['DO']:.2f}",
                    f"{overall['DD']:.2f}"
                ])

                period_table = _make_styled_table(period_data, [100, 80, 80, 80, 80], branding)
                story.append(period_table)
                story.append(Spacer(1, 16))

        # Reserve Line Statistics
        if reserve_lines is not None and not reserve_lines.empty:
            reserve_subset = reserve_lines[reserve_lines["Line"].isin(df["Line"])].copy()
            reserve_subset = reserve_subset[reserve_subset["IsReserve"] == True]

            if not reserve_subset.empty:
                story.append(Paragraph("Reserve Lines Analysis", heading2_style))
                story.append(Spacer(1, 8))

                total_reserve = len(reserve_subset)
                captain_slots = int(reserve_subset["CaptainSlots"].sum())
                fo_slots = int(reserve_subset["FOSlots"].sum())
                total_slots = captain_slots + fo_slots
                total_regular = len(df) - total_reserve

                reserve_percentage = (total_slots / total_regular * 100) if total_regular > 0 else 0.0

                reserve_data = [
                    ["Metric", "Value"],
                    ["Total Reserve Lines", str(total_reserve)],
                    ["Captain Slots", str(captain_slots)],
                    ["First Officer Slots", str(fo_slots)],
                    ["Total Reserve Slots", str(total_slots)],
                    ["Regular Lines", str(total_regular)],
                    ["Reserve Percentage", f"{reserve_percentage:.1f}%"]
                ]

                reserve_table = _make_styled_table(reserve_data, [200, 100], branding)
                story.append(reserve_table)
                story.append(Spacer(1, 16))

        # Distributions Section (continued on same page)
        story.append(Spacer(1, 20))
        story.append(hr)
        story.append(Spacer(1, 16))

        # CT Distribution
        ct_distribution = _create_binned_distribution(df['CT'], bin_width=5.0, label='Range')
        if not ct_distribution.empty:
            ct_content = []
            # Include main "Distribution Analysis" header with CT section to keep together
            ct_content.append(Paragraph("Distribution Analysis", heading2_style))
            ct_content.append(Spacer(1, 12))
            ct_content.append(Paragraph("Credit Time (CT) Distribution", heading2_style))
            ct_content.append(Spacer(1, 8))

            ct_data = [["Range", "Lines", "Percent"]]
            for _, row in ct_distribution.iterrows():
                ct_data.append([row['Range'], str(row['Lines']), row['Percent']])

            ct_table = _make_styled_table(ct_data, [120, 100, 100], branding)
            ct_content.append(ct_table)
            ct_content.append(Spacer(1, 12))

            # CT Charts - Side by side (Brand Teal and Sky)
            ct_chart_path = _save_bar_chart_png(
                ct_distribution,
                'Credit Time Distribution (Count)',
                'Range',
                'Lines',
                'Credit Time Range',
                'Number of Lines',
                '#1BB3A4'  # Brand Teal
            )
            ct_pct_chart_path = _save_percentage_bar_chart_png(
                ct_distribution,
                'Credit Time Distribution (Percentage)',
                'Range',
                'Percent',
                'Credit Time Range',
                '#2E9BE8'  # Brand Sky
            )

            if ct_chart_path and ct_pct_chart_path:
                temp_files.extend([ct_chart_path, ct_pct_chart_path])
                ct_img = Image(ct_chart_path, width=3.5*inch, height=2.6*inch)
                ct_pct_img = Image(ct_pct_chart_path, width=3.5*inch, height=2.6*inch)

                # Place charts side by side in a table
                charts_table = Table([[ct_img, ct_pct_img]], colWidths=[3.6*inch, 3.6*inch])
                charts_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ]))
                ct_content.append(charts_table)

            # Keep title, table, and charts together
            story.append(KeepTogether(ct_content))
            story.append(Spacer(1, 20))

        # BT Distribution
        bt_distribution = _create_binned_distribution(df['BT'], bin_width=5.0, label='Range')
        if not bt_distribution.empty:
            bt_content = []
            bt_content.append(Paragraph("Block Time (BT) Distribution", heading2_style))
            bt_content.append(Spacer(1, 8))

            bt_data = [["Range", "Lines", "Percent"]]
            for _, row in bt_distribution.iterrows():
                bt_data.append([row['Range'], str(row['Lines']), row['Percent']])

            bt_table = _make_styled_table(bt_data, [120, 100, 100], branding)
            bt_content.append(bt_table)
            bt_content.append(Spacer(1, 12))

            # BT Charts - Side by side (Dark Teal variants)
            bt_chart_path = _save_bar_chart_png(
                bt_distribution,
                'Block Time Distribution (Count)',
                'Range',
                'Lines',
                'Block Time Range',
                'Number of Lines',
                '#0C7C73'  # Dark Teal
            )
            bt_pct_chart_path = _save_percentage_bar_chart_png(
                bt_distribution,
                'Block Time Distribution (Percentage)',
                'Range',
                'Percent',
                'Block Time Range',
                '#5BCFC2'  # Light Teal
            )

            if bt_chart_path and bt_pct_chart_path:
                temp_files.extend([bt_chart_path, bt_pct_chart_path])
                bt_img = Image(bt_chart_path, width=3.5*inch, height=2.6*inch)
                bt_pct_img = Image(bt_pct_chart_path, width=3.5*inch, height=2.6*inch)

                # Place charts side by side in a table
                charts_table = Table([[bt_img, bt_pct_img]], colWidths=[3.6*inch, 3.6*inch])
                charts_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ]))
                bt_content.append(charts_table)

            # Keep title, table, and charts together
            story.append(KeepTogether(bt_content))
            story.append(Spacer(1, 20))

        # PAGE 3 - Days Off and Buy-up Analysis
        story.append(PageBreak())

        # Days Off Distribution
        do_distribution = _create_value_distribution(df['DO'], label='Days Off')
        if not do_distribution.empty:
            do_content = []
            do_content.append(Paragraph("Days Off (DO) Distribution", heading2_style))
            do_content.append(Spacer(1, 8))

            do_data = [["Days Off", "Lines", "Percent"]]
            for _, row in do_distribution.iterrows():
                do_data.append([str(row['Days Off']), str(row['Lines']), row['Percent']])

            do_table = _make_styled_table(do_data, [120, 100, 100], branding)
            do_content.append(do_table)
            do_content.append(Spacer(1, 12))

            # DO Charts - Side by side (Sky variants)
            do_chart_path = _save_bar_chart_png(
                do_distribution,
                'Days Off Distribution (Count)',
                'Days Off',
                'Lines',
                'Days Off',
                'Number of Lines',
                '#2E9BE8'  # Brand Sky
            )
            do_pct_chart_path = _save_percentage_bar_chart_png(
                do_distribution,
                'Days Off Distribution (Percentage)',
                'Days Off',
                'Percent',
                'Days Off',
                '#7EC8F6'  # Light Sky
            )

            if do_chart_path and do_pct_chart_path:
                temp_files.extend([do_chart_path, do_pct_chart_path])
                do_img = Image(do_chart_path, width=3.5*inch, height=2.6*inch)
                do_pct_img = Image(do_pct_chart_path, width=3.5*inch, height=2.6*inch)

                # Place charts side by side in a table
                charts_table = Table([[do_img, do_pct_img]], colWidths=[3.6*inch, 3.6*inch])
                charts_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ]))
                do_content.append(charts_table)

            # Keep title, table, and charts together
            story.append(KeepTogether(do_content))
            story.append(Spacer(1, 20))

        # Horizontal rule
        story.append(hr)

        # Buy-up vs Non Buy-up Analysis - Keep all together on same page
        threshold = 75.0
        buy_up_content = []
        buy_up_content.append(Paragraph(f"Buy-up Analysis (Threshold: {threshold:.0f} CT)", heading2_style))
        buy_up_content.append(Spacer(1, 12))

        total = len(df)
        buy_up_df = df[df['CT'] < threshold]
        non_buy_up_df = df[df['CT'] >= threshold]

        buy_up_data = [
            ["Category", "Lines", "Percent", "Avg CT", "Avg BT", "Avg DO", "Avg DD"],
            [
                f"Buy-up (<{threshold:.0f} CT)",
                str(len(buy_up_df)),
                f"{(len(buy_up_df) / total * 100):.1f}%" if total else "0%",
                f"{buy_up_df['CT'].mean():.2f}" if not buy_up_df.empty else "N/A",
                f"{buy_up_df['BT'].mean():.2f}" if not buy_up_df.empty else "N/A",
                f"{buy_up_df['DO'].mean():.2f}" if not buy_up_df.empty else "N/A",
                f"{buy_up_df['DD'].mean():.2f}" if not buy_up_df.empty else "N/A"
            ],
            [
                f"Non Buy-up (≥{threshold:.0f} CT)",
                str(len(non_buy_up_df)),
                f"{(len(non_buy_up_df) / total * 100):.1f}%" if total else "0%",
                f"{non_buy_up_df['CT'].mean():.2f}" if not non_buy_up_df.empty else "N/A",
                f"{non_buy_up_df['BT'].mean():.2f}" if not non_buy_up_df.empty else "N/A",
                f"{non_buy_up_df['DO'].mean():.2f}" if not non_buy_up_df.empty else "N/A",
                f"{non_buy_up_df['DD'].mean():.2f}" if not non_buy_up_df.empty else "N/A"
            ]
        ]

        buy_up_table = _make_styled_table(buy_up_data, [130, 60, 60, 60, 60, 60, 60], branding)
        buy_up_content.append(buy_up_table)
        buy_up_content.append(Spacer(1, 16))

        # Buy-up pie chart with brand colors
        if total > 0:
            labels = [f'Buy-up (<{threshold:.0f} CT)', f'Non Buy-up (≥{threshold:.0f} CT)']
            counts = [len(buy_up_df), len(non_buy_up_df)]
            colors_list = ['#1BB3A4', '#0C1E36']  # Brand Teal and Navy

            pie_path = _save_pie_chart_png('Buy-up vs Non Buy-up', labels, counts, colors_list)
            if pie_path:
                temp_files.append(pie_path)
                pie_img = Image(pie_path, width=3*inch, height=3*inch)
                buy_up_content.append(pie_img)
                buy_up_content.append(Spacer(1, 20))

        # Keep header, table, and chart together
        story.append(KeepTogether(buy_up_content))

        # Build PDF with header/footer
        def add_page_decorations(canvas, doc):
            _draw_header(canvas, doc, branding)
            _draw_footer(canvas, doc)

        doc.build(story, onFirstPage=add_page_decorations, onLaterPages=add_page_decorations)

        # Read PDF bytes
        with open(doc.filename, 'rb') as f:
            pdf_bytes = f.read()

        # Clean up the main PDF file
        try:
            os.unlink(doc.filename)
        except Exception:
            pass

        return pdf_bytes

    finally:
        # Clean up temporary image files
        for temp_file in temp_files:
            try:
                if temp_file and os.path.exists(temp_file):
                    os.unlink(temp_file)
            except Exception:
                pass  # Silently ignore cleanup errors


def _create_binned_distribution(series: pd.Series, bin_width: float, label: str) -> pd.DataFrame:
    """Create binned distribution for continuous variables."""
    if series.empty:
        return pd.DataFrame(columns=[label, 'Lines', 'Percent'])

    minimum = float(series.min())
    maximum = float(series.max())
    if bin_width <= 0:
        bin_width = max((maximum - minimum) / 5, 1) or 1

    start = math.floor(minimum / bin_width) * bin_width
    end = math.ceil(maximum / bin_width) * bin_width
    if end <= start:
        end = start + bin_width

    edges = [start]
    while edges[-1] < end:
        edges.append(edges[-1] + bin_width)
    if edges[-1] < maximum + 1e-6:
        edges.append(edges[-1] + bin_width)

    bins = pd.cut(series, bins=edges, include_lowest=True, right=False)
    counts = bins.value_counts().sort_index()
    total = counts.sum()

    rows = []
    for interval, count in counts.items():
        left = interval.left
        right = interval.right
        label_text = f"{left:.1f}-{right:.1f}" if bin_width < 1 else f"{left:.0f}-{right:.0f}"
        percent = f"{(count / total * 100):.1f}%" if total else "0.0%"
        rows.append({label: label_text, 'Lines': int(count), 'Percent': percent})

    return pd.DataFrame(rows)


def _create_value_distribution(series: pd.Series, label: str) -> pd.DataFrame:
    """Create distribution for discrete values (e.g., days off)."""
    if series.empty:
        return pd.DataFrame(columns=[label, 'Lines', 'Percent'])

    # Convert to integers for day counts
    series_int = series.astype(int)
    counts = series_int.value_counts().sort_index()
    total = counts.sum()

    rows = []
    for value, count in counts.items():
        percent = f"{(count / total * 100):.1f}%" if total else "0.0%"
        rows.append({label: int(value), 'Lines': int(count), 'Percent': percent})

    return pd.DataFrame(rows)
