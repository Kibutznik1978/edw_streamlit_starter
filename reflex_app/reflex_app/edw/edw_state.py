"""EDW Pairing Analyzer State Management.

This module manages the state for the EDW (Early/Day/Window) Pairing Analyzer,
including PDF upload, processing, filtering, and results display.
"""

import reflex as rx
from typing import Optional, Dict, List, Any
from pathlib import Path
import tempfile
import pandas as pd
import plotly.graph_objects as go
import sys
import os
from io import BytesIO

from ..database.base_state import DatabaseState

# Add path to import from root directory modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from export_pdf import create_pdf_report


class EDWState(DatabaseState):
    """State management for EDW Pairing Analyzer."""

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
    report_date: str = ""

    # ========== Results State ==========
    # Trip summary statistics
    unique_pairings: int = 0
    total_trips: int = 0
    edw_trips: int = 0
    day_trips: int = 0
    hot_standby_trips: int = 0

    # Weighted EDW metrics
    trip_weighted_pct: float = 0.0
    tafb_weighted_pct: float = 0.0
    duty_day_weighted_pct: float = 0.0

    # Detailed trip data (as JSON-serializable list of dicts)
    trips_data: List[Dict[str, Any]] = []

    # Trip text map for detail viewer (trip_id -> raw_text)
    trip_text_map: Dict[str, str] = {}

    # Duty day distribution data
    duty_dist_data: List[Dict[str, Any]] = []

    # Duty day statistics (list of records for table rendering)
    duty_day_stats: List[Dict[str, Any]] = []

    # ========== Filter State ==========
    # Max duty day length filter
    filter_duty_day_min: float = 0.0
    filter_duty_day_max_available: float = 24.0

    # Max legs per duty filter
    filter_legs_min: int = 0
    filter_legs_max_available: int = 10

    # Duty day criteria filters (for combined condition matching)
    duty_duration_min: float = 0.0
    duty_legs_min: int = 0
    duty_edw_filter: str = "Any"  # "Any", "EDW Only", "Non-EDW Only"
    match_mode: str = "Disabled"  # "Disabled", "Any duty day matches", "All duty days match"

    # EDW/Hot Standby filters
    filter_edw: str = "All"  # "All", "EDW Only", "Day Only"
    filter_hot_standby: str = "All"  # "All", "Hot Standby Only", "Exclude Hot Standby"

    # Sort options
    sort_by: str = "Trip ID"  # "Trip ID", "Frequency", "TAFB Hours", "Duty Days", etc.

    # Exclude 1-day trips toggle
    exclude_turns: bool = False

    # ========== Selected Trip for Detail Viewer ==========
    selected_trip_id: str = ""

    # ========== Table State ==========
    table_page: int = 1
    table_page_size: int = 25
    table_sort_column: str = "Trip ID"
    table_sort_ascending: bool = True

    # ========== Save to Database State ==========
    save_status: str = ""  # Success/error message
    save_in_progress: bool = False

    # ========== Notes ==========
    user_notes: str = ""

    # ========== Computed Variables ==========

    @rx.var
    def has_results(self) -> bool:
        """Check if analysis results are available."""
        return len(self.trips_data) > 0

    @rx.var
    def filtered_trips(self) -> List[Dict[str, Any]]:
        """Apply all filters to trips data and return filtered list."""
        if not self.trips_data:
            return []

        filtered = self.trips_data.copy()

        # Filter by max duty day length
        if self.filter_duty_day_min > 0:
            filtered = [
                trip for trip in filtered
                if trip.get("max_duty_length", 0) >= self.filter_duty_day_min
            ]

        # Filter by max legs per duty
        if self.filter_legs_min > 0:
            filtered = [
                trip for trip in filtered
                if trip.get("max_legs_per_duty", 0) >= self.filter_legs_min
            ]

        # Filter by duty day criteria (combined conditions)
        if self.match_mode != "Disabled":
            filtered = [
                trip for trip in filtered
                if self._trip_matches_duty_criteria(trip)
            ]

        # Filter by EDW status
        if self.filter_edw == "EDW Only":
            filtered = [trip for trip in filtered if trip.get("is_edw", False)]
        elif self.filter_edw == "Day Only":
            filtered = [trip for trip in filtered if not trip.get("is_edw", False)]

        # Filter by Hot Standby status
        if self.filter_hot_standby == "Hot Standby Only":
            filtered = [trip for trip in filtered if trip.get("is_hot_standby", False)]
        elif self.filter_hot_standby == "Exclude Hot Standby":
            filtered = [trip for trip in filtered if not trip.get("is_hot_standby", False)]

        return filtered

    def _trip_matches_duty_criteria(self, trip: Dict[str, Any]) -> bool:
        """Check if trip matches duty day criteria based on match mode."""
        duty_day_details = trip.get("duty_day_details", [])
        if not duty_day_details:
            return False

        matching_days = [
            dd for dd in duty_day_details
            if self._duty_day_meets_criteria(dd)
        ]

        if self.match_mode == "Any duty day matches":
            return len(matching_days) > 0
        elif self.match_mode == "All duty days match":
            return len(matching_days) == len(duty_day_details)

        return False

    def _duty_day_meets_criteria(self, duty_day: Dict[str, Any]) -> bool:
        """Check if a single duty day meets all criteria."""
        # Duration check
        duration_ok = duty_day.get("duration_hours", 0) >= self.duty_duration_min

        # Legs check
        legs_ok = duty_day.get("num_legs", 0) >= self.duty_legs_min

        # EDW status check
        edw_ok = True
        if self.duty_edw_filter == "EDW Only":
            edw_ok = duty_day.get("is_edw", False)
        elif self.duty_edw_filter == "Non-EDW Only":
            edw_ok = not duty_day.get("is_edw", False)

        return duration_ok and legs_ok and edw_ok

    @rx.var
    def filtered_trip_count(self) -> int:
        """Count of filtered trips."""
        return len(self.filtered_trips)

    @rx.var
    def available_trip_ids(self) -> List[str]:
        """List of available trip IDs for detail viewer."""
        if not self.filtered_trips:
            return []

        trip_ids = [
            str(trip.get("trip_id", ""))
            for trip in self.filtered_trips
            if trip.get("trip_id")
        ]
        return sorted(set(trip_ids))

    @rx.var
    def selected_trip_data(self) -> Dict[str, Any]:
        """Parse and return data for the currently selected trip.

        Returns:
            Parsed trip data dict with trip_id, date_freq, duty_days, trip_summary.
            Returns empty dict if no trip is selected or parsing fails.
        """
        if not self.selected_trip_id or self.selected_trip_id not in self.trip_text_map:
            return {}

        try:
            # Add project root to path to import edw_reporter
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..'))
            if project_root not in sys.path:
                sys.path.insert(0, project_root)

            from edw_reporter import parse_trip_for_table

            trip_text = self.trip_text_map[self.selected_trip_id]
            return parse_trip_for_table(trip_text)
        except Exception as e:
            # Return error dict if parsing fails
            return {"error": str(e)}

    @rx.var
    def selected_trip_duty_days(self) -> List[Dict[str, Any]]:
        """Return duty days list for the selected trip.

        Explicitly typed for use in rx.foreach.

        Returns:
            List of duty day dictionaries, or empty list if not available.
        """
        trip_data = self.selected_trip_data
        if not trip_data or "duty_days" not in trip_data:
            return []

        duty_days = trip_data.get("duty_days", [])
        # Ensure we return a list type (not None or other)
        return duty_days if isinstance(duty_days, list) else []

    @rx.var
    def duty_dist_display(self) -> List[Dict[str, Any]]:
        """Duty day distribution data with optional 1-day trip exclusion."""
        if not self.duty_dist_data:
            return []

        if self.exclude_turns:
            return [
                item for item in self.duty_dist_data
                # Handle both "Duty Days" (from DataFrame) and "duty_days" (alternative)
                if (item.get("Duty Days") or item.get("duty_days", 0)) != 1
            ]

        return self.duty_dist_data

    @rx.var
    def duty_day_count_chart(self) -> go.Figure:
        """Generate duty day count bar chart."""
        data = self.duty_dist_display

        # Create empty figure if no data
        if not data:
            fig = go.Figure()
            fig.update_layout(
                title="Duty Day Count Distribution",
                xaxis_title="Number of Duty Days",
                yaxis_title="Number of Trips",
                template="plotly_white",
                height=400,
            )
            return fig

        # Extract data - handle both naming conventions
        duty_days = []
        trips = []
        for item in data:
            # Try both "Duty Days" and "duty_days" keys
            dd = item.get("Duty Days") or item.get("duty_days", 0)
            t = item.get("Trips") or item.get("trips", 0)
            duty_days.append(dd)
            trips.append(t)

        # Create bar chart
        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=duty_days,
            y=trips,
            text=trips,
            textposition='outside',
            marker=dict(
                color='#3b82f6',  # Blue color
                line=dict(color='#1e40af', width=1)
            ),
            hovertemplate='<b>%{x} Duty Days</b><br>Trips: %{y}<extra></extra>',
        ))

        fig.update_layout(
            title=dict(
                text="Duty Day Count Distribution",
                font=dict(size=18),
                x=0.5,
                xanchor='center',
            ),
            xaxis=dict(
                title="Number of Duty Days",
                tickmode='array',
                tickvals=duty_days,  # Explicitly set tick values to match data
                ticktext=[str(int(d)) for d in duty_days],  # Show all labels
            ),
            yaxis=dict(
                title="Number of Trips",
            ),
            template="plotly_white",
            height=400,
            margin=dict(l=50, r=50, t=60, b=60),  # Increased bottom margin
            showlegend=False,
        )

        return fig

    @rx.var
    def sorted_filtered_trips(self) -> List[Dict[str, Any]]:
        """Apply sorting to filtered trips."""
        if not self.filtered_trips:
            return []

        trips = self.filtered_trips.copy()

        # Sort by selected column
        try:
            trips.sort(
                key=lambda x: x.get(self.table_sort_column, ""),
                reverse=not self.table_sort_ascending
            )
        except Exception:
            # If sorting fails, return unsorted
            pass

        return trips

    @rx.var
    def paginated_trips(self) -> List[Dict[str, Any]]:
        """Apply pagination to sorted filtered trips."""
        if not self.sorted_filtered_trips:
            return []

        start_idx = (self.table_page - 1) * self.table_page_size
        end_idx = start_idx + self.table_page_size

        return self.sorted_filtered_trips[start_idx:end_idx]

    @rx.var
    def total_pages(self) -> int:
        """Calculate total number of pages."""
        if not self.sorted_filtered_trips:
            return 1

        import math
        return max(1, math.ceil(len(self.sorted_filtered_trips) / self.table_page_size))

    @rx.var
    def duty_day_percent_chart(self) -> go.Figure:
        """Generate duty day percentage bar chart."""
        data = self.duty_dist_display

        # Create empty figure if no data
        if not data:
            fig = go.Figure()
            fig.update_layout(
                title="Duty Day Percentage Distribution",
                xaxis_title="Number of Duty Days",
                yaxis_title="Percentage of Trips",
                template="plotly_white",
                height=400,
            )
            return fig

        # Extract data - handle both naming conventions
        duty_days = []
        percents = []
        for item in data:
            # Try both "Duty Days" and "duty_days" keys
            dd = item.get("Duty Days") or item.get("duty_days", 0)
            p = item.get("Percent") or item.get("percent", 0.0)
            duty_days.append(dd)
            percents.append(p)

        # Create bar chart
        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=duty_days,
            y=percents,
            text=[f"{p:.1f}%" for p in percents],
            textposition='outside',
            marker=dict(
                color='#10b981',  # Green color
                line=dict(color='#047857', width=1)
            ),
            hovertemplate='<b>%{x} Duty Days</b><br>Percentage: %{y:.1f}%<extra></extra>',
        ))

        fig.update_layout(
            title=dict(
                text="Duty Day Percentage Distribution",
                font=dict(size=18),
                x=0.5,
                xanchor='center',
            ),
            xaxis=dict(
                title="Number of Duty Days",
                tickmode='array',
                tickvals=duty_days,  # Explicitly set tick values to match data
                ticktext=[str(int(d)) for d in duty_days],  # Show all labels
            ),
            yaxis=dict(
                title="Percentage of Trips (%)",
            ),
            template="plotly_white",
            height=400,
            margin=dict(l=50, r=50, t=60, b=60),  # Increased bottom margin
            showlegend=False,
        )

        return fig

    # ========== Event Handlers ==========

    def set_exclude_turns(self, value: bool):
        """Set exclude_turns toggle value."""
        self.exclude_turns = value

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
            # Get first file
            file = files[0]
            self.uploaded_file_name = file.filename

            # Read file data
            file_data = await file.read()

            # Save to temporary file
            tmpdir = Path(tempfile.mkdtemp())
            pdf_path = tmpdir / file.filename
            pdf_path.write_bytes(file_data)

            # Update progress
            self.processing_progress = 10
            self.processing_message = "Extracting PDF text..."
            yield  # Push progress update to frontend

            # Import EDW reporter functions (lazy import to avoid circular dependencies)
            # Add project root to path to import edw_reporter from parent directory
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
            if project_root not in sys.path:
                sys.path.insert(0, project_root)

            from edw_reporter import (
                extract_pdf_header_info,
                run_edw_report
            )

            # Extract header information
            header_info = extract_pdf_header_info(pdf_path)
            self.domicile = header_info.get("domicile", "Unknown")
            self.aircraft = header_info.get("fleet_type", "Unknown")
            self.bid_period = header_info.get("bid_period", "Unknown")
            self.date_range = header_info.get("date_range", "Unknown")
            self.report_date = header_info.get("report_date", "Unknown")

            self.processing_progress = 30
            self.processing_message = "Analyzing trips..."
            yield  # Push progress update to frontend

            # Create output directory
            out_dir = tmpdir / "outputs"
            out_dir.mkdir(exist_ok=True)

            # Run EDW analysis with progress callback
            results = run_edw_report(
                pdf_path,
                out_dir,
                domicile=self.domicile,
                aircraft=self.aircraft,
                bid_period=self.bid_period,
                progress_callback=self._update_progress
            )

            # Store results
            self._process_results(results)

            self.processing_progress = 100
            self.processing_message = "Analysis complete!"
            self.is_processing = False
            yield  # Push completion state to frontend

        except Exception as e:
            self.upload_error = f"Error processing PDF: {str(e)}"
            self.is_processing = False
            self.processing_progress = 0
            yield  # Push error state to frontend

    def _update_progress(self, progress: int, message: str):
        """Progress callback for EDW report generation."""
        self.processing_progress = progress
        self.processing_message = message

    def _process_results(self, results: Dict[str, Any]):
        """Process and store EDW analysis results."""
        # Extract trip summary
        trip_summary = results.get("trip_summary")
        if trip_summary is not None and len(trip_summary) >= 4:
            self.unique_pairings = int(trip_summary.loc[0, "Value"])
            self.total_trips = int(trip_summary.loc[1, "Value"])
            self.edw_trips = int(trip_summary.loc[2, "Value"])
            self.day_trips = int(trip_summary.loc[3, "Value"])

        # Extract hot standby summary
        hs_summary = results.get("hot_standby_summary")
        if hs_summary is not None and len(hs_summary) >= 1:
            self.hot_standby_trips = int(hs_summary.loc[0, "Value"])

        # Extract weighted metrics
        weighted = results.get("weighted_summary")
        if weighted is not None and len(weighted) >= 3:
            self.trip_weighted_pct = float(weighted.loc[0, "Value"].strip("%"))
            self.tafb_weighted_pct = float(weighted.loc[1, "Value"].strip("%"))
            self.duty_day_weighted_pct = float(weighted.loc[2, "Value"].strip("%"))

        # Store trip data
        df_trips = results.get("df_trips")
        if df_trips is not None:
            self.trips_data = df_trips.to_dict("records")

            # Calculate max values for filters
            if len(df_trips) > 0:
                self.filter_duty_day_max_available = float(df_trips["Max Duty Length"].max())
                self.filter_legs_max_available = int(df_trips["Max Legs/Duty"].max())

        # Store trip text map
        self.trip_text_map = results.get("trip_text_map", {})

        # Store duty day distribution
        duty_dist = results.get("duty_dist")
        if duty_dist is not None:
            self.duty_dist_data = duty_dist.to_dict("records")

        # Store duty day statistics (as list of records for easy table rendering)
        duty_stats = results.get("duty_day_stats")
        if duty_stats is not None:
            self.duty_day_stats = duty_stats.to_dict("records")

    def reset_filters(self):
        """Reset all filters to default values."""
        self.filter_duty_day_min = 0.0
        self.filter_legs_min = 0
        self.duty_duration_min = 0.0
        self.duty_legs_min = 0
        self.duty_edw_filter = "Any"
        self.match_mode = "Disabled"
        self.filter_edw = "All"
        self.filter_hot_standby = "All"
        self.sort_by = "Trip ID"
        self.exclude_turns = False
        # Reset table to first page when filters change
        self.table_page = 1

    def set_table_page(self, page: int):
        """Set current table page."""
        self.table_page = max(1, min(page, self.total_pages))

    def set_table_page_size(self, size: str):
        """Set table page size and reset to first page."""
        self.table_page_size = int(size)
        self.table_page = 1

    def table_sort(self, column: str):
        """Sort table by column. Toggle direction if same column clicked."""
        if self.table_sort_column == column:
            # Toggle sort direction
            self.table_sort_ascending = not self.table_sort_ascending
        else:
            # New column, default to ascending
            self.table_sort_column = column
            self.table_sort_ascending = True
        # Reset to first page when sorting changes
        self.table_page = 1

    def select_trip_from_table(self, trip_id: str):
        """Select a trip from the table (for detail viewer)."""
        self.selected_trip_id = str(trip_id)

    async def save_to_database(self):
        """Save EDW analysis results to database.

        Saves to 3 tables:
        1. bid_periods - Master record with domicile, aircraft, bid_period
        2. trips - Individual trip records with EDW analysis
        3. edw_summary_stats - Aggregated statistics

        Handles duplicate detection and optionally overwrites existing data.
        """
        if not self.is_authenticated:
            self.save_status = "Error: Please login to save data"
            return

        if not self.trips_data:
            self.save_status = "Error: No data to save"
            return

        if not self.domicile or not self.aircraft or not self.bid_period:
            self.save_status = "Error: Missing bid period metadata"
            return

        self.save_in_progress = True
        self.save_status = "Checking for existing data..."
        yield  # Push initial status to frontend

        try:
            client = self.get_db_client()
            if not client:
                self.save_status = "Error: Database connection failed"
                self.save_in_progress = False
                yield
                return

            # Step 1: Check if bid period already exists
            self.save_status = "Checking for duplicates..."
            yield

            existing_periods = await self.query_table(
                "bid_periods",
                filters={
                    "domicile": self.domicile,
                    "aircraft": self.aircraft,
                    "bid_period": self.bid_period
                }
            )

            bid_period_id = None

            if existing_periods and len(existing_periods) > 0:
                # Bid period exists - delete old data and reuse ID
                bid_period_id = existing_periods[0]["id"]
                self.save_status = f"Found existing data. Replacing..."
                yield

                # Delete old trips and stats (cascade will handle this, but being explicit)
                client.table("trips").delete().eq("bid_period_id", bid_period_id).execute()
                client.table("edw_summary_stats").delete().eq("bid_period_id", bid_period_id).execute()

                # Update the bid period upload date
                client.table("bid_periods").update({
                    "upload_date": "now()"
                }).eq("id", bid_period_id).execute()

            else:
                # Step 2: Insert new bid period
                self.save_status = "Creating bid period record..."
                yield

                bid_period_data = {
                    "domicile": self.domicile,
                    "aircraft": self.aircraft,
                    "bid_period": self.bid_period
                }

                result = await self.insert_row("bid_periods", bid_period_data)
                if not result:
                    self.save_status = f"Error: Failed to create bid period record - {self.error_message}"
                    self.save_in_progress = False
                    yield
                    return

                bid_period_id = result["id"]

            # Step 3: Insert trips
            self.save_status = f"Saving {len(self.trips_data)} trip records..."
            yield

            trips_inserted = 0
            for trip in self.trips_data:
                trip_data = {
                    "bid_period_id": bid_period_id,
                    "trip_id": trip.get("Trip ID", ""),
                    "is_edw": trip.get("EDW", False) == "Yes" if isinstance(trip.get("EDW"), str) else trip.get("is_edw", False),
                    "edw_reason": None,  # Could be enhanced to store which duty days triggered EDW
                    "tafb_hours": float(trip.get("TAFB Hours", 0)) if trip.get("TAFB Hours") else None,
                    "duty_days": int(trip.get("Duty Days", 0)) if trip.get("Duty Days") else None,
                    "credit_time_hours": None,  # Not currently tracked in trips_data
                    "raw_text": self.trip_text_map.get(trip.get("Trip ID", ""), "")
                }

                result = client.table("trips").insert(trip_data).execute()
                if result and result.data:
                    trips_inserted += 1

            self.save_status = f"Saved {trips_inserted} trip records. Calculating summary stats..."
            yield

            # Step 4: Calculate and insert summary statistics
            # Count EDW vs non-EDW trips
            edw_count = sum(1 for t in self.trips_data if (t.get("EDW") == "Yes" if isinstance(t.get("EDW"), str) else t.get("is_edw", False)))
            total_count = len(self.trips_data)
            non_edw_count = total_count - edw_count

            # Calculate TAFB totals
            total_tafb = sum(float(t.get("TAFB Hours", 0)) for t in self.trips_data if t.get("TAFB Hours"))
            edw_tafb = sum(
                float(t.get("TAFB Hours", 0))
                for t in self.trips_data
                if t.get("TAFB Hours") and (t.get("EDW") == "Yes" if isinstance(t.get("EDW"), str) else t.get("is_edw", False))
            )

            # Calculate duty day totals
            total_duty_days = sum(int(t.get("Duty Days", 0)) for t in self.trips_data if t.get("Duty Days"))
            edw_duty_days = sum(
                int(t.get("Duty Days", 0))
                for t in self.trips_data
                if t.get("Duty Days") and (t.get("EDW") == "Yes" if isinstance(t.get("EDW"), str) else t.get("is_edw", False))
            )

            summary_data = {
                "bid_period_id": bid_period_id,
                "total_trips": total_count,
                "edw_trips": edw_count,
                "non_edw_trips": non_edw_count,
                "trip_weighted_pct": round(self.trip_weighted_pct, 2),
                "total_tafb_hours": round(total_tafb, 2),
                "edw_tafb_hours": round(edw_tafb, 2),
                "tafb_weighted_pct": round(self.tafb_weighted_pct, 2),
                "total_duty_days": total_duty_days,
                "edw_duty_days": edw_duty_days,
                "duty_day_weighted_pct": round(self.duty_day_weighted_pct, 2)
            }

            result = await self.insert_row("edw_summary_stats", summary_data)
            if not result:
                self.save_status = f"Warning: Trips saved but summary stats failed - {self.error_message}"
                self.save_in_progress = False
                yield
                return

            # Success!
            self.save_status = f"✅ Successfully saved {trips_inserted} trips to database!"
            self.save_in_progress = False
            yield

        except Exception as e:
            print(f"Save error: {e}")
            import traceback
            traceback.print_exc()
            self.save_status = f"Error saving to database: {str(e)}"
            self.save_in_progress = False
            yield

    def generate_csv_export(self) -> str:
        """Generate CSV export of filtered trip data.

        Returns:
            CSV string of filtered trips with all columns.
        """
        if not self.filtered_trips:
            return ""

        # Convert to DataFrame for easy CSV generation
        df = pd.DataFrame(self.filtered_trips)

        # Select and order columns for export
        export_columns = [
            "Trip ID",
            "Frequency",
            "TAFB Hours",
            "TAFB Days",
            "Duty Days",
            "Max Duty Length",
            "Max Legs/Duty",
            "EDW",
            "Hot Standby",
        ]

        # Only include columns that exist
        columns_to_export = [col for col in export_columns if col in df.columns]
        df_export = df[columns_to_export]

        # Convert boolean columns to Yes/No
        if "EDW" in df_export.columns:
            df_export["EDW"] = df_export["EDW"].map({True: "Yes", False: "No"})
        if "Hot Standby" in df_export.columns:
            df_export["Hot Standby"] = df_export["Hot Standby"].map({True: "Yes", False: "No"})

        # Generate CSV
        return df_export.to_csv(index=False)

    def generate_excel_download(self) -> bytes:
        """Generate Excel workbook for download.

        Creates a multi-sheet Excel workbook with:
        - Trip Records (filtered trips data)
        - Duty Distribution (duty day counts and percentages)
        - Trip Summary (counts and EDW percentages)
        - Weighted Summary (weighted EDW metrics)
        - Duty Day Statistics (averages for All/EDW/Non-EDW)
        - Hot Standby Summary (if applicable)

        Returns:
            bytes: Excel file as bytes
        """
        if not self.filtered_trips:
            return b""

        try:
            # Convert filtered trips to DataFrame
            df_trips = pd.DataFrame(self.filtered_trips)

            # Duty Distribution (exclude Hot Standby)
            df_regular = df_trips[~df_trips["Hot Standby"]] if "Hot Standby" in df_trips.columns else df_trips
            duty_dist = df_regular[df_regular["Duty Days"] > 0].groupby("Duty Days")["Frequency"].sum().reset_index(name="Trips")
            duty_dist["Percent"] = (duty_dist["Trips"] / duty_dist["Trips"].sum() * 100).round(1) if len(duty_dist) > 0 else 0

            # Trip Summary
            trip_summary = pd.DataFrame({
                "Metric": ["Unique Pairings", "Total Trips", "EDW Trips", "Day Trips", "Hot Standby Trips"],
                "Value": [
                    self.unique_pairings,
                    self.total_trips,
                    self.edw_trips,
                    self.day_trips,
                    self.hot_standby_trips
                ],
            })

            # Weighted Summary
            weighted_summary = pd.DataFrame({
                "Metric": [
                    "Trip-weighted EDW trip %",
                    "TAFB-weighted EDW trip %",
                    "Duty-day-weighted EDW trip %",
                ],
                "Value": [
                    f"{self.trip_weighted_pct:.1f}%",
                    f"{self.tafb_weighted_pct:.1f}%",
                    f"{self.duty_day_weighted_pct:.1f}%",
                ],
            })

            # Duty Day Statistics
            duty_day_stats_df = pd.DataFrame(self.duty_day_stats)

            # Create Excel file in memory
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_trips.to_excel(writer, sheet_name="Trip Records", index=False)
                duty_dist.to_excel(writer, sheet_name="Duty Distribution", index=False)
                trip_summary.to_excel(writer, sheet_name="Trip Summary", index=False)
                weighted_summary.to_excel(writer, sheet_name="Weighted Summary", index=False)
                duty_day_stats_df.to_excel(writer, sheet_name="Duty Day Statistics", index=False)

            # Get bytes from BytesIO
            output.seek(0)
            return output.getvalue()

        except Exception as e:
            print(f"Error generating Excel: {e}")
            return b""

    def generate_pdf_download(self) -> bytes:
        """Generate PDF report for download.

        Creates a professional multi-page PDF report with:
        - Trip summary statistics
        - Weighted EDW metrics
        - Duty day statistics
        - Trip length distribution charts
        - EDW percentages analysis

        Returns:
            bytes: PDF file as bytes
        """
        if not self.filtered_trips:
            return b""

        try:
            # Prepare trip summary data (dict format for KPI cards)
            trip_summary = {
                "Unique Pairings": self.unique_pairings,
                "Total Trips": self.total_trips,
                "EDW Trips": self.edw_trips,
                "Day Trips": self.day_trips,
            }

            # Prepare weighted summary data (dict format for table)
            weighted_summary = {
                "Trip-weighted EDW trip %": f"{self.trip_weighted_pct:.1f}%",
                "TAFB-weighted EDW trip %": f"{self.tafb_weighted_pct:.1f}%",
                "Duty-day-weighted EDW trip %": f"{self.duty_day_weighted_pct:.1f}%",
            }

            # Prepare duty day stats (list of lists format for table)
            duty_day_stats = [["Metric", "All", "EDW", "Non-EDW"]]
            for stat in self.duty_day_stats:
                duty_day_stats.append([
                    stat["Metric"],
                    stat["All"],
                    stat["EDW"],
                    stat["Non-EDW"]
                ])

            # Prepare trip length distribution (list of dicts format)
            df_trips = pd.DataFrame(self.filtered_trips)
            df_regular = df_trips[~df_trips["Hot Standby"]] if "Hot Standby" in df_trips.columns else df_trips
            duty_dist = df_regular[df_regular["Duty Days"] > 0].groupby("Duty Days")["Frequency"].sum().reset_index(name="Trips")

            trip_length_distribution = [
                {"duty_days": int(row["Duty Days"]), "trips": int(row["Trips"])}
                for _, row in duty_dist.iterrows()
            ]

            # Prepare data dictionary for create_pdf_report
            pdf_data = {
                "title": f"{self.domicile} {self.aircraft} – Bid {self.bid_period}",
                "subtitle": "Executive Dashboard • Pairing Breakdown & Duty-Day Metrics",
                "trip_summary": trip_summary,
                "weighted_summary": weighted_summary,
                "duty_day_stats": duty_day_stats,
                "trip_length_distribution": trip_length_distribution,
                "notes": "Generated from EDW Pairing Analyzer",
                "generated_by": "Aero Crew Data App"
            }

            # Branding configuration
            branding = {
                "primary_hex": "#1E40AF",
                "accent_hex": "#F3F4F6",
                "rule_hex": "#E5E7EB",
                "muted_hex": "#6B7280",
                "bg_alt_hex": "#FAFAFA",
                "sky_hex": "#2E9BE8",
                "logo_path": None,
                "title_left": f"{self.domicile} {self.aircraft} – Bid {self.bid_period} | Pairing Analysis Report"
            }

            # Create PDF in temporary file
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                tmp_path = tmp_file.name

            try:
                # Generate PDF using export_pdf module
                create_pdf_report(pdf_data, tmp_path, branding)

                # Read PDF bytes
                with open(tmp_path, 'rb') as f:
                    pdf_bytes = f.read()

                return pdf_bytes

            finally:
                # Clean up temporary file
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        except Exception as e:
            print(f"Error generating PDF: {e}")
            import traceback
            traceback.print_exc()
            return b""

    # Download Event Handlers
    # These methods return rx.download() EventSpecs for use in on_click handlers

    def download_csv(self):
        """Event handler for CSV download from table component."""
        csv_data = self.generate_csv_export()
        return rx.download(
            data=csv_data.encode('utf-8'),
            filename="trip_records.csv",
        )

    def download_excel(self):
        """Event handler for Excel download from downloads component."""
        excel_bytes = self.generate_excel_download()
        filename = f"{self.domicile}_{self.aircraft}_Bid{self.bid_period}_EDW_Report.xlsx"
        return rx.download(
            data=excel_bytes,
            filename=filename,
        )

    def download_pdf(self):
        """Event handler for PDF download from downloads component."""
        pdf_bytes = self.generate_pdf_download()
        filename = f"{self.domicile}_{self.aircraft}_Bid{self.bid_period}_EDW_Report.pdf"
        return rx.download(
            data=pdf_bytes,
            filename=filename,
        )
