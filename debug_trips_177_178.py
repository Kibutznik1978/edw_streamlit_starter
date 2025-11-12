#!/usr/bin/env python3
"""
Debug script to examine trips 177 and 178 for leg counting issues.
"""
from pathlib import Path
import sys
import re

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from edw_reporter import parse_pairings, parse_trip_id, parse_max_legs_per_duty_day, parse_duty_day_details

# Find trips 177 and 178
pdf_path = Path(__file__).parent / "test_data" / "PacketPrint_BID2507_757_ONT.pdf"

if not pdf_path.exists():
    print(f"PDF not found at: {pdf_path}")
    print("Please ensure the PDF is in the test_data directory")
    sys.exit(1)

print("Parsing PDF...")
trips = parse_pairings(pdf_path)
print(f"Found {len(trips)} trips\n")

# Find trips 177 and 178
target_trips = {}
for trip_text in trips:
    trip_id = parse_trip_id(trip_text)
    if trip_id in [177, 178]:
        target_trips[trip_id] = trip_text

if not target_trips:
    print("❌ Trips 177 and 178 not found!")
    sys.exit(1)

for trip_id in sorted(target_trips.keys()):
    trip_text = target_trips[trip_id]

    print("=" * 80)
    print(f"TRIP {trip_id} RAW TEXT:")
    print("=" * 80)
    print(trip_text)
    print("\n")

    print("=" * 80)
    print(f"TRIP {trip_id} PARSED DETAILS:")
    print("=" * 80)

    max_legs = parse_max_legs_per_duty_day(trip_text)
    print(f"Max legs per duty day: {max_legs}")

    duty_details = parse_duty_day_details(trip_text)
    print(f"\nDuty day details:")
    for dd in duty_details:
        print(f"  Day {dd['day']}: {dd['num_legs']} legs, {dd['duration_hours']:.2f}h duration")

    print("\n" + "=" * 80)
    print(f"TRIP {trip_id} LEG DETECTION ANALYSIS:")
    print("=" * 80)

    lines = trip_text.split('\n')
    in_duty = False
    duty_num = 0

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Detect duty day start
        if 'Briefing' in line or (stripped and stripped[0] == '(' and 'Duty' in lines[i+2:i+4] if i+3 < len(lines) else False):
            in_duty = True
            duty_num += 1
            print(f"\n--- DUTY DAY {duty_num} START ---")
            continue

        # Detect duty day end
        if 'Debriefing' in line or stripped == 'Duty Time:':
            in_duty = False
            print(f"--- DUTY DAY {duty_num} END ---\n")
            continue

        # Check if this would be counted as a leg
        if in_duty and stripped:
            # Multi-line leg detection
            is_multi_line = re.match(r'^(UPS|DH|GT)(\\s|\\d|N/A)', stripped, re.IGNORECASE)
            # MD-11 format (bare flight number)
            is_md11 = re.match(r'^\\d{3,4}(-\\d+)?$', stripped)
            # Single-line leg detection
            is_single_line = re.search(r'(UPS|DH|GT)', stripped, re.IGNORECASE) and (
                re.search(r'[A-Z]{3}-[A-Z]{3}', stripped) or re.search(r'\\(\\d+\\)\\d{2}:\\d{2}', stripped)
            )

            if is_multi_line:
                print(f"  [LEG - Multi-line] Line {i}: {stripped}")
            elif is_md11:
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if re.match(r'^[A-Z]{3}-[A-Z]{3}(\\([A-Z]\\))?$', next_line):
                        print(f"  [LEG - MD-11] Line {i}: {stripped} -> {next_line}")
                    else:
                        print(f"  [NOT LEG - No route] Line {i}: {stripped} (next: {next_line})")
            elif is_single_line:
                print(f"  [LEG - Single-line] Line {i}: {stripped[:80]}...")
            elif re.search(r'UPS|DH|GT', stripped, re.IGNORECASE):
                print(f"  [NOT LEG - Missing route/time] Line {i}: {stripped[:80]}...")

    print("\n")
