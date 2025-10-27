"""
pdf_generation/edw_pdf.py
EDW (Early/Day/Window) pairing analysis PDF report generation.

Creates professional 3-page PDF reports with:
- Trip summary KPI cards
- EDW vs Non-EDW visualizations
- Weighted EDW metrics
- Duty day statistics
- Trip length distributions
"""

import os
from typing import Dict, Any, Optional

# ReportLab imports
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image,
    PageBreak, HRFlowable, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
from reportlab.lib.units import inch

# Import from our pdf_generation modules
from .base import (
    DEFAULT_BRANDING, hex_to_reportlab_color,
    draw_header, draw_footer, make_kpi_row, make_styled_table
)
from .charts import (
    save_edw_pie_chart, save_trip_length_bar_chart,
    save_trip_length_percentage_bar_chart,
    save_edw_percentages_comparison_chart,
    save_weighted_method_pie_chart,
    save_duty_day_grouped_bar_chart,
    save_duty_day_radar_chart
)


def _make_weighted_summary_table(weighted_summary: Dict[str, str], branding: Dict[str, Any]):
    """
    Create weighted summary table with zebra striping.

    Args:
        weighted_summary: Dict with metric names and values
        branding: Branding dictionary with colors

    Returns:
        ReportLab Table with weighted EDW metrics
    """
    from reportlab.platypus import Table, TableStyle

    # Convert dict to list of lists
    data = [["Metric", "Value"]]
    for metric, value in weighted_summary.items():
        data.append([metric, value])

    # Create table
    table = Table(data, colWidths=[340, 100])

    # Style
    accent_color = hex_to_reportlab_color(branding["accent_hex"])
    rule_color = hex_to_reportlab_color(branding["rule_hex"])
    bg_alt_color = hex_to_reportlab_color(branding["bg_alt_hex"])

    style = TableStyle([
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), accent_color),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#111827")),
        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 10),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),

        # Grid
        ('GRID', (0, 0), (-1, -1), 0.5, rule_color),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),

        # Zebra striping
        ('BACKGROUND', (0, 2), (-1, 2), bg_alt_color),
    ])

    table.setStyle(style)
    return table


def _make_duty_day_stats_table(duty_day_stats, branding: Dict[str, Any]):
    """
    Create duty day statistics table.

    Args:
        duty_day_stats: 2D list with duty day statistics
        branding: Branding dictionary with colors

    Returns:
        ReportLab Table with duty day stats
    """
    from reportlab.platypus import Table, TableStyle

    # Create table
    table = Table(duty_day_stats, colWidths=[160, 90, 90, 90])

    # Style
    accent_color = hex_to_reportlab_color(branding["accent_hex"])
    rule_color = hex_to_reportlab_color(branding["rule_hex"])
    bg_alt_color = hex_to_reportlab_color(branding["bg_alt_hex"])

    style = TableStyle([
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), accent_color),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#111827")),
        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 10),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),

        # Grid
        ('GRID', (0, 0), (-1, -1), 0.5, rule_color),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),

        # Zebra striping (every other row after header)
        ('BACKGROUND', (0, 2), (-1, 2), bg_alt_color),
        ('BACKGROUND', (0, 4), (-1, 4), bg_alt_color),
    ])

    table.setStyle(style)
    return table


def _make_trip_length_table(trip_length_distribution, total_trips: int, branding: Dict[str, Any]):
    """
    Create trip length distribution table with percentages.

    Args:
        trip_length_distribution: List of dicts with 'duty_days' and 'trips'
        total_trips: Total number of trips for percentage calculation
        branding: Branding dictionary with colors

    Returns:
        ReportLab Table with trip length distribution
    """
    from reportlab.platypus import Table, TableStyle

    # Build table data
    data = [["Duty Days", "Trips", "Percent"]]
    for item in trip_length_distribution:
        duty_days = item["duty_days"]
        trips = item["trips"]
        percent = f"{(trips / total_trips * 100):.1f}%" if total_trips > 0 else "0%"
        data.append([str(duty_days), str(trips), percent])

    # Create table
    table = Table(data, colWidths=[120, 120, 120])

    # Style
    accent_color = hex_to_reportlab_color(branding["accent_hex"])
    rule_color = hex_to_reportlab_color(branding["rule_hex"])
    bg_alt_color = hex_to_reportlab_color(branding["bg_alt_hex"])

    style = TableStyle([
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), accent_color),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#111827")),
        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 10),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),

        # Grid
        ('GRID', (0, 0), (-1, -1), 0.5, rule_color),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ])

    # Add zebra striping
    for i in range(2, len(data), 2):
        style.add('BACKGROUND', (0, i), (-1, i), bg_alt_color)

    table.setStyle(style)
    return table


def create_edw_pdf_report(
    data: Dict[str, Any],
    output_path: str,
    branding: Optional[Dict[str, Any]] = None
) -> None:
    """
    Generate a professional 3-page EDW analysis report PDF.

    Args:
        data: Dictionary containing report data with keys:
            - title: Main report title
            - subtitle: Report subtitle
            - trip_summary: Dict of KPI metrics
            - weighted_summary: Dict of weighted metrics
            - duty_day_stats: List of lists for duty day statistics table
            - trip_length_distribution: List of dicts with duty_days and trips
            - notes: Optional notes text
            - generated_by: Optional attribution text
        output_path: Path where PDF will be saved
        branding: Optional dictionary with color scheme and branding elements

    Raises:
        ValueError: If required data keys are missing
        IOError: If output path is not writable
    """
    # Validate required data keys
    required_keys = ["title", "subtitle", "trip_summary", "weighted_summary",
                     "duty_day_stats", "trip_length_distribution"]
    missing_keys = [key for key in required_keys if key not in data]
    if missing_keys:
        raise ValueError(f"Missing required data keys: {missing_keys}")

    # Merge with default branding
    branding = {**DEFAULT_BRANDING, **(branding or {})}

    # Create document
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=60,  # Space for header
        bottomMargin=50  # Space for footer
    )

    # Prepare styles
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#111827"),
        spaceAfter=6,
        alignment=TA_CENTER
    )

    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=hex_to_reportlab_color(branding["muted_hex"]),
        spaceAfter=20,
        alignment=TA_CENTER
    )

    heading2_style = ParagraphStyle(
        'CustomHeading2',
        parent=styles['Heading2'],
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#111827"),
        spaceAfter=6,
        spaceBefore=12
    )

    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=10,
        textColor=hex_to_reportlab_color(branding["muted_hex"]),
        spaceAfter=12
    )

    # Build story (content flow)
    story = []
    temp_files = []  # Track temp files for cleanup

    try:
        # PAGE 1
        # Title and subtitle
        story.append(Paragraph(data["title"], title_style))
        story.append(Paragraph(data["subtitle"], subtitle_style))
        story.append(Spacer(1, 12))

        # KPI Cards
        kpi_table = make_kpi_row(data["trip_summary"], branding)
        story.append(kpi_table)
        story.append(Spacer(1, 20))

        # Horizontal rule
        hr = HRFlowable(
            width="100%",
            thickness=1,
            color=hex_to_reportlab_color(branding["rule_hex"]),
            spaceAfter=16,
            spaceBefore=4
        )
        story.append(hr)

        # Charts section
        story.append(Paragraph("Visual Analytics", heading2_style))
        story.append(Spacer(1, 8))

        # Create charts
        edw_trips = data["trip_summary"].get("EDW Trips", 0)
        total_trips = data["trip_summary"].get("Total Trips", 0)
        non_edw_trips = total_trips - edw_trips

        donut_path = save_edw_pie_chart(edw_trips, non_edw_trips)
        temp_files.append(donut_path)

        bar_path = save_trip_length_bar_chart(data["trip_length_distribution"], "Trip Length Distribution")
        temp_files.append(bar_path)

        # Place charts side by side
        from reportlab.platypus import Table, TableStyle
        donut_img = Image(donut_path, width=2.5*inch, height=2.5*inch)
        bar_img = Image(bar_path, width=3*inch, height=2.5*inch)

        chart_table = Table([[donut_img, bar_img]], colWidths=[2.75*inch, 3.25*inch])
        chart_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        story.append(chart_table)
        story.append(Spacer(1, 20))

        # Horizontal rule
        story.append(hr)

        # Weighted Summary
        story.append(Paragraph("Weighted EDW Metrics", heading2_style))
        story.append(Spacer(1, 8))
        weighted_table = _make_weighted_summary_table(data["weighted_summary"], branding)
        story.append(weighted_table)
        story.append(Spacer(1, 16))

        # Duty Day Statistics - Keep together to prevent page break
        duty_section = [
            Paragraph("Duty Day Statistics", heading2_style),
            Spacer(1, 8),
            _make_duty_day_stats_table(data["duty_day_stats"], branding)
        ]
        story.append(KeepTogether(duty_section))
        story.append(Spacer(1, 16))

        # Duty Day Statistics Visualizations
        grouped_bar_path = save_duty_day_grouped_bar_chart(data["duty_day_stats"])
        temp_files.append(grouped_bar_path)

        radar_chart_path = save_duty_day_radar_chart(data["duty_day_stats"])
        temp_files.append(radar_chart_path)

        # Place both charts side by side
        grouped_bar_img = Image(grouped_bar_path, width=4*inch, height=2.6*inch)
        radar_chart_img = Image(radar_chart_path, width=2.5*inch, height=2.5*inch)

        chart_comparison_table = Table(
            [[grouped_bar_img, radar_chart_img]],
            colWidths=[4.2*inch, 2.8*inch]
        )
        chart_comparison_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ]))
        story.append(chart_comparison_table)

        # Notes if provided
        if data.get("notes"):
            story.append(Spacer(1, 16))
            story.append(Paragraph(f"<i>Note: {data['notes']}</i>", body_style))

        # PAGE 2
        story.append(PageBreak())

        story.append(Paragraph("Trip Length Breakdown", heading2_style))
        story.append(Paragraph(
            "Distribution by Duty Days (Hot Standby excluded)",
            body_style
        ))
        story.append(Spacer(1, 12))

        # Trip length table
        trip_table = _make_trip_length_table(
            data["trip_length_distribution"],
            total_trips,
            branding
        )
        story.append(trip_table)
        story.append(Spacer(1, 20))

        # Trip length charts - both absolute numbers and percentages
        bar_path_large = save_trip_length_bar_chart(
            data["trip_length_distribution"],
            "Trip Length Distribution (Absolute Numbers)"
        )
        temp_files.append(bar_path_large)

        bar_pct_path = save_trip_length_percentage_bar_chart(
            data["trip_length_distribution"],
            "Trip Length Distribution (Percentage)"
        )
        temp_files.append(bar_pct_path)

        # Place charts side by side
        bar_img_large = Image(bar_path_large, width=3.5*inch, height=3*inch)
        bar_pct_img = Image(bar_pct_path, width=3.5*inch, height=3*inch)

        trip_charts_table = Table(
            [[bar_img_large, bar_pct_img]],
            colWidths=[3.6*inch, 3.6*inch]
        )
        trip_charts_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        story.append(trip_charts_table)
        story.append(Spacer(1, 24))

        # Horizontal rule
        story.append(hr)

        # Filter out single-day trips
        multi_day_trips = [item for item in data["trip_length_distribution"] if item["duty_days"] > 1]
        total_multi_day = sum(item["trips"] for item in multi_day_trips)

        if multi_day_trips:
            # Multi-day trip analysis section
            multi_day_section = []

            multi_day_section.append(Paragraph("Trip Length Analysis (Single-Day Trips Excluded)", heading2_style))
            multi_day_section.append(Paragraph(
                "Focus on multi-day pairings by removing 1-day trips",
                body_style
            ))
            multi_day_section.append(Spacer(1, 12))

            # Multi-day only table
            accent_color = hex_to_reportlab_color(branding["accent_hex"])
            rule_color = hex_to_reportlab_color(branding["rule_hex"])
            bg_alt_color = hex_to_reportlab_color(branding["bg_alt_hex"])

            multi_day_data = [["Duty Days", "Trips", "Percentage"]]
            for item in multi_day_trips:
                duty_days = item["duty_days"]
                trips = item["trips"]
                percent = f"{(trips / total_multi_day * 100):.1f}%" if total_multi_day > 0 else "0%"
                multi_day_data.append([str(duty_days), str(trips), percent])

            multi_day_table = Table(multi_day_data, colWidths=[120, 120, 120])

            # Apply table style
            table_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), accent_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#111827")),
                ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 10),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, rule_color),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
            ])

            # Add zebra striping
            for i in range(2, len(multi_day_data), 2):
                table_style.add('BACKGROUND', (0, i), (-1, i), bg_alt_color)

            multi_day_table.setStyle(table_style)
            multi_day_section.append(multi_day_table)
            multi_day_section.append(Spacer(1, 20))

            # Charts for multi-day trips
            multi_bar_path = save_trip_length_bar_chart(
                multi_day_trips,
                "Multi-Day Trips (Absolute Numbers)"
            )
            temp_files.append(multi_bar_path)

            multi_bar_pct_path = save_trip_length_percentage_bar_chart(
                multi_day_trips,
                "Multi-Day Trips (Percentage)"
            )
            temp_files.append(multi_bar_pct_path)

            # Place charts side by side
            multi_bar_img = Image(multi_bar_path, width=3.5*inch, height=3*inch)
            multi_bar_pct_img = Image(multi_bar_pct_path, width=3.5*inch, height=3*inch)

            multi_charts_table = Table(
                [[multi_bar_img, multi_bar_pct_img]],
                colWidths=[3.6*inch, 3.6*inch]
            )
            multi_charts_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ]))
            multi_day_section.append(multi_charts_table)

            # Add entire section as KeepTogether
            story.append(KeepTogether(multi_day_section))
            story.append(Spacer(1, 20))
        else:
            story.append(Paragraph("Trip Length Analysis (Single-Day Trips Excluded)", heading2_style))
            story.append(Paragraph("<i>No multi-day trips found in dataset.</i>", body_style))
            story.append(Spacer(1, 20))

        # PAGE 3 - EDW Percentages Analysis
        story.append(PageBreak())

        story.append(Paragraph("EDW Percentages Analysis", heading2_style))
        story.append(Paragraph(
            "Comparison of EDW metrics across different weighting methods",
            body_style
        ))
        story.append(Spacer(1, 12))

        # EDW Percentages comparison bar chart
        edw_pct_bar_path = save_edw_percentages_comparison_chart(data["weighted_summary"])
        temp_files.append(edw_pct_bar_path)

        edw_pct_bar_img = Image(edw_pct_bar_path, width=5*inch, height=3.5*inch)
        story.append(edw_pct_bar_img)
        story.append(Spacer(1, 24))

        # Horizontal rule
        hr = HRFlowable(
            width="100%",
            thickness=1,
            color=hex_to_reportlab_color(branding["rule_hex"]),
            spaceAfter=16,
            spaceBefore=4
        )
        story.append(hr)

        # Three pie charts showing each weighting method
        story.append(Paragraph("EDW Distribution by Weighting Method", heading2_style))
        story.append(Spacer(1, 12))

        # Extract percentages for pie charts
        percentages = {}
        for key in ["Trip-weighted EDW trip %", "TAFB-weighted EDW trip %", "Duty-day-weighted EDW trip %"]:
            value_str = data["weighted_summary"].get(key, "0%")
            value_str = value_str.replace('%', '').strip()
            try:
                percentages[key] = float(value_str)
            except ValueError:
                percentages[key] = 0.0

        # Create three pie charts
        trip_pie_path = save_weighted_method_pie_chart(
            percentages["Trip-weighted EDW trip %"],
            "Trip-Weighted",
            "trip"
        )
        temp_files.append(trip_pie_path)

        tafb_pie_path = save_weighted_method_pie_chart(
            percentages["TAFB-weighted EDW trip %"],
            "TAFB-Weighted",
            "tafb"
        )
        temp_files.append(tafb_pie_path)

        duty_pie_path = save_weighted_method_pie_chart(
            percentages["Duty-day-weighted EDW trip %"],
            "Duty Day-Weighted",
            "duty"
        )
        temp_files.append(duty_pie_path)

        # Place three pie charts in a row
        trip_pie_img = Image(trip_pie_path, width=2*inch, height=2*inch)
        tafb_pie_img = Image(tafb_pie_path, width=2*inch, height=2*inch)
        duty_pie_img = Image(duty_pie_path, width=2*inch, height=2*inch)

        pie_table = Table(
            [[trip_pie_img, tafb_pie_img, duty_pie_img]],
            colWidths=[2.1*inch, 2.1*inch, 2.1*inch]
        )
        pie_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        story.append(pie_table)
        story.append(Spacer(1, 20))

        # Footer line with data source
        footer_text = ""
        if data.get("notes"):
            footer_text += f"Data Source: {data['notes']}"
        if data.get("generated_by"):
            if footer_text:
                footer_text += " • "
            footer_text += f"Prepared by: {data['generated_by']}"

        if footer_text:
            footer_para = Paragraph(f"<i>{footer_text}</i>", body_style)
            story.append(footer_para)

        # Build PDF with header/footer
        def add_page_decorations(canvas, doc):
            draw_header(canvas, doc, branding)
            draw_footer(canvas, doc)

        doc.build(story, onFirstPage=add_page_decorations, onLaterPages=add_page_decorations)

    finally:
        # Clean up temporary image files
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except Exception:
                pass  # Silently ignore cleanup errors
