"""
Excel workbook generation for EDW analysis reports.

This module handles creating structured Excel files with multiple sheets
containing trip records, statistics, and summaries.
"""

from pathlib import Path

import pandas as pd

from .parser import clean_text


def save_edw_excel(
    output_path: Path,
    df_trips,
    duty_dist,
    trip_summary,
    weighted_summary,
    duty_day_stats,
    hot_standby_summary,
):
    """
    Save EDW analysis data to Excel workbook with multiple sheets.

    Args:
        output_path: Path where Excel file should be saved
        df_trips: DataFrame with all trip records
        duty_dist: DataFrame with duty day distribution
        trip_summary: DataFrame with trip summary statistics
        weighted_summary: DataFrame with weighted EDW percentages
        duty_day_stats: DataFrame with duty day statistics
        hot_standby_summary: DataFrame with hot standby summary

    Returns:
        Path to the created Excel file
    """
    with pd.ExcelWriter(output_path) as writer:
        # Write each sheet
        df_trips.to_excel(writer, sheet_name=clean_text("Trip Records"), index=False)
        duty_dist.to_excel(writer, sheet_name=clean_text("Duty Distribution"), index=False)
        trip_summary.to_excel(writer, sheet_name=clean_text("Trip Summary"), index=False)
        weighted_summary.to_excel(writer, sheet_name=clean_text("Weighted Summary"), index=False)
        duty_day_stats.to_excel(writer, sheet_name=clean_text("Duty Day Statistics"), index=False)
        hot_standby_summary.to_excel(
            writer, sheet_name=clean_text("Hot Standby Summary"), index=False
        )

    return output_path


def build_edw_dataframes(df_trips):
    """
    Build all statistical dataframes from trip records.

    This function calculates all statistics and creates DataFrames ready for Excel export.

    Args:
        df_trips: DataFrame with trip records (must include columns: Frequency, EDW, TAFB Hours,
                  Duty Days, Hot Standby, Duty Day Details)

    Returns:
        Dictionary with keys:
        - 'duty_dist': Duty day distribution DataFrame
        - 'trip_summary': Trip summary DataFrame
        - 'weighted_summary': Weighted EDW percentages DataFrame
        - 'duty_day_stats': Duty day statistics DataFrame
        - 'hot_standby_summary': Hot standby summary DataFrame
    """
    # Duty Day distribution (exclude 0s and Hot Standby) - weighted by frequency
    # Filter out Hot Standby pairings from distribution analysis
    df_regular_trips = df_trips[~df_trips["Hot Standby"]]
    duty_dist = (
        df_regular_trips[df_regular_trips["Duty Days"] > 0]
        .groupby("Duty Days")["Frequency"]
        .sum()
        .reset_index(name="Trips")
    )
    duty_dist["Percent"] = (duty_dist["Trips"] / duty_dist["Trips"].sum() * 100).round(1)

    # Summaries - account for frequency
    unique_pairings = len(df_trips)
    total_trips = df_trips["Frequency"].sum()  # Total number of actual trips
    edw_trips = df_trips[df_trips["EDW"]]["Frequency"].sum()  # EDW trips weighted by frequency
    hot_standby_pairings = len(df_trips[df_trips["Hot Standby"]])  # Unique hot standby pairings
    hot_standby_trips = df_trips[df_trips["Hot Standby"]][
        "Frequency"
    ].sum()  # Hot standby occurrences

    trip_weighted = edw_trips / total_trips * 100 if total_trips else 0

    # TAFB weighted - multiply TAFB by frequency
    tafb_total = (df_trips["TAFB Hours"] * df_trips["Frequency"]).sum()
    tafb_edw = (
        df_trips[df_trips["EDW"]]["TAFB Hours"] * df_trips[df_trips["EDW"]]["Frequency"]
    ).sum()
    tafb_weighted = (tafb_edw / tafb_total * 100) if tafb_total > 0 else 0

    # Duty day weighted - multiply duty days by frequency
    dutyday_total = (df_trips["Duty Days"] * df_trips["Frequency"]).sum()
    dutyday_edw = (
        df_trips[df_trips["EDW"]]["Duty Days"] * df_trips[df_trips["EDW"]]["Frequency"]
    ).sum()
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
                if duty_day.get("is_edw", False):
                    edw_duty_days.append(duty_day)
                else:
                    non_edw_duty_days.append(duty_day)

    # Calculate averages
    avg_legs_all = (
        sum(dd["num_legs"] for dd in all_duty_days) / len(all_duty_days) if all_duty_days else 0
    )
    avg_legs_edw = (
        sum(dd["num_legs"] for dd in edw_duty_days) / len(edw_duty_days) if edw_duty_days else 0
    )
    avg_legs_non_edw = (
        sum(dd["num_legs"] for dd in non_edw_duty_days) / len(non_edw_duty_days)
        if non_edw_duty_days
        else 0
    )

    avg_duration_all = (
        sum(dd["duration_hours"] for dd in all_duty_days) / len(all_duty_days)
        if all_duty_days
        else 0
    )
    avg_duration_edw = (
        sum(dd["duration_hours"] for dd in edw_duty_days) / len(edw_duty_days)
        if edw_duty_days
        else 0
    )
    avg_duration_non_edw = (
        sum(dd["duration_hours"] for dd in non_edw_duty_days) / len(non_edw_duty_days)
        if non_edw_duty_days
        else 0
    )

    avg_block_all = (
        sum(dd["block_hours"] for dd in all_duty_days) / len(all_duty_days) if all_duty_days else 0
    )
    avg_block_edw = (
        sum(dd["block_hours"] for dd in edw_duty_days) / len(edw_duty_days) if edw_duty_days else 0
    )
    avg_block_non_edw = (
        sum(dd["block_hours"] for dd in non_edw_duty_days) / len(non_edw_duty_days)
        if non_edw_duty_days
        else 0
    )

    avg_credit_all = (
        sum(dd["credit_hours"] for dd in all_duty_days) / len(all_duty_days) if all_duty_days else 0
    )
    avg_credit_edw = (
        sum(dd["credit_hours"] for dd in edw_duty_days) / len(edw_duty_days) if edw_duty_days else 0
    )
    avg_credit_non_edw = (
        sum(dd["credit_hours"] for dd in non_edw_duty_days) / len(non_edw_duty_days)
        if non_edw_duty_days
        else 0
    )

    # Build summary DataFrames
    trip_summary = pd.DataFrame(
        {
            "Metric": ["Unique Pairings", "Total Trips", "EDW Trips", "Day Trips", "Pct EDW"],
            "Value": [
                unique_pairings,
                total_trips,
                edw_trips,
                total_trips - edw_trips,
                f"{trip_weighted:.1f}%",
            ],
        }
    )

    weighted_summary = pd.DataFrame(
        {
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
        }
    )

    duty_day_stats = pd.DataFrame(
        {
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
        }
    )

    hot_standby_summary = pd.DataFrame(
        {
            "Metric": ["Hot Standby Pairings", "Hot Standby Trips"],
            "Value": [hot_standby_pairings, hot_standby_trips],
        }
    )

    return {
        "duty_dist": duty_dist,
        "trip_summary": trip_summary,
        "weighted_summary": weighted_summary,
        "duty_day_stats": duty_day_stats,
        "hot_standby_summary": hot_standby_summary,
    }
