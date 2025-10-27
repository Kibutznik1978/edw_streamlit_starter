"""
Main orchestration and PDF report generation for EDW analysis.

This module coordinates the entire analysis workflow and produces formatted
PDF reports with charts and professional styling.
"""

from pathlib import Path
from io import BytesIO
from datetime import datetime
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Set backend for headless environments (Streamlit Cloud)
import matplotlib.pyplot as plt
from PIL import Image as PILImage
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    Image,
    PageBreak,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfgen import canvas

from .parser import (
    parse_pairings,
    parse_trip_id,
    parse_tafb,
    parse_duty_days,
    parse_max_duty_day_length,
    parse_max_legs_per_duty_day,
    parse_duty_day_details,
    parse_trip_frequency,
    clean_text,
)
from .analyzer import is_edw_trip, is_hot_standby
from .excel_export import save_edw_excel, build_edw_dataframes


# -------------------------------------------------------------------
# Professional PDF Styling Functions
# -------------------------------------------------------------------
def _hex_to_reportlab_color(hex_str: str) -> colors.Color:
    """Convert hex color string to ReportLab Color object."""
    hex_str = hex_str.lstrip('#')
    r, g, b = int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16)
    return colors.Color(r/255.0, g/255.0, b/255.0)


def _draw_edw_header(canvas_obj: canvas.Canvas, doc, title: str) -> None:
    """Draw professional header bar on each page."""
    canvas_obj.saveState()

    # Draw header bar
    primary_color = _hex_to_reportlab_color("#1E40AF")
    canvas_obj.setFillColor(primary_color)
    canvas_obj.rect(0, letter[1] - 40, letter[0], 40, fill=1, stroke=0)

    # Draw title text
    canvas_obj.setFillColor(colors.white)
    canvas_obj.setFont('Helvetica-Bold', 11)
    canvas_obj.drawString(36, letter[1] - 25, title)

    canvas_obj.restoreState()


def _draw_edw_footer(canvas_obj: canvas.Canvas, doc) -> None:
    """Draw footer on each page."""
    canvas_obj.saveState()

    # Footer text
    canvas_obj.setFont('Helvetica', 8)
    canvas_obj.setFillColor(colors.HexColor("#6B7280"))

    # Left: timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    canvas_obj.drawString(36, 30, f"Generated: {timestamp}")

    # Right: page number
    page_num = canvas_obj.getPageNumber()
    canvas_obj.drawRightString(letter[0] - 36, 30, f"Page {page_num}")

    canvas_obj.restoreState()


def _make_professional_table(data, col_widths=None):
    """Create a professionally styled table with zebra striping."""
    accent_color = _hex_to_reportlab_color("#F3F4F6")
    rule_color = _hex_to_reportlab_color("#E5E7EB")
    bg_alt_color = _hex_to_reportlab_color("#FAFAFA")

    table = Table(data, colWidths=col_widths)

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


# -------------------------------------------------------------------
# Main Reporting Function
# -------------------------------------------------------------------
def run_edw_report(pdf_path: Path, output_dir: Path, domicile: str, aircraft: str, bid_period: str, progress_callback=None):
    """
    Generate comprehensive EDW report from pairing PDF.

    This function orchestrates the entire analysis workflow:
    1. Parse PDF to extract trips
    2. Analyze each trip for EDW status
    3. Calculate statistics
    4. Generate Excel workbook
    5. Create charts
    6. Build PDF report

    Args:
        pdf_path: Path to the pairing PDF file
        output_dir: Directory where outputs should be saved
        domicile: Airport code (e.g., "ONT", "SDF")
        aircraft: Fleet type (e.g., "757", "MD-11")
        bid_period: Bid period identifier (e.g., "2507")
        progress_callback: Optional callback function(progress, message) to report progress (0-100)

    Returns:
        Dictionary with:
        - 'excel': Path to Excel file
        - 'report_pdf': Path to PDF report
        - 'df_trips': DataFrame with all trip records
        - 'duty_dist': Duty day distribution DataFrame
        - 'trip_summary': Trip summary DataFrame
        - 'weighted_summary': Weighted percentages DataFrame
        - 'duty_day_stats': Duty day statistics DataFrame
        - 'hot_standby_summary': Hot standby summary DataFrame
        - 'trip_text_map': Dictionary mapping Trip ID to raw trip text

    Raises:
        ValueError: If no valid pairings found in PDF or if wrong PDF type uploaded
    """
    if progress_callback:
        progress_callback(5, "Starting PDF parsing...")

    trips = parse_pairings(pdf_path, progress_callback=progress_callback)

    if progress_callback:
        progress_callback(45, f"Analyzing {len(trips)} pairings...")

    trip_records = []
    trip_text_map = {}  # Map Trip ID to raw trip text
    total_trips = len(trips)
    for idx, trip_text in enumerate(trips, start=1):
        trip_id = parse_trip_id(trip_text)
        frequency = parse_trip_frequency(trip_text)
        hot_standby = is_hot_standby(trip_text)
        edw_flag = is_edw_trip(trip_text)
        tafb_hours = parse_tafb(trip_text)
        tafb_days = tafb_hours / 24.0 if tafb_hours else 0.0
        duty_days = parse_duty_days(trip_text)
        max_duty_length = parse_max_duty_day_length(trip_text)
        max_legs = parse_max_legs_per_duty_day(trip_text)
        duty_day_details = parse_duty_day_details(trip_text, is_edw_trip)

        trip_records.append({
            "Trip ID": trip_id,
            "Frequency": frequency,
            "Hot Standby": hot_standby,
            "TAFB Hours": round(tafb_hours, 2),
            "TAFB Days": round(tafb_days, 2),
            "Duty Days": duty_days,
            "Max Duty Length": round(max_duty_length, 2),
            "Max Legs/Duty": max_legs,
            "EDW": edw_flag,
            "Duty Day Details": duty_day_details,  # Store list of duty day info
        })

        # Store raw trip text indexed by Trip ID
        if trip_id is not None:
            trip_text_map[trip_id] = trip_text

        # Update progress every 25 trips (45-55% of total progress)
        if progress_callback and idx % 25 == 0:
            progress = int(45 + (idx / total_trips) * 10)  # 45% to 55%
            progress_callback(progress, f"Analyzing pairings... ({idx}/{total_trips})")

    df_trips = pd.DataFrame(trip_records)

    # Handle empty or malformed dataframe
    if df_trips.empty:
        raise ValueError(
            "❌ No valid pairings found in PDF.\n\n"
            "**Possible causes:**\n"
            "- This might be a **Bid Line PDF** (should be uploaded to Tab 2: Bid Line Analyzer)\n"
            "- The PDF format may not be supported\n"
            "- The PDF may be corrupted or empty\n\n"
            "**Expected format:** Pairing PDF with Trip IDs and duty day information"
        )

    if "Hot Standby" not in df_trips.columns:
        raise ValueError("No valid trips parsed from PDF. Please check PDF format.")

    if progress_callback:
        progress_callback(60, "Calculating statistics...")

    # Build all statistical dataframes
    stats_dfs = build_edw_dataframes(df_trips)
    duty_dist = stats_dfs['duty_dist']
    trip_summary = stats_dfs['trip_summary']
    weighted_summary = stats_dfs['weighted_summary']
    duty_day_stats = stats_dfs['duty_day_stats']
    hot_standby_summary = stats_dfs['hot_standby_summary']

    # Extract weighted percentages for charts
    trip_weighted = float(weighted_summary.iloc[0]['Value'].rstrip('%'))
    tafb_weighted = float(weighted_summary.iloc[1]['Value'].rstrip('%'))
    dutyday_weighted = float(weighted_summary.iloc[2]['Value'].rstrip('%'))

    # Extract trip counts for charts
    total_trips_count = df_trips["Frequency"].sum()
    edw_trips_count = df_trips[df_trips["EDW"]]["Frequency"].sum()

    if progress_callback:
        progress_callback(65, "Generating Excel workbook...")

    # Excel export
    excel_path = output_dir / f"{domicile}_{aircraft}_Bid{bid_period}_EDW_Report_Data.xlsx"
    save_edw_excel(excel_path, df_trips, duty_dist, trip_summary, weighted_summary, duty_day_stats, hot_standby_summary)

    if progress_callback:
        progress_callback(70, "Creating charts...")

    # -------------------- Charts --------------------
    # Duty Day Count (bar)
    fig_duty_count, ax1 = plt.subplots()
    ax1.bar(duty_dist["Duty Days"], duty_dist["Trips"])
    for i, v in enumerate(duty_dist["Trips"]):
        ax1.text(duty_dist["Duty Days"].iloc[i], v, str(v), ha="center", va="bottom")
    ax1.set_title("Trips by Duty Day Count\n(excludes Hot Standby)")
    ax1.set_xlabel("Duty Days")
    ax1.set_ylabel("Trips")

    # Duty Day Percent (bar)
    fig_duty_percent, ax2 = plt.subplots()
    ax2.bar(duty_dist["Duty Days"], duty_dist["Percent"])
    for i, v in enumerate(duty_dist["Percent"]):
        ax2.text(duty_dist["Duty Days"].iloc[i], v, f"{v:.1f}%", ha="center", va="bottom")
    ax2.set_title("Percentage of Trips by Duty Days\n(excludes Hot Standby)")
    ax2.set_xlabel("Duty Days")
    ax2.set_ylabel("Percent")

    # Weighted EDW % (bar)
    fig_edw_bar, ax3 = plt.subplots()
    edw_metrics = ["Pairing %", "Trip-weighted", "TAFB-weighted", "Duty-day-weighted"]
    edw_values = [trip_weighted, trip_weighted, tafb_weighted, dutyday_weighted]
    ax3.bar(edw_metrics, edw_values)
    for i, v in enumerate(edw_values):
        ax3.text(i, v, f"{v:.1f}%", ha="center", va="bottom")
    ax3.set_ylim(0, 100)
    ax3.set_title("EDW Percentages by Method")
    ax3.set_ylabel("Percent")

    # EDW vs Day Trips (pie)
    fig_edw_vs_day, ax4 = plt.subplots()
    ax4.pie([edw_trips_count, total_trips_count - edw_trips_count],
            labels=["EDW Trips", "Day Trips"], autopct="%1.1f%%")
    ax4.set_title("EDW vs Day Trips")

    # Weighted percentages pies
    fig_trip_weight, ax5 = plt.subplots()
    ax5.pie([trip_weighted, 100 - trip_weighted], labels=["EDW", "Day"], autopct="%1.1f%%")
    ax5.set_title("Trip-weighted EDW %")

    fig_tafb_weight, ax6 = plt.subplots()
    ax6.pie([tafb_weighted, 100 - tafb_weighted], labels=["EDW", "Day"], autopct="%1.1f%%")
    ax6.set_title("TAFB-weighted EDW %")

    fig_dutyday_weight, ax7 = plt.subplots()
    ax7.pie([dutyday_weighted, 100 - dutyday_weighted], labels=["EDW", "Day"], autopct="%1.1f%%")
    ax7.set_title("Duty-day-weighted EDW %")

    if progress_callback:
        progress_callback(85, "Building PDF report...")

    # -------------------- PDF Build --------------------
    pdf_report_path = output_dir / f"{domicile}_{aircraft}_Bid{bid_period}_EDW_Report.pdf"
    styles = getSampleStyleSheet()

    # Professional title style
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#111827"),
        spaceAfter=6,
        alignment=TA_CENTER
    )

    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=_hex_to_reportlab_color("#6B7280"),
        spaceAfter=16,
        alignment=TA_CENTER
    )

    story = []

    # Page 1 – Duty breakdown
    story.append(Paragraph(f"{domicile} {aircraft} – Bid {bid_period} | Trip Length Breakdown", title_style))
    story.append(Paragraph("Note: Distribution excludes Hot Standby pairings", subtitle_style))
    story.append(Spacer(1, 12))
    data = [list(duty_dist.columns)] + duty_dist.values.tolist()
    data = [[clean_text(cell) for cell in row] for row in data]
    t = _make_professional_table(data)
    story.append(t)
    story.append(Spacer(1, 12))
    for fig in [fig_duty_count, fig_duty_percent]:
        buf = BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight")
        buf.seek(0)
        img = PILImage.open(buf)
        img_path = output_dir / f"chart_{hash(fig)}.png"
        img.save(img_path)
        story.append(Image(str(img_path), width=400, height=300))
        story.append(Spacer(1, 12))
    story.append(PageBreak())

    # Page 2 – EDW breakdown
    heading2_style = ParagraphStyle(
        'CustomHeading2',
        parent=styles['Heading2'],
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#111827"),
        spaceAfter=8,
        spaceBefore=12
    )

    story.append(Paragraph(f"{domicile} {aircraft} – Bid {bid_period} | EDW Breakdown", title_style))
    story.append(Spacer(1, 12))
    for caption, df in {"Trip Summary": trip_summary, "Weighted Summary": weighted_summary, "Duty Day Statistics": duty_day_stats}.items():
        story.append(Paragraph(clean_text(caption), heading2_style))
        data = [list(df.columns)] + df.values.tolist()
        data = [[clean_text(cell) for cell in row] for row in data]
        t = _make_professional_table(data)
        story.append(t)
        story.append(Spacer(1, 12))
    buf = BytesIO()
    fig_edw_bar.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    img = PILImage.open(buf)
    img_path = output_dir / "EDW_Bar.png"
    img.save(img_path)
    story.append(Image(str(img_path), width=400, height=300))
    story.append(PageBreak())

    # Page 3 – Pies
    for fig in [fig_edw_vs_day, fig_trip_weight, fig_tafb_weight, fig_dutyday_weight]:
        buf = BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight")
        buf.seek(0)
        img = PILImage.open(buf)
        img_path = output_dir / f"pie_{hash(fig)}.png"
        img.save(img_path)
        story.append(Image(str(img_path), width=300, height=300))
        story.append(Spacer(1, 12))

    # Create document with margins for header/footer
    doc = SimpleDocTemplate(
        str(pdf_report_path),
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=60,  # Space for header
        bottomMargin=50  # Space for footer
    )

    # Header title for all pages
    header_title = f"{domicile} {aircraft} – Bid {bid_period} | Pairing Analysis Report"

    # Build PDF with header/footer
    def add_page_decorations(canvas_obj, doc):
        _draw_edw_header(canvas_obj, doc, header_title)
        _draw_edw_footer(canvas_obj, doc)

    doc.build(story, onFirstPage=add_page_decorations, onLaterPages=add_page_decorations)

    if progress_callback:
        progress_callback(100, "Complete!")

    return {
        "excel": excel_path,
        "report_pdf": pdf_report_path,
        "df_trips": df_trips,
        "duty_dist": duty_dist,
        "trip_summary": trip_summary,
        "weighted_summary": weighted_summary,
        "duty_day_stats": duty_day_stats,
        "hot_standby_summary": hot_standby_summary,
        "trip_text_map": trip_text_map,
    }
