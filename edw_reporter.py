import re
import unicodedata
from pathlib import Path
from io import BytesIO
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Set backend for headless environments (Streamlit Cloud)
import matplotlib.pyplot as plt
from PIL import Image as PILImage

from datetime import datetime
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
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfgen import canvas


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
# PDF Header Extraction
# -------------------------------------------------------------------
def extract_pdf_header_info(pdf_path: Path):
    """
    Extract bid period, domicile, fleet type, and date range from PDF header.
    Checks the first page, and if header info is not found, checks the second page.
    Returns a dictionary with the extracted information.
    """
    reader = PdfReader(str(pdf_path))
    if len(reader.pages) == 0:
        return {
            'bid_period': 'Unknown',
            'domicile': 'Unknown',
            'fleet_type': 'Unknown',
            'date_range': 'Unknown',
            'report_date': 'Unknown'
        }

    # Initialize results
    result = {
        'bid_period': 'Unknown',
        'domicile': 'Unknown',
        'fleet_type': 'Unknown',
        'date_range': 'Unknown',
        'report_date': 'Unknown'
    }

    # Helper function to extract header info from page text
    def extract_from_text(text, current_result):
        extracted = current_result.copy()

        # Extract Bid Period (e.g., "Bid Period : 2601")
        if extracted['bid_period'] == 'Unknown':
            bid_period_match = re.search(r"Bid\s+Period\s*:\s*(\d+)", text, re.IGNORECASE)
            if bid_period_match:
                extracted['bid_period'] = bid_period_match.group(1)

        # Extract Domicile (e.g., "Domicile: ONT")
        if extracted['domicile'] == 'Unknown':
            domicile_match = re.search(r"Domicile\s*:\s*([A-Z]{3})", text, re.IGNORECASE)
            if domicile_match:
                extracted['domicile'] = domicile_match.group(1)

        # Extract Fleet Type (e.g., "Fleet Type: 757")
        if extracted['fleet_type'] == 'Unknown':
            fleet_match = re.search(r"Fleet\s+Type\s*:\s*([A-Z0-9\-]+)", text, re.IGNORECASE)
            if fleet_match:
                extracted['fleet_type'] = fleet_match.group(1)

        # Extract Bid Period Date Range (e.g., "Bid Period Date Range: 30Nov2025 - 25Jan2026")
        if extracted['date_range'] == 'Unknown':
            date_range_match = re.search(r"Bid\s+Period\s+Date\s+Range\s*:\s*(.+?)(?:\n|Date/Time)", text, re.IGNORECASE)
            if date_range_match:
                extracted['date_range'] = date_range_match.group(1).strip()

        # Extract Date/Time (e.g., "Date/Time: 16Oct2025 16:32")
        if extracted['report_date'] == 'Unknown':
            report_date_match = re.search(r"Date/Time\s*:\s*(.+?)(?:\n|$)", text, re.IGNORECASE)
            if report_date_match:
                extracted['report_date'] = report_date_match.group(1).strip()

        return extracted

    # Try extracting from first page
    first_page_text = reader.pages[0].extract_text()
    result = extract_from_text(first_page_text, result)

    # If any critical fields are still Unknown, try second page
    if (result['bid_period'] == 'Unknown' or
        result['domicile'] == 'Unknown' or
        result['fleet_type'] == 'Unknown') and len(reader.pages) >= 2:
        second_page_text = reader.pages[1].extract_text()
        result = extract_from_text(second_page_text, result)

    return result


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


def parse_max_duty_day_length(trip_text):
    """
    Extract all duty day lengths from trip text and return the maximum length in hours.
    Returns 0.0 if no duty days found.

    Example patterns: "Duty 12h30", "Duty 8h15"
    """
    duty_pattern = re.findall(r"(?i)Duty\s+(\d+)h(\d+)", trip_text)
    if not duty_pattern:
        return 0.0

    duty_lengths = []
    for hours_str, mins_str in duty_pattern:
        hours = int(hours_str)
        mins = int(mins_str)
        total_hours = hours + mins / 60.0
        duty_lengths.append(total_hours)

    return max(duty_lengths) if duty_lengths else 0.0


def parse_max_legs_per_duty_day(trip_text):
    """
    Extract the maximum number of flight legs in any single duty day.
    Returns 0 if no legs found.

    A duty day is defined as text between "Briefing" and "Debriefing" (or fallback patterns).
    Handles both PDF formats:
    - Multi-line: Flight numbers on separate lines ("UPS 986")
    - Single-line: Flight data on one line ("1 (Su)Su UPS5969 ONT-SDF ...")
    - Fallback: Older PDFs without Briefing/Debriefing keywords

    Example: A trip with duty days containing 2, 1, and 4 legs would return 4.
    """
    # Split text into lines
    lines = trip_text.split('\n')

    legs_per_duty_day = []
    current_duty_legs = 0
    in_duty = False

    for i, line in enumerate(lines):
        # Check if we're starting a duty day
        is_briefing = re.search(r'\bBriefing\b', line, re.IGNORECASE)

        # Fallback: detect duty start without "Briefing"
        # Only use fallback when we didn't recently see "Briefing" keyword
        is_fallback_start = False
        if not is_briefing and i + 3 < len(lines):
            # Check if "Briefing" appeared in the last 2 lines
            recent_briefing = any(
                i - offset >= 0 and re.search(r'\bBriefing\b', lines[i - offset], re.IGNORECASE)
                for offset in range(1, 3)
            )

            if not recent_briefing:
                time_match = re.match(r'\((\d+)\)(\d{2}:\d{2})', line.strip())
                duration_match = re.match(r'(\d+)h(\d+)', lines[i + 1].strip())
                duty_label = lines[i + 2].strip() == 'Duty'
                if time_match and duration_match and duty_label:
                    is_fallback_start = True

        if is_briefing or is_fallback_start:
            in_duty = True
            current_duty_legs = 0

        # Check if we're ending a duty day
        is_debriefing = re.search(r'\bDebriefing\b', line, re.IGNORECASE)
        is_fallback_end = (line.strip() == 'Duty Time:')

        if is_debriefing or is_fallback_end:
            if in_duty:
                legs_per_duty_day.append(current_duty_legs)
                in_duty = False
                current_duty_legs = 0
        # Count flight legs
        elif in_duty:
            stripped = line.strip()

            # Multi-line format: Flight number on its own line
            # Match lines starting with UPS/DH/GT
            if re.match(r'^(UPS|DH|GT)(\s|\d|N/A)', stripped, re.IGNORECASE):
                current_duty_legs += 1
            # MD-11 format: Bare 3-4 digit flight number followed by route
            elif re.match(r'^\d{3,4}$', stripped):
                # Verify next line is a route (with optional suffix like (C))
                if i + 1 < len(lines) and re.match(r'^[A-Z]{3}-[A-Z]{3}(\([A-Z]\))?$', lines[i + 1].strip()):
                    current_duty_legs += 1
            # Single-line format: Flight data on one line with day pattern
            # Pattern: "1 (Su)Su UPS5969 ONT-SDF ..." or "1 (  )   UPS 984 ONT-BFI ..."
            elif re.search(r'(UPS|DH|GT)', stripped, re.IGNORECASE):
                # Verify it's a flight line (has route pattern or time pattern)
                if re.search(r'[A-Z]{3}-[A-Z]{3}', stripped) or re.search(r'\(\d+\)\d{2}:\d{2}', stripped):
                    current_duty_legs += 1

    # Handle case where duty day doesn't have debriefing (incomplete data)
    if in_duty and current_duty_legs > 0:
        legs_per_duty_day.append(current_duty_legs)

    return max(legs_per_duty_day) if legs_per_duty_day else 0


def parse_duty_day_details(trip_text):
    """
    Extract detailed information for each duty day in a trip.

    Returns: List of dictionaries, one per duty day:
    [
        {'day': 1, 'duration_hours': 7.73, 'num_legs': 2, 'block_hours': 4.88, 'is_edw': True},
        {'day': 2, 'duration_hours': 12.5, 'num_legs': 3, 'block_hours': 6.25, 'is_edw': False},
        ...
    ]

    Returns empty list if no duty days found.
    """
    lines = trip_text.split('\n')

    duty_day_details = []
    current_duty_day = None
    duty_day_number = 0
    briefing_line_idx = None

    for i, line in enumerate(lines):
        # Start of a new duty day (Briefing OR fallback pattern)
        is_briefing = re.search(r'\bBriefing\b', line, re.IGNORECASE)

        # Fallback: detect duty start without "Briefing"
        # Only use fallback when we didn't recently see "Briefing" keyword
        is_fallback_start = False
        if not is_briefing and i + 3 < len(lines):
            # Check if "Briefing" appeared in the last 2 lines
            recent_briefing = any(
                i - offset >= 0 and re.search(r'\bBriefing\b', lines[i - offset], re.IGNORECASE)
                for offset in range(1, 3)
            )

            if not recent_briefing:
                time_match = re.match(r'\((\d+)\)(\d{2}:\d{2})', line.strip())
                duration_match = re.match(r'(\d+)h(\d+)', lines[i + 1].strip())
                duty_label = lines[i + 2].strip() == 'Duty'
                if time_match and duration_match and duty_label:
                    is_fallback_start = True

        if is_briefing or is_fallback_start:
            if current_duty_day:
                # Extract duty/block/credit times before appending (for MD-11 format without Debriefing)
                if briefing_line_idx is not None and current_duty_day['duration_hours'] == 0.0:
                    for j in range(briefing_line_idx, i):
                        # Multi-line format: "Duty" on its own line
                        duty_match = re.match(r'^\s*Duty\s*$', lines[j].strip(), re.IGNORECASE)
                        if duty_match and j + 1 < len(lines):
                            time_match = re.match(r'(\d+)h(\d+)', lines[j + 1].strip())
                            if time_match:
                                hours = int(time_match.group(1))
                                mins = int(time_match.group(2))
                                current_duty_day['duration_hours'] = round(hours + mins / 60.0, 2)

                        # Block time
                        block_match = re.match(r'^\s*Block\s*$', lines[j].strip(), re.IGNORECASE)
                        if block_match and j + 1 < len(lines):
                            time_match = re.match(r'(\d+)h(\d+)', lines[j + 1].strip())
                            if time_match:
                                hours = int(time_match.group(1))
                                mins = int(time_match.group(2))
                                current_duty_day['block_hours'] = round(hours + mins / 60.0, 2)

                        # Credit time
                        credit_match = re.match(r'^\s*Credit\s*$', lines[j].strip(), re.IGNORECASE)
                        if credit_match and j + 1 < len(lines):
                            time_match = re.match(r'(\d+)h(\d+)', lines[j + 1].strip())
                            if time_match:
                                hours = int(time_match.group(1))
                                mins = int(time_match.group(2))
                                current_duty_day['credit_hours'] = round(hours + mins / 60.0, 2)

                # Check if this duty day is EDW before appending
                if briefing_line_idx is not None:
                    duty_day_text = '\n'.join(lines[briefing_line_idx:i])
                    current_duty_day['is_edw'] = is_edw_trip(duty_day_text)
                duty_day_details.append(current_duty_day)

            duty_day_number += 1
            briefing_line_idx = i
            current_duty_day = {
                'day': duty_day_number,
                'duration_hours': 0.0,
                'num_legs': 0,
                'block_hours': 0.0,
                'credit_hours': 0.0,
                'is_edw': False
            }

        # End of duty day - capture duration and block time by searching between briefing and debriefing
        is_debriefing = re.search(r'\bDebriefing\b', line, re.IGNORECASE)
        is_fallback_end = (line.strip() == 'Duty Time:')

        if current_duty_day and (is_debriefing or is_fallback_end):
            # Search from briefing through a few lines after debriefing for "Duty", "Block", and "Credit" times
            # Handles both formats:
            # - Multi-line: "Duty" on one line, "7h44" on next (appears AFTER Debriefing)
            # - Single-line: "Briefing (00)08:50 1h00 Duty 7h34 Crew: 1/1/0"
            if briefing_line_idx is not None:
                # Search up to 5 lines after debriefing to catch duty/block/credit times
                search_end = min(i + 6, len(lines))
                for j in range(briefing_line_idx, search_end):
                    # Multi-line format: "Duty" on its own line
                    duty_match = re.match(r'^\s*Duty\s*$', lines[j].strip(), re.IGNORECASE)
                    if duty_match and j + 1 < len(lines):
                        time_match = re.match(r'(\d+)h(\d+)', lines[j + 1].strip())
                        if time_match:
                            hours = int(time_match.group(1))
                            mins = int(time_match.group(2))
                            current_duty_day['duration_hours'] = round(hours + mins / 60.0, 2)

                    # Single-line format: "Duty 7h34" embedded in line
                    inline_duty_match = re.search(r'\bDuty\s+(\d+)h(\d+)', lines[j])
                    if inline_duty_match and current_duty_day['duration_hours'] == 0.0:
                        hours = int(inline_duty_match.group(1))
                        mins = int(inline_duty_match.group(2))
                        current_duty_day['duration_hours'] = round(hours + mins / 60.0, 2)

                    # Block time - Multi-line format: "Block" on its own line
                    block_match = re.match(r'^\s*Block\s*$', lines[j].strip(), re.IGNORECASE)
                    if block_match and j + 1 < len(lines):
                        time_match = re.match(r'(\d+)h(\d+)', lines[j + 1].strip())
                        if time_match:
                            hours = int(time_match.group(1))
                            mins = int(time_match.group(2))
                            current_duty_day['block_hours'] = round(hours + mins / 60.0, 2)

                    # Single-line format: "Block 4h53" embedded in line
                    # Avoid matching "Block Time:" from trip summary
                    inline_block_match = re.search(r'\bBlock\s+(\d+)h(\d+)', lines[j])
                    if inline_block_match and 'Block Time:' not in lines[j] and current_duty_day['block_hours'] == 0.0:
                        hours = int(inline_block_match.group(1))
                        mins = int(inline_block_match.group(2))
                        current_duty_day['block_hours'] = round(hours + mins / 60.0, 2)

                    # Credit time - Multi-line format: "Credit" on its own line
                    credit_match = re.match(r'^\s*Credit\s*$', lines[j].strip(), re.IGNORECASE)
                    if credit_match and j + 1 < len(lines):
                        # Credit format can be "6h19L" or "6h19"
                        time_match = re.match(r'(\d+)h(\d+)', lines[j + 1].strip())
                        if time_match:
                            hours = int(time_match.group(1))
                            mins = int(time_match.group(2))
                            current_duty_day['credit_hours'] = round(hours + mins / 60.0, 2)

                    # Single-line format: "Credit 6h19L" embedded in line
                    # Avoid matching "Credit Time:" from trip summary
                    inline_credit_match = re.search(r'\bCredit\s+(\d+)h(\d+)', lines[j])
                    if inline_credit_match and 'Credit Time:' not in lines[j] and current_duty_day['credit_hours'] == 0.0:
                        hours = int(inline_credit_match.group(1))
                        mins = int(inline_credit_match.group(2))
                        current_duty_day['credit_hours'] = round(hours + mins / 60.0, 2)

        # Count flight legs within duty day
        elif current_duty_day:
            stripped = line.strip()

            # Multi-line format: Flight number on its own line (starts with UPS/DH/GT)
            if re.match(r'^(UPS|DH|GT)(\s|\d|N/A)', stripped, re.IGNORECASE):
                current_duty_day['num_legs'] += 1
            # MD-11 format: Bare 3-4 digit flight number followed by route
            elif re.match(r'^\d{3,4}$', stripped):
                # Verify next line is a route (with optional suffix like (C))
                if i + 1 < len(lines) and re.match(r'^[A-Z]{3}-[A-Z]{3}(\([A-Z]\))?$', lines[i + 1].strip()):
                    current_duty_day['num_legs'] += 1
            # Single-line format: Flight data on one line with day pattern
            # Pattern: "1 (  )   UPS 984 ONT-BFI ..." or contains UPS/DH/GT with route
            elif re.search(r'(UPS|DH|GT)', stripped, re.IGNORECASE):
                # Verify it's a flight line (has route pattern or time pattern)
                if re.search(r'[A-Z]{3}-[A-Z]{3}', stripped) or re.search(r'\(\d+\)\d{2}:\d{2}', stripped):
                    current_duty_day['num_legs'] += 1

    # Don't forget the last duty day
    if current_duty_day:
        # Extract duty/block times for last duty day (for MD-11 format without Debriefing)
        if briefing_line_idx is not None and current_duty_day['duration_hours'] == 0.0:
            for j in range(briefing_line_idx, len(lines)):
                # Multi-line format: "Duty" on its own line
                duty_match = re.match(r'^\s*Duty\s*$', lines[j].strip(), re.IGNORECASE)
                if duty_match and j + 1 < len(lines):
                    time_match = re.match(r'(\d+)h(\d+)', lines[j + 1].strip())
                    if time_match:
                        hours = int(time_match.group(1))
                        mins = int(time_match.group(2))
                        current_duty_day['duration_hours'] = round(hours + mins / 60.0, 2)

                # Block time
                block_match = re.match(r'^\s*Block\s*$', lines[j].strip(), re.IGNORECASE)
                if block_match and j + 1 < len(lines):
                    time_match = re.match(r'(\d+)h(\d+)', lines[j + 1].strip())
                    if time_match:
                        hours = int(time_match.group(1))
                        mins = int(time_match.group(2))
                        current_duty_day['block_hours'] = round(hours + mins / 60.0, 2)

                # Credit time
                credit_match = re.match(r'^\s*Credit\s*$', lines[j].strip(), re.IGNORECASE)
                if credit_match and j + 1 < len(lines):
                    time_match = re.match(r'(\d+)h(\d+)', lines[j + 1].strip())
                    if time_match:
                        hours = int(time_match.group(1))
                        mins = int(time_match.group(2))
                        current_duty_day['credit_hours'] = round(hours + mins / 60.0, 2)

        # Check EDW for the last duty day
        if briefing_line_idx is not None:
            duty_day_text = '\n'.join(lines[briefing_line_idx:])
            current_duty_day['is_edw'] = is_edw_trip(duty_day_text)
        duty_day_details.append(current_duty_day)

    return duty_day_details


def parse_trip_id(trip_text):
    """Extract the actual Trip ID number from the trip text"""
    m = re.search(r"Trip\s*Id:\s*(\d+)", trip_text, re.IGNORECASE)
    if m:
        return int(m.group(1))
    return None


def parse_trip_for_table(trip_text):
    """
    Parse trip text into a structured format for table display.
    Uses MARKER-BASED PARSING for robustness across different PDF formats.

    This version doesn't rely on fixed line skip counts, making it more resilient
    to format variations between different flight types (UPS, GT, DH) and PDF templates.

    Returns:
        {
            'trip_id': int,
            'date_freq': str,
            'duty_days': [
                {
                    'flights': [...],
                    'duty_start': str,
                    'duty_end': str,
                    'duty_time': str,
                    'block_total': str,
                    'credit': str,
                    'rest': str
                }
            ],
            'trip_summary': {...}
        }
    """
    lines = trip_text.split('\n')

    trip_id = parse_trip_id(trip_text)

    # Find date/frequency line
    date_freq = None
    for line in lines:
        if (re.search(r'\d+\s+trips?\)', line, re.IGNORECASE) or
            re.search(r'Only on|^\d{2}\w{3}\d{4}', line, re.IGNORECASE)):
            date_freq = line.strip()
            break

    duty_days = []
    current_duty = None
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # Start of duty day (Briefing marker OR fallback pattern for older PDFs)
        is_briefing = re.search(r'\bBriefing\b', line, re.IGNORECASE)

        # Fallback: Detect duty day start pattern without "Briefing" keyword
        # Pattern: (HH)MM:SS followed by duration followed by "Duty" label
        # Only use fallback when we didn't recently see "Briefing" keyword
        is_fallback_duty_start = False
        if not is_briefing and i + 3 < len(lines):
            # Check if "Briefing" appeared in the last 2 lines
            recent_briefing = any(
                i - offset >= 0 and re.search(r'\bBriefing\b', lines[i - offset], re.IGNORECASE)
                for offset in range(1, 3)
            )

            if not recent_briefing:
                # Check if current line is a time pattern
                time_match = re.match(r'\((\d+)\)(\d{2}:\d{2})', line)
                # Next line should be duration
                duration_match = re.match(r'(\d+)h(\d+)', lines[i + 1].strip()) if i + 1 < len(lines) else None
                # Line after that should be "Duty" label
                duty_label = lines[i + 2].strip() == 'Duty' if i + 2 < len(lines) else False

                if time_match and duration_match and duty_label:
                    is_fallback_duty_start = True

        if is_briefing or is_fallback_duty_start:
            if current_duty:
                duty_days.append(current_duty)

            # Capture briefing time and duty time from the line
            # Multi-line format: "Briefing" on one line, time on next
            # Single-line format: "Briefing (05)13:30 1h00 Duty 9h22 ..."
            duty_start = None
            duty_time_val = None

            # Try to extract from same line (single-line format or Briefing marker)
            time_match = re.search(r'\((\d+)\)(\d{2}:\d{2})', line)
            if time_match:
                duty_start = f"({time_match.group(1)}){time_match.group(2)}"

            # Extract Duty time if on same line
            duty_match = re.search(r'\bDuty\s+(\d+h\d+)', line)
            if duty_match:
                duty_time_val = duty_match.group(1)

            # Fallback: If this is the fallback pattern, extract from specific lines
            if is_fallback_duty_start:
                # Line i: (HH)MM:SS - duty start time
                if not duty_start:
                    duty_start = line
                # Line i+3: duration value after "Duty" label
                if i + 3 < len(lines) and not duty_time_val:
                    duty_time_val = lines[i + 3].strip()

            # If not found yet, check next line (multi-line format with Briefing)
            if not duty_start and i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if re.match(r'\(\d+\)\d{2}:\d{2}', next_line):
                    duty_start = next_line

            current_duty = {
                'flights': [],
                'duty_start': duty_start,
                'duty_end': None,
                'duty_time': duty_time_val,
                'block_total': None,
                'credit': None,
                'rest': None
            }
            i += 1
            continue

        # End of duty day (Debriefing marker OR fallback pattern)
        is_debriefing = re.search(r'\bDebriefing\b', line, re.IGNORECASE)

        # Fallback: Detect duty day end without "Debriefing" keyword
        # Pattern: "Duty Time:" label (after "Rest" marker)
        is_fallback_duty_end = False
        if current_duty and not is_debriefing and line == 'Duty Time:':
            is_fallback_duty_end = True

        if current_duty and (is_debriefing or is_fallback_duty_end):
            # Capture debriefing time and credit from the line
            # Multi-line format: "Debriefing" on one line, time on next
            # Single-line format: "Debriefing (16)22:52 0h15 Credit 6h19L ..."
            # Fallback format: "Duty Time:" followed by duration, then time

            # Try to extract from same line (single-line format)
            time_match = re.search(r'\((\d+)\)(\d{2}:\d{2})', line)
            if time_match:
                current_duty['duty_end'] = f"({time_match.group(1)}){time_match.group(2)}"

            # Fallback: For "Duty Time:" pattern, duty end time is 2 lines down
            if is_fallback_duty_end and i + 2 < len(lines):
                # Line i+1 is the duty time value (already captured)
                # Line i+2 is the duty end time
                end_time_line = lines[i + 2].strip()
                if re.match(r'\(\d+\)\d{2}:\d{2}', end_time_line):
                    current_duty['duty_end'] = end_time_line

            # Extract Credit if on same line
            credit_match = re.search(r'\bCredit\s+(\S+)', line)
            if credit_match:
                current_duty['credit'] = credit_match.group(1)

            # If not on same line, check next line (multi-line format)
            if not current_duty['duty_end'] and i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if re.match(r'\(\d+\)\d{2}:\d{2}', next_line):
                    current_duty['duty_end'] = next_line

            i += 1
            continue

        # Inside a duty day
        if current_duty is not None:
            # MARKER-BASED FLIGHT DETECTION
            # Handles both single-line and multi-line flight formats
            is_flight = False
            is_single_line = False
            has_day_pattern = re.match(r'^\d+\s+\(', line)

            # Check if this is single-line format (all data on one line)
            if has_day_pattern and re.search(r'(UPS|GT|DH)', line, re.IGNORECASE):
                # Single-line format: "1 (Su)Su UPS5969 ONT-SDF (06)14:30 ..."
                is_flight = True
                is_single_line = True

            # Case 1: Multi-line format - Day pattern followed by flight number on next line
            elif has_day_pattern and i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if re.match(r'^(UPS|GT|DH)', next_line, re.IGNORECASE):
                    is_flight = True
                    day_info = line
                    flight_num = next_line
                    data_start_offset = 2  # Route starts at i+2
                # MD-11 format: Day pattern followed by bare numeric flight number
                elif re.match(r'^\d{3,4}$', next_line):  # 3-4 digit flight number
                    # Verify line after that is a route (with optional suffix like (C))
                    if i + 2 < len(lines) and re.match(r'^[A-Z]{3}-[A-Z]{3}(\([A-Z]\))?$', lines[i + 2].strip()):
                        is_flight = True
                        day_info = line
                        flight_num = next_line
                        data_start_offset = 2  # Route starts at i+2

            # Case 2: Flight number without day pattern (continuation flight)
            elif not has_day_pattern and re.match(r'^(UPS|GT|DH)', line, re.IGNORECASE):
                # Verify next line is a route (with optional suffix like (C))
                if i + 1 < len(lines) and re.match(r'^[A-Z]{3}-[A-Z]{3}(\([A-Z]\))?$', lines[i + 1].strip()):
                    is_flight = True
                    day_info = None
                    flight_num = line
                    data_start_offset = 1  # Route starts at i+1

            # Case 3: MD-11 format - Bare numeric flight number (3-4 digits)
            elif not has_day_pattern and re.match(r'^\d{3,4}$', line):
                # Verify next line is a route (with optional suffix like (C))
                if i + 1 < len(lines) and re.match(r'^[A-Z]{3}-[A-Z]{3}(\([A-Z]\))?$', lines[i + 1].strip()):
                    is_flight = True
                    day_info = None
                    flight_num = line
                    data_start_offset = 1  # Route starts at i+1

            if is_flight:
                # Parse flight data
                flight_data = {
                    'day': None,
                    'flight': '',
                    'route': '',
                    'depart': '',
                    'arrive': '',
                    'block': '',
                    'connection': ''
                }

                if is_single_line:
                    # SINGLE-LINE FORMAT: Parse all data from one line
                    # Pattern: "1 (Su)Su UPS5969 ONT-SDF (06)14:30 (13)18:10 3h40 76P 1h48 1/1/0 Block 6h19 ..."

                    # Extract day pattern (everything before flight number)
                    day_match = re.match(r'^(\d+\s+\([^)]*\)\S*)', line)
                    if day_match:
                        flight_data['day'] = day_match.group(1)

                    # Extract flight number
                    flight_match = re.search(r'((?:UPS|GT|DH)\s*\S+)', line, re.IGNORECASE)
                    if flight_match:
                        flight_data['flight'] = flight_match.group(1)

                    # Extract route
                    route_match = re.search(r'([A-Z]{3}-[A-Z]{3})', line)
                    if route_match:
                        flight_data['route'] = route_match.group(1)

                    # Extract times (depart and arrive)
                    time_matches = re.findall(r'\((\d+)\)(\d{2}:\d{2})', line)
                    if len(time_matches) >= 1:
                        flight_data['depart'] = f"({time_matches[0][0]}){time_matches[0][1]}"
                    if len(time_matches) >= 2:
                        flight_data['arrive'] = f"({time_matches[1][0]}){time_matches[1][1]}"

                    # Extract block time (first time duration after times)
                    block_match = re.search(r'(\d+h\d+)', line)
                    if block_match:
                        flight_data['block'] = block_match.group(1)

                    # Extract connection time (second time duration)
                    conn_matches = re.findall(r'(\d+h\d+)', line)
                    if len(conn_matches) >= 2:
                        flight_data['connection'] = conn_matches[1]

                    # Extract Block subtotal if present (duty day total)
                    # Pattern: "... Block 6h19 ..."
                    block_total_match = re.search(r'\bBlock\s+(\d+h\d+)', line)
                    if block_total_match and not current_duty['block_total']:
                        current_duty['block_total'] = block_total_match.group(1)

                    # Extract Credit if present (duty day total)
                    # Pattern: "... Credit 6h32L ..."
                    # BUT NOT "Credit Time:" (that's trip summary)
                    if not current_duty['credit'] and 'Credit Time:' not in line:
                        credit_match = re.search(r'\bCredit\s+(\S+)', line)
                        if credit_match:
                            current_duty['credit'] = credit_match.group(1)

                    current_duty['flights'].append(flight_data)
                    i += 1  # Move to next line
                    continue

                else:
                    # MULTI-LINE FORMAT: Parse fields from sequential lines
                    flight_data['day'] = day_info
                    flight_data['flight'] = flight_num

                    # Read expected fields one by one
                    offset = data_start_offset

                    # Route (required, may have suffix like (C))
                    if i + offset < len(lines):
                        potential_route = lines[i + offset].strip()
                        route_match = re.match(r'^([A-Z]{3}-[A-Z]{3})(\([A-Z]\))?$', potential_route)
                        if route_match:
                            flight_data['route'] = route_match.group(1)  # Capture route without suffix
                            offset += 1

                    # Depart time
                    if i + offset < len(lines):
                        potential_depart = lines[i + offset].strip()
                        if re.match(r'\(\d+\)\d{2}:\d{2}', potential_depart):
                            flight_data['depart'] = potential_depart
                            offset += 1

                    # Arrive time
                    if i + offset < len(lines):
                        potential_arrive = lines[i + offset].strip()
                        if re.match(r'\(\d+\)\d{2}:\d{2}', potential_arrive):
                            flight_data['arrive'] = potential_arrive
                            offset += 1

                    # Block time
                    if i + offset < len(lines):
                        potential_block = lines[i + offset].strip()
                        if re.match(r'\d+h\d+', potential_block):
                            flight_data['block'] = potential_block
                            offset += 1

                    # Aircraft type (skip if present - we don't store it)
                    # It's usually 2-3 characters like "75P", "76P", "76M"
                    if i + offset < len(lines):
                        potential_aircraft = lines[i + offset].strip()
                        if re.match(r'^[0-9]{2}[A-Z]$', potential_aircraft):
                            offset += 1

                    # Connection time (look ahead a bit if needed)
                    max_look_ahead = 3
                    for look in range(max_look_ahead):
                        if i + offset + look >= len(lines):
                            break
                        potential_conn = lines[i + offset + look].strip()
                        if re.match(r'^\d+h\d+$', potential_conn):
                            flight_data['connection'] = potential_conn
                            offset += look + 1
                            break

                    # Crew needs field (usually "1/1/0" format) - skip if present
                    if i + offset < len(lines):
                        potential_crew = lines[i + offset].strip()
                        if re.match(r'^\d+/\d+/\d+$', potential_crew):
                            offset += 1

                    current_duty['flights'].append(flight_data)

                    # KEY: Skip past all the flight data we just read
                    # This prevents re-processing and works regardless of format variations
                    i += offset
                    continue

            # MARKER-BASED DUTY SUMMARY DETECTION
            # These use exact label matching, safe regardless of structure

            # Duty time
            if line == 'Duty' and i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if re.match(r'\d+h\d+', next_line):
                    current_duty['duty_time'] = next_line

            # Block total
            # Handle both formats:
            # 1. Block on its own line: "Block" followed by "4h50"
            # 2. Block embedded in flight line: "... Block 4h53 ..."
            if not current_duty['block_total']:
                if line == 'Block' and i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if re.match(r'\d+h\d+', next_line):
                        current_duty['block_total'] = next_line
                else:
                    # Try to extract Block from within the line
                    block_match = re.search(r'\bBlock\s+(\d+h\d+)', line)
                    if block_match:
                        current_duty['block_total'] = block_match.group(1)

            # Credit
            # Handle both standalone "Credit" line and embedded "Credit XXX" pattern
            if not current_duty['credit']:
                if line == 'Credit' and i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line and next_line != '-':
                        current_duty['credit'] = next_line
                else:
                    # Try to extract Credit from within the line
                    # But NOT if it's "Credit Time:" (that's trip summary)
                    if 'Credit Time:' not in line:
                        credit_match = re.search(r'\bCredit\s+(\S+)', line)
                        if credit_match:
                            current_duty['credit'] = credit_match.group(1)

            # Rest/Layover
            if line == 'Rest' and i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line and next_line != '-':
                    current_duty['rest'] = next_line

        i += 1

    # Append last duty day
    if current_duty:
        duty_days.append(current_duty)

    # Parse trip summary
    # Handles both formats:
    # - Multi-line: Label on one line, value on next
    # - Single-line: Label and value on same line (e.g., "Credit Time: 6h00M")
    trip_summary = {}
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Try to extract value from same line first (single-line format)
        # Then fall back to next line (multi-line format)

        # Credit Time
        if 'Credit Time:' in line:
            match = re.search(r'Credit Time:\s*(\S+)', line)
            if match:
                trip_summary['Credit'] = match.group(1)
            elif i + 1 < len(lines):
                trip_summary['Credit'] = lines[i + 1].strip()

        # Block Time
        if 'Block Time:' in line:
            match = re.search(r'Block Time:\s*(\S+)', line)
            if match:
                trip_summary['Blk'] = match.group(1)
            elif i + 1 < len(lines):
                trip_summary['Blk'] = lines[i + 1].strip()

        # Duty Time (trip summary, not duty day summary)
        if 'Duty Time:' in line and 'Summary' not in lines[max(0, i-5):i+1]:
            match = re.search(r'Duty Time:\s*(\S+)', line)
            if match:
                trip_summary['Duty Time'] = match.group(1)
            elif i + 1 < len(lines):
                trip_summary['Duty Time'] = lines[i + 1].strip()

        # TAFB
        if 'TAFB:' in line:
            match = re.search(r'TAFB:\s*(\S+)', line)
            if match:
                trip_summary['TAFB'] = match.group(1)
            elif i + 1 < len(lines):
                trip_summary['TAFB'] = lines[i + 1].strip()

        # Premium
        if 'Premium:' in line:
            match = re.search(r'Premium:\s*(\S+)', line)
            if match:
                trip_summary['Prem'] = match.group(1)
            elif i + 1 < len(lines):
                trip_summary['Prem'] = lines[i + 1].strip()

        # Per Diem
        if 'per Diem:' in line:
            match = re.search(r'per Diem:\s*(\S+)', line)
            if match:
                trip_summary['PDiem'] = match.group(1)
            elif i + 1 < len(lines):
                trip_summary['PDiem'] = lines[i + 1].strip()

        # LDGS
        if 'LDGS' in line:
            match = re.search(r'LDGS\s+(\d+)', line)
            if match:
                trip_summary['LDGS'] = match.group(1)
            elif i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line.isdigit():
                    trip_summary['LDGS'] = next_line

        # Domicile
        if 'Domicile:' in line:
            match = re.search(r'Domicile:\s*(\S+)', line)
            if match:
                trip_summary['Domicile'] = match.group(1)
            elif i + 1 < len(lines):
                trip_summary['Domicile'] = lines[i + 1].strip()

        # Crew has value on same line
        if 'Crew:' in line:
            match = re.search(r'Crew:\s*(\S+)', line)
            if match:
                trip_summary['Crew'] = match.group(1)

        i += 1

    # Count duty days
    trip_summary['Duty Days'] = str(len(duty_days))

    return {
        'trip_id': trip_id,
        'date_freq': date_freq,
        'duty_days': duty_days,
        'trip_summary': trip_summary
    }


def format_trip_details(trip_text):
    """
    Parse and format trip text into structured data for display.
    Returns a dictionary with formatted sections including duty days.
    """
    lines = trip_text.split('\n')

    # Extract header info
    trip_id = parse_trip_id(trip_text)

    # Find date/frequency line
    date_freq = None
    for line in lines:
        if re.search(r'\d+\s+trips?\)', line, re.IGNORECASE):
            date_freq = line.strip()
            break

    # Parse duty days - track sections between Briefing and Debriefing
    duty_days = []
    current_duty = None
    current_flight = None

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Start of duty day
        if re.search(r'\bBriefing\b', line, re.IGNORECASE):
            if current_duty:
                duty_days.append(current_duty)
            current_duty = {
                'briefing': None,
                'debriefing': None,
                'flights': [],
                'duty_time': None,
                'block_time': None,
                'credit': None,
                'rest': None
            }
            # Next line should have briefing time
            if i + 1 < len(lines):
                current_duty['briefing'] = lines[i + 1].strip()

        # Flight number
        elif current_duty and re.match(r'^UPS\s*\d+$', line, re.IGNORECASE):
            current_flight = {'flight': line}
            current_duty['flights'].append(current_flight)

        # Route (XXX-XXX)
        elif current_flight and re.match(r'^[A-Z]{3}-[A-Z]{3}$', line):
            current_flight['route'] = line
            # Look ahead for start time, end time, block time, aircraft
            if i + 1 < len(lines):
                current_flight['start'] = lines[i + 1].strip()
            if i + 2 < len(lines):
                current_flight['end'] = lines[i + 2].strip()
            if i + 3 < len(lines):
                current_flight['block'] = lines[i + 3].strip()
            if i + 4 < len(lines):
                current_flight['aircraft'] = lines[i + 4].strip()
            if i + 5 < len(lines):
                current_flight['connection'] = lines[i + 5].strip()

        # Debriefing
        elif current_duty and re.search(r'\bDebriefing\b', line, re.IGNORECASE):
            if i + 1 < len(lines):
                current_duty['debriefing'] = lines[i + 1].strip()

        # Duty time
        elif current_duty and re.search(r'Duty\s+(\d+h\d+)', line, re.IGNORECASE):
            match = re.search(r'Duty\s+(\d+h\d+)', line, re.IGNORECASE)
            current_duty['duty_time'] = match.group(1)

        # Block time (in duty summary)
        elif current_duty and re.search(r'Block\s+(\d+h\d+)', line, re.IGNORECASE):
            match = re.search(r'Block\s+(\d+h\d+)', line, re.IGNORECASE)
            if not current_duty['block_time']:
                current_duty['block_time'] = match.group(1)

        # Credit
        elif current_duty and re.search(r'Credit\s+(\S+)', line, re.IGNORECASE):
            match = re.search(r'Credit\s+(\S+)', line, re.IGNORECASE)
            current_duty['credit'] = match.group(1)

        # Rest period
        elif current_duty and re.search(r'Rest\s+(\S+)', line, re.IGNORECASE):
            match = re.search(r'Rest\s+(.+)', line, re.IGNORECASE)
            current_duty['rest'] = match.group(1).strip()

        i += 1

    if current_duty:
        duty_days.append(current_duty)

    # Extract trip-level summary
    trip_summary = {}
    for line in lines:
        if 'TAFB:' in line:
            match = re.search(r'TAFB:\s*(\S+)', line)
            if match:
                trip_summary['TAFB'] = match.group(1)
        if 'Credit Time:' in line:
            match = re.search(r'Credit Time:\s*(\S+)', line)
            if match:
                trip_summary['Credit Time'] = match.group(1)
        if 'Block Time:' in line and 'Block Time:' not in [k for k in trip_summary.keys()]:
            match = re.search(r'Block Time:\s*(\S+)', line)
            if match:
                trip_summary['Block Time'] = match.group(1)
        if 'Duty Time:' in line:
            match = re.search(r'Duty Time:\s*(\S+)', line)
            if match:
                trip_summary['Duty Time'] = match.group(1)
        if 'Premium:' in line:
            match = re.search(r'Premium:\s*(\S+)', line)
            if match:
                trip_summary['Premium'] = match.group(1)
        if 'per Diem:' in line or 'Per Diem:' in line:
            match = re.search(r'[Pp]er [Dd]iem:\s*(\S+)', line)
            if match:
                trip_summary['Per Diem'] = match.group(1)
        if 'LDGS' in line:
            match = re.search(r'LDGS\s+(\d+)', line)
            if match:
                trip_summary['Landings'] = match.group(1)

    return {
        'trip_id': trip_id,
        'date_freq': date_freq,
        'duty_days': duty_days,
        'trip_summary': trip_summary
    }


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
        duty_day_details = parse_duty_day_details(trip_text)

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

    # Duty Day Statistics - calculate from duty_day_details (excluding Hot Standby)
    all_duty_days = []
    edw_duty_days = []
    non_edw_duty_days = []

    # Filter out Hot Standby trips to be consistent with distribution charts
    for _, row in df_trips[~df_trips["Hot Standby"]].iterrows():
        duty_day_details = row["Duty Day Details"]
        frequency = row["Frequency"]

        # Each duty day detail appears 'frequency' times
        for duty_day in duty_day_details:
            for _ in range(frequency):
                all_duty_days.append(duty_day)
                if duty_day.get('is_edw', False):
                    edw_duty_days.append(duty_day)
                else:
                    non_edw_duty_days.append(duty_day)

    # Calculate averages
    avg_legs_all = sum(dd['num_legs'] for dd in all_duty_days) / len(all_duty_days) if all_duty_days else 0
    avg_legs_edw = sum(dd['num_legs'] for dd in edw_duty_days) / len(edw_duty_days) if edw_duty_days else 0
    avg_legs_non_edw = sum(dd['num_legs'] for dd in non_edw_duty_days) / len(non_edw_duty_days) if non_edw_duty_days else 0

    avg_duration_all = sum(dd['duration_hours'] for dd in all_duty_days) / len(all_duty_days) if all_duty_days else 0
    avg_duration_edw = sum(dd['duration_hours'] for dd in edw_duty_days) / len(edw_duty_days) if edw_duty_days else 0
    avg_duration_non_edw = sum(dd['duration_hours'] for dd in non_edw_duty_days) / len(non_edw_duty_days) if non_edw_duty_days else 0

    avg_block_all = sum(dd['block_hours'] for dd in all_duty_days) / len(all_duty_days) if all_duty_days else 0
    avg_block_edw = sum(dd['block_hours'] for dd in edw_duty_days) / len(edw_duty_days) if edw_duty_days else 0
    avg_block_non_edw = sum(dd['block_hours'] for dd in non_edw_duty_days) / len(non_edw_duty_days) if non_edw_duty_days else 0

    avg_credit_all = sum(dd['credit_hours'] for dd in all_duty_days) / len(all_duty_days) if all_duty_days else 0
    avg_credit_edw = sum(dd['credit_hours'] for dd in edw_duty_days) / len(edw_duty_days) if edw_duty_days else 0
    avg_credit_non_edw = sum(dd['credit_hours'] for dd in non_edw_duty_days) / len(non_edw_duty_days) if non_edw_duty_days else 0

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

    duty_day_stats = pd.DataFrame({
        "Metric": [
            "Avg Legs/Duty Day",
            "Avg Duty Day Length",
            "Avg Block Time",
            "Avg Credit Time",
        ],
        "All": [
            f"{avg_legs_all:.2f}",
            f"{avg_duration_all:.2f}h",
            f"{avg_block_all:.2f}h",
            f"{avg_credit_all:.2f}h",
        ],
        "EDW": [
            f"{avg_legs_edw:.2f}",
            f"{avg_duration_edw:.2f}h",
            f"{avg_block_edw:.2f}h",
            f"{avg_credit_edw:.2f}h",
        ],
        "Non-EDW": [
            f"{avg_legs_non_edw:.2f}",
            f"{avg_duration_non_edw:.2f}h",
            f"{avg_block_non_edw:.2f}h",
            f"{avg_credit_non_edw:.2f}h",
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
        "Duty Day Statistics": duty_day_stats,
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





