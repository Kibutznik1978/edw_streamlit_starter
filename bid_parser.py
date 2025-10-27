"""Utilities for parsing bid line PDFs into structured tabular data."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, Iterable, IO, List, Optional, Sequence, Tuple, Dict, Any

import pandas as pd
import pdfplumber

from config import RESERVE_DAY_KEYWORDS, SHIFTABLE_RESERVE_KEYWORD, VTO_KEYWORDS

# Regex used by legacy/fallback parsing
LINE_RE = re.compile(
    r"(?P<line_id>\d{1,4})\s+"
    r"(?P<ct>\d{2,3}\.\d)\s+"
    r"(?P<bt>\d{2,3}\.\d)\s+"
    r"(?P<do>\d{1,2})\s+"
    r"(?P<dd>\d{1,2})"
)

_TABLE_SETTINGS = {
    "vertical_strategy": "lines",
    "horizontal_strategy": "text",
}
PAY_PERIOD_RE = re.compile(
    r"(?:PP|P0P\d*|[P0O]{1,2})\s*(?P<period>[12])\s*\((?P<code>[^\)]+)\)(?P<body>.*?)(?=(?:PP|P0P\d*|[P0O]{1,2})\s*[12]\s*\([^\)]+\)|$)",
    re.IGNORECASE | re.DOTALL,
)



_BLOCK_SEPARATOR_RE = re.compile(r"Comment:\s*", re.IGNORECASE)
_BLOCK_HEADER_RE = re.compile(r"^[A-Z]{2,}\s+(?P<line>\d{1,4})\b", re.MULTILINE)

# Build regex patterns dynamically from config keywords
_VTO_PATTERN_RE = re.compile(r"\b(" + "|".join(VTO_KEYWORDS) + r")\b", re.IGNORECASE)
_RESERVE_DAY_PATTERN_RE = re.compile(r"\b(" + "|".join(RESERVE_DAY_KEYWORDS) + r")\b", re.IGNORECASE)
_SHIFTABLE_RESERVE_RE = re.compile(re.escape(SHIFTABLE_RESERVE_KEYWORD), re.IGNORECASE)
_HOT_STANDBY_RE = re.compile(r"\b(HSBY|HOT\s*STANDBY|HOTSTANDBY)\b", re.IGNORECASE)
_AVAILABILITY_PATTERN_RE = re.compile(r"(\d+)/(\d+)/(\d+)")
_CREW_COMPOSITION_RE = re.compile(r"^[A-Z]{2,}\s+\d{1,4}\s+(\d+)/(\d+)/(\d+)/?", re.MULTILINE)


@dataclass
class ParseDiagnostics:
    """Metadata describing how a PDF was parsed."""

    used_text: bool
    used_tables: bool
    warnings: List[str]
    pay_periods: Optional[pd.DataFrame] = None
    reserve_lines: Optional[pd.DataFrame] = None  # DataFrame with columns: Line, IsReserve, IsHotStandby, CaptainSlots, FOSlots


def extract_bid_line_header_info(pdf_file: IO[bytes]) -> Dict[str, Any]:
    """
    Extract header information from a bid line PDF.
    Checks the first page, and if header info is not found, checks the second page.

    Extracts:
    - Bid Period (e.g., "2507")
    - Bid Period Date Range (e.g., "02Nov2025 - 30Nov2025")
    - Domicile (e.g., "ONT")
    - Fleet Type (e.g., "757")
    - Date/Time (e.g., "26Sep2025 11:35")

    Args:
        pdf_file: File-like object containing the PDF data

    Returns:
        Dictionary with keys: bid_period, bid_period_date_range, domicile, fleet_type, date_time
        Returns None for any field that cannot be extracted.
    """
    pdf_file.seek(0)

    result = {
        "bid_period": None,
        "bid_period_date_range": None,
        "domicile": None,
        "fleet_type": None,
        "date_time": None
    }

    # Helper function to extract header info from page text
    def extract_from_text(text, current_result):
        extracted = current_result.copy()

        # Extract Bid Period (e.g., "Bid Period : 2507")
        if extracted["bid_period"] is None:
            bid_period_match = re.search(r"Bid\s+Period\s*:?\s*(\d{4})", text, re.IGNORECASE)
            if bid_period_match:
                extracted["bid_period"] = bid_period_match.group(1)

        # Extract Bid Period Date Range (e.g., "Bid Period Date Range: 02Nov2025 - 30Nov2025")
        if extracted["bid_period_date_range"] is None:
            date_range_match = re.search(
                r"Bid\s+Period\s+Date\s+Range\s*:?\s*(\d{2}[A-Za-z]{3}\d{4}\s*-\s*\d{2}[A-Za-z]{3}\d{4})",
                text,
                re.IGNORECASE
            )
            if date_range_match:
                extracted["bid_period_date_range"] = date_range_match.group(1)

        # Extract Domicile (e.g., "Domicile: ONT")
        if extracted["domicile"] is None:
            domicile_match = re.search(r"Domicile\s*:?\s*([A-Z]{3})", text, re.IGNORECASE)
            if domicile_match:
                extracted["domicile"] = domicile_match.group(1).upper()

        # Extract Fleet Type (e.g., "Fleet Type: 757")
        if extracted["fleet_type"] is None:
            fleet_match = re.search(r"Fleet\s+Type\s*:?\s*([\w\-]+)", text, re.IGNORECASE)
            if fleet_match:
                extracted["fleet_type"] = fleet_match.group(1)

        # Extract Date/Time (e.g., "Date/Time: 26Sep2025 11:35")
        if extracted["date_time"] is None:
            datetime_match = re.search(
                r"Date/Time\s*:?\s*(\d{2}[A-Za-z]{3}\d{4}\s+\d{1,2}:\d{2})",
                text,
                re.IGNORECASE
            )
            if datetime_match:
                extracted["date_time"] = datetime_match.group(1)

        return extracted

    try:
        with pdfplumber.open(pdf_file) as pdf:
            if not pdf.pages:
                return result

            # Try extracting from first page
            first_page_text = pdf.pages[0].extract_text()
            if first_page_text:
                result = extract_from_text(first_page_text, result)

            # If any critical fields are still None, try second page
            if (result["bid_period"] is None or
                result["domicile"] is None or
                result["fleet_type"] is None) and len(pdf.pages) >= 2:
                second_page_text = pdf.pages[1].extract_text()
                if second_page_text:
                    result = extract_from_text(second_page_text, result)

    except Exception:
        # Silently return partial results if extraction fails
        pass

    return result


def parse_bid_lines(
    pdf_file: IO[bytes],
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> Tuple[pd.DataFrame, ParseDiagnostics]:
    """Parse a bid roster PDF into a DataFrame of line statistics.

    Args:
        pdf_file: File-like object containing the PDF data
        progress_callback: Optional callback function(current_page, total_pages) to report progress
    """

    pdf_file.seek(0)

    block_records: List[dict] = []
    fallback_records: List[dict] = []
    table_records: List[dict] = []
    warnings: List[str] = []
    reserve_info: List[dict] = []  # Track reserve line information

    with pdfplumber.open(pdf_file) as pdf:
        total_pages = len(pdf.pages)

        for index, page in enumerate(pdf.pages, start=1):
            if progress_callback:
                progress_callback(index, total_pages)

            records, block_warnings, page_reserve_info = _parse_line_blocks(page, index)
            if records:
                block_records.extend(records)
            if page_reserve_info:
                reserve_info.extend(page_reserve_info)
            warnings.extend(block_warnings)

            if not records:
                lines = _extract_page_lines(page)
                if lines:
                    fallback_records.extend(_parse_lines_from_text(lines))

            for table in page.extract_tables(table_settings=_TABLE_SETTINGS) or []:
                table_records.extend(_parse_lines_from_table(table))

    if block_records:
        primary_records = block_records
        allowed_table_lines = {record["Line"] for record in block_records}
        table_records = []
    else:
        primary_records = fallback_records
        allowed_table_lines = None

    if allowed_table_lines is not None and table_records:
        table_records = [record for record in table_records if record["Line"] in allowed_table_lines]

    merged_records, diag_warnings = _merge_records(primary_records, table_records, allowed_table_lines)
    warnings.extend(diag_warnings)

    if not merged_records:
        # Provide helpful error message for wrong PDF type
        raise ValueError(
            "❌ No valid bid lines found in PDF.\n\n"
            "**Possible causes:**\n"
            "- This might be a **Pairing PDF** (should be uploaded to Tab 1: EDW Pairing Analyzer)\n"
            "- The PDF format may not be supported\n"
            "- The PDF may be corrupted or empty\n\n"
            "**Expected format:** Bid Line PDF with Line numbers, CT, BT, DO, DD values"
        )

    else:
        raw_df = pd.DataFrame(merged_records)
        if "Period" in raw_df.columns and raw_df["Period"].notna().any():
            pay_period_df = raw_df.sort_values(["Line", "Period"]).reset_index(drop=True)
            df, pay_periods_output = _aggregate_pay_periods(pay_period_df)
        else:
            pay_periods_output = pd.DataFrame(columns=["Line", "Period", "PayPeriodCode", "CT", "BT", "DO", "DD"])
            df = raw_df.sort_values("Line").reset_index(drop=True)
            expected_cols = [col for col in ["Line", "CT", "BT", "DO", "DD"] if col in df.columns]
            df = df[expected_cols]

    # Create reserve lines DataFrame
    reserve_df = None
    if reserve_info:
        reserve_df = pd.DataFrame(reserve_info)
        # Remove duplicates (same line might appear on multiple pages)
        reserve_df = reserve_df.drop_duplicates(subset=["Line"]).reset_index(drop=True)

    diagnostics = ParseDiagnostics(
        used_text=bool(primary_records),
        used_tables=bool(table_records),
        warnings=warnings,
        pay_periods=pay_periods_output if not pay_periods_output.empty else None,
        reserve_lines=reserve_df,
    )
    return df, diagnostics


def _detect_reserve_line(block: str) -> Tuple[bool, bool, int, int]:
    """Detect if a line is a reserve line or hot standby and extract captain/FO slot counts.

    Returns:
        Tuple of (is_reserve, is_hot_standby, captain_slots, fo_slots)
    """
    # Check for Hot Standby patterns first (HSBY, HOT STANDBY, etc.)
    is_hot_standby = bool(_HOT_STANDBY_RE.search(block))

    # Check for reserve day patterns (RA, SA, RB, SB, RC, SC, RD, SD)
    has_reserve_days = bool(_RESERVE_DAY_PATTERN_RE.search(block))

    # Check for "SHIFTABLE RESERVE" in comments
    has_shiftable_reserve = bool(_SHIFTABLE_RESERVE_RE.search(block))

    # Check for CT:0.00 BT:0.00 pattern (DD:14 might be missing)
    # Allow both "0:00" and "0.00" formats
    ct_zero = re.search(r"CT\s*:?\s*0+[:\.]0+", block, re.IGNORECASE)
    bt_zero = re.search(r"BT\s*:?\s*0+[:\.]0+", block, re.IGNORECASE)
    dd_fourteen = re.search(r"DD\s*:?\s*14\b", block, re.IGNORECASE)

    # Reserve if CT=0 AND BT=0 (with or without DD:14)
    has_zero_credit_block = bool(ct_zero and bt_zero)

    # Also consider DD:14 even if CT/BT aren't explicitly zero (might be malformed)
    has_reserve_metrics = has_zero_credit_block or (ct_zero and dd_fourteen) or (bt_zero and dd_fourteen)

    is_reserve = has_reserve_days or has_shiftable_reserve or has_reserve_metrics

    # Extract availability pattern (e.g., 1/1/0 means 1 captain, 1 FO)
    captain_slots = 0
    fo_slots = 0
    availability_match = _AVAILABILITY_PATTERN_RE.search(block)
    if availability_match and is_reserve:
        try:
            captain_slots = int(availability_match.group(1))
            fo_slots = int(availability_match.group(2))
            # Third number is typically other/unassigned, we can ignore it
        except (ValueError, IndexError):
            pass

    return is_reserve, is_hot_standby, captain_slots, fo_slots


def _extract_crew_composition(block: str) -> Tuple[int, int]:
    """Extract crew composition (captain/FO slots) from a line block.

    Looks for the pattern x/x/x/ after the line header (e.g., "ONT 40 1/1/0/")
    where first number = captain slots, second = FO slots, third = ignored

    Args:
        block: The text block containing the line data

    Returns:
        Tuple of (captain_slots, fo_slots) where values are 0 or 1 for regular lines
    """
    # Try the more specific crew composition pattern first (right after line header)
    crew_match = _CREW_COMPOSITION_RE.search(block)
    if crew_match:
        try:
            captain_slots = int(crew_match.group(1))
            fo_slots = int(crew_match.group(2))
            # Third group is ignored (old F/E position, no longer used)
            return captain_slots, fo_slots
        except (ValueError, IndexError):
            pass

    # Fallback to general availability pattern (used for reserve lines)
    availability_match = _AVAILABILITY_PATTERN_RE.search(block)
    if availability_match:
        try:
            captain_slots = int(availability_match.group(1))
            fo_slots = int(availability_match.group(2))
            return captain_slots, fo_slots
        except (ValueError, IndexError):
            pass

    # Default: if not found, assume available to both (1/1)
    return 0, 0


def _detect_split_vto_line(block: str, period_records: List[dict]) -> Tuple[bool, Optional[str], Optional[int]]:
    """Detect if a line is a split VTO/VTOR/VOR line (one period regular, one period VTO).

    Args:
        block: The text block containing the line data
        period_records: List of pay period records parsed from the block

    Returns:
        Tuple of (is_split, vto_type, vto_period) where:
        - is_split: True if one period has data and one is all zeros
        - vto_type: "VTO", "VTOR", or "VOR" (or None if not split)
        - vto_period: 1 or 2 indicating which period is VTO (or None if not split)
    """
    # Check if block mentions VTO/VTOR/VOR
    vto_match = _VTO_PATTERN_RE.search(block)
    if not vto_match:
        return False, None, None

    vto_type = vto_match.group(1).upper()  # VTO, VTOR, or VOR

    # If we don't have exactly 2 pay periods, it's not a split line
    if len(period_records) != 2:
        return False, None, None

    # Check each period to see if one is all zeros
    period_1 = period_records[0]
    period_2 = period_records[1]

    # Helper to check if a period has all zero values
    def is_zero_period(record):
        ct = record.get("CT", 0) or 0
        bt = record.get("BT", 0) or 0
        do = record.get("DO", 0) or 0
        dd = record.get("DD", 0) or 0
        return ct == 0 and bt == 0 and do == 0 and dd == 0

    # Helper to check if a period has actual data
    def has_data(record):
        ct = record.get("CT", 0) or 0
        bt = record.get("BT", 0) or 0
        return ct > 0 or bt > 0

    period_1_zero = is_zero_period(period_1)
    period_2_zero = is_zero_period(period_2)
    period_1_has_data = has_data(period_1)
    period_2_has_data = has_data(period_2)

    # Split line: one period has data, the other is all zeros
    if period_1_has_data and period_2_zero:
        return True, vto_type, 2
    elif period_2_has_data and period_1_zero:
        return True, vto_type, 1

    # Not a split line (either both have data or both are zero)
    return False, None, None


def _parse_line_blocks(page: pdfplumber.page.Page, page_number: int) -> Tuple[List[dict], List[str], List[dict]]:
    """Parse line blocks from a page.

    Returns:
        Tuple of (records, warnings, reserve_info)
        where reserve_info is a list of dicts with keys: Line, IsReserve, CaptainSlots, FOSlots
    """
    text = page.extract_text() or ""
    if not text:
        return [], [f"No text extracted from page {page_number}."], []

    segments = _BLOCK_SEPARATOR_RE.split(text)
    if len(segments) <= 1:
        return [], [], []

    records: List[dict] = []
    warnings: List[str] = []
    reserve_info: List[dict] = []

    merged_segments = _merge_headerless_segments(segments[1:])

    for block in merged_segments:
        block_records, block_warnings = _parse_block_text(block, page_number)
        if block_records:
            records.extend(block_records)

            # Detect reserve line status for this block
            line_id = block_records[0]["Line"]  # All records in block have same line ID
            is_reserve, is_hot_standby, captain_slots, fo_slots = _detect_reserve_line(block)
            reserve_info.append({
                "Line": line_id,
                "IsReserve": is_reserve,
                "IsHotStandby": is_hot_standby,
                "CaptainSlots": captain_slots,
                "FOSlots": fo_slots,
            })
        warnings.extend(block_warnings)

    return records, warnings, reserve_info



def _merge_headerless_segments(segments: Sequence[str]) -> List[str]:
    merged: List[str] = []
    current_parts: List[str] = []

    for raw_block in segments:
        block = raw_block.strip()
        if not block:
            continue

        has_header = bool(_BLOCK_HEADER_RE.search(block))
        if has_header:
            if current_parts:
                merged.append("\n".join(current_parts))
            current_parts = [block]
        else:
            if current_parts:
                current_parts.append(block)
            else:
                current_parts = [block]

    if current_parts:
        merged.append("\n".join(current_parts))

    return merged



def _parse_block_text(block: str, page_number: int) -> Tuple[List[dict], List[str]]:
    warnings: List[str] = []

    header_match = _BLOCK_HEADER_RE.search(block)
    if not header_match:
        warnings.append(_format_warning(page_number, block, "Missing line header"))
        return [], warnings

    line_id = int(header_match.group("line"))

    # Extract crew composition (Captain/FO slots) for this line
    captain_slots, fo_slots = _extract_crew_composition(block)

    period_records: List[dict] = []
    matches = list(PAY_PERIOD_RE.finditer(block))
    if matches:
        # Check if this is a reserve line
        is_reserve, _, _, _ = _detect_reserve_line(block)

        for match in matches:
            segment = match.group(0)
            period = int(match.group("period").strip())
            code = match.group("code").strip()

            ct_value = _extract_time_field(segment, "CT")
            bt_value = _extract_time_field(segment, "BT")
            do_value = _extract_int_field(segment, "DO")
            dd_value = _extract_int_field(segment, "DD")

            # For reserve lines, DO might be missing - that's okay, default to 0
            if is_reserve and do_value is None:
                do_value = 0

            fields_missing = [label for label, value in [("CT", ct_value), ("BT", bt_value), ("DO", do_value), ("DD", dd_value)] if value is None]
            if fields_missing:
                warnings.append(
                    _format_warning(
                        page_number,
                        segment,
                        f"Missing fields for PP{period}: {', '.join(fields_missing)}",
                    )
                )
                continue

            period_records.append(
                {
                    "Line": line_id,
                    "Period": period,
                    "PayPeriodCode": code,
                    "CT": ct_value,
                    "BT": bt_value,
                    "DO": do_value,
                    "DD": dd_value,
                    "CaptainSlots": captain_slots,
                    "FOSlots": fo_slots,
                }
            )

    if period_records:
        # Check if this is a split VTO/VTOR/VOR line
        is_split, vto_type, vto_period = _detect_split_vto_line(block, period_records)

        if is_split:
            # This is a split line - add VTO metadata to all records
            for record in period_records:
                record["VTOType"] = vto_type
                record["VTOPeriod"] = vto_period
            return period_records, warnings
        elif _VTO_PATTERN_RE.search(block):
            # This is a VTO line but not split (both periods are VTO) - skip it
            return [], []
        else:
            # Regular line with no VTO
            for record in period_records:
                record["VTOType"] = None
                record["VTOPeriod"] = None
            return period_records, warnings

    # Fallback: treat block as a single-period entry

    # Skip VTO/VTOR/VOR lines in fallback (single-period VTO lines)
    if _VTO_PATTERN_RE.search(block):
        return [], []

    ct_value = _extract_time_field(block, "CT")
    bt_value = _extract_time_field(block, "BT")
    do_value = _extract_int_field(block, "DO")
    dd_value = _extract_int_field(block, "DD")

    # Check if this is a reserve line (CT=0, BT=0, or has reserve indicators)
    is_reserve, _, _, _ = _detect_reserve_line(block)

    # For reserve lines, DO (Days Off) might be missing - that's okay, default to 0
    if is_reserve and do_value is None:
        do_value = 0

    fields_missing = [label for label, value in [("CT", ct_value), ("BT", bt_value), ("DO", do_value), ("DD", dd_value)] if value is None]
    if fields_missing:
        warnings.append(
            _format_warning(
                page_number,
                block,
                f"Missing fields: {', '.join(fields_missing)}",
            )
        )
        return [], warnings

    record = {
        "Line": line_id,
        "Period": 1,
        "PayPeriodCode": None,
        "CT": ct_value,
        "BT": bt_value,
        "DO": do_value,
        "DD": dd_value,
        "CaptainSlots": captain_slots,
        "FOSlots": fo_slots,
        "VTOType": None,
        "VTOPeriod": None,
    }
    return [record], warnings


def _extract_time_field(block: str, label: str) -> Optional[float]:
    # First try exact match
    pattern = re.compile(rf"{label}\s*:?\s*([0-9]{{1,3}}:[0-9]{{2}})")
    match = pattern.search(block)
    if match:
        return _time_to_hours(match.group(1))

    # Fallback for corrupted labels (common in PP2 segments due to PDF extraction issues):
    # Look for patterns like "CHTX:", "CSTD:", "LCFTT:", "CT:F", "CHTA:N" etc.
    # where label letters are mixed with other characters
    if label == "CT":
        # Try to find a time value near any C*T* pattern
        # Look for patterns like: CT:F 82:45, CHTA:N 81:12, CT:N 83:02, CT:F 8R2A:45
        # Pattern allows for letters/spaces between CT and colon, and after colon
        flexible_pattern = re.compile(r"[A-Z\s]*C[A-Z\s]*T[A-Z]*\s*:[A-Z\s]*\s*([0-9]+:[0-9]{2})", re.IGNORECASE)
        match = flexible_pattern.search(block)
        if match:
            time_str = match.group(1)
            # Validate it's a proper time format
            if re.match(r"^[0-9]{1,3}:[0-9]{2}$", time_str):
                return _time_to_hours(time_str)

        # Also try matching heavily corrupted formats like "8R2A:45" where digits are mixed with letters
        # Look for C*T* followed by colon, then any mix of letters/digits, then colon and 2 digits
        corrupted_pattern = re.compile(r"[A-Z\s]*C[A-Z\s]*T[A-Z]*\s*:[A-Z\s]*\s*([0-9A-Z]+:[0-9]{2})", re.IGNORECASE)
        match = corrupted_pattern.search(block)
        if match:
            time_str = match.group(1)
            # Clean out letters, keeping only digits and colon
            cleaned = re.sub(r"[^0-9:]", "", time_str)
            if re.match(r"^[0-9]{1,3}:[0-9]{2}$", cleaned):
                return _time_to_hours(cleaned)

    elif label == "BT":
        # Similar pattern for BT
        flexible_pattern = re.compile(r"[A-Z\s]*B[A-Z\s]*T[A-Z]*\s*:[A-Z\s]*\s*([0-9]+:[0-9]{2})", re.IGNORECASE)
        match = flexible_pattern.search(block)
        if match:
            time_str = match.group(1)
            if re.match(r"^[0-9]{1,3}:[0-9]{2}$", time_str):
                return _time_to_hours(time_str)

        # Corrupted BT patterns
        corrupted_pattern = re.compile(r"[A-Z\s]*B[A-Z\s]*T[A-Z]*\s*:\s*([0-9A-Z]+:[0-9]{2})", re.IGNORECASE)
        match = corrupted_pattern.search(block)
        if match:
            time_str = match.group(1)
            cleaned = re.sub(r"[^0-9:]", "", time_str)
            if re.match(r"^[0-9]{1,3}:[0-9]{2}$", cleaned):
                return _time_to_hours(cleaned)

    return None


def _extract_int_field(block: str, label: str) -> Optional[int]:
    pattern = re.compile(rf"{label}\s*:?\s*(\d{{1,2}})")
    match = pattern.search(block)
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def _time_to_hours(value: str) -> float:
    hours_str, minutes_str = value.split(":", 1)
    hours = int(hours_str)
    minutes = int(minutes_str)
    return round(hours + minutes / 60.0, 2)


def _format_warning(page_number: int, block: str, message: str) -> str:
    snippet = " ".join(block.split())[:80]
    return f"Page {page_number}: {message} -> {snippet}"


def _extract_page_lines(page: pdfplumber.page.Page) -> List[str]:
    collected: List[str] = []
    primary_text = page.extract_text() or ""
    if primary_text:
        collected.extend(primary_text.splitlines())

    if len(collected) < 5:
        for line in _extract_column_text(page):
            if line not in collected:
                collected.append(line)

    return collected


def _extract_column_text(page: pdfplumber.page.Page) -> List[str]:
    width = getattr(page, "width", None)
    height = getattr(page, "height", None)
    if not width or not height:
        return []

    column_lines: List[str] = []
    mid = width / 2
    gutter = width * 0.02
    bboxes = [
        (0, 0, max(mid - gutter, 0), height),
        (min(mid + gutter, width), 0, width, height),
    ]

    for bbox in bboxes:
        try:
            cropped = page.within_bbox(bbox)
        except Exception:  # pragma: no cover - guard for pdfplumber edge cases
            continue
        if not cropped:
            continue
        text = cropped.extract_text() or ""
        if text:
            column_lines.extend(text.splitlines())
    return column_lines


def _aggregate_pay_periods(pay_period_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    if pay_period_df.empty:
        empty = pd.DataFrame(columns=["Line", "CT", "BT", "DO", "DD"])
        return empty, pay_period_df

    tidy = pay_period_df.dropna(subset=["Period"]).copy()
    if tidy.empty:
        tidy = pay_period_df.copy()

    tidy["Period"] = tidy["Period"].astype(int)
    value_cols = ["CT", "BT", "DO", "DD"]
    metrics = tidy[value_cols].apply(pd.to_numeric, errors="coerce").fillna(0)
    mask_vto = metrics.abs().sum(axis=1) == 0
    filtered = tidy.loc[~mask_vto].copy()

    base = filtered if not filtered.empty else tidy

    aggregated = base.groupby("Line")[value_cols].mean()

    metric_pivot = base.pivot_table(index="Line", columns="Period", values=value_cols, aggfunc="first")
    if not metric_pivot.empty:
        metric_pivot = metric_pivot.sort_index(axis=1, level=1)
        for metric, period in metric_pivot.columns:
            aggregated[f"{metric}_PP{int(period)}"] = metric_pivot[(metric, period)]

    if "PayPeriodCode" in base.columns:
        code_pivot = base.pivot_table(index="Line", columns="Period", values="PayPeriodCode", aggfunc="first")
        if not code_pivot.empty:
            code_pivot = code_pivot.sort_index(axis=1)
            for period in code_pivot.columns:
                aggregated[f"PayPeriodCode_PP{int(period)}"] = code_pivot[period]

    # Convert Line from index to column
    aggregated = aggregated.reset_index()

    # Add crew composition if present (CaptainSlots and FOSlots should be same for all periods of a line)
    if "CaptainSlots" in tidy.columns and "FOSlots" in tidy.columns:
        crew_info = tidy.groupby("Line").agg({
            "CaptainSlots": "first",
            "FOSlots": "first"
        }).reset_index()
        aggregated = aggregated.merge(crew_info, on="Line", how="left")

    # Add VTO metadata if present (using original tidy data which includes VTO periods)
    if "VTOType" in tidy.columns:
        # Get VTO info from the original data (before filtering)
        vto_info = tidy.groupby("Line").agg({
            "VTOType": "first",
            "VTOPeriod": "first"
        }).reset_index()
        aggregated = aggregated.merge(vto_info, on="Line", how="left")

    column_order = ["Line", "CT", "BT", "DO", "DD"] + [
        col for col in aggregated.columns if col not in {"Line", "CT", "BT", "DO", "DD"}
    ]
    aggregated = aggregated[column_order]
    used_periods = base.reset_index(drop=True)
    return aggregated, used_periods



def _parse_lines_from_text(lines: Iterable[str]) -> List[dict]:
    records: List[dict] = []
    for candidate in _normalized_candidates(lines):
        # Skip lines with VTO/VTOR/VOR mentions
        if _VTO_PATTERN_RE.search(candidate):
            continue
        matches = list(LINE_RE.finditer(candidate))
        if not matches:
            continue
        for match in matches:
            try:
                records.append(_match_to_record(match))
            except ValueError:
                continue
    return records


def _normalized_candidates(lines: Iterable[str]) -> Iterable[str]:
    buffer: Optional[str] = None
    for raw_line in lines:
        stripped = raw_line.strip()
        if not stripped or stripped.lower().startswith("line "):
            continue

        normalized = re.sub(r"\s+", " ", stripped)
        if buffer:
            combined = f"{buffer} {normalized}".strip()
            if LINE_RE.search(combined):
                yield combined
                buffer = None
                continue
            buffer = combined
            if len(buffer.split()) > 10:
                buffer = None
            continue

        if LINE_RE.search(normalized):
            yield normalized
        else:
            buffer = normalized

    if buffer and LINE_RE.search(buffer):
        yield buffer


def _match_to_record(match: re.Match) -> dict:
    return {
        "Line": int(match.group("line_id")),
        "CT": float(match.group("ct")),
        "BT": float(match.group("bt")),
        "DO": int(match.group("do")),
        "DD": int(match.group("dd")),
        "CaptainSlots": 0,
        "FOSlots": 0,
    }


def _parse_lines_from_table(table: Sequence[Sequence[Optional[str]]]) -> List[dict]:
    records: List[dict] = []
    for row in table:
        if not row:
            continue
        cells = [re.sub(r"\s+", " ", cell).strip() for cell in row if cell]
        if not cells or cells[0].lower().startswith("line"):
            continue
        if len(cells) < 5:
            continue
        # Check if any cell contains VTO/VTOR/VOR (typically in comment column)
        row_text = " ".join(str(cell) for cell in row if cell)
        if _VTO_PATTERN_RE.search(row_text):
            continue
        maybe_record = _cells_to_record(cells)
        if maybe_record:
            records.append(maybe_record)
    return records


def _cells_to_record(cells: Sequence[str]) -> Optional[dict]:
    try:
        line_id = int(re.sub(r"[^\d]", "", cells[0]))
        ct_val = float(_normalize_numeric(cells[1]))
        bt_val = float(_normalize_numeric(cells[2]))
        do_val = int(_normalize_numeric(cells[3], allow_float=False))
        dd_val = int(_normalize_numeric(cells[4], allow_float=False))
    except (ValueError, IndexError):
        return None
    return {
        "Line": line_id,
        "CT": ct_val,
        "BT": bt_val,
        "DO": do_val,
        "DD": dd_val,
        "CaptainSlots": 0,
        "FOSlots": 0,
    }


def _normalize_numeric(value: str, allow_float: bool = True) -> str:
    cleaned = value.replace("O", "0").replace("o", "0")
    cleaned = re.sub(r"[^\d\.]+", "", cleaned)
    if not allow_float:
        cleaned = cleaned.split(".")[0]
    return cleaned


def _merge_records(text_records: List[dict], table_records: List[dict], allowed_table_lines: Optional[set[int]] = None) -> Tuple[List[dict], List[str]]:
    merged: dict[int, dict] = {}
    warnings: List[str] = []

    table_source = table_records
    if allowed_table_lines is not None:
        table_source = [record for record in table_records if record["Line"] in allowed_table_lines]

    for record in table_source:
        key = (record["Line"], record.get("Period"))
        merged[key] = record

    for record in text_records:
        key = (record["Line"], record.get("Period"))
        if key in merged and merged[key] != record:
            warnings.append(f"Conflicting data for line {record['Line']}; using text extraction.")
        merged[key] = record

    if not merged:
        warnings.append("No line entries detected in the document.")

    return list(merged.values()), warnings
