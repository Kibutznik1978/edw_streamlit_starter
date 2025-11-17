"""Bid Line Analyzer State Management.

This module manages the state for the Bid Line Analyzer,
including PDF upload, processing, data editing, filtering, and exports.
"""

import reflex as rx
from typing import Optional, Dict, List, Any
from pathlib import Path
import tempfile
import pandas as pd
import sys

from ..database.base_state import DatabaseState

# Add path to import from root directory modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from bid_parser import parse_bid_lines, extract_bid_line_header_info
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

            # Update progress
            self.processing_progress = 30
            self.processing_message = "Parsing bid lines..."
            yield  # Push progress update

            # Parse bid lines
            with open(pdf_path, "rb") as f:
                df, diagnostics = parse_bid_lines(f, progress_callback=None)

            # Convert DataFrame to JSON-serializable format
            self.original_data_json = df.to_dict("records")
            self.edited_data_json = df.to_dict("records")  # Start with copy of original

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

            # Clear any previous edits
            self.edited_cells = []
            self.validation_warnings = []

            # Calculate statistics
            self._calculate_statistics()

            # Update progress
            self.processing_progress = 100
            self.processing_message = "Parsing complete!"
            self.is_processing = False
            yield  # Push completion state

        except Exception as e:
            self.upload_error = f"Error processing PDF: {str(e)}"
            self.is_processing = False
            self.processing_progress = 0
            yield  # Push error state

    def update_cell(self, row_idx: int, column: str, new_value: Any):
        """Handle inline cell edit."""
        if row_idx < 0 or row_idx >= len(self.edited_data_json):
            return

        old_value = self.edited_data_json[row_idx].get(column)

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

        # CT statistics
        if "CT" in df.columns:
            self.ct_min = float(df["CT"].min())
            self.ct_max = float(df["CT"].max())
            self.ct_mean = float(df["CT"].mean())
            self.ct_median = float(df["CT"].median())

        # BT statistics
        if "BT" in df.columns:
            self.bt_min = float(df["BT"].min())
            self.bt_max = float(df["BT"].max())
            self.bt_mean = float(df["BT"].mean())
            self.bt_median = float(df["BT"].median())

        # DO statistics
        if "DO" in df.columns:
            self.do_min = int(df["DO"].min())
            self.do_max = int(df["DO"].max())
            self.do_mean = float(df["DO"].mean())
            self.do_median = float(df["DO"].median())

        # DD statistics
        if "DD" in df.columns:
            self.dd_min = int(df["DD"].min())
            self.dd_max = int(df["DD"].max())
            self.dd_mean = float(df["DD"].mean())
            self.dd_median = float(df["DD"].median())

        # Pay period statistics (if available)
        if self.pay_periods_json:
            pp_df = pd.DataFrame(self.pay_periods_json)

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
        """Calculate reserve line slot statistics."""
        if not self.reserve_lines_json:
            self.reserve_captain_slots = 0
            self.reserve_fo_slots = 0
            self.hot_standby_captain_slots = 0
            self.hot_standby_fo_slots = 0
            return

        df = pd.DataFrame(self.reserve_lines_json)

        # Regular reserve lines (excluding hot standby)
        regular_reserve = df[~df.get("IsHotStandby", False)]
        if not regular_reserve.empty:
            self.reserve_captain_slots = int(regular_reserve["CaptainSlots"].sum())
            self.reserve_fo_slots = int(regular_reserve["FOSlots"].sum())

        # Hot standby lines
        hot_standby = df[df.get("IsHotStandby", False)]
        if not hot_standby.empty:
            self.hot_standby_captain_slots = int(hot_standby["CaptainSlots"].sum())
            self.hot_standby_fo_slots = int(hot_standby["FOSlots"].sum())
