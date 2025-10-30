"""
PDF parsing and text extraction module for EDW analysis.

This module contains all functions related to reading and parsing pairing PDFs,
extracting trip data, duty day information, and other metrics.
"""

import re
import unicodedata
from pathlib import Path
from PyPDF2 import PdfReader


# -------------------------------------------------------------------
# Text Sanitizer
# -------------------------------------------------------------------
def clean_text(text: str) -> str:
    """
    Normalize Unicode and sanitize special characters for PDF/Excel compatibility.

    Args:
        text: Input text string

    Returns:
        Sanitized text with normalized Unicode and replaced special characters
    """
    if not isinstance(text, str):
        return text
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\u00A0", " ")
    text = re.sub(r"[■•▪●]", "-", text)
    return text


# -------------------------------------------------------------------
# PDF Header Extraction
# -------------------------------------------------------------------
def extract_pdf_header_info(pdf_path: Path):
    """
    Extract bid period, domicile, fleet type, and date range from PDF header.
    Checks the first page, and if header info is not found, checks the second page.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Dictionary with extracted information:
        {
            'bid_period': str,
            'domicile': str,
            'fleet_type': str,
            'date_range': str,
            'report_date': str
        }
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
# PDF Parsing
# -------------------------------------------------------------------
def parse_pairings(pdf_path: Path, progress_callback=None):
    """
    Extract individual trip/pairing texts from PDF.

    Stops parsing when it reaches "Open Trips Report" section to avoid
    duplicate trips that are in open time.

    Args:
        pdf_path: Path to the PDF file
        progress_callback: Optional callback function(progress, message) for progress updates

    Returns:
        List of trip text strings (only assigned pairings, not open time)
    """
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
        # Stop parsing when we hit "Open Trips Report" section
        # This section contains duplicate trips in open time that we don't need
        if re.search(r"Open\s+Trips?\s+Report", line, re.IGNORECASE):
            # Save the current trip if we have one
            if current_trip and in_trip:
                trips.append("\n".join(current_trip))
            if progress_callback:
                progress_callback(45, f"Stopped at 'Open Trips Report' - found {len(trips)} pairings")
            break  # Stop parsing - we've reached open time duplicates

        if re.match(r"^\s*Trip\s*Id", line, re.IGNORECASE):
            if current_trip:
                trips.append("\n".join(current_trip))
            current_trip = [line]  # Start new trip with the Trip Id line
            in_trip = True
        elif in_trip:
            current_trip.append(line)
    else:
        # Loop completed without break - add final trip if we have one
        if current_trip and in_trip:
            trips.append("\n".join(current_trip))

    return trips


# -------------------------------------------------------------------
# Time and Metric Extraction
# -------------------------------------------------------------------
def extract_local_times(trip_text):
    """
    Extract all local times from trip text.

    Local times are in the format (HH)MM:SS where HH is the local hour.

    Args:
        trip_text: Raw trip text

    Returns:
        List of time strings in HH:MM format
    """
    times = []
    pattern = re.compile(r"\((\d{1,2})\)(\d{2}):(\d{2})")
    for match in pattern.finditer(trip_text):
        local_hour = int(match.group(1))
        minute = int(match.group(3))
        times.append(f"{local_hour:02d}:{minute:02d}")
    return times


def parse_trip_id(trip_text):
    """
    Extract the Trip ID number from trip text.

    Args:
        trip_text: Raw trip text

    Returns:
        Trip ID as integer, or None if not found
    """
    m = re.search(r"Trip\s*Id:\s*(\d+)", trip_text, re.IGNORECASE)
    if m:
        return int(m.group(1))
    return None


def parse_tafb(trip_text):
    """
    Extract TAFB (Time Away From Base) in hours.

    Args:
        trip_text: Raw trip text

    Returns:
        TAFB hours as float
    """
    m = re.search(r"TAFB:\s*(\d+)h(\d+)", trip_text)
    if not m:
        return 0.0
    hours = int(m.group(1))
    mins = int(m.group(2))
    return hours + mins / 60.0


def parse_duty_days(trip_text):
    """
    Count the number of duty days in a trip.

    Args:
        trip_text: Raw trip text

    Returns:
        Number of duty days as integer
    """
    duty_blocks = re.findall(r"(?i)Duty\s+\d+h\d+", trip_text)
    return len(duty_blocks)


def parse_max_duty_day_length(trip_text):
    """
    Extract all duty day lengths from trip text and return the maximum length in hours.

    Args:
        trip_text: Raw trip text

    Returns:
        Maximum duty day length in hours as float, 0.0 if no duty days found

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

    A duty day is defined as text between "Briefing" and "Debriefing" (or fallback patterns).
    Handles both PDF formats:
    - Multi-line: Flight numbers on separate lines ("UPS 986")
    - Single-line: Flight data on one line ("1 (Su)Su UPS5969 ONT-SDF ...")
    - Fallback: Older PDFs without Briefing/Debriefing keywords

    Args:
        trip_text: Raw trip text

    Returns:
        Maximum legs per duty day as integer, 0 if no legs found

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


def parse_duty_day_details(trip_text, is_edw_func):
    """
    Extract detailed information for each duty day in a trip.

    Args:
        trip_text: Raw trip text
        is_edw_func: Function to determine if a duty day is EDW (from analyzer module)

    Returns:
        List of dictionaries, one per duty day:
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
                    current_duty_day['is_edw'] = is_edw_func(duty_day_text)
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
            current_duty_day['is_edw'] = is_edw_func(duty_day_text)
        duty_day_details.append(current_duty_day)

    return duty_day_details


def parse_trip_frequency(trip_text):
    """
    Extract how many times this trip runs from the date range line.

    Args:
        trip_text: Raw trip text

    Returns:
        Frequency as integer (defaults to 1 if not found)

    Looks for patterns like "(5 trips)" or "(4 trips)"
    """
    m = re.search(r"\((\d+)\s+trips?\)", trip_text, re.IGNORECASE)
    if m:
        return int(m.group(1))
    # If no frequency found, assume it runs once
    return 1


def parse_trip_for_table(trip_text, is_edw_func):
    """
    Parse trip text into a structured format for table display.
    Uses MARKER-BASED PARSING for robustness across different PDF formats.

    This version doesn't rely on fixed line skip counts, making it more resilient
    to format variations between different flight types (UPS, GT, DH) and PDF templates.

    Args:
        trip_text: Raw trip text
        is_edw_func: Function to determine if text is EDW (from analyzer module)

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

    Args:
        trip_text: Raw trip text

    Returns:
        Dictionary with formatted sections including duty days
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
