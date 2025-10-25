#!/usr/bin/env python3
"""
Test multi-day layover parsing
Validates that 50+ hour layovers are parsed correctly
"""

from datetime import datetime, timedelta
from safte_integration import trip_to_duty_periods, extract_trip_start_date

def test_50_hour_layover():
    """Test that a 50-hour layover advances the date correctly."""

    print("=" * 80)
    print("TEST: 50-Hour Layover Parsing with Actual Trip Date")
    print("=" * 80)

    # Simulate the pairing structure from the user's screenshot
    # Using actual times from the PDF screenshot
    # Duty Day 1: Last flight arrives at 04:36 local (10:36 zulu), debrief adds 15min → 04:51 local
    # 50h 39min layover (from 04:51 to next briefing at 07:30, two days later)
    # Duty Day 2: Briefing at 07:30 local (13:30 zulu)

    parsed_trip = {
        'trip_id': 'TEST_LAYOVER',
        'date_freq': 'Only on Mon 10Nov2025',  # Trip start date
        'duty_days': [
            {
                'duty_start': '(21)03:32',  # Nov 10 at 21:32 local, 03:32 zulu
                'duty_end': '(04)10:51',    # Nov 11 at 04:51 local (10:36 arrival + 15min), 10:51 zulu
                'rest': '50h39 S1',         # 50 hour 39 minute layover
            },
            {
                'duty_start': '(07)13:30',  # Nov 13 at 07:30 local (two days later), 13:30 zulu
                'duty_end': '(16)22:25',    # Nov 13 at 16:25 local (22:10 arrival + 15min), 22:25 zulu
                'rest': None,               # No layover after last duty day
            },
        ]
    }

    # Extract trip start date from date_freq
    reference_date = extract_trip_start_date(parsed_trip)
    if reference_date:
        print(f"Extracted trip start date: {reference_date.strftime('%Y-%m-%d %A')}")
    else:
        print("Failed to extract trip start date, using default")
        reference_date = datetime(2025, 11, 10, 0, 0, 0)

    duty_periods = trip_to_duty_periods(parsed_trip, reference_date)

    print(f"\nReference date: {reference_date.strftime('%Y-%m-%d %A')}")
    print(f"\nParsed duty periods:")
    print("-" * 80)

    for i, (start, end) in enumerate(duty_periods, 1):
        duration = end - start
        hours = duration.total_seconds() / 3600

        print(f"\nDuty Period {i}:")
        print(f"  Start: {start.strftime('%Y-%m-%d %A %H:%M')} (day {start.day})")
        print(f"  End:   {end.strftime('%Y-%m-%d %A %H:%M')} (day {end.day})")
        print(f"  Duration: {hours:.2f} hours")

        if i < len(duty_periods):
            next_start = duty_periods[i][0]
            layover = next_start - end
            layover_hours = layover.total_seconds() / 3600
            print(f"  Layover to next duty: {layover_hours:.2f} hours ({layover})")

    # Validate the layover
    if len(duty_periods) >= 2:
        duty3_end = duty_periods[0][1]
        duty4_start = duty_periods[1][0]
        layover = duty4_start - duty3_end
        layover_hours = layover.total_seconds() / 3600

        print("\n" + "=" * 80)
        print("LAYOVER VALIDATION")
        print("=" * 80)
        print(f"Duty 3 ends:    {duty3_end.strftime('%Y-%m-%d %A %H:%M')} (day {duty3_end.day})")
        print(f"Duty 4 starts:  {duty4_start.strftime('%Y-%m-%d %A %H:%M')} (day {duty4_start.day})")
        print(f"Layover:        {layover_hours:.2f} hours ({layover})")
        print(f"Expected:       ~50-51 hours (50h 39min from pairing)")

        # Check if layover is approximately correct (50-51 hours)
        if 49 <= layover_hours <= 52:
            print(f"\n✅ PASS: Layover correctly parsed as {layover_hours:.2f} hours")
            return True
        else:
            print(f"\n❌ FAIL: Layover is {layover_hours:.2f} hours, expected ~50 hours")
            return False
    else:
        print("\n❌ FAIL: Not enough duty periods parsed")
        return False

def test_short_layover():
    """Test that a normal overnight layover (12 hours) still works."""

    print("\n" + "=" * 80)
    print("TEST: Normal Overnight Layover (12 hours)")
    print("=" * 80)

    parsed_trip = {
        'trip_id': 'TEST_OVERNIGHT',
        'duty_days': [
            {
                'duty_start': '(06)06:00',  # 6 AM
                'duty_end': '(14)14:00',    # 2 PM (8 hour duty)
                'rest': '16h00',            # 16 hour overnight layover
            },
            {
                'duty_start': '(06)06:00',  # 6 AM next day (16 hour layover)
                'duty_end': '(14)14:00',    # 2 PM
                'rest': None,
            },
        ]
    }

    reference_date = datetime(2025, 10, 24, 0, 0, 0)
    duty_periods = trip_to_duty_periods(parsed_trip, reference_date)

    if len(duty_periods) >= 2:
        duty1_end = duty_periods[0][1]
        duty2_start = duty_periods[1][0]
        layover = duty2_start - duty1_end
        layover_hours = layover.total_seconds() / 3600

        print(f"Duty 1 ends:    {duty1_end.strftime('%Y-%m-%d %H:%M')} (day {duty1_end.day})")
        print(f"Duty 2 starts:  {duty2_start.strftime('%Y-%m-%d %H:%M')} (day {duty2_start.day})")
        print(f"Layover:        {layover_hours:.2f} hours")

        # Should advance by 1 day (16 hour layover)
        if duty2_start.day == duty1_end.day + 1 and 15 <= layover_hours <= 17:
            print(f"\n✅ PASS: Normal layover correctly parsed")
            return True
        else:
            print(f"\n❌ FAIL: Layover calculation incorrect")
            return False

    return False

if __name__ == "__main__":
    print("\nTesting Multi-Day Layover Parsing Fix\n")

    test1 = test_50_hour_layover()
    test2 = test_short_layover()

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"50-hour layover test: {'✅ PASS' if test1 else '❌ FAIL'}")
    print(f"Short layover test:   {'✅ PASS' if test2 else '❌ FAIL'}")
    print("=" * 80)

    if test1 and test2:
        print("\n✅ All tests passed - multi-day layover bug is fixed!")
        exit(0)
    else:
        print("\n❌ Some tests failed")
        exit(1)
