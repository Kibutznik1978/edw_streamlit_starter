#!/usr/bin/env python3
"""Inspect SDF PDF to understand why reserve detection is failing."""

import pdfplumber

pdf_path = "/Users/giladswerdlow/Desktop/2601/SDF/BidLinePrint_BID2601_757_SDF.pdf"

with pdfplumber.open(pdf_path) as pdf:
    print(f"Total pages: {len(pdf.pages)}")

    # Look at first 3 pages
    for page_num in range(min(3, len(pdf.pages))):
        page = pdf.pages[page_num]
        text = page.extract_text()

        print(f"\n{'='*80}")
        print(f"PAGE {page_num + 1}")
        print(f"{'='*80}")

        # Show first 2000 characters
        print(text[:2000])

        if page_num == 0:
            # Also check for tables on first page
            tables = page.extract_tables()
            if tables:
                print(f"\n\nFound {len(tables)} tables on page 1")
                for i, table in enumerate(tables[:2]):  # Show first 2 tables
                    print(f"\nTable {i+1}:")
                    for row in table[:5]:  # Show first 5 rows
                        print(row)
