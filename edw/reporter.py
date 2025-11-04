"""
Main orchestration for EDW analysis.

This module coordinates the entire analysis workflow:
- Parses pairing PDFs
- Analyzes trips for EDW status
- Generates statistics
- Produces Excel and PDF reports
"""

from pathlib import Path

import pandas as pd

# Import PDF generation from centralized module
from pdf_generation import create_edw_pdf_report

from .analyzer import is_edw_trip, is_hot_standby
from .excel_export import build_edw_dataframes, save_edw_excel
from .parser import (
    parse_duty_day_details,
    parse_duty_days,
    parse_max_duty_day_length,
    parse_max_legs_per_duty_day,
    parse_pairings,
    parse_tafb,
    parse_trip_frequency,
    parse_trip_id,
)


# -------------------------------------------------------------------
# Main Reporting Function
# -------------------------------------------------------------------
def run_edw_report(
    pdf_path: Path,
    output_dir: Path,
    domicile: str,
    aircraft: str,
    bid_period: str,
    progress_callback=None,
):
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

        trip_records.append(
            {
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
            }
        )

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
    duty_dist = stats_dfs["duty_dist"]
    trip_summary = stats_dfs["trip_summary"]
    weighted_summary = stats_dfs["weighted_summary"]
    duty_day_stats = stats_dfs["duty_day_stats"]
    hot_standby_summary = stats_dfs["hot_standby_summary"]

    if progress_callback:
        progress_callback(65, "Generating Excel workbook...")

    # Excel export
    excel_path = output_dir / f"{domicile}_{aircraft}_Bid{bid_period}_EDW_Report_Data.xlsx"
    save_edw_excel(
        excel_path,
        df_trips,
        duty_dist,
        trip_summary,
        weighted_summary,
        duty_day_stats,
        hot_standby_summary,
    )

    if progress_callback:
        progress_callback(70, "Creating PDF report...")

    # -------------------- PDF Report Generation --------------------
    # Prepare data for PDF generation module
    pdf_report_path = output_dir / f"{domicile}_{aircraft}_Bid{bid_period}_EDW_Report.pdf"

    # Convert DataFrames to formats expected by create_edw_pdf_report
    trip_summary_dict = {row["Metric"]: row["Value"] for _, row in trip_summary.iterrows()}

    weighted_summary_dict = {row["Metric"]: row["Value"] for _, row in weighted_summary.iterrows()}

    # Convert duty_day_stats DataFrame to list of lists
    duty_day_stats_list = [list(duty_day_stats.columns)] + duty_day_stats.values.tolist()

    # Convert duty_dist DataFrame to list of dicts for charts
    trip_length_dist = [
        {"duty_days": int(row["Duty Days"]), "trips": int(row["Trips"])}
        for _, row in duty_dist.iterrows()
    ]

    # Build report data dictionary
    report_data = {
        "title": f"{domicile} {aircraft} – Bid {bid_period} | Pairing Analysis Report",
        "subtitle": "EDW (Early/Day/Window) Trip Analysis",
        "trip_summary": trip_summary_dict,
        "weighted_summary": weighted_summary_dict,
        "duty_day_stats": duty_day_stats_list,
        "trip_length_distribution": trip_length_dist,
        "notes": f"Analysis of {len(trips)} pairings",
        "generated_by": "EDW Pairing Analyzer",
    }

    # Generate PDF using centralized module
    create_edw_pdf_report(data=report_data, output_path=str(pdf_report_path))

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
