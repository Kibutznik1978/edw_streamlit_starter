#!/usr/bin/env python3
"""
Debug script to see what's being parsed from the PDF
"""
import sys
from PyPDF2 import PdfReader
from edw_reporter import parse_trip_for_table
import json

if len(sys.argv) < 2:
    print("Usage: python debug_parsing.py <pdf_file>")
    sys.exit(1)

pdf_path = sys.argv[1]

# Read PDF
reader = PdfReader(pdf_path)
text = ""
for page in reader.pages:
    text += page.extract_text()

# Split into trips
trips = []
lines = text.split('\n')
current_trip = []
trip_start_found = False

for line in lines:
    if 'Trip Id:' in line:
        if current_trip:
            trips.append('\n'.join(current_trip))
        current_trip = [line]
        trip_start_found = True
    elif trip_start_found:
        current_trip.append(line)

if current_trip:
    trips.append('\n'.join(current_trip))

# Parse first trip (or trip 204 if we can find it)
target_trip = None
for trip_text in trips:
    if 'Trip Id: 204' in trip_text:
        target_trip = trip_text
        break

if not target_trip and trips:
    target_trip = trips[0]

if target_trip:
    print("=" * 80)
    print("RAW TRIP TEXT (first 100 lines):")
    print("=" * 80)
    trip_lines = target_trip.split('\n')
    for i, line in enumerate(trip_lines[:100]):
        print(f"{i:3d}: {repr(line)}")

    print("\n" + "=" * 80)
    print("PARSED TRIP DATA:")
    print("=" * 80)

    parsed = parse_trip_for_table(target_trip)
    print(json.dumps(parsed, indent=2, default=str))

    print("\n" + "=" * 80)
    print("DUTY DAY DETAILS:")
    print("=" * 80)

    for i, duty in enumerate(parsed.get('duty_days', []), 1):
        print(f"\nDuty Day {i}:")
        print(f"  duty_start: {duty.get('duty_start')}")
        print(f"  duty_end:   {duty.get('duty_end')}")
        print(f"  rest (L/O): {duty.get('rest')}")
        print(f"  Flights ({len(duty.get('flights', []))}):")

        for j, flight in enumerate(duty.get('flights', []), 1):
            print(f"    Flight {j}:")
            print(f"      route:  {flight.get('route')}")
            print(f"      arrive: {flight.get('arrive')}")
            print(f"      debrief_completion: {flight.get('debrief_completion')}")
else:
    print("No trips found in PDF")
