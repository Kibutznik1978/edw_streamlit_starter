import re
import unicodedata
from pathlib import Path
from io import BytesIO
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Set backend for headless environments (Streamlit Cloud)
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

    A duty day is defined as text between "Briefing" and "Debriefing".
    Legs are counted as lines matching flight numbers like:
    - UPS flights: "UPS 986" or "UPS2344"
    - Deadhead flights: "DH AA1820", "DH WN2969", "DH DL1342"
    - Ground transport: "GT N/A BUS G"

    Example: A trip with duty days containing 2, 1, and 4 legs would return 4.
    """
    # Split text into lines
    lines = trip_text.split('\n')

    legs_per_duty_day = []
    current_duty_legs = 0
    in_duty = False

    for line in lines:
        # Check if we're starting a duty day
        if re.search(r'\bBriefing\b', line, re.IGNORECASE):
            in_duty = True
            current_duty_legs = 0
        # Check if we're ending a duty day
        elif re.search(r'\bDebriefing\b', line, re.IGNORECASE):
            if in_duty:
                legs_per_duty_day.append(current_duty_legs)
                in_duty = False
                current_duty_legs = 0
        # Count flight legs - look for UPS, DH (deadhead), or GT (ground transport)
        elif in_duty:
            # Match patterns like:
            # - "UPS 986" or "UPS2344" (operating flights - with or without space)
            # - "DH AA1820" or "DH WN2969" (deadhead flights)
            # - "GT N/A BUS G" (ground transportation)
            stripped = line.strip()
            # Match UPS/DH/GT followed by space, digit, or other chars (no space requirement)
            if re.match(r'^(UPS|DH|GT)(\s|\d|N/A)', stripped, re.IGNORECASE):
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
        {'day': 1, 'duration_hours': 7.73, 'num_legs': 2, 'is_edw': True},
        {'day': 2, 'duration_hours': 12.5, 'num_legs': 3, 'is_edw': False},
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
        # Start of a new duty day
        if re.search(r'\bBriefing\b', line, re.IGNORECASE):
            if current_duty_day:
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
                'is_edw': False
            }

        # End of duty day - capture duration by searching between briefing and debriefing
        elif current_duty_day and re.search(r'\bDebriefing\b', line, re.IGNORECASE):
            # Search backwards from debriefing to briefing for "Duty" label
            # Pattern: "Duty" followed by "XhY" format on next line
            if briefing_line_idx is not None:
                for j in range(briefing_line_idx, i):
                    duty_match = re.match(r'^\s*Duty\s*$', lines[j].strip(), re.IGNORECASE)
                    if duty_match and j + 1 < len(lines):
                        time_match = re.match(r'(\d+)h(\d+)', lines[j + 1].strip())
                        if time_match:
                            hours = int(time_match.group(1))
                            mins = int(time_match.group(2))
                            current_duty_day['duration_hours'] = round(hours + mins / 60.0, 2)
                            break

        # Count flight legs within duty day
        elif current_duty_day:
            stripped = line.strip()
            # Match UPS/DH/GT followed by space, digit, or other chars
            if re.match(r'^(UPS|DH|GT)(\s|\d|N/A)', stripped, re.IGNORECASE):
                current_duty_day['num_legs'] += 1

    # Don't forget the last duty day
    if current_duty_day:
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
    Returns duty days with flights and summaries.
    """
    lines = trip_text.split('\n')

    trip_id = parse_trip_id(trip_text)

    # Find date/frequency line
    date_freq = None
    for line in lines:
        # Look for frequency like "(5 trips)" or date patterns like "Only on..." or "02Dec2025-10Dec2025"
        if (re.search(r'\d+\s+trips?\)', line, re.IGNORECASE) or
            re.search(r'Only on|^\d{2}\w{3}\d{4}', line, re.IGNORECASE)):
            date_freq = line.strip()
            break

    duty_days = []
    current_duty = None
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # Start of duty day (Briefing marker)
        if re.search(r'\bBriefing\b', line, re.IGNORECASE):
            if current_duty:
                duty_days.append(current_duty)

            # Capture briefing time from next line
            duty_start = None
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if re.match(r'\(\d+\)\d{2}:\d{2}', next_line):
                    duty_start = next_line

            current_duty = {
                'flights': [],
                'duty_start': duty_start,
                'duty_end': None,
                'duty_time': None,
                'block_total': None,
                'credit': None,
                'rest': None
            }
            i += 1
            continue

        # End of duty day (Debriefing marker)
        if current_duty and re.search(r'\bDebriefing\b', line, re.IGNORECASE):
            # Capture debriefing time from next line
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if re.match(r'\(\d+\)\d{2}:\d{2}', next_line):
                    current_duty['duty_end'] = next_line
            # Don't append yet - we might have more info like duty time, rest, etc.
            i += 1
            continue

        # Inside a duty day
        if current_duty is not None:
            # Look for flight pattern: day indicator followed by flight number
            # Pattern: "1 (  )   " or "1 (Mo)Tu " followed by "UPS 986"
            day_pattern = re.match(r'^\d+\s+\(', line)
            if day_pattern and i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                # Check if next line is a flight number (UPS, GT, or DH)
                if re.match(r'^(UPS|GT|DH)', next_line, re.IGNORECASE):
                    # This is a flight with day indicator
                    day_info = line
                    flight_num = next_line

                    # Next line should be route
                    if i + 2 < len(lines) and re.match(r'^[A-Z]{3}-[A-Z]{3}$', lines[i + 2].strip()):
                        route = lines[i + 2].strip()
                        depart = lines[i + 3].strip() if i + 3 < len(lines) else ''
                        arrive = lines[i + 4].strip() if i + 4 < len(lines) else ''
                        block = lines[i + 5].strip() if i + 5 < len(lines) and re.match(r'\d+h\d+', lines[i + 5].strip()) else ''
                        # Connection time is usually at i + 7 (after aircraft type)
                        connection = lines[i + 7].strip() if i + 7 < len(lines) and re.match(r'\d+h\d+', lines[i + 7].strip()) else ''

                        current_duty['flights'].append({
                            'day': day_info,
                            'flight': flight_num,
                            'route': route,
                            'depart': depart,
                            'arrive': arrive,
                            'block': block,
                            'connection': connection
                        })
                        # Skip past this flight's data (route, times, block, aircraft, connection, crew needs)
                        i += 9
                        continue

            # Look for flight number without day pattern (continuation of same day)
            elif re.match(r'^(UPS|GT|DH)', line, re.IGNORECASE):
                # Check if this is actually a new flight (not already processed)
                # Next line should be route
                if i + 1 < len(lines) and re.match(r'^[A-Z]{3}-[A-Z]{3}$', lines[i + 1].strip()):
                    flight_num = line
                    route = lines[i + 1].strip()
                    depart = lines[i + 2].strip() if i + 2 < len(lines) else ''
                    arrive = lines[i + 3].strip() if i + 3 < len(lines) else ''
                    block = lines[i + 4].strip() if i + 4 < len(lines) and re.match(r'\d+h\d+', lines[i + 4].strip()) else ''
                    connection = lines[i + 6].strip() if i + 6 < len(lines) and re.match(r'\d+h\d+', lines[i + 6].strip()) else ''

                    current_duty['flights'].append({
                        'day': None,
                        'flight': flight_num,
                        'route': route,
                        'depart': depart,
                        'arrive': arrive,
                        'block': block,
                        'connection': connection
                    })
                    # Skip past this flight's data
                    i += 8
                    continue

            # Capture duty summary info
            # Check if line is "Duty" and next line has time
            if line == 'Duty' and i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if re.match(r'\d+h\d+', next_line):
                    current_duty['duty_time'] = next_line

            # Check if line is "Block" and next line has time
            if line == 'Block' and i + 1 < len(lines) and not current_duty['block_total']:
                next_line = lines[i + 1].strip()
                if re.match(r'\d+h\d+', next_line):
                    current_duty['block_total'] = next_line

            # Check if line is "Credit" and next line has value
            if line == 'Credit' and i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line and next_line != '-':
                    current_duty['credit'] = next_line

            # Check if line is "Rest" and next line has value
            if line == 'Rest' and i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line and next_line != '-':
                    current_duty['rest'] = next_line

        i += 1

    if current_duty:
        duty_days.append(current_duty)

    # Extract trip summary
    trip_summary = {}
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Crew has value on same line
        if 'Crew:' in line:
            match = re.search(r'Crew:\s*(\S+)', line)
            if match:
                trip_summary['Crew'] = match.group(1)

        # Most fields have value on next line
        if line == 'Domicile:' and i + 1 < len(lines):
            trip_summary['Domicile'] = lines[i + 1].strip()

        if line == 'Credit Time:' and i + 1 < len(lines):
            trip_summary['Credit'] = lines[i + 1].strip()

        if line == 'Block Time:' and i + 1 < len(lines):
            trip_summary['Blk'] = lines[i + 1].strip()

        if line == 'Duty Time:' and i + 1 < len(lines):
            # Only capture if not already captured from duty day summary
            if 'Duty Time' not in trip_summary:
                trip_summary['Duty Time'] = lines[i + 1].strip()

        if line == 'Premium:' and i + 1 < len(lines):
            trip_summary['Prem'] = lines[i + 1].strip()

        if line == 'per Diem:' and i + 1 < len(lines):
            trip_summary['PDiem'] = lines[i + 1].strip()

        if line == 'TAFB:' and i + 1 < len(lines):
            trip_summary['TAFB'] = lines[i + 1].strip()

        if line == 'LDGS' and i + 1 < len(lines):
            next_val = lines[i + 1].strip()
            if next_val.isdigit():
                trip_summary['LDGS'] = next_val

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
        "trip_text_map": trip_text_map,
    }





