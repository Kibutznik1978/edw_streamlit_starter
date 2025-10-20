# Export PDF Integration Guide

## Overview

The `export_pdf.py` module provides a professional, executive-style analytics report generator using ReportLab and Matplotlib. This guide shows how to integrate it into your Streamlit application.

## Features

- **Professional Layout**: Branded header/footer on every page
- **KPI Cards**: Rounded rectangles displaying key metrics
- **Charts**:
  - Donut chart (EDW vs Non-EDW trips)
  - Bar chart (Trip Length Distribution)
  - **NEW:** Bar chart comparing EDW percentages by weighting method
  - **NEW:** Three pie charts showing EDW distribution for each method (Trip-Weighted, TAFB-Weighted, Duty Day-Weighted)
- **Tables**: Weighted summary, duty day statistics, and trip length breakdown
- **Responsive**: Automatically creates as many pages as needed (typically 3 pages)
- **Clean Code**: Pure functions, defensive coding, automatic temp file cleanup

## Quick Start

### 1. Import the Module

```python
from export_pdf import create_pdf_report
```

### 2. Prepare Your Data

The function expects a dictionary with the following structure:

```python
data = {
    "title": "ONT 757 – Bid 2601",
    "subtitle": "Executive Dashboard • EDW Breakdown & Duty-Day Metrics",
    "trip_summary": {              # KPI cards (first 4 displayed)
        "Unique Pairings": 272,
        "Total Trips": 522,
        "EDW Trips": 242,
        "Day Trips": 280,
    },
    "weighted_summary": {          # 2-column table
        "Trip-weighted EDW trip %": "46.4%",
        "TAFB-weighted EDW trip %": "73.3%",
        "Duty-day-weighted EDW trip %": "66.2%",
    },
    "duty_day_stats": [            # 4-column table
        ["Metric", "All", "EDW", "Non-EDW"],
        ["Avg Legs/Duty Day", "1.81", "2.04", "1.63"],
        ["Avg Duty Day Length", "7.41 h", "8.22 h", "6.78 h"],
        ["Avg Block Time", "3.61 h", "4.33 h", "3.06 h"],
        ["Avg Credit Time", "5.05 h", "5.44 h", "4.75 h"],
    ],
    "trip_length_distribution": [  # List of dicts
        {"duty_days": 1, "trips": 238},
        {"duty_days": 2, "trips": 1},
        {"duty_days": 3, "trips": 4},
        # ... more entries
    ],
    "notes": "Hot Standby pairings were excluded from trip-length distribution.",
    "generated_by": "Data Analysis App"  # Optional
}
```

### 3. Configure Branding (Optional)

```python
branding = {
    "primary_hex": "#111827",  # Header background color
    "accent_hex":  "#F3F4F6",  # KPI card and table header background
    "rule_hex":    "#E5E7EB",  # Dividers and grid lines
    "muted_hex":   "#6B7280",  # Subtitles and footer text
    "bg_alt_hex":  "#FAFAFA",  # Zebra row background
    "logo_path":   None,       # Optional: path to logo image
    "title_left":  "ONT 757 – Bid 2601 | EDW Analysis Report"  # Header text
}
```

### 4. Generate the PDF

```python
import tempfile
from export_pdf import create_pdf_report

# Generate PDF to temp file
with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
    pdf_path = tmp_file.name
    create_pdf_report(data, pdf_path, branding)
```

### 5. Add Download Button to Streamlit

```python
import streamlit as st

# After generating the PDF
with open(pdf_path, "rb") as pdf_file:
    pdf_bytes = pdf_file.read()

    st.download_button(
        label="📄 Download Executive PDF Report",
        data=pdf_bytes,
        file_name=f"{domicile}_{aircraft}_Bid{bid_period}_Executive_Report.pdf",
        mime="application/pdf"
    )
```

## Complete Streamlit Integration Example

```python
import streamlit as st
import tempfile
import os
from export_pdf import create_pdf_report

# ... your existing analysis code ...

# After analysis is complete and results are available
if st.button("Generate Executive PDF Report"):
    with st.spinner("Generating executive PDF report..."):
        try:
            # Prepare data structure
            data = {
                "title": f"{domicile} {aircraft} – Bid {bid_period}",
                "subtitle": "Executive Dashboard • EDW Breakdown & Duty-Day Metrics",
                "trip_summary": {
                    "Unique Pairings": unique_pairings,
                    "Total Trips": total_trips,
                    "EDW Trips": edw_trips,
                    "Day Trips": day_trips,
                },
                "weighted_summary": {
                    "Trip-weighted EDW trip %": f"{trip_weighted_pct:.1f}%",
                    "TAFB-weighted EDW trip %": f"{tafb_weighted_pct:.1f}%",
                    "Duty-day-weighted EDW trip %": f"{dd_weighted_pct:.1f}%",
                },
                "duty_day_stats": [
                    ["Metric", "All", "EDW", "Non-EDW"],
                    ["Avg Legs/Duty Day", f"{avg_legs_all:.2f}", f"{avg_legs_edw:.2f}", f"{avg_legs_non:.2f}"],
                    ["Avg Duty Day Length", f"{avg_duty_all:.2f} h", f"{avg_duty_edw:.2f} h", f"{avg_duty_non:.2f} h"],
                    ["Avg Block Time", f"{avg_block_all:.2f} h", f"{avg_block_edw:.2f} h", f"{avg_block_non:.2f} h"],
                    ["Avg Credit Time", f"{avg_credit_all:.2f} h", f"{avg_credit_edw:.2f} h", f"{avg_credit_non:.2f} h"],
                ],
                "trip_length_distribution": [
                    {"duty_days": dd, "trips": count}
                    for dd, count in trip_length_dist.items()
                ],
                "notes": "Hot Standby pairings were excluded from trip-length distribution.",
                "generated_by": "EDW Pairing Analyzer"
            }

            # Configure branding
            branding = {
                "primary_hex": "#111827",
                "accent_hex": "#F3F4F6",
                "rule_hex": "#E5E7EB",
                "muted_hex": "#6B7280",
                "bg_alt_hex": "#FAFAFA",
                "logo_path": None,  # Add your logo path if available
                "title_left": f"{domicile} {aircraft} – Bid {bid_period} | EDW Analysis Report"
            }

            # Generate PDF
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                pdf_path = tmp_file.name
                create_pdf_report(data, pdf_path, branding)

            # Provide download button
            with open(pdf_path, "rb") as pdf_file:
                pdf_bytes = pdf_file.read()

                st.download_button(
                    label="📄 Download Executive PDF Report",
                    data=pdf_bytes,
                    file_name=f"{domicile}_{aircraft}_Bid{bid_period}_Executive_Report.pdf",
                    mime="application/pdf"
                )

            # Clean up temp file
            try:
                os.unlink(pdf_path)
            except:
                pass

            st.success("Executive PDF report generated successfully!")

        except Exception as e:
            st.error(f"Error generating PDF: {e}")
```

## Data Mapping from EDW Reporter

If you're using the existing `edw_reporter.py` module, here's how to map the data:

```python
from edw_reporter import run_edw_report

# Run analysis
results = run_edw_report(pdf_path, notes)

# Map to export_pdf format
data = {
    "title": f"{results['domicile']} {results['fleet_type']} – Bid {results['bid_period']}",
    "subtitle": "Executive Dashboard • EDW Breakdown & Duty-Day Metrics",
    "trip_summary": {
        "Unique Pairings": results['summary']['Unique Pairings'],
        "Total Trips": results['summary']['Total Trips'],
        "EDW Trips": results['summary']['EDW Trips'],
        "Day Trips": results['summary']['Day Trips'],
    },
    "weighted_summary": {
        "Trip-weighted EDW trip %": f"{results['summary']['Pct EDW']}",
        "TAFB-weighted EDW trip %": f"{results['summary']['TAFB-weighted EDW trip %']}",
        "Duty-day-weighted EDW trip %": f"{results['summary']['Duty-day-weighted EDW trip %']}",
    },
    "duty_day_stats": results['duty_day_stats_table'],  # Already formatted as list of lists
    "trip_length_distribution": [
        {"duty_days": int(dd), "trips": count}
        for dd, count in results['trip_length_distribution'].items()
        if dd != "Hot Standby"  # Exclude Hot Standby
    ],
    "notes": results.get('notes', ''),
    "generated_by": "EDW Pairing Analyzer"
}
```

## Customization

### Adding a Logo

1. Save your logo image file (PNG recommended)
2. Add path to branding dict:

```python
branding = {
    ...
    "logo_path": "/path/to/your/logo.png"
}
```

The logo will appear in the top-right corner of the header (60x30px, aspect ratio preserved).

### Changing Colors

Modify any color in the branding dictionary using hex codes:

```python
branding = {
    "primary_hex": "#1E3A8A",  # Navy blue header
    "accent_hex": "#DBEAFE",   # Light blue cards
    "rule_hex": "#93C5FD",     # Medium blue lines
    "muted_hex": "#475569",    # Dark gray text
    "bg_alt_hex": "#F1F5F9",   # Light gray rows
}
```

### Adding Additional Pages

The report automatically flows to additional pages. To add custom sections:

```python
# In export_pdf.py, before the final doc.build():
story.append(PageBreak())
story.append(Paragraph("Additional Analysis", heading2_style))
# ... add more content
```

## Error Handling

The function performs validation and provides clear error messages:

```python
try:
    create_pdf_report(data, output_path, branding)
except ValueError as e:
    print(f"Data validation error: {e}")
except IOError as e:
    print(f"File system error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Testing

Run the standalone test:

```bash
# Activate virtual environment
source .venv/bin/activate

# Generate sample PDF
python export_pdf.py

# Open the generated PDF
open /tmp/sample_report.pdf
```

## Dependencies

The following packages are required (already in `requirements.txt`):

```
reportlab>=4.0.0
matplotlib>=3.7.0
```

## Troubleshooting

### Issue: "Missing required data keys"
**Solution**: Ensure all required keys are present in the data dictionary. Check the error message for specific missing keys.

### Issue: Charts not appearing
**Solution**: Ensure matplotlib is using the 'Agg' backend (non-interactive). This is set automatically in the module.

### Issue: Temp files not cleaning up
**Solution**: The module automatically cleans up temp chart images in a `finally` block. If issues persist, check `/tmp` directory permissions.

### Issue: Logo not appearing
**Solution**:
- Verify logo file path exists
- Use PNG format for best results
- Check file permissions
- Logo errors are silently ignored to prevent PDF generation failure

## Report Layout

The generated PDF contains **3 pages**:

### Page 1: Executive Overview
- Title and subtitle
- 4 KPI cards (Unique Pairings, Total Trips, EDW Trips, Day Trips)
- Donut chart: EDW vs Non-EDW trips
- Bar chart: Trip Length Distribution
- Weighted Summary table
- Duty Day Statistics table

### Page 2: Trip Length Breakdown
- Detailed trip length table with percentages
- Large bar chart for detailed distribution analysis
- Data source and attribution footer

### Page 3: EDW Percentages Analysis (NEW)
- Bar chart comparing three weighting methods:
  - Trip-Weighted EDW %
  - TAFB-Weighted EDW %
  - Duty Day-Weighted EDW %
- Three pie charts showing EDW distribution for each method
  - Blue color scheme for Trip-Weighted
  - Green color scheme for TAFB-Weighted
  - Orange color scheme for Duty Day-Weighted

## Performance Notes

- **Chart Generation**: Each chart takes ~0.1-0.3 seconds (7 charts total)
- **PDF Build**: Total generation time ~2-3 seconds for typical report
- **File Size**: Expect 180-220 KB depending on chart complexity
- **Memory**: Temp files are created but automatically cleaned up

## Next Steps

1. Test the module with sample data: `python export_pdf.py`
2. Integrate into your Streamlit app using the examples above
3. Customize branding colors to match your organization
4. Add logo if available
5. Map your existing data structures to the expected format

For questions or issues, refer to the module docstrings or check the sample implementation in `if __name__ == "__main__"` block.
