"""
pdf_generation/bid_line_pdf.py
Bid line analysis PDF report generation.

Creates professional 3-page PDF reports with:
- Summary statistics and KPI cards
- Pay period comparisons
- Reserve line analysis
- Distribution charts (CT, BT, DO, DD)
- Buy-up analysis
"""

import math
import os
import tempfile
from typing import Any, Dict, Optional

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER

# ReportLab imports
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    HRFlowable,
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

from config import BUYUP_THRESHOLD_HOURS

# Import from models and config
from models.pdf_models import ReportMetadata

# Import from our pdf_generation modules
from .base import (
    DEFAULT_BRANDING,
    draw_footer,
    draw_header,
    hex_to_reportlab_color,
    make_kpi_row,
    make_styled_table,
)
from .charts import save_bar_chart, save_percentage_bar_chart, save_pie_chart


def _create_binned_distribution(series: pd.Series, bin_width: float, label: str) -> pd.DataFrame:
    """
    Create binned distribution for continuous variables.

    Args:
        series: Pandas Series with numeric data
        bin_width: Width of each bin
        label: Column label for the range

    Returns:
        DataFrame with columns: [label, 'Lines', 'Percent']
    """
    if series.empty:
        return pd.DataFrame(columns=[label, "Lines", "Percent"])

    minimum = float(series.min())
    maximum = float(series.max())
    if bin_width <= 0:
        bin_width = max((maximum - minimum) / 5, 1) or 1

    start = math.floor(minimum / bin_width) * bin_width
    end = math.ceil(maximum / bin_width) * bin_width
    if end <= start:
        end = start + bin_width

    edges = [start]
    while edges[-1] < end:
        edges.append(edges[-1] + bin_width)
    if edges[-1] < maximum + 1e-6:
        edges.append(edges[-1] + bin_width)

    bins = pd.cut(series, bins=edges, include_lowest=True, right=False)
    counts = bins.value_counts().sort_index()
    total = counts.sum()

    rows = []
    for interval, count in counts.items():
        left = interval.left
        right = interval.right
        label_text = f"{left:.1f}-{right:.1f}" if bin_width < 1 else f"{left:.0f}-{right:.0f}"
        percent = f"{(count / total * 100):.1f}%" if total else "0.0%"
        rows.append({label: label_text, "Lines": int(count), "Percent": percent})

    return pd.DataFrame(rows)


def _create_value_distribution(series: pd.Series, label: str) -> pd.DataFrame:
    """
    Create distribution for discrete values (e.g., days off).

    Args:
        series: Pandas Series with discrete numeric data
        label: Column label for the value

    Returns:
        DataFrame with columns: [label, 'Lines', 'Percent']
    """
    if series.empty:
        return pd.DataFrame(columns=[label, "Lines", "Percent"])

    # Convert to integers for day counts
    series_int = series.astype(int)
    counts = series_int.value_counts().sort_index()
    total = counts.sum()

    rows = []
    for value, count in counts.items():
        percent = f"{(count / total * 100):.1f}%" if total else "0.0%"
        rows.append({label: int(value), "Lines": int(count), "Percent": percent})

    return pd.DataFrame(rows)


def create_bid_line_pdf_report(
    df: pd.DataFrame,
    metadata: Optional[ReportMetadata] = None,
    pay_periods: Optional[pd.DataFrame] = None,
    reserve_lines: Optional[pd.DataFrame] = None,
    branding: Optional[Dict[str, Any]] = None,
) -> bytes:
    """
    Create a professional PDF report for bid line analysis.

    Args:
        df: DataFrame with bid line data (columns: Line, CT, BT, DO, DD, etc.)
        metadata: Report metadata (title, subtitle, filters)
        pay_periods: DataFrame with pay period data (columns: Line, Period, CT, BT, DO, DD)
        reserve_lines: DataFrame with reserve line data (columns: Line, IsReserve, IsHotStandby, CaptainSlots, FOSlots)
        branding: Optional branding dictionary

    Returns:
        PDF bytes

    Raises:
        ValueError: If DataFrame is empty
    """
    if df.empty:
        raise ValueError("Cannot render PDF for empty dataset.")

    metadata = metadata or ReportMetadata()
    branding = {**DEFAULT_BRANDING, **(branding or {})}

    # Identify reserve lines (exclude regular reserve, keep HSBY for CT/DO/DD)
    reserve_line_numbers = set()  # Regular reserve lines - exclude from everything
    hsby_line_numbers = set()  # HSBY lines - exclude only from BT

    if reserve_lines is not None and not reserve_lines.empty:
        if "IsReserve" in reserve_lines.columns and "IsHotStandby" in reserve_lines.columns:
            # Regular reserve lines (not HSBY): exclude from everything
            regular_reserve_mask = reserve_lines["IsReserve"] & ~reserve_lines["IsHotStandby"]
            reserve_line_numbers = set(reserve_lines[regular_reserve_mask]["Line"].tolist())

            # HSBY lines: exclude only from BT
            hsby_mask = reserve_lines["IsHotStandby"]
            hsby_line_numbers = set(reserve_lines[hsby_mask]["Line"].tolist())

    # Filter dataframes
    # For CT, DO, DD: exclude regular reserve (keep HSBY)
    df_non_reserve = df[~df["Line"].isin(reserve_line_numbers)] if reserve_line_numbers else df

    # For BT: exclude both regular reserve AND HSBY
    all_exclude_for_bt = reserve_line_numbers | hsby_line_numbers
    df_for_bt = df[~df["Line"].isin(all_exclude_for_bt)] if all_exclude_for_bt else df

    # Create document
    doc = SimpleDocTemplate(
        tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=60,  # Space for header
        bottomMargin=50,  # Space for footer
    )

    # Prepare styles
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#111827"),
        spaceAfter=6,
        alignment=TA_CENTER,
    )

    subtitle_style = ParagraphStyle(
        "CustomSubtitle",
        parent=styles["Normal"],
        fontSize=12,
        textColor=hex_to_reportlab_color(branding["muted_hex"]),
        spaceAfter=20,
        alignment=TA_CENTER,
    )

    heading2_style = ParagraphStyle(
        "CustomHeading2",
        parent=styles["Heading2"],
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#111827"),
        spaceAfter=6,
        spaceBefore=12,
    )

    body_style = ParagraphStyle(
        "CustomBody",
        parent=styles["Normal"],
        fontSize=10,
        textColor=hex_to_reportlab_color(branding["muted_hex"]),
        spaceAfter=12,
    )

    # Build story (content flow)
    story = []
    temp_files = []  # Track temp files for cleanup

    try:
        # PAGE 1
        # Title and subtitle
        story.append(Paragraph(metadata.title, title_style))
        if metadata.subtitle:
            story.append(Paragraph(metadata.subtitle, subtitle_style))
        else:
            story.append(Spacer(1, 12))

        story.append(Spacer(1, 12))

        # KPI Cards - Summary Statistics with ranges
        ct_stats = (
            df_non_reserve["CT"].agg(["mean", "min", "max"])
            if not df_non_reserve.empty
            else df["CT"].agg(["mean", "min", "max"])
        )
        bt_stats = (
            df_for_bt["BT"].agg(["mean", "min", "max"])
            if not df_for_bt.empty
            else df["BT"].agg(["mean", "min", "max"])
        )
        do_stats = (
            df_non_reserve["DO"].agg(["mean", "min", "max"])
            if not df_non_reserve.empty
            else df["DO"].agg(["mean", "min", "max"])
        )
        dd_stats = (
            df_non_reserve["DD"].agg(["mean", "min", "max"])
            if not df_non_reserve.empty
            else df["DD"].agg(["mean", "min", "max"])
        )

        kpi_metrics = {
            "Avg Credit": {
                "value": f"{ct_stats['mean']:.1f}",
                "range": f"↑ Range {ct_stats['min']:.1f}-{ct_stats['max']:.1f}",
            },
            "Avg Block": {
                "value": f"{bt_stats['mean']:.1f}",
                "range": f"↑ Range {bt_stats['min']:.1f}-{bt_stats['max']:.1f}",
            },
            "Avg Days Off": {
                "value": f"{do_stats['mean']:.1f}",
                "range": f"↑ Range {int(do_stats['min'])}-{int(do_stats['max'])}",
            },
            "Avg Duty Days": {
                "value": f"{dd_stats['mean']:.1f}",
                "range": f"↑ Range {int(dd_stats['min'])}-{int(dd_stats['max'])}",
            },
        }
        kpi_table = make_kpi_row(kpi_metrics, branding)
        story.append(kpi_table)
        story.append(Spacer(1, 20))

        # Horizontal rule
        hr = HRFlowable(
            width="100%",
            thickness=1,
            color=hex_to_reportlab_color(branding["rule_hex"]),
            spaceAfter=16,
            spaceBefore=4,
        )
        story.append(hr)

        # Summary Statistics Table
        story.append(Paragraph("Summary Statistics", heading2_style))
        story.append(Spacer(1, 8))

        # Calculate statistics
        ct_summary = (
            df_non_reserve["CT"].agg(["min", "max", "mean", "median", "std"])
            if not df_non_reserve.empty
            else df["CT"].agg(["min", "max", "mean", "median", "std"])
        )
        bt_summary = (
            df_for_bt["BT"].agg(["min", "max", "mean", "median", "std"])
            if not df_for_bt.empty
            else df["BT"].agg(["min", "max", "mean", "median", "std"])
        )
        do_summary = (
            df_non_reserve["DO"].agg(["min", "max", "mean", "median", "std"])
            if not df_non_reserve.empty
            else df["DO"].agg(["min", "max", "mean", "median", "std"])
        )
        dd_summary = (
            df_non_reserve["DD"].agg(["min", "max", "mean", "median", "std"])
            if not df_non_reserve.empty
            else df["DD"].agg(["min", "max", "mean", "median", "std"])
        )

        summary_data = [["Metric", "Min", "Max", "Average", "Median", "Std Dev"]]
        for metric, stats in [
            ("CT", ct_summary),
            ("BT", bt_summary),
            ("DO", do_summary),
            ("DD", dd_summary),
        ]:
            summary_data.append(
                [
                    metric,
                    f"{stats['min']:.2f}",
                    f"{stats['max']:.2f}",
                    f"{stats['mean']:.2f}",
                    f"{stats['median']:.2f}",
                    f"{stats['std']:.2f}",
                ]
            )

        summary_table = make_styled_table(summary_data, [80, 70, 70, 80, 70, 80], branding)
        story.append(summary_table)
        story.append(Spacer(1, 16))

        # Pay Period Averages
        if pay_periods is not None and not pay_periods.empty:
            subset = pay_periods[pay_periods["Line"].isin(df["Line"])].copy()

            if not subset.empty:
                story.append(Paragraph("Pay Period Averages", heading2_style))
                story.append(Spacer(1, 8))

                # Filter for pay period averages
                subset_non_reserve = (
                    subset[~subset["Line"].isin(reserve_line_numbers)]
                    if reserve_line_numbers
                    else subset
                )
                subset_for_bt = (
                    subset[~subset["Line"].isin(all_exclude_for_bt)]
                    if all_exclude_for_bt
                    else subset
                )

                # Calculate metrics
                period_data = [["Pay Period", "Avg CT", "Avg BT", "Avg DO", "Avg DD"]]
                for period in sorted(subset["Period"].unique()):
                    period_subset_non_reserve = subset_non_reserve[
                        subset_non_reserve["Period"] == period
                    ]
                    period_subset_for_bt = subset_for_bt[subset_for_bt["Period"] == period]

                    ct_avg = (
                        period_subset_non_reserve["CT"].mean()
                        if not period_subset_non_reserve.empty
                        else 0
                    )
                    bt_avg = (
                        period_subset_for_bt["BT"].mean() if not period_subset_for_bt.empty else 0
                    )
                    do_avg = (
                        period_subset_non_reserve["DO"].mean()
                        if not period_subset_non_reserve.empty
                        else 0
                    )
                    dd_avg = (
                        period_subset_non_reserve["DD"].mean()
                        if not period_subset_non_reserve.empty
                        else 0
                    )

                    period_data.append(
                        [
                            f"PP{int(period)}",
                            f"{ct_avg:.2f}",
                            f"{bt_avg:.2f}",
                            f"{do_avg:.2f}",
                            f"{dd_avg:.2f}",
                        ]
                    )

                # Add overall row
                ct_overall = subset_non_reserve["CT"].mean() if not subset_non_reserve.empty else 0
                bt_overall = subset_for_bt["BT"].mean() if not subset_for_bt.empty else 0
                do_overall = subset_non_reserve["DO"].mean() if not subset_non_reserve.empty else 0
                dd_overall = subset_non_reserve["DD"].mean() if not subset_non_reserve.empty else 0

                period_data.append(
                    [
                        "Overall",
                        f"{ct_overall:.2f}",
                        f"{bt_overall:.2f}",
                        f"{do_overall:.2f}",
                        f"{dd_overall:.2f}",
                    ]
                )

                period_table = make_styled_table(period_data, [100, 80, 80, 80, 80], branding)
                story.append(period_table)
                story.append(Spacer(1, 16))

        # Reserve Line Statistics
        if reserve_lines is not None and not reserve_lines.empty:
            reserve_subset = reserve_lines[reserve_lines["Line"].isin(df["Line"])].copy()
            reserve_subset = reserve_subset[reserve_subset["IsReserve"]]

            if not reserve_subset.empty:
                story.append(Paragraph("Reserve Lines Analysis", heading2_style))
                story.append(Spacer(1, 8))

                total_reserve = len(reserve_subset)
                captain_slots = int(reserve_subset["CaptainSlots"].sum())
                fo_slots = int(reserve_subset["FOSlots"].sum())
                total_slots = captain_slots + fo_slots
                total_regular = len(df) - total_reserve

                reserve_percentage = (
                    (total_slots / total_regular * 100) if total_regular > 0 else 0.0
                )

                reserve_data = [
                    ["Metric", "Value"],
                    ["Total Reserve Lines", str(total_reserve)],
                    ["Captain Slots", str(captain_slots)],
                    ["First Officer Slots", str(fo_slots)],
                    ["Total Reserve Slots", str(total_slots)],
                    ["Regular Lines", str(total_regular)],
                    ["Reserve Percentage", f"{reserve_percentage:.1f}%"],
                ]

                reserve_table = make_styled_table(reserve_data, [200, 100], branding)
                story.append(reserve_table)
                story.append(Spacer(1, 16))

        # Distributions Section
        story.append(Spacer(1, 20))
        story.append(hr)
        story.append(Spacer(1, 16))

        # CT Distribution (exclude reserve lines, consistent with KPI metrics)
        ct_distribution = (
            _create_binned_distribution(df_non_reserve["CT"], bin_width=5.0, label="Range")
            if not df_non_reserve.empty
            else pd.DataFrame()
        )
        if not ct_distribution.empty:
            ct_content = []
            ct_content.append(Paragraph("Distribution Analysis", heading2_style))
            ct_content.append(Spacer(1, 12))
            ct_content.append(Paragraph("Credit Time (CT) Distribution", heading2_style))
            ct_content.append(Spacer(1, 8))

            ct_data = [["Range", "Lines", "Percent"]]
            for _, row in ct_distribution.iterrows():
                ct_data.append([row["Range"], str(row["Lines"]), row["Percent"]])

            ct_table = make_styled_table(ct_data, [120, 100, 100], branding)
            ct_content.append(ct_table)
            ct_content.append(Spacer(1, 12))

            # CT Charts - Side by side
            ct_chart_path = save_bar_chart(
                ct_distribution,
                "Credit Time Distribution (Count)",
                "Range",
                "Lines",
                "Credit Time Range",
                "Number of Lines",
                "#1BB3A4",  # Brand Teal
            )
            ct_pct_chart_path = save_percentage_bar_chart(
                ct_distribution,
                "Credit Time Distribution (Percentage)",
                "Range",
                "Percent",
                "Credit Time Range",
                "#2E9BE8",  # Brand Sky
            )

            if ct_chart_path and ct_pct_chart_path:
                temp_files.extend([ct_chart_path, ct_pct_chart_path])
                from reportlab.lib.units import inch
                from reportlab.platypus import Table, TableStyle

                ct_img = Image(ct_chart_path, width=3.5 * inch, height=2.6 * inch)
                ct_pct_img = Image(ct_pct_chart_path, width=3.5 * inch, height=2.6 * inch)

                # Place charts side by side in a table
                charts_table = Table([[ct_img, ct_pct_img]], colWidths=[3.6 * inch, 3.6 * inch])
                charts_table.setStyle(
                    TableStyle(
                        [
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ]
                    )
                )
                ct_content.append(charts_table)

            # Keep title, table, and charts together
            story.append(KeepTogether(ct_content))
            story.append(Spacer(1, 20))

        # BT Distribution (exclude reserve AND HSBY, consistent with KPI metrics)
        bt_distribution = (
            _create_binned_distribution(df_for_bt["BT"], bin_width=5.0, label="Range")
            if not df_for_bt.empty
            else pd.DataFrame()
        )
        if not bt_distribution.empty:
            bt_content = []
            bt_content.append(Paragraph("Block Time (BT) Distribution", heading2_style))
            bt_content.append(Spacer(1, 8))

            bt_data = [["Range", "Lines", "Percent"]]
            for _, row in bt_distribution.iterrows():
                bt_data.append([row["Range"], str(row["Lines"]), row["Percent"]])

            bt_table = make_styled_table(bt_data, [120, 100, 100], branding)
            bt_content.append(bt_table)
            bt_content.append(Spacer(1, 12))

            # BT Charts - Side by side
            bt_chart_path = save_bar_chart(
                bt_distribution,
                "Block Time Distribution (Count)",
                "Range",
                "Lines",
                "Block Time Range",
                "Number of Lines",
                "#0C7C73",  # Dark Teal
            )
            bt_pct_chart_path = save_percentage_bar_chart(
                bt_distribution,
                "Block Time Distribution (Percentage)",
                "Range",
                "Percent",
                "Block Time Range",
                "#5BCFC2",  # Light Teal
            )

            if bt_chart_path and bt_pct_chart_path:
                temp_files.extend([bt_chart_path, bt_pct_chart_path])
                from reportlab.lib.units import inch
                from reportlab.platypus import Table, TableStyle

                bt_img = Image(bt_chart_path, width=3.5 * inch, height=2.6 * inch)
                bt_pct_img = Image(bt_pct_chart_path, width=3.5 * inch, height=2.6 * inch)

                # Place charts side by side in a table
                charts_table = Table([[bt_img, bt_pct_img]], colWidths=[3.6 * inch, 3.6 * inch])
                charts_table.setStyle(
                    TableStyle(
                        [
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ]
                    )
                )
                bt_content.append(charts_table)

            # Keep title, table, and charts together
            story.append(KeepTogether(bt_content))
            story.append(Spacer(1, 20))

        # PAGE 3 - Days Off and Buy-up Analysis
        story.append(PageBreak())

        # Days Off Distribution - Use pay_periods for accurate counts (not averaged)
        # If pay_periods available, use it to show both PP1 and PP2 separately (2 entries per line)
        # Otherwise fall back to averaged DO from main df
        if pay_periods is not None and not pay_periods.empty:
            # Filter pay periods to match lines in df
            filtered_pay_periods = pay_periods[pay_periods["Line"].isin(df["Line"])]
            # Exclude reserve lines
            pp_non_reserve = (
                filtered_pay_periods[~filtered_pay_periods["Line"].isin(reserve_line_numbers)]
                if reserve_line_numbers
                else filtered_pay_periods
            )
            do_distribution = (
                _create_value_distribution(pp_non_reserve["DO"], label="Days Off")
                if not pp_non_reserve.empty
                else pd.DataFrame()
            )
            do_note = "Showing total averages for both pay periods combined"
        else:
            do_distribution = (
                _create_value_distribution(df_non_reserve["DO"], label="Days Off")
                if not df_non_reserve.empty
                else pd.DataFrame()
            )
            do_note = "Note: Showing averaged values across pay periods"
        if not do_distribution.empty:
            do_content = []
            do_content.append(Paragraph("Days Off (DO) Distribution", heading2_style))
            do_content.append(Spacer(1, 8))

            do_data = [["Days Off", "Lines", "Percent"]]
            for _, row in do_distribution.iterrows():
                do_data.append([str(row["Days Off"]), str(row["Lines"]), row["Percent"]])

            do_table = make_styled_table(do_data, [120, 100, 100], branding)
            do_content.append(do_table)
            do_content.append(Spacer(1, 12))

            # DO Charts - Side by side
            do_chart_path = save_bar_chart(
                do_distribution,
                "Days Off Distribution (Count)",
                "Days Off",
                "Lines",
                "Days Off",
                "Number of Lines",
                "#2E9BE8",  # Brand Sky
            )
            do_pct_chart_path = save_percentage_bar_chart(
                do_distribution,
                "Days Off Distribution (Percentage)",
                "Days Off",
                "Percent",
                "Days Off",
                "#7EC8F6",  # Light Sky
            )

            if do_chart_path and do_pct_chart_path:
                temp_files.extend([do_chart_path, do_pct_chart_path])
                from reportlab.lib.units import inch
                from reportlab.platypus import Table, TableStyle

                do_img = Image(do_chart_path, width=3.5 * inch, height=2.6 * inch)
                do_pct_img = Image(do_pct_chart_path, width=3.5 * inch, height=2.6 * inch)

                # Place charts side by side in a table
                charts_table = Table([[do_img, do_pct_img]], colWidths=[3.6 * inch, 3.6 * inch])
                charts_table.setStyle(
                    TableStyle(
                        [
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ]
                    )
                )
                do_content.append(charts_table)

            # Add note about data source
            do_content.append(Spacer(1, 8))
            do_content.append(Paragraph(do_note, body_style))

            # Keep title, table, and charts together
            story.append(KeepTogether(do_content))
            story.append(Spacer(1, 20))

        # Duty Days Distribution - Use pay_periods for accurate counts (not averaged)
        if pay_periods is not None and not pay_periods.empty:
            # Filter pay periods to match lines in df
            filtered_pay_periods = pay_periods[pay_periods["Line"].isin(df["Line"])]
            # Exclude reserve lines
            pp_non_reserve = (
                filtered_pay_periods[~filtered_pay_periods["Line"].isin(reserve_line_numbers)]
                if reserve_line_numbers
                else filtered_pay_periods
            )
            dd_distribution = (
                _create_value_distribution(pp_non_reserve["DD"], label="Duty Days")
                if not pp_non_reserve.empty
                else pd.DataFrame()
            )
            dd_note = "Showing total averages for both pay periods combined"
        else:
            dd_distribution = (
                _create_value_distribution(df_non_reserve["DD"], label="Duty Days")
                if not df_non_reserve.empty
                else pd.DataFrame()
            )
            dd_note = "Note: Showing averaged values across pay periods"
        if not dd_distribution.empty:
            dd_content = []
            dd_content.append(Paragraph("Duty Days (DD) Distribution", heading2_style))
            dd_content.append(Spacer(1, 8))

            dd_data = [["Duty Days", "Lines", "Percent"]]
            for _, row in dd_distribution.iterrows():
                dd_data.append([str(row["Duty Days"]), str(row["Lines"]), row["Percent"]])

            dd_table = make_styled_table(dd_data, [120, 100, 100], branding)
            dd_content.append(dd_table)
            dd_content.append(Spacer(1, 12))

            # DD Charts - Side by side
            dd_chart_path = save_bar_chart(
                dd_distribution,
                "Duty Days Distribution (Count)",
                "Duty Days",
                "Lines",
                "Duty Days",
                "Number of Lines",
                "#1BB3A4",  # Brand Teal
            )
            dd_pct_chart_path = save_percentage_bar_chart(
                dd_distribution,
                "Duty Days Distribution (Percentage)",
                "Duty Days",
                "Percent",
                "Duty Days",
                "#0C7C73",  # Dark Teal
            )

            if dd_chart_path and dd_pct_chart_path:
                temp_files.extend([dd_chart_path, dd_pct_chart_path])
                from reportlab.lib.units import inch
                from reportlab.platypus import Table, TableStyle

                dd_img = Image(dd_chart_path, width=3.5 * inch, height=2.6 * inch)
                dd_pct_img = Image(dd_pct_chart_path, width=3.5 * inch, height=2.6 * inch)

                # Place charts side by side in a table
                charts_table = Table([[dd_img, dd_pct_img]], colWidths=[3.6 * inch, 3.6 * inch])
                charts_table.setStyle(
                    TableStyle(
                        [
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ]
                    )
                )
                dd_content.append(charts_table)

            # Add note about data source
            dd_content.append(Spacer(1, 8))
            dd_content.append(Paragraph(dd_note, body_style))

            # Keep title, table, and charts together
            story.append(KeepTogether(dd_content))
            story.append(Spacer(1, 20))

        # Pay Period Breakdown Section (only if multiple pay periods exist)
        if pay_periods is not None and not pay_periods.empty:
            # Check if we have multiple pay periods
            unique_periods = sorted(pay_periods["Period"].unique())
            if len(unique_periods) > 1:
                # Add page break before pay period breakdown
                story.append(PageBreak())

                # Pay Period Breakdown Header
                story.append(Paragraph("Pay Period Breakdown", heading2_style))
                story.append(Spacer(1, 8))
                story.append(Paragraph("Individual distributions for each pay period", body_style))
                story.append(Spacer(1, 16))

                # Get filtered pay periods data
                filtered_pay_periods = pay_periods[pay_periods["Line"].isin(df["Line"])]
                # Exclude reserve lines
                pp_non_reserve = (
                    filtered_pay_periods[~filtered_pay_periods["Line"].isin(reserve_line_numbers)]
                    if reserve_line_numbers
                    else filtered_pay_periods
                )
                pp_for_bt = (
                    filtered_pay_periods[~filtered_pay_periods["Line"].isin(all_exclude_for_bt)]
                    if all_exclude_for_bt
                    else filtered_pay_periods
                )

                # Create distributions for each pay period
                for period in unique_periods:
                    # Period Header
                    story.append(Paragraph(f"Pay Period {int(period)}", heading2_style))
                    story.append(Spacer(1, 12))

                    # Filter data for this specific pay period
                    period_data_non_reserve = pp_non_reserve[pp_non_reserve["Period"] == period]
                    period_data_for_bt = pp_for_bt[pp_for_bt["Period"] == period]

                    # CT Distribution for this pay period
                    if not period_data_non_reserve.empty:
                        ct_pp_distribution = _create_binned_distribution(
                            period_data_non_reserve["CT"], bin_width=5.0, label="Range"
                        )
                        if not ct_pp_distribution.empty:
                            ct_pp_content = []
                            ct_pp_content.append(Paragraph("Credit Time (CT)", heading2_style))
                            ct_pp_content.append(Spacer(1, 8))

                            ct_pp_data = [["Range", "Lines", "Percent"]]
                            for _, row in ct_pp_distribution.iterrows():
                                ct_pp_data.append([row["Range"], str(row["Lines"]), row["Percent"]])

                            ct_pp_table = make_styled_table(ct_pp_data, [120, 100, 100], branding)
                            ct_pp_content.append(ct_pp_table)
                            ct_pp_content.append(Spacer(1, 12))

                            # CT Charts - Side by side
                            ct_pp_chart_path = save_bar_chart(
                                ct_pp_distribution,
                                f"PP{int(period)} Credit Time (Count)",
                                "Range",
                                "Lines",
                                "Credit Time Range",
                                "Number of Lines",
                                "#1BB3A4",
                            )
                            ct_pp_pct_chart_path = save_percentage_bar_chart(
                                ct_pp_distribution,
                                f"PP{int(period)} Credit Time (Percentage)",
                                "Range",
                                "Percent",
                                "Credit Time Range",
                                "#2E9BE8",
                            )

                            if ct_pp_chart_path and ct_pp_pct_chart_path:
                                temp_files.extend([ct_pp_chart_path, ct_pp_pct_chart_path])
                                from reportlab.lib.units import inch
                                from reportlab.platypus import Table, TableStyle

                                ct_pp_img = Image(
                                    ct_pp_chart_path, width=3.5 * inch, height=2.6 * inch
                                )
                                ct_pp_pct_img = Image(
                                    ct_pp_pct_chart_path, width=3.5 * inch, height=2.6 * inch
                                )

                                charts_table = Table(
                                    [[ct_pp_img, ct_pp_pct_img]], colWidths=[3.6 * inch, 3.6 * inch]
                                )
                                charts_table.setStyle(
                                    TableStyle(
                                        [
                                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                                            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                                        ]
                                    )
                                )
                                ct_pp_content.append(charts_table)

                            story.append(KeepTogether(ct_pp_content))
                            story.append(Spacer(1, 16))

                    # BT Distribution for this pay period
                    if not period_data_for_bt.empty:
                        bt_pp_distribution = _create_binned_distribution(
                            period_data_for_bt["BT"], bin_width=5.0, label="Range"
                        )
                        if not bt_pp_distribution.empty:
                            bt_pp_content = []
                            bt_pp_content.append(Paragraph("Block Time (BT)", heading2_style))
                            bt_pp_content.append(Spacer(1, 8))

                            bt_pp_data = [["Range", "Lines", "Percent"]]
                            for _, row in bt_pp_distribution.iterrows():
                                bt_pp_data.append([row["Range"], str(row["Lines"]), row["Percent"]])

                            bt_pp_table = make_styled_table(bt_pp_data, [120, 100, 100], branding)
                            bt_pp_content.append(bt_pp_table)
                            bt_pp_content.append(Spacer(1, 12))

                            # BT Charts - Side by side
                            bt_pp_chart_path = save_bar_chart(
                                bt_pp_distribution,
                                f"PP{int(period)} Block Time (Count)",
                                "Range",
                                "Lines",
                                "Block Time Range",
                                "Number of Lines",
                                "#0C7C73",
                            )
                            bt_pp_pct_chart_path = save_percentage_bar_chart(
                                bt_pp_distribution,
                                f"PP{int(period)} Block Time (Percentage)",
                                "Range",
                                "Percent",
                                "Block Time Range",
                                "#5BCFC2",
                            )

                            if bt_pp_chart_path and bt_pp_pct_chart_path:
                                temp_files.extend([bt_pp_chart_path, bt_pp_pct_chart_path])
                                from reportlab.lib.units import inch
                                from reportlab.platypus import Table, TableStyle

                                bt_pp_img = Image(
                                    bt_pp_chart_path, width=3.5 * inch, height=2.6 * inch
                                )
                                bt_pp_pct_img = Image(
                                    bt_pp_pct_chart_path, width=3.5 * inch, height=2.6 * inch
                                )

                                charts_table = Table(
                                    [[bt_pp_img, bt_pp_pct_img]], colWidths=[3.6 * inch, 3.6 * inch]
                                )
                                charts_table.setStyle(
                                    TableStyle(
                                        [
                                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                                            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                                        ]
                                    )
                                )
                                bt_pp_content.append(charts_table)

                            story.append(KeepTogether(bt_pp_content))
                            story.append(Spacer(1, 16))

                    # DO Distribution for this pay period
                    if not period_data_non_reserve.empty:
                        do_pp_distribution = _create_value_distribution(
                            period_data_non_reserve["DO"], label="Days Off"
                        )
                        if not do_pp_distribution.empty:
                            do_pp_content = []
                            do_pp_content.append(Paragraph("Days Off (DO)", heading2_style))
                            do_pp_content.append(Spacer(1, 8))

                            do_pp_data = [["Days Off", "Lines", "Percent"]]
                            for _, row in do_pp_distribution.iterrows():
                                do_pp_data.append(
                                    [str(row["Days Off"]), str(row["Lines"]), row["Percent"]]
                                )

                            do_pp_table = make_styled_table(do_pp_data, [120, 100, 100], branding)
                            do_pp_content.append(do_pp_table)
                            do_pp_content.append(Spacer(1, 12))

                            # DO Charts - Side by side
                            do_pp_chart_path = save_bar_chart(
                                do_pp_distribution,
                                f"PP{int(period)} Days Off (Count)",
                                "Days Off",
                                "Lines",
                                "Days Off",
                                "Number of Lines",
                                "#2E9BE8",
                            )
                            do_pp_pct_chart_path = save_percentage_bar_chart(
                                do_pp_distribution,
                                f"PP{int(period)} Days Off (Percentage)",
                                "Days Off",
                                "Percent",
                                "Days Off",
                                "#7EC8F6",
                            )

                            if do_pp_chart_path and do_pp_pct_chart_path:
                                temp_files.extend([do_pp_chart_path, do_pp_pct_chart_path])
                                from reportlab.lib.units import inch
                                from reportlab.platypus import Table, TableStyle

                                do_pp_img = Image(
                                    do_pp_chart_path, width=3.5 * inch, height=2.6 * inch
                                )
                                do_pp_pct_img = Image(
                                    do_pp_pct_chart_path, width=3.5 * inch, height=2.6 * inch
                                )

                                charts_table = Table(
                                    [[do_pp_img, do_pp_pct_img]], colWidths=[3.6 * inch, 3.6 * inch]
                                )
                                charts_table.setStyle(
                                    TableStyle(
                                        [
                                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                                            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                                        ]
                                    )
                                )
                                do_pp_content.append(charts_table)

                            story.append(KeepTogether(do_pp_content))
                            story.append(Spacer(1, 16))

                    # DD Distribution for this pay period
                    if not period_data_non_reserve.empty:
                        dd_pp_distribution = _create_value_distribution(
                            period_data_non_reserve["DD"], label="Duty Days"
                        )
                        if not dd_pp_distribution.empty:
                            dd_pp_content = []
                            dd_pp_content.append(Paragraph("Duty Days (DD)", heading2_style))
                            dd_pp_content.append(Spacer(1, 8))

                            dd_pp_data = [["Duty Days", "Lines", "Percent"]]
                            for _, row in dd_pp_distribution.iterrows():
                                dd_pp_data.append(
                                    [str(row["Duty Days"]), str(row["Lines"]), row["Percent"]]
                                )

                            dd_pp_table = make_styled_table(dd_pp_data, [120, 100, 100], branding)
                            dd_pp_content.append(dd_pp_table)
                            dd_pp_content.append(Spacer(1, 12))

                            # DD Charts - Side by side
                            dd_pp_chart_path = save_bar_chart(
                                dd_pp_distribution,
                                f"PP{int(period)} Duty Days (Count)",
                                "Duty Days",
                                "Lines",
                                "Duty Days",
                                "Number of Lines",
                                "#1BB3A4",
                            )
                            dd_pp_pct_chart_path = save_percentage_bar_chart(
                                dd_pp_distribution,
                                f"PP{int(period)} Duty Days (Percentage)",
                                "Duty Days",
                                "Percent",
                                "Duty Days",
                                "#0C7C73",
                            )

                            if dd_pp_chart_path and dd_pp_pct_chart_path:
                                temp_files.extend([dd_pp_chart_path, dd_pp_pct_chart_path])
                                from reportlab.lib.units import inch
                                from reportlab.platypus import Table, TableStyle

                                dd_pp_img = Image(
                                    dd_pp_chart_path, width=3.5 * inch, height=2.6 * inch
                                )
                                dd_pp_pct_img = Image(
                                    dd_pp_pct_chart_path, width=3.5 * inch, height=2.6 * inch
                                )

                                charts_table = Table(
                                    [[dd_pp_img, dd_pp_pct_img]], colWidths=[3.6 * inch, 3.6 * inch]
                                )
                                charts_table.setStyle(
                                    TableStyle(
                                        [
                                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                                            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                                        ]
                                    )
                                )
                                dd_pp_content.append(charts_table)

                            story.append(KeepTogether(dd_pp_content))
                            story.append(Spacer(1, 16))

                    # Add divider between pay periods (except after the last one)
                    if period != unique_periods[-1]:
                        story.append(hr)
                        story.append(Spacer(1, 16))

                # Add page break before buy-up analysis
                story.append(PageBreak())

        # Horizontal rule
        story.append(hr)

        # Buy-up vs Non Buy-up Analysis
        threshold = BUYUP_THRESHOLD_HOURS
        buy_up_content = []
        buy_up_content.append(
            Paragraph(f"Buy-up Analysis (Threshold: {threshold:.0f} CT)", heading2_style)
        )
        buy_up_content.append(Spacer(1, 12))

        total = len(df)
        buy_up_df = df[df["CT"] < threshold]
        non_buy_up_df = df[df["CT"] >= threshold]

        # Filter for buy-up analysis
        buy_up_df_non_reserve = (
            buy_up_df[~buy_up_df["Line"].isin(reserve_line_numbers)]
            if reserve_line_numbers
            else buy_up_df
        )
        non_buy_up_df_non_reserve = (
            non_buy_up_df[~non_buy_up_df["Line"].isin(reserve_line_numbers)]
            if reserve_line_numbers
            else non_buy_up_df
        )

        buy_up_df_for_bt = (
            buy_up_df[~buy_up_df["Line"].isin(all_exclude_for_bt)]
            if all_exclude_for_bt
            else buy_up_df
        )
        non_buy_up_df_for_bt = (
            non_buy_up_df[~non_buy_up_df["Line"].isin(all_exclude_for_bt)]
            if all_exclude_for_bt
            else non_buy_up_df
        )

        buy_up_data = [
            ["Category", "Lines", "Percent", "Avg CT", "Avg BT", "Avg DO", "Avg DD"],
            [
                f"Buy-up (<{threshold:.0f} CT)",
                str(len(buy_up_df)),
                f"{(len(buy_up_df) / total * 100):.1f}%" if total else "0%",
                (
                    f"{buy_up_df_non_reserve['CT'].mean():.2f}"
                    if not buy_up_df_non_reserve.empty
                    else "N/A"
                ),
                f"{buy_up_df_for_bt['BT'].mean():.2f}" if not buy_up_df_for_bt.empty else "N/A",
                (
                    f"{buy_up_df_non_reserve['DO'].mean():.2f}"
                    if not buy_up_df_non_reserve.empty
                    else "N/A"
                ),
                (
                    f"{buy_up_df_non_reserve['DD'].mean():.2f}"
                    if not buy_up_df_non_reserve.empty
                    else "N/A"
                ),
            ],
            [
                f"Non Buy-up (≥{threshold:.0f} CT)",
                str(len(non_buy_up_df)),
                f"{(len(non_buy_up_df) / total * 100):.1f}%" if total else "0%",
                (
                    f"{non_buy_up_df_non_reserve['CT'].mean():.2f}"
                    if not non_buy_up_df_non_reserve.empty
                    else "N/A"
                ),
                (
                    f"{non_buy_up_df_for_bt['BT'].mean():.2f}"
                    if not non_buy_up_df_for_bt.empty
                    else "N/A"
                ),
                (
                    f"{non_buy_up_df_non_reserve['DO'].mean():.2f}"
                    if not non_buy_up_df_non_reserve.empty
                    else "N/A"
                ),
                (
                    f"{non_buy_up_df_non_reserve['DD'].mean():.2f}"
                    if not non_buy_up_df_non_reserve.empty
                    else "N/A"
                ),
            ],
        ]

        buy_up_table = make_styled_table(buy_up_data, [130, 60, 60, 60, 60, 60, 60], branding)
        buy_up_content.append(buy_up_table)
        buy_up_content.append(Spacer(1, 16))

        # Buy-up pie chart
        if total > 0:
            labels = [f"Buy-up (<{threshold:.0f} CT)", f"Non Buy-up (≥{threshold:.0f} CT)"]
            counts = [len(buy_up_df), len(non_buy_up_df)]
            colors_list = ["#1BB3A4", "#0C1E36"]  # Brand Teal and Navy

            pie_path = save_pie_chart("Buy-up vs Non Buy-up", labels, counts, colors_list)
            if pie_path:
                temp_files.append(pie_path)
                from reportlab.lib.units import inch

                pie_img = Image(pie_path, width=3 * inch, height=3 * inch)
                buy_up_content.append(pie_img)
                buy_up_content.append(Spacer(1, 20))

        # Keep header, table, and chart together
        story.append(KeepTogether(buy_up_content))

        # Build PDF with header/footer
        def add_page_decorations(canvas, doc):
            draw_header(canvas, doc, branding)
            draw_footer(canvas, doc)

        doc.build(story, onFirstPage=add_page_decorations, onLaterPages=add_page_decorations)

        # Read PDF bytes
        with open(doc.filename, "rb") as f:
            pdf_bytes = f.read()

        # Clean up the main PDF file
        try:
            os.unlink(doc.filename)
        except Exception:
            pass

        return pdf_bytes

    finally:
        # Clean up temporary image files
        for temp_file in temp_files:
            try:
                if temp_file and os.path.exists(temp_file):
                    os.unlink(temp_file)
            except Exception:
                pass  # Silently ignore cleanup errors
