import re
import unicodedata
from pathlib import Path
from io import BytesIO
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image as PILImage

from PyPDF2 import PdfReader
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
from reportlab.lib.styles import getSampleStyleSheet


# -------------------------------------------------------------------
# Text Sanitizer
# -------------------------------------------------------------------
def clean_text(text: str) -> str:
    if not isinstance(text, str):
        return text
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\u00A0", " ")
    text = re.sub(r"[■•▪●]", "-", text)
    return text


# -------------------------------------------------------------------
# PDF Parsing & EDW Logic
# -------------------------------------------------------------------
def parse_pairings(pdf_path: Path, progress_callback=None):
    reader = PdfReader(str(pdf_path))
    all_text = ""
    total_pages = len(reader.pages)

    for i, page in enumerate(reader.pages, start=1):
        all_text += page.extract_text() + "\n"
        # Update progress during PDF parsing (0-40% of total progress)
        if progress_callback and i % 10 == 0:  # Update every 10 pages
            progress = int(5 + (i / total_pages) * 35)  # 5% to 40%
            progress_callback(progress, f"Parsing PDF... ({i}/{total_pages} pages)")

    trips = []
    current_trip = []
    in_trip = False  # Flag to track if we've started collecting trips

    for line in all_text.splitlines():
        if re.match(r"^\s*Trip\s*Id", line, re.IGNORECASE):
            if current_trip:
                trips.append("\n".join(current_trip))
            current_trip = [line]  # Start new trip with the Trip Id line
            in_trip = True
        elif in_trip:
            current_trip.append(line)

    if current_trip and in_trip:
        trips.append("\n".join(current_trip))

    return trips


def extract_local_times(trip_text):
    times = []
    pattern = re.compile(r"\((\d{1,2})\)(\d{2}):(\d{2})")
    for match in pattern.finditer(trip_text):
        local_hour = int(match.group(1))
        minute = int(match.group(3))
        times.append(f"{local_hour:02d}:{minute:02d}")
    return times


def is_edw_trip(trip_text):
    times = extract_local_times(trip_text)
    for t in times:
        hh, mm = map(int, t.split(":"))
        if (hh == 2 and mm >= 30) or (hh in [3, 4]) or (hh == 5 and mm == 0):
            return True
    return False


def parse_tafb(trip_text):
    m = re.search(r"TAFB:\s*(\d+)h(\d+)", trip_text)
    if not m:
        return 0.0
    hours = int(m.group(1))
    mins = int(m.group(2))
    return hours + mins / 60.0


def parse_duty_days(trip_text):
    duty_blocks = re.findall(r"(?i)Duty\s+\d+h\d+", trip_text)
    return len(duty_blocks)


def parse_trip_id(trip_text):
    """Extract the actual Trip ID number from the trip text"""
    m = re.search(r"Trip\s*Id:\s*(\d+)", trip_text, re.IGNORECASE)
    if m:
        return int(m.group(1))
    return None


def parse_trip_frequency(trip_text):
    """Extract how many times this trip runs from the date range line"""
    # Look for patterns like "(5 trips)" or "(4 trips)"
    m = re.search(r"\((\d+)\s+trips?\)", trip_text, re.IGNORECASE)
    if m:
        return int(m.group(1))
    # If no frequency found, assume it runs once
    return 1


def is_hot_standby(trip_text):
    """
    Identify Hot Standby pairings.
    These are single-segment pairings where departure and arrival are the same (e.g., ONT-ONT).
    Pairings with positioning legs (e.g., ONT-DFW, DFW-DFW, DFW-ONT) are NOT hot standby.

    Logic: Only mark as Hot Standby if there's exactly ONE flight segment and it's XXX-XXX.
    """
    # Look for airport pair patterns like "ONT-ONT", "SDF-SDF", etc.
    # Format is typically: FLIGHT_NUMBER\nDEPT-ARVL
    pattern = re.compile(r"\b([A-Z]{3})-([A-Z]{3})\b")
    matches = pattern.findall(trip_text)

    # Only mark as Hot Standby if:
    # 1. Exactly one route segment found
    # 2. That segment has same departure and arrival
    if len(matches) == 1:
        dept, arvl = matches[0]
        if dept == arvl:
            return True

    return False


# -------------------------------------------------------------------
# Excel Utilities
# -------------------------------------------------------------------
def _save_excel(dfs: dict, output_path: Path):
    with pd.ExcelWriter(output_path) as writer:
        for sheet, df in dfs.items():
            df.to_excel(writer, sheet_name=clean_text(sheet), index=False)


# -------------------------------------------------------------------
# Main Reporting
# -------------------------------------------------------------------
def run_edw_report(pdf_path: Path, output_dir: Path, domicile: str, aircraft: str, bid_period: str, progress_callback=None):
    """
    Generate EDW report from PDF.

    Args:
        progress_callback: Optional callback function(progress, message) to report progress (0-100)
    """
    if progress_callback:
        progress_callback(5, "Starting PDF parsing...")

    trips = parse_pairings(pdf_path, progress_callback=progress_callback)

    if progress_callback:
        progress_callback(45, f"Analyzing {len(trips)} pairings...")

    trip_records = []
    total_trips = len(trips)
    for idx, trip_text in enumerate(trips, start=1):
        trip_id = parse_trip_id(trip_text)
        frequency = parse_trip_frequency(trip_text)
        hot_standby = is_hot_standby(trip_text)
        edw_flag = is_edw_trip(trip_text)
        tafb_hours = parse_tafb(trip_text)
        tafb_days = tafb_hours / 24.0 if tafb_hours else 0.0
        duty_days = parse_duty_days(trip_text)

        trip_records.append({
            "Trip ID": trip_id,
            "Frequency": frequency,
            "Hot Standby": hot_standby,
            "TAFB Hours": round(tafb_hours, 2),
            "TAFB Days": round(tafb_days, 2),
            "Duty Days": duty_days,
            "EDW": edw_flag,
        })

        # Update progress every 25 trips (45-55% of total progress)
        if progress_callback and idx % 25 == 0:
            progress = int(45 + (idx / total_trips) * 10)  # 45% to 55%
            progress_callback(progress, f"Analyzing pairings... ({idx}/{total_trips})")

    df_trips = pd.DataFrame(trip_records)

    if progress_callback:
        progress_callback(60, "Calculating statistics...")

    # Duty Day distribution (exclude 0s and Hot Standby) - weighted by frequency
    # Filter out Hot Standby pairings from distribution analysis
    df_regular_trips = df_trips[~df_trips["Hot Standby"]]
    duty_dist = df_regular_trips[df_regular_trips["Duty Days"] > 0].groupby("Duty Days")["Frequency"].sum().reset_index(name="Trips")
    duty_dist["Percent"] = (duty_dist["Trips"] / duty_dist["Trips"].sum() * 100).round(1)

    # Summaries - account for frequency
    unique_pairings = len(df_trips)
    total_trips = df_trips["Frequency"].sum()  # Total number of actual trips
    edw_trips = df_trips[df_trips["EDW"]]["Frequency"].sum()  # EDW trips weighted by frequency
    hot_standby_pairings = len(df_trips[df_trips["Hot Standby"]])  # Unique hot standby pairings
    hot_standby_trips = df_trips[df_trips["Hot Standby"]]["Frequency"].sum()  # Hot standby occurrences

    trip_weighted = edw_trips / total_trips * 100 if total_trips else 0

    # TAFB weighted - multiply TAFB by frequency
    tafb_total = (df_trips["TAFB Hours"] * df_trips["Frequency"]).sum()
    tafb_edw = (df_trips[df_trips["EDW"]]["TAFB Hours"] * df_trips[df_trips["EDW"]]["Frequency"]).sum()
    tafb_weighted = (tafb_edw / tafb_total * 100) if tafb_total > 0 else 0

    # Duty day weighted - multiply duty days by frequency
    dutyday_total = (df_trips["Duty Days"] * df_trips["Frequency"]).sum()
    dutyday_edw = (df_trips[df_trips["EDW"]]["Duty Days"] * df_trips[df_trips["EDW"]]["Frequency"]).sum()
    dutyday_weighted = (dutyday_edw / dutyday_total * 100) if dutyday_total > 0 else 0

    trip_summary = pd.DataFrame({
        "Metric": ["Unique Pairings", "Total Trips", "EDW Trips", "Day Trips", "Pct EDW"],
        "Value": [unique_pairings, total_trips, edw_trips, total_trips - edw_trips, f"{trip_weighted:.1f}%"],
    })

    weighted_summary = pd.DataFrame({
        "Metric": [
            "Trip-weighted EDW trip %",
            "TAFB-weighted EDW trip %",
            "Duty-day-weighted EDW trip %",
        ],
        "Value": [
            f"{trip_weighted:.1f}%",
            f"{tafb_weighted:.1f}%",
            f"{dutyday_weighted:.1f}%",
        ],
    })

    hot_standby_summary = pd.DataFrame({
        "Metric": ["Hot Standby Pairings", "Hot Standby Trips"],
        "Value": [hot_standby_pairings, hot_standby_trips],
    })

    if progress_callback:
        progress_callback(65, "Generating Excel workbook...")

    # Excel export
    excel_path = output_dir / f"{domicile}_{aircraft}_Bid{bid_period}_EDW_Report_Data.xlsx"
    _save_excel({
        "Trip Records": df_trips,
        "Duty Distribution": duty_dist,
        "Trip Summary": trip_summary,
        "Weighted Summary": weighted_summary,
        "Hot Standby Summary": hot_standby_summary,
    }, excel_path)

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
    ax4.pie([edw_trips, total_trips - edw_trips],
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
    story = []

    # Page 1 – Duty breakdown
    story.append(Paragraph(f"{domicile} {aircraft} – Bid {bid_period} Trip Length Breakdown", styles["Title"]))
    story.append(Spacer(1, 6))
    story.append(Paragraph("Note: Distribution excludes Hot Standby pairings", styles["Normal"]))
    story.append(Spacer(1, 12))
    data = [list(duty_dist.columns)] + duty_dist.values.tolist()
    data = [[clean_text(cell) for cell in row] for row in data]
    t = Table(data)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
    ]))
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
    story.append(Paragraph(f"{domicile} {aircraft} – Bid {bid_period} EDW Breakdown", styles["Title"]))
    story.append(Spacer(1, 12))
    for caption, df in {"Trip Summary": trip_summary, "Weighted Summary": weighted_summary}.items():
        story.append(Paragraph(clean_text(caption), styles["Heading2"]))
        data = [list(df.columns)] + df.values.tolist()
        data = [[clean_text(cell) for cell in row] for row in data]
        t = Table(data)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ]))
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

    doc = SimpleDocTemplate(str(pdf_report_path), pagesize=letter)
    doc.build(story)

    if progress_callback:
        progress_callback(100, "Complete!")

    return {
        "excel": excel_path,
        "report_pdf": pdf_report_path,
        "df_trips": df_trips,
        "duty_dist": duty_dist,
        "trip_summary": trip_summary,
        "weighted_summary": weighted_summary,
        "hot_standby_summary": hot_standby_summary,
    }





