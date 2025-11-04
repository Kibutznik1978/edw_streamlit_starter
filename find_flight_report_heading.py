"""
Simple script to find the "Trips to Flight Report" heading in the PDF.
"""

import sys
from pathlib import Path
from PyPDF2 import PdfReader

def find_heading(pdf_path: str):
    """Find lines containing 'trip', 'flight', and 'report'."""
    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        print(f"❌ Error: File not found: {pdf_path}")
        return

    print(f"🔍 Searching: {pdf_path.name}")
    print("=" * 80)

    reader = PdfReader(str(pdf_path))
    all_text = ""

    print(f"Reading {len(reader.pages)} pages...")
    for page in reader.pages:
        all_text += page.extract_text() + "\n"

    print(f"\nSearching for lines containing 'trip', 'flight', and 'report'...\n")

    found_count = 0
    for line_num, line in enumerate(all_text.splitlines(), 1):
        line_lower = line.lower()
        if 'trip' in line_lower and 'flight' in line_lower and 'report' in line_lower:
            print(f"Line {line_num}: '{line}'")
            found_count += 1

    if found_count == 0:
        print("❌ No lines found with all three words.")
        print("\nSearching for 'Trips to Flight' without 'Report'...")
        for line_num, line in enumerate(all_text.splitlines(), 1):
            line_lower = line.lower()
            if 'trips to flight' in line_lower:
                print(f"Line {line_num}: '{line}'")

    print(f"\n{'=' * 80}")
    print(f"Found {found_count} matching lines")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python find_flight_report_heading.py <path_to_pdf>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    find_heading(pdf_path)
