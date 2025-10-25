#!/usr/bin/env python3
"""
Debug script to examine the exact boundary between Duty Days 4 and 5
"""
from PyPDF2 import PdfReader

pdf_path = "test_data/PacketPrint_BID2507_757_ONT.pdf"

# Read PDF
reader = PdfReader(pdf_path)
text = ""
for page in reader.pages:
    text += page.extract_text()

# Split into trips
trips = []
lines = text.split('\n')
current_trip = []
for line in lines:
    if 'Trip Id:' in line:
        if current_trip:
            trips.append('\n'.join(current_trip))
        current_trip = [line]
    else:
        current_trip.append(line)
if current_trip:
    trips.append('\n'.join(current_trip))

# Get first trip (204)
trip_lines = trips[0].split('\n')

# Find RFD-STL (should be the last flight in Duty Day 4)
for i, line in enumerate(trip_lines):
    if 'RFD-STL' in line:
        print(f"Found RFD-STL at line {i}")
        print("\nLines around RFD-STL:")
        for j in range(max(0, i-2), min(len(trip_lines), i+25)):
            print(f"{j:3d}: {repr(trip_lines[j])}")
        break
