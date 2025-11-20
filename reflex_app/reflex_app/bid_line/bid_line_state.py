"""Bid Line Analyzer State Management.

This module manages the state for the Bid Line Analyzer,
including PDF upload, processing, data editing, filtering, and exports.
"""

import asyncio
import contextlib
import math
from io import BytesIO
import reflex as rx
from typing import Optional, Dict, List, Any, Tuple, Set
from pathlib import Path
import tempfile
import pandas as pd
import sys

from ..database.base_state import DatabaseState

# Add path to import from root directory modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from bid_parser import parse_bid_lines, extract_bid_line_header_info, ParseDiagnostics
from pdf_generation import ReportMetadata, create_bid_line_pdf_report
from config.validation import (
    CT_MAX_WARNING, BT_MAX_WARNING, DO_MAX_WARNING, DD_MAX_WARNING,
    CT_RANGE_MIN, CT_RANGE_MAX, BT_RANGE_MIN, BT_RANGE_MAX,
    DO_RANGE_MIN, DO_RANGE_MAX, DD_RANGE_MIN, DD_RANGE_MAX
)


class BidLineState(DatabaseState):
    """State management for Bid Line Analyzer."""

    # ========== Upload State ==========
    uploaded_file_name: str = ""
    is_processing: bool = False
    processing_progress: int = 0
    processing_message: str = ""
    upload_error: str = ""

    # ========== Header Information ==========
    domicile: str = ""
    aircraft: str = ""
    bid_period: str = ""
    date_range: str = ""
    date_time: str = ""

    # ========== Data State ==========
    # Original data (never modified after parsing)
    original_data_json: List[Dict[str, Any]] = []

    # Edited data (contains user modifications)
    edited_data_json: List[Dict[str, Any]] = []

    # Reserve lines information
    reserve_lines_json: List[Dict[str, Any]] = []

    # Pay period information (if available)
    pay_periods_json: List[Dict[str, Any]] = []

    # Diagnostics from parsing
    parse_warnings: List[str] = []
    used_text_parsing: bool = False
    used_table_parsing: bool = False

    # ========== Filter State ==========
    # Credit Time (CT) filter
    filter_ct_min: float = CT_RANGE_MIN
    filter_ct_max: float = CT_RANGE_MAX

    # Block Time (BT) filter
    filter_bt_min: float = BT_RANGE_MIN
    filter_bt_max: float = BT_RANGE_MAX

    # Days Off (DO) filter
    filter_do_min: int = DO_RANGE_MIN
    filter_do_max: int = DO_RANGE_MAX

    # Duty Days (DD) filter
    filter_dd_min: int = DD_RANGE_MIN
    filter_dd_max: int = DD_RANGE_MAX

    # ========== Edit Tracking State ==========
    # List of cell changes: [{row_idx, column, old_value, new_value}]
    edited_cells: List[Dict[str, Any]] = []

    # Validation warnings for edited data
    validation_warnings: List[str] = []

    # Advanced edit mode (allows editing all columns)
    advanced_edit_mode: bool = False

    # UI state: whether the Change History card is expanded
    change_history_expanded: bool = False

    # ========== Statistics State ==========
    # Basic statistics (computed from filtered data)
    ct_min: float = 0.0
    ct_max: float = 0.0
    ct_mean: float = 0.0
    ct_median: float = 0.0

    bt_min: float = 0.0
    bt_max: float = 0.0
    bt_mean: float = 0.0
    bt_median: float = 0.0

    do_min: int = 0
    do_max: int = 0
    do_mean: float = 0.0
    do_median: float = 0.0

    dd_min: int = 0
    dd_max: int = 0
    dd_mean: float = 0.0
    dd_median: float = 0.0

    # Pay period statistics (if pay period data available)
    pp1_ct_mean: float = 0.0
    pp2_ct_mean: float = 0.0
    pp1_bt_mean: float = 0.0
    pp2_bt_mean: float = 0.0
    pp1_do_mean: float = 0.0
    pp2_do_mean: float = 0.0
    pp1_dd_mean: float = 0.0
    pp2_dd_mean: float = 0.0

    # Reserve line statistics
    reserve_captain_slots: int = 0
    reserve_fo_slots: int = 0
    hot_standby_captain_slots: int = 0
    hot_standby_fo_slots: int = 0
    gateway_standby_summary: List[Dict[str, Any]] = []
    reserve_line_count: int = 0
    hot_standby_line_count: int = 0
    airport_standby_line_count: int = 0
    gateway_standby_line_count: int = 0
    regular_captain_lines: int = 0
    regular_fo_lines: int = 0
    vto_full_captain_lines: int = 0
    vto_full_fo_lines: int = 0
    vto_split_captain_lines: int = 0
    vto_split_fo_lines: int = 0
    vtor_captain_lines: int = 0
    vtor_fo_lines: int = 0

    # ========== Save to Database State ==========
    save_status: str = ""  # Success/error message
    save_in_progress: bool = False

    # ========== Notes ==========
    user_notes: str = ""

    # ========== Computed Variables ==========

    @rx.var
    def has_results(self) -> bool:
        """Check if parsed data is available."""
        return len(self.edited_data_json) > 0

    @rx.var
    def has_pay_periods(self) -> bool:
        """Check if pay period data is available."""
        return len(self.pay_periods_json) > 0

    @rx.var
    def has_edits(self) -> bool:
        """Check if user has made any edits."""
        return len(self.edited_cells) > 0

    @rx.var
    def total_lines(self) -> int:
        """Total number of bid lines."""
        return len(self.edited_data_json)

    @rx.var
    def filtered_lines_count(self) -> int:
        """Number of lines after applying filters."""
        return len(self.filtered_data)

    @rx.var
    def filters_active(self) -> bool:
        """Check if any filters are active (differ from defaults)."""
        return (
            self.filter_ct_min != CT_RANGE_MIN or
            self.filter_ct_max != CT_RANGE_MAX or
            self.filter_bt_min != BT_RANGE_MIN or
            self.filter_bt_max != BT_RANGE_MAX or
            self.filter_do_min != DO_RANGE_MIN or
            self.filter_do_max != DO_RANGE_MAX or
            self.filter_dd_min != DD_RANGE_MIN or
            self.filter_dd_max != DD_RANGE_MAX
        )

    @rx.var
    def filtered_data(self) -> List[Dict[str, Any]]:
        """Apply filters to edited data and return filtered list."""
        if not self.edited_data_json:
            return []

        filtered = self.edited_data_json.copy()

        # Apply CT filter
        if self.filter_ct_min > CT_RANGE_MIN or self.filter_ct_max < CT_RANGE_MAX:
            filtered = [
                line for line in filtered
                if self.filter_ct_min <= line.get("CT", 0) <= self.filter_ct_max
            ]

        # Apply BT filter
        if self.filter_bt_min > BT_RANGE_MIN or self.filter_bt_max < BT_RANGE_MAX:
            filtered = [
                line for line in filtered
                if self.filter_bt_min <= line.get("BT", 0) <= self.filter_bt_max
            ]

        # Apply DO filter
        if self.filter_do_min > DO_RANGE_MIN or self.filter_do_max < DO_RANGE_MAX:
            filtered = [
                line for line in filtered
                if self.filter_do_min <= line.get("DO", 0) <= self.filter_do_max
            ]

        # Apply DD filter
        if self.filter_dd_min > DD_RANGE_MIN or self.filter_dd_max < DD_RANGE_MAX:
            filtered = [
                line for line in filtered
                if self.filter_dd_min <= line.get("DD", 0) <= self.filter_dd_max
            ]

        return filtered

    @rx.var
    def table_column_names(self) -> List[str]:
        """Ordered list of available columns for the editor."""
        if not self.edited_data_json:
            return []

        first_row = self.edited_data_json[0]
        return list(first_row.keys())

    @rx.var
    def ct_distribution_data(self) -> List[Dict[str, Any]]:
        """Generate Credit Time distribution data for charts (5-hour buckets)."""
        rows = self._filter_regular_rows(self.filtered_data)
        if not rows:
            return []

        bucket_size = 5
        bins: Dict[str, int] = {}
        for line in rows:
            ct = line.get("CT", 0)
            try:
                val = float(ct)
                if math.isnan(val) or val <= 0:
                    continue
            except (TypeError, ValueError):
                continue
            bin_start = int((val // bucket_size) * bucket_size)
            bin_label = f"{bin_start}-{bin_start + bucket_size}"
            bins[bin_label] = bins.get(bin_label, 0) + 1

        # Convert to list of dicts for Recharts
        result = [{"Range": label, "Count": count} for label, count in sorted(bins.items())]
        return result

    @rx.var
    def bt_distribution_data(self) -> List[Dict[str, Any]]:
        """Generate Block Time distribution data for charts (5-hour buckets)."""
        rows = self._filter_regular_rows(self.filtered_data)
        if not rows:
            return []

        bucket_size = 5
        bins: Dict[str, int] = {}
        for line in rows:
            bt = line.get("BT", 0)
            try:
                val = float(bt)
                if math.isnan(val) or val <= 0:
                    continue
            except (TypeError, ValueError):
                continue
            bin_start = int((val // bucket_size) * bucket_size)
            bin_label = f"{bin_start}-{bin_start + bucket_size}"
            bins[bin_label] = bins.get(bin_label, 0) + 1

        # Convert to list of dicts for Recharts
        result = [{"Range": label, "Count": count} for label, count in sorted(bins.items())]
        return result

    @rx.var
    def do_distribution_data(self) -> List[Dict[str, Any]]:
        """Generate Days Off distribution data for charts.

        Counts occurrences of each discrete value.
        """
        rows = self._filter_regular_rows(self.filtered_data)
        if not rows:
            return []

        # Count occurrences of each DO value
        counts: Dict[int, int] = {}
        min_value = None
        max_value = None

        for line in rows:
            for value in self._collect_metric_values(line, "DO"):
                try:
                    numeric = float(value)
                    if math.isnan(numeric):
                        continue
                    do_value = int(round(numeric))
                except (TypeError, ValueError):
                    continue

                counts[do_value] = counts.get(do_value, 0) + 1
                min_value = do_value if min_value is None else min(min_value, do_value)
                max_value = do_value if max_value is None else max(max_value, do_value)

        if not counts:
            return []

        for value in range(min_value, max_value + 1):
            counts.setdefault(value, 0)

        # Convert to list of dicts for Recharts, sorted by DO value
        result = [{"Days": days, "Count": count} for days, count in sorted(counts.items())]
        return result

    @rx.var
    def dd_distribution_data(self) -> List[Dict[str, Any]]:
        """Generate Duty Days distribution data for charts.

        Counts occurrences of each discrete value.
        """
        rows = self._filter_regular_rows(self.filtered_data)
        if not rows:
            return []

        # Count occurrences of each DD value
        counts: Dict[int, int] = {}
        min_value = None
        max_value = None

        for line in rows:
            for value in self._collect_metric_values(line, "DD"):
                try:
                    numeric = float(value)
                    if math.isnan(numeric):
                        continue
                    dd_value = int(round(numeric))
                except (TypeError, ValueError):
                    continue

                counts[dd_value] = counts.get(dd_value, 0) + 1
                min_value = dd_value if min_value is None else min(min_value, dd_value)
                max_value = dd_value if max_value is None else max(max_value, dd_value)

        if not counts:
            return []

        for value in range(min_value, max_value + 1):
            counts.setdefault(value, 0)

        # Convert to list of dicts for Recharts, sorted by DD value
        result = [{"Days": days, "Count": count} for days, count in sorted(counts.items())]
        return result

    @rx.var
    def ct_distribution_pp1(self) -> List[Dict[str, Any]]:
        """CT distribution data for Pay Period 1."""
        return self._continuous_distribution_by_period("CT", 5)["PP1"]

    @rx.var
    def ct_distribution_pp2(self) -> List[Dict[str, Any]]:
        """CT distribution data for Pay Period 2."""
        return self._continuous_distribution_by_period("CT", 5)["PP2"]

    @rx.var
    def bt_distribution_pp1(self) -> List[Dict[str, Any]]:
        """BT distribution data for Pay Period 1."""
        return self._continuous_distribution_by_period("BT", 5)["PP1"]

    @rx.var
    def bt_distribution_pp2(self) -> List[Dict[str, Any]]:
        """BT distribution data for Pay Period 2."""
        return self._continuous_distribution_by_period("BT", 5)["PP2"]

    @rx.var
    def do_distribution_pp1(self) -> List[Dict[str, Any]]:
        """DO distribution data for Pay Period 1."""
        return self._discrete_distribution_by_period("DO")["PP1"]

    @rx.var
    def do_distribution_pp2(self) -> List[Dict[str, Any]]:
        """DO distribution data for Pay Period 2."""
        return self._discrete_distribution_by_period("DO")["PP2"]

    @rx.var
    def dd_distribution_pp1(self) -> List[Dict[str, Any]]:
        """DD distribution data for Pay Period 1."""
        return self._discrete_distribution_by_period("DD")["PP1"]

    @rx.var
    def dd_distribution_pp2(self) -> List[Dict[str, Any]]:
        """DD distribution data for Pay Period 2."""
        return self._discrete_distribution_by_period("DD")["PP2"]

    @rx.var
    def ct_distribution_max_count(self) -> int:
        """Maximum count across CT distribution charts."""
        return self._max_distribution_count(self.ct_distribution_pp1, self.ct_distribution_pp2)

    @rx.var
    def bt_distribution_max_count(self) -> int:
        """Maximum count across BT distribution charts."""
        return self._max_distribution_count(self.bt_distribution_pp1, self.bt_distribution_pp2)

    @rx.var
    def do_distribution_max_count(self) -> int:
        """Maximum count across DO distribution charts."""
        return self._max_distribution_count(self.do_distribution_pp1, self.do_distribution_pp2)

    @rx.var
    def dd_distribution_max_count(self) -> int:
        """Maximum count across DD distribution charts."""
        return self._max_distribution_count(self.dd_distribution_pp1, self.dd_distribution_pp2)

    @rx.var
    def ct_distribution_y_domain(self) -> Tuple[int, int]:
        max_count = max(1, self.ct_distribution_max_count)
        return (0, max_count + 2)

    @rx.var
    def bt_distribution_y_domain(self) -> Tuple[int, int]:
        max_count = max(1, self.bt_distribution_max_count)
        return (0, max_count + 2)

    @rx.var
    def do_distribution_y_domain(self) -> Tuple[int, int]:
        max_count = max(1, self.do_distribution_max_count)
        return (0, max_count + 2)

    @rx.var
    def dd_distribution_y_domain(self) -> Tuple[int, int]:
        max_count = max(1, self.dd_distribution_max_count)
        return (0, max_count + 2)

    @rx.var
    def ct_edit_count(self) -> int:
        """Count of CT column edits."""
        return sum(1 for edit in self.edited_cells if edit.get("column") == "CT")

    @rx.var
    def bt_edit_count(self) -> int:
        """Count of BT column edits."""
        return sum(1 for edit in self.edited_cells if edit.get("column") == "BT")

    @rx.var
    def do_edit_count(self) -> int:
        """Count of DO column edits."""
        return sum(1 for edit in self.edited_cells if edit.get("column") == "DO")

    @rx.var
    def dd_edit_count(self) -> int:
        """Count of DD column edits."""
        return sum(1 for edit in self.edited_cells if edit.get("column") == "DD")

    @rx.var
    def edited_cell_keys(self) -> List[str]:
        """Return list of keys for edited cells in format 'row_idx:column'.

        Used by editor component to check if a cell has been edited.
        """
        return [f"{edit['row_idx']}:{edit['column']}" for edit in self.edited_cells]

    @rx.var
    def edited_line_numbers(self) -> List[int]:
        """Return list of line numbers that have been edited.

        Used by editor component for row highlighting.
        """
        return list(set(edit.get("line") for edit in self.edited_cells if edit.get("line") is not None))

    # ========== Dynamic Column Headers ==========

    @rx.var
    def has_dual_pay_periods(self) -> bool:
        """Check if data contains dual pay periods (averaged values).

        Returns True if any record has CT_PP2, BT_PP2, etc. columns,
        indicating the data represents averages of two pay periods.
        """
        if not self.edited_data_json:
            return False

        # Check first record for PP2 columns
        first_record = self.edited_data_json[0]
        return "CT_PP2" in first_record or "BT_PP2" in first_record

    @rx.var
    def ct_header(self) -> str:
        """Column header for CT - 'AVG CT' for dual periods, 'CT' for single period."""
        return "AVG CT" if self.has_dual_pay_periods else "CT"

    @rx.var
    def bt_header(self) -> str:
        """Column header for BT - 'AVG BT' for dual periods, 'BT' for single period."""
        return "AVG BT" if self.has_dual_pay_periods else "BT"

    @rx.var
    def do_header(self) -> str:
        """Column header for DO - 'AVG DO' for dual periods, 'DO' for single period."""
        return "AVG DO" if self.has_dual_pay_periods else "DO"

    @rx.var
    def dd_header(self) -> str:
        """Column header for DD - 'AVG DD' for dual periods, 'DD' for single period."""
        return "AVG DD" if self.has_dual_pay_periods else "DD"

    @rx.var
    def averaging_tooltip(self) -> str:
        """Tooltip explaining whether values are averaged or direct."""
        if self.has_dual_pay_periods:
            return "Values shown are averages of two pay periods (PP1 and PP2). Individual period values are shown in separate columns."
        else:
            return "Values shown are from a single pay period."

    # ========== Formatted Statistics (for display) ==========

    @rx.var
    def ct_mean_fmt(self) -> str:
        """CT mean formatted to 2 decimal places."""
        return f"{self.ct_mean:.2f}"

    @rx.var
    def ct_median_fmt(self) -> str:
        """CT median formatted to 2 decimal places."""
        return f"{self.ct_median:.2f}"

    @rx.var
    def bt_mean_fmt(self) -> str:
        """BT mean formatted to 2 decimal places."""
        return f"{self.bt_mean:.2f}"

    @rx.var
    def bt_median_fmt(self) -> str:
        """BT median formatted to 2 decimal places."""
        return f"{self.bt_median:.2f}"

    @rx.var
    def do_mean_fmt(self) -> str:
        """DO mean formatted to 2 decimal places."""
        return f"{self.do_mean:.2f}"

    @rx.var
    def do_median_fmt(self) -> str:
        """DO median formatted to 2 decimal places."""
        return f"{self.do_median:.2f}"

    @rx.var
    def dd_mean_fmt(self) -> str:
        """DD mean formatted to 2 decimal places."""
        return f"{self.dd_mean:.2f}"

    @rx.var
    def dd_median_fmt(self) -> str:
        """DD median formatted to 2 decimal places."""
        return f"{self.dd_median:.2f}"

    @rx.var
    def pp1_ct_mean_fmt(self) -> str:
        """Pay Period 1 CT mean formatted to 2 decimal places."""
        return f"{self.pp1_ct_mean:.2f}"

    @rx.var
    def pp2_ct_mean_fmt(self) -> str:
        """Pay Period 2 CT mean formatted to 2 decimal places."""
        return f"{self.pp2_ct_mean:.2f}"

    @rx.var
    def pp1_bt_mean_fmt(self) -> str:
        """Pay Period 1 BT mean formatted to 2 decimal places."""
        return f"{self.pp1_bt_mean:.2f}"

    @rx.var
    def pp2_bt_mean_fmt(self) -> str:
        """Pay Period 2 BT mean formatted to 2 decimal places."""
        return f"{self.pp2_bt_mean:.2f}"

    @rx.var
    def pp1_do_mean_fmt(self) -> str:
        """Pay Period 1 DO mean formatted to 2 decimal places."""
        return f"{self.pp1_do_mean:.2f}"

    @rx.var
    def pp2_do_mean_fmt(self) -> str:
        """Pay Period 2 DO mean formatted to 2 decimal places."""
        return f"{self.pp2_do_mean:.2f}"

    @rx.var
    def pp1_dd_mean_fmt(self) -> str:
        """Pay Period 1 DD mean formatted to 2 decimal places."""
        return f"{self.pp1_dd_mean:.2f}"

    @rx.var
    def pp2_dd_mean_fmt(self) -> str:
        """Pay Period 2 DD mean formatted to 2 decimal places."""
        return f"{self.pp2_dd_mean:.2f}"

    # Pay period differences (formatted)
    @rx.var
    def pp_ct_diff_fmt(self) -> str:
        """Pay period CT difference formatted to 2 decimal places."""
        diff = self.pp2_ct_mean - self.pp1_ct_mean
        return f"{diff:+.2f}" if diff >= 0 else f"{diff:.2f}"

    @rx.var
    def pp_bt_diff_fmt(self) -> str:
        """Pay period BT difference formatted to 2 decimal places."""
        diff = self.pp2_bt_mean - self.pp1_bt_mean
        return f"{diff:+.2f}" if diff >= 0 else f"{diff:.2f}"

    @rx.var
    def pp_do_diff_fmt(self) -> str:
        """Pay period DO difference formatted to 2 decimal places."""
        diff = self.pp2_do_mean - self.pp1_do_mean
        return f"{diff:+.2f}" if diff >= 0 else f"{diff:.2f}"

    @rx.var
    def pp_dd_diff_fmt(self) -> str:
        """Pay period DD difference formatted to 2 decimal places."""
        diff = self.pp2_dd_mean - self.pp1_dd_mean
        return f"{diff:+.2f}" if diff >= 0 else f"{diff:.2f}"

    # ========== Helper Methods ==========

    def _format_numeric_values(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format numeric values to 2 decimal places to avoid floating point display issues.

        Args:
            data: List of bid line records

        Returns:
            List of records with formatted numeric values
        """
        formatted_data = []
        for record in data:
            formatted_record = {}
            for key, value in record.items():
                # Round floats to 2 decimal places
                if isinstance(value, float):
                    formatted_record[key] = round(value, 2)
                else:
                    formatted_record[key] = value
            formatted_data.append(formatted_record)
        return formatted_data

    # ========== Event Handlers ==========

    async def handle_upload(self, files: List[rx.UploadFile]):
        """Handle PDF file upload and processing."""
        if not files:
            return

        self.upload_error = ""
        self.is_processing = True
        self.processing_progress = 0
        self.processing_message = "Starting PDF processing..."
        yield  # Push initial state to frontend

        parsing_task = None
        try:
            # Read file data
            file = files[0]
            self.uploaded_file_name = file.filename
            file_data = await file.read()

            # Save to temporary file for processing
            tmpdir = Path(tempfile.mkdtemp())
            pdf_path = tmpdir / file.filename
            pdf_path.write_bytes(file_data)

            # Update progress
            self.processing_progress = 10
            self.processing_message = "Extracting header information..."
            yield  # Push progress update

            # Extract header info
            with open(pdf_path, "rb") as f:
                header_info = extract_bid_line_header_info(f)

            self.domicile = header_info.get("domicile", "")
            self.aircraft = header_info.get("fleet_type", "")
            self.bid_period = header_info.get("bid_period", "")
            self.date_range = header_info.get("bid_period_date_range", "")
            self.date_time = header_info.get("date_time", "")

            # Update progress before parsing
            self.processing_progress = 25
            self.processing_message = "Preparing to parse bid lines..."
            yield

            # Parse bid lines with streaming progress updates
            loop = asyncio.get_running_loop()
            progress_queue: asyncio.Queue[Tuple[int, int]] = asyncio.Queue()
            parsing_task = asyncio.create_task(
                asyncio.to_thread(
                    self._parse_pdf_with_progress,
                    pdf_path,
                    loop,
                    progress_queue,
                )
            )

            async for _ in self._consume_parse_progress(progress_queue, parsing_task):
                yield

            df, diagnostics = parsing_task.result()

            # Convert DataFrame to JSON-serializable format and format numeric values
            raw_data = df.to_dict("records")
            formatted_data = self._format_numeric_values(raw_data)

            self.processing_progress = 92
            self.processing_message = "Formatting parsed data..."
            yield

            self.original_data_json = formatted_data
            self.edited_data_json = [dict(record) for record in formatted_data]  # Deep copy

            # Store diagnostics
            self.parse_warnings = diagnostics.warnings
            self.used_text_parsing = diagnostics.used_text
            self.used_table_parsing = diagnostics.used_tables

            # Store pay period data if available
            if diagnostics.pay_periods is not None:
                self.pay_periods_json = diagnostics.pay_periods.to_dict("records")
            else:
                self.pay_periods_json = []

            # Store reserve lines if available
            if diagnostics.reserve_lines is not None:
                self.reserve_lines_json = diagnostics.reserve_lines.to_dict("records")
                # Calculate reserve statistics
                self._calculate_reserve_statistics()
            else:
                self.reserve_lines_json = []
                self._calculate_reserve_statistics()

            # Update line category counts
            self._calculate_line_category_counts()

            # Tag hot standby lines in the main dataset for table display
            self._annotate_hot_standby_lines()

            # Clear any previous edits
            self.edited_cells = []
            self.validation_warnings = []

            # Calculate statistics
            self.processing_progress = 96
            self.processing_message = "Calculating statistics..."
            yield

            self._calculate_statistics()

            # Update progress
            self.processing_progress = 100
            self.processing_message = "Parsing complete!"
            self.is_processing = False
            yield  # Push completion state

        except Exception as e:
            if parsing_task:
                parsing_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await parsing_task
            self.upload_error = f"Error processing PDF: {str(e)}"
            self.is_processing = False
            self.processing_progress = 0
            yield  # Push error state

    def update_cell(self, row_idx: int, column: str, new_value: Any):
        """Handle inline cell edit."""
        if row_idx < 0 or row_idx >= len(self.edited_data_json):
            return

        old_value = self.edited_data_json[row_idx].get(column)

        # Convert numeric columns to proper types
        numeric_columns = [
            "CT", "BT", "DO", "DD", "P_PP1", "DO_PP1", "CT_PP1", "BT_PP1", "DD_PP1",
            "P_PP2", "DO_PP2", "CT_PP2", "BT_PP2", "DD_PP2"
        ]

        if column in numeric_columns and new_value is not None and new_value != "":
            try:
                # Try to convert to float first, then int if it's a whole number
                float_val = float(new_value)
                # For DO and DD, keep as int
                if column in ["DO", "DD", "DO_PP1", "DO_PP2", "DD_PP1", "DD_PP2"]:
                    new_value = int(float_val)
                else:
                    # For CT and BT, keep as float
                    new_value = float_val
            except (ValueError, TypeError):
                # If conversion fails, keep as-is (will be caught by validation)
                pass

        # Update the cell
        self.edited_data_json[row_idx][column] = new_value

        # Track the change
        self.edited_cells.append({
            "row_idx": row_idx,
            "line": self.edited_data_json[row_idx].get("Line"),
            "column": column,
            "old_value": old_value,
            "new_value": new_value
        })

        # Validate the edit
        self._validate_edits()

        # Recalculate statistics
        self._calculate_statistics()

    def reset_edits(self):
        """Reset edited data to original parsed values."""
        self.edited_data_json = [dict(row) for row in self.original_data_json]
        self.edited_cells = []
        self.validation_warnings = []
        self._calculate_statistics()

    def toggle_advanced_edit_mode(self):
        """Toggle advanced edit mode on/off."""
        self.advanced_edit_mode = not self.advanced_edit_mode

    def toggle_change_history(self):
        """Toggle the change history card between collapsed/expanded."""
        self.change_history_expanded = not self.change_history_expanded

    def _get_hot_standby_line_numbers(self) -> Set[int]:
        """Return the set of line numbers flagged as Hot Standby."""
        if not self.reserve_lines_json:
            return set()

        return {
            entry.get("Line")
            for entry in self.reserve_lines_json
            if entry.get("IsHotStandby") and entry.get("Line") is not None
        }

    def _get_regular_reserve_line_numbers(self) -> Set[int]:
        """Return the set of reserve line numbers (excluding HSBY)."""
        if not self.reserve_lines_json:
            return set()

        return {
            entry.get("Line")
            for entry in self.reserve_lines_json
            if entry.get("IsReserve") and not entry.get("IsHotStandby") and entry.get("Line") is not None
        }

    def _get_non_regular_line_numbers(self) -> Set[int]:
        """Lines that should be excluded from regular statistics (reserve + HSBY)."""
        return self._get_regular_reserve_line_numbers() | self._get_hot_standby_line_numbers()

    def _filter_regular_rows(self, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove reserve and HSBY lines from a list of row dictionaries."""
        if not rows:
            return []

        exclude = self._get_non_regular_line_numbers()
        if not exclude:
            return rows

        filtered_rows: List[Dict[str, Any]] = []
        for row in rows:
            line_id = row.get("Line")
            if line_id in exclude:
                continue
            filtered_rows.append(row)
        return filtered_rows

    def _annotate_hot_standby_lines(self):
        """Add/remove the Hot Standby display column on parsed line data."""
        hs_lines = self._get_hot_standby_line_numbers()

        def apply_flag(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            updated_rows: List[Dict[str, Any]] = []
            for row in rows:
                new_row = dict(row)
                if hs_lines and row.get("Line") in hs_lines:
                    new_row["Hot Standby"] = "HSBY"
                elif hs_lines:
                    new_row["Hot Standby"] = ""
                else:
                    new_row.pop("Hot Standby", None)
                updated_rows.append(new_row)
            return updated_rows

        self.original_data_json = apply_flag(self.original_data_json)
        self.edited_data_json = apply_flag(self.edited_data_json)

    def _exclude_non_regular_lines(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove reserve and HSBY lines from DataFrame-based calculations."""
        if df.empty or "Line" not in df.columns:
            return df

        exclude = self._get_non_regular_line_numbers()
        if not exclude:
            return df

        return df[~df["Line"].isin(exclude)]

    def _collect_metric_values(self, row: Dict[str, Any], metric: str) -> List[Any]:
        """Collect per-period metric values for a given row."""
        values: List[Any] = []
        for suffix in ("PP1", "PP2"):
            key = f"{metric}_{suffix}"
            if key in row:
                val = row.get(key)
                if val not in (None, "", "NaN"):
                    values.append(val)

        if not values and metric in row:
            val = row.get(metric)
            if val not in (None, "", "NaN"):
                values.append(val)

        return values

    def _continuous_distribution_by_period(self, metric: str, bucket_size: int) -> Dict[str, List[Dict[str, Any]]]:
        """Build bucketed distributions for CT/BT by pay period."""
        periods = ("PP1", "PP2")
        distribution: Dict[str, List[Dict[str, Any]]] = {p: [] for p in periods}
        has_period_data = False
        rows = self._filter_regular_rows(self.filtered_data)

        for period in periods:
            counts: Dict[str, int] = {}
            for row in rows:
                key = f"{metric}_{period}"
                value = row.get(key)
                if value in (None, "", "NaN"):
                    continue
                try:
                    val = float(value)
                    if math.isnan(val) or val <= 0:
                        continue
                except (TypeError, ValueError):
                    continue

                bucket_start = int((val // bucket_size) * bucket_size)
                label = f"{bucket_start}-{bucket_start + bucket_size}"
                counts[label] = counts.get(label, 0) + 1

            if counts:
                has_period_data = True
                distribution[period] = [{"Range": label, "Count": count} for label, count in sorted(counts.items())]
            else:
                distribution[period] = []

        if not has_period_data:
            fallback_counts: Dict[str, int] = {}
            for row in rows:
                value = row.get(metric)
                if value in (None, "", "NaN"):
                    continue
                try:
                    val = float(value)
                    if math.isnan(val) or val <= 0:
                        continue
                except (TypeError, ValueError):
                    continue
                bucket_start = int((val // bucket_size) * bucket_size)
                label = f"{bucket_start}-{bucket_start + bucket_size}"
                fallback_counts[label] = fallback_counts.get(label, 0) + 1

            distribution["PP1"] = [{"Range": label, "Count": count} for label, count in sorted(fallback_counts.items())]
            distribution["PP2"] = []

        return distribution

    def _discrete_distribution_by_period(self, metric: str) -> Dict[str, List[Dict[str, Any]]]:
        """Build integer day distributions for DO/DD by pay period."""
        periods = ("PP1", "PP2")
        distribution: Dict[str, List[Dict[str, Any]]] = {p: [] for p in periods}
        has_period_data = False
        rows = self._filter_regular_rows(self.filtered_data)

        for period in periods:
            counts: Dict[int, int] = {}
            min_value: Optional[int] = None
            max_value: Optional[int] = None
            for row in rows:
                key = f"{metric}_{period}"
                value = row.get(key)
                if value in (None, "", "NaN"):
                    continue
                try:
                    numeric = float(value)
                    if math.isnan(numeric):
                        continue
                    day_value = int(round(numeric))
                except (TypeError, ValueError):
                    continue

                counts[day_value] = counts.get(day_value, 0) + 1
                min_value = day_value if min_value is None else min(min_value, day_value)
                max_value = day_value if max_value is None else max(max_value, day_value)

            if counts:
                has_period_data = True
                for day in range(min_value, max_value + 1):
                    counts.setdefault(day, 0)
                distribution[period] = [{"Days": day, "Count": count} for day, count in sorted(counts.items())]
            else:
                distribution[period] = []

        if not has_period_data:
            counts: Dict[int, int] = {}
            min_value: Optional[int] = None
            max_value: Optional[int] = None
            for row in rows:
                value = row.get(metric)
                if value in (None, "", "NaN"):
                    continue
                try:
                    numeric = float(value)
                    if math.isnan(numeric):
                        continue
                    day_value = int(round(numeric))
                except (TypeError, ValueError):
                    continue
                counts[day_value] = counts.get(day_value, 0) + 1
                min_value = day_value if min_value is None else min(min_value, day_value)
                max_value = day_value if max_value is None else max(max_value, day_value)

            if counts:
                for day in range(min_value, max_value + 1):
                    counts.setdefault(day, 0)
                distribution["PP1"] = [{"Days": day, "Count": count} for day, count in sorted(counts.items())]
            else:
                distribution["PP1"] = []

            distribution["PP2"] = []

        return distribution

    @staticmethod
    def _max_distribution_count(dataset_a: List[Dict[str, Any]], dataset_b: List[Dict[str, Any]]) -> int:
        """Return max count across two distribution datasets."""
        counts = [item.get("Count", 0) for item in dataset_a] + [item.get("Count", 0) for item in dataset_b]
        return max(counts) if counts else 0

    async def _consume_parse_progress(
        self,
        progress_queue: "asyncio.Queue[Tuple[int, int]]",
        parsing_task: "asyncio.Task",
    ):
        """Stream progress updates from the parse thread to the UI."""
        while True:
            updated = False
            while True:
                try:
                    current_page, total_pages = progress_queue.get_nowait()
                except asyncio.QueueEmpty:
                    break

                updated = True
                total_pages = max(total_pages, 1)
                percent = 25 + int((current_page / total_pages) * 60)
                self.processing_progress = min(percent, 90)
                self.processing_message = f"Parsing PDF page {current_page} of {total_pages}..."
                yield

            if parsing_task.done() and progress_queue.empty():
                break

            if not updated:
                await asyncio.sleep(0.05)

    def _parse_pdf_with_progress(
        self,
        pdf_path: Path,
        loop: asyncio.AbstractEventLoop,
        progress_queue: "asyncio.Queue[Tuple[int, int]]",
    ) -> Tuple[pd.DataFrame, ParseDiagnostics]:
        """Parse bid lines on a worker thread and push page progress back to the loop."""

        def progress_callback(current_page: int, total_pages: int):
            loop.call_soon_threadsafe(
                progress_queue.put_nowait,
                (current_page, total_pages),
            )

        with open(pdf_path, "rb") as f:
            return parse_bid_lines(f, progress_callback=progress_callback)

    def undo_edit(self, edit_idx: int):
        """Undo a specific edit by its index in edited_cells list.

        Args:
            edit_idx: Index of the edit to undo in the edited_cells list
        """
        if edit_idx < 0 or edit_idx >= len(self.edited_cells):
            return

        # Get the edit to undo
        edit = self.edited_cells[edit_idx]
        row_idx = edit["row_idx"]
        column = edit["column"]
        old_value = edit["old_value"]

        # Revert the cell to its old value
        if row_idx < len(self.edited_data_json):
            self.edited_data_json[row_idx][column] = old_value

        # Remove this edit from the list
        self.edited_cells.pop(edit_idx)

        # Re-validate and recalculate
        self._validate_edits()
        self._calculate_statistics()

    def reset_filters(self):
        """Reset all filters to default values."""
        self.filter_ct_min = CT_RANGE_MIN
        self.filter_ct_max = CT_RANGE_MAX
        self.filter_bt_min = BT_RANGE_MIN
        self.filter_bt_max = BT_RANGE_MAX
        self.filter_do_min = DO_RANGE_MIN
        self.filter_do_max = DO_RANGE_MAX
        self.filter_dd_min = DD_RANGE_MIN
        self.filter_dd_max = DD_RANGE_MAX
        # Recalculate statistics with new filters
        self._calculate_statistics()

    # Filter setter methods
    def set_filter_ct_min(self, value: float):
        """Set CT minimum filter."""
        self.filter_ct_min = value
        self._calculate_statistics()

    def set_filter_ct_max(self, value: float):
        """Set CT maximum filter."""
        self.filter_ct_max = value
        self._calculate_statistics()

    def set_filter_bt_min(self, value: float):
        """Set BT minimum filter."""
        self.filter_bt_min = value
        self._calculate_statistics()

    def set_filter_bt_max(self, value: float):
        """Set BT maximum filter."""
        self.filter_bt_max = value
        self._calculate_statistics()

    def set_filter_do_min(self, value: int):
        """Set DO minimum filter."""
        self.filter_do_min = value
        self._calculate_statistics()

    def set_filter_do_max(self, value: int):
        """Set DO maximum filter."""
        self.filter_do_max = value
        self._calculate_statistics()

    def set_filter_dd_min(self, value: int):
        """Set DD minimum filter."""
        self.filter_dd_min = value
        self._calculate_statistics()

    def set_filter_dd_max(self, value: int):
        """Set DD maximum filter."""
        self.filter_dd_max = value
        self._calculate_statistics()

    # ========== Private Helper Methods ==========

    def _validate_edits(self):
        """Validate edited data and populate validation warnings."""
        warnings = []

        for line in self.edited_data_json:
            line_num = line.get("Line", "Unknown")
            ct = line.get("CT", 0)
            bt = line.get("BT", 0)
            do = line.get("DO", 0)
            dd = line.get("DD", 0)

            # Warning: CT or BT > 150 hours
            if ct > CT_MAX_WARNING:
                warnings.append(f"Line {line_num}: CT ({ct:.1f}) exceeds {CT_MAX_WARNING} hours")
            if bt > BT_MAX_WARNING:
                warnings.append(f"Line {line_num}: BT ({bt:.1f}) exceeds {BT_MAX_WARNING} hours")

            # Warning: BT > CT (block time should not exceed credit time)
            if bt > ct:
                warnings.append(f"Line {line_num}: BT ({bt:.1f}) > CT ({ct:.1f})")

            # Warning: DO or DD > 20 days
            if do > DO_MAX_WARNING:
                warnings.append(f"Line {line_num}: DO ({do}) exceeds {DO_MAX_WARNING} days")
            if dd > DD_MAX_WARNING:
                warnings.append(f"Line {line_num}: DD ({dd}) exceeds {DD_MAX_WARNING} days")

            # Warning: DO + DD > 31 (exceeds month length)
            if do + dd > 31:
                warnings.append(f"Line {line_num}: DO + DD ({do + dd}) exceeds 31 days")

        self.validation_warnings = warnings

    def _calculate_statistics(self):
        """Calculate statistics from filtered data."""
        if not self.filtered_data:
            # Reset all statistics to zero
            self.ct_min = self.ct_max = self.ct_mean = self.ct_median = 0.0
            self.bt_min = self.bt_max = self.bt_mean = self.bt_median = 0.0
            self.do_min = self.do_max = self.do_mean = self.do_median = 0.0
            self.dd_min = self.dd_max = self.dd_mean = self.dd_median = 0.0
            return

        # Convert to DataFrame for easier statistics calculation
        df = pd.DataFrame(self.filtered_data)

        # Convert numeric columns to proper numeric types (handles string values from edits)
        numeric_columns = [
            "CT", "BT", "DO", "DD",
            "CT_PP1", "CT_PP2", "BT_PP1", "BT_PP2",
            "DO_PP1", "DO_PP2", "DD_PP1", "DD_PP2"
        ]
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # Exclude reserve and hot standby lines from statistics
        df = self._exclude_non_regular_lines(df)

        # If all lines were filtered out, reset statistics
        if df.empty:
            self.ct_min = self.ct_max = self.ct_mean = self.ct_median = 0.0
            self.bt_min = self.bt_max = self.bt_mean = self.bt_median = 0.0
            self.do_min = self.do_max = self.do_mean = self.do_median = 0.0
            self.dd_min = self.dd_max = self.dd_mean = self.dd_median = 0.0
            return

        # Check if we have dual pay periods (CT_PP1 and CT_PP2 columns exist)
        has_dual_periods = "CT_PP1" in df.columns and "CT_PP2" in df.columns

        # CT statistics
        if "CT" in df.columns:
            if has_dual_periods and "CT_PP1" in df.columns and "CT_PP2" in df.columns:
                # For dual periods: use actual period values for min/max
                all_ct_values = pd.concat([df["CT_PP1"], df["CT_PP2"]]).dropna()
                if not all_ct_values.empty:
                    self.ct_min = float(all_ct_values.min())
                    self.ct_max = float(all_ct_values.max())
            else:
                # For single period: use averaged values
                self.ct_min = float(df["CT"].min())
                self.ct_max = float(df["CT"].max())

            # Mean and median always use averaged CT (mathematically equivalent)
            self.ct_mean = float(df["CT"].mean())
            self.ct_median = float(df["CT"].median())

        # BT statistics
        if "BT" in df.columns:
            if has_dual_periods and "BT_PP1" in df.columns and "BT_PP2" in df.columns:
                # For dual periods: use actual period values for min/max
                all_bt_values = pd.concat([df["BT_PP1"], df["BT_PP2"]]).dropna()
                if not all_bt_values.empty:
                    self.bt_min = float(all_bt_values.min())
                    self.bt_max = float(all_bt_values.max())
            else:
                # For single period: use averaged values
                self.bt_min = float(df["BT"].min())
                self.bt_max = float(df["BT"].max())

            # Mean and median always use averaged BT (mathematically equivalent)
            self.bt_mean = float(df["BT"].mean())
            self.bt_median = float(df["BT"].median())

        # DO statistics
        if "DO" in df.columns:
            if has_dual_periods and "DO_PP1" in df.columns and "DO_PP2" in df.columns:
                # For dual periods: use actual period values for min/max
                all_do_values = pd.concat([df["DO_PP1"], df["DO_PP2"]]).dropna()
                if not all_do_values.empty:
                    self.do_min = int(all_do_values.min())
                    self.do_max = int(all_do_values.max())
            else:
                # For single period: use averaged values
                self.do_min = int(df["DO"].min())
                self.do_max = int(df["DO"].max())

            # Mean and median always use averaged DO (mathematically equivalent)
            self.do_mean = float(df["DO"].mean())
            self.do_median = float(df["DO"].median())

        # DD statistics
        if "DD" in df.columns:
            if has_dual_periods and "DD_PP1" in df.columns and "DD_PP2" in df.columns:
                # For dual periods: use actual period values for min/max
                all_dd_values = pd.concat([df["DD_PP1"], df["DD_PP2"]]).dropna()
                if not all_dd_values.empty:
                    self.dd_min = int(all_dd_values.min())
                    self.dd_max = int(all_dd_values.max())
            else:
                # For single period: use averaged values
                self.dd_min = int(df["DD"].min())
                self.dd_max = int(df["DD"].max())

            # Mean and median always use averaged DD (mathematically equivalent)
            self.dd_mean = float(df["DD"].mean())
            self.dd_median = float(df["DD"].median())

        # Pay period statistics (if available)
        if self.pay_periods_json:
            pp_df = pd.DataFrame(self.pay_periods_json)
            pp_df = self._exclude_non_regular_lines(pp_df)

            if "Period" in pp_df.columns:
                pp1 = pp_df[pp_df["Period"] == 1]
                pp2 = pp_df[pp_df["Period"] == 2]

                # PP1 statistics
                if not pp1.empty:
                    self.pp1_ct_mean = float(pp1["CT"].mean()) if "CT" in pp1.columns else 0.0
                    self.pp1_bt_mean = float(pp1["BT"].mean()) if "BT" in pp1.columns else 0.0
                    self.pp1_do_mean = float(pp1["DO"].mean()) if "DO" in pp1.columns else 0.0
                    self.pp1_dd_mean = float(pp1["DD"].mean()) if "DD" in pp1.columns else 0.0

                # PP2 statistics
                if not pp2.empty:
                    self.pp2_ct_mean = float(pp2["CT"].mean()) if "CT" in pp2.columns else 0.0
                    self.pp2_bt_mean = float(pp2["BT"].mean()) if "BT" in pp2.columns else 0.0
                    self.pp2_do_mean = float(pp2["DO"].mean()) if "DO" in pp2.columns else 0.0
                    self.pp2_dd_mean = float(pp2["DD"].mean()) if "DD" in pp2.columns else 0.0

    def _calculate_reserve_statistics(self):
        """Calculate reserve line slot statistics and gateway summaries."""
        self.gateway_standby_summary = []
        self.reserve_line_count = 0
        self.hot_standby_line_count = 0
        self.airport_standby_line_count = 0
        self.gateway_standby_line_count = 0
        if not self.reserve_lines_json:
            self.reserve_captain_slots = 0
            self.reserve_fo_slots = 0
            self.hot_standby_captain_slots = 0
            self.hot_standby_fo_slots = 0
            return

        df = pd.DataFrame(self.reserve_lines_json)

        # Regular reserve lines (excluding hot standby)
        regular_reserve = df[(df.get("IsReserve", False) == True) & (~df.get("IsHotStandby", False))]
        if not regular_reserve.empty:
            self.reserve_captain_slots = int(regular_reserve["CaptainSlots"].sum())
            self.reserve_fo_slots = int(regular_reserve["FOSlots"].sum())
            self.reserve_line_count = int(regular_reserve["Line"].nunique())
        else:
            self.reserve_captain_slots = 0
            self.reserve_fo_slots = 0
            self.reserve_line_count = 0

        # Hot standby lines
        hot_standby = df[df.get("IsHotStandby", False) == True]
        if not hot_standby.empty:
            self.hot_standby_captain_slots = int(hot_standby["CaptainSlots"].sum())
            self.hot_standby_fo_slots = int(hot_standby["FOSlots"].sum())
            self.hot_standby_line_count = int(hot_standby["Line"].nunique())
        else:
            self.hot_standby_captain_slots = 0
            self.hot_standby_fo_slots = 0
            self.hot_standby_line_count = 0

        airport_standby = hot_standby[hot_standby.get("StandbyType") == "airport"]
        self.airport_standby_line_count = (
            int(airport_standby["Line"].nunique()) if not airport_standby.empty else 0
        )

        gateway_standby = hot_standby[hot_standby.get("StandbyType") == "gateway"]
        if not gateway_standby.empty:
            self.gateway_standby_line_count = int(gateway_standby["Line"].nunique())
            valid_gateways = gateway_standby.dropna(subset=["GatewayCode"])
            if not valid_gateways.empty:
                summary = (
                    valid_gateways.groupby("GatewayCode").size().reset_index(name="count")
                )
                summary = summary.sort_values("GatewayCode")
                self.gateway_standby_summary = [
                    {"gateway": row["GatewayCode"], "line_count": int(row["count"])}
                    for _, row in summary.iterrows()
                ]
            else:
                self.gateway_standby_summary = []
        else:
            self.gateway_standby_line_count = 0
            self.gateway_standby_summary = []

    def _calculate_line_category_counts(self):
        """Calculate regular/VTO/VTOR line counts per position."""
        self.regular_captain_lines = 0
        self.regular_fo_lines = 0
        self.vto_full_captain_lines = 0
        self.vto_full_fo_lines = 0
        self.vto_split_captain_lines = 0
        self.vto_split_fo_lines = 0
        self.vtor_captain_lines = 0
        self.vtor_fo_lines = 0

        if not self.reserve_lines_json:
            return

        lines_with_vto_data = {row.get("Line") for row in self.original_data_json if row.get("VTOType")}

        for entry in self.reserve_lines_json:
            line_type = entry.get("LineType") or (
                "hot_standby"
                if entry.get("IsHotStandby")
                else ("reserve" if entry.get("IsReserve") else "regular")
            )
            captain_slots = int(entry.get("CaptainSlots") or 0)
            fo_slots = int(entry.get("FOSlots") or 0)
            line_id = entry.get("Line")

            if line_type == "regular":
                self.regular_captain_lines += captain_slots
                self.regular_fo_lines += fo_slots
            elif line_type == "vto":
                if line_id in lines_with_vto_data:
                    self.vto_split_captain_lines += captain_slots
                    self.vto_split_fo_lines += fo_slots
                else:
                    self.vto_full_captain_lines += captain_slots
                    self.vto_full_fo_lines += fo_slots
            elif line_type == "vtor":
                self.vtor_captain_lines += captain_slots
                self.vtor_fo_lines += fo_slots
    # ========== Download Generation ==========

    def _build_download_filename(self, extension: str) -> str:
        """Construct a consistent filename for bid line exports."""
        domicile = self.domicile or "BID"
        aircraft = self.aircraft or "LINE"
        bid_period = self.bid_period or "XXXX"
        return f"{domicile}_{aircraft}_Bid{bid_period}_BidLines.{extension}"

    def _filtered_pay_periods_dataframe(self) -> pd.DataFrame:
        """Return pay period data limited to the currently filtered lines."""
        if not self.pay_periods_json:
            return pd.DataFrame()

        df = pd.DataFrame(self.pay_periods_json)
        if df.empty or "Line" not in df.columns:
            return df

        filtered_lines = {
            row.get("Line")
            for row in self.filtered_data
            if row.get("Line") is not None
        }
        if filtered_lines:
            df = df[df["Line"].isin(filtered_lines)]
        return df

    def _reserve_dataframe(self) -> pd.DataFrame:
        """Return DataFrame of reserve lines."""
        if not self.reserve_lines_json:
            return pd.DataFrame()
        return pd.DataFrame(self.reserve_lines_json)

    def _summary_dataframe(self) -> pd.DataFrame:
        """Build a summary table for Excel export."""
        summary_rows = [
            {"Metric": "Total Lines (Filtered)", "Value": len(self.filtered_data)},
            {"Metric": "Average Credit Time (CT)", "Value": f"{self.ct_mean:.2f} hrs"},
            {"Metric": "Average Block Time (BT)", "Value": f"{self.bt_mean:.2f} hrs"},
            {"Metric": "Average Days Off (DO)", "Value": f"{self.do_mean:.1f} days"},
            {"Metric": "Average Duty Days (DD)", "Value": f"{self.dd_mean:.1f} days"},
            {"Metric": "Reserve Lines", "Value": self.reserve_line_count},
            {"Metric": "Reserve Captain Slots", "Value": self.reserve_captain_slots},
            {"Metric": "Reserve F/O Slots", "Value": self.reserve_fo_slots},
            {"Metric": "Hot Standby Lines", "Value": self.hot_standby_line_count},
            {"Metric": "HSBY Captain Slots", "Value": self.hot_standby_captain_slots},
            {"Metric": "HSBY F/O Slots", "Value": self.hot_standby_fo_slots},
        ]
        return pd.DataFrame(summary_rows)

    def generate_excel_download(self) -> bytes:
        """Create an Excel workbook that mirrors the filtered data and diagnostics."""
        if not self.filtered_data:
            return b""

        try:
            df_lines = pd.DataFrame(self.filtered_data)
            if df_lines.empty:
                return b""

            preferred_columns = [
                "Line", "CT", "BT", "DO", "DD",
                "CT_PP1", "BT_PP1", "DO_PP1", "DD_PP1",
                "CT_PP2", "BT_PP2", "DO_PP2", "DD_PP2",
                "CaptainSlots", "FOSlots", "VTOType", "VTOPeriod",
                "Hot Standby",
            ]
            existing_cols = [col for col in preferred_columns if col in df_lines.columns]
            remaining_cols = [col for col in df_lines.columns if col not in existing_cols]
            ordered_cols = existing_cols + remaining_cols
            df_lines = df_lines[ordered_cols]
            if "Line" in df_lines.columns:
                df_lines = df_lines.sort_values("Line")

            summary_df = self._summary_dataframe()
            pay_periods_df = self._filtered_pay_periods_dataframe()
            reserve_df = self._reserve_dataframe()

            output = BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df_lines.to_excel(writer, sheet_name="Bid Lines", index=False)
                if not summary_df.empty:
                    summary_df.to_excel(writer, sheet_name="Summary", index=False)
                if not pay_periods_df.empty:
                    pay_periods_df.to_excel(writer, sheet_name="Pay Periods", index=False)
                if not reserve_df.empty:
                    reserve_df.to_excel(writer, sheet_name="Reserve Lines", index=False)

            output.seek(0)
            return output.getvalue()

        except Exception as exc:  # pragma: no cover - defensive logging
            print(f"Error generating bid line Excel export: {exc}")
            return b""

    def generate_pdf_download(self) -> bytes:
        """Create the bid line PDF report using the shared generator."""
        if not self.filtered_data:
            return b""

        try:
            df = pd.DataFrame(self.filtered_data)
            if df.empty:
                return b""

            title = f"{self.domicile} {self.aircraft} – Bid {self.bid_period}".strip()
            subtitle = (
                f"Bid Line Analysis Report • {self.date_range}"
                if self.date_range
                else "Bid Line Analysis Report"
            )
            metadata = ReportMetadata(title=title or "Bid Line Analysis Report", subtitle=subtitle)

            branding = {
                "primary_hex": "#1E40AF",
                "accent_hex": "#F3F4F6",
                "rule_hex": "#E5E7EB",
                "muted_hex": "#6B7280",
                "bg_alt_hex": "#FAFAFA",
                "logo_path": None,
                "title_left": f"{title} | Bid Line Analysis Report" if title else None,
            }

            pay_periods_df = pd.DataFrame(self.pay_periods_json) if self.pay_periods_json else None
            if pay_periods_df is not None and pay_periods_df.empty:
                pay_periods_df = None

            reserve_df = pd.DataFrame(self.reserve_lines_json) if self.reserve_lines_json else None
            if reserve_df is not None and reserve_df.empty:
                reserve_df = None

            pdf_bytes = create_bid_line_pdf_report(
                df,
                metadata=metadata,
                pay_periods=pay_periods_df,
                reserve_lines=reserve_df,
                branding=branding,
            )
            return pdf_bytes

        except Exception as exc:  # pragma: no cover - defensive logging
            print(f"Error generating bid line PDF: {exc}")
            return b""

    # ========== Download Event Handlers ==========

    def download_excel(self):
        """Trigger Excel download using Reflex download helper."""
        excel_bytes = self.generate_excel_download()
        if excel_bytes:
            filename = self._build_download_filename("xlsx")
            return rx.download(data=excel_bytes, filename=filename)

    def download_pdf(self):
        """Trigger PDF download using Reflex download helper."""
        pdf_bytes = self.generate_pdf_download()
        if pdf_bytes:
            filename = self._build_download_filename("pdf")
            return rx.download(data=pdf_bytes, filename=filename)
