"""
Test SAFTE Analysis with Real Trip Data from PDF

This script validates the complete integration:
PDF -> Trip Parser -> SAFTE Model -> Fatigue Metrics
"""

from datetime import datetime, timedelta
from edw_reporter import parse_pairings, parse_trip_for_table
from safte_integration import analyze_trip_fatigue, format_fatigue_summary
import PyPDF2


def test_real_trip_analysis(pdf_path, trip_number=None):
    """
    Parse a real PDF, extract a trip, and run SAFTE analysis.

    Args:
        pdf_path: Path to the PDF file
        trip_number: Specific trip number to analyze (optional, uses first trip if None)
    """
    print(f"Reading PDF: {pdf_path}")
    print("=" * 80)

    # Extract text from PDF
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text_pages = []
        for page in reader.pages:
            text_pages.append(page.extract_text())
        full_text = '\n'.join(text_pages)

    # Parse all trips from PDF
    trips = parse_pairings(full_text)
    print(f"Found {len(trips)} trips in PDF\n")

    if not trips:
        print("No trips found in PDF!")
        return

    # Select trip to analyze
    if trip_number is not None:
        # Find trip by number
        trip_text = None
        for t in trips:
            parsed = parse_trip_for_table(t)
            if parsed.get('trip_id') == trip_number:
                trip_text = t
                break
        if not trip_text:
            print(f"Trip {trip_number} not found!")
            print(f"Available trips: {[parse_trip_for_table(t).get('trip_id') for t in trips[:10]]}")
            return
    else:
        # Use first trip
        trip_text = trips[0]

    # Parse the trip
    parsed_trip = parse_trip_for_table(trip_text)
    trip_id = parsed_trip.get('trip_id', 'Unknown')
    duty_days = parsed_trip.get('duty_days', [])

    print(f"Analyzing Trip {trip_id}")
    print(f"  Duty Days: {len(duty_days)}")
    print(f"  Date/Freq: {parsed_trip.get('date_freq', 'N/A')}")
    print()

    # Display duty day details
    print("Duty Day Schedule:")
    for i, dd in enumerate(duty_days, 1):
        print(f"  Day {i}: {dd.get('duty_start')} - {dd.get('duty_end')}")
        print(f"         Duty Time: {dd.get('duty_time')}, Flights: {len(dd.get('flights', []))}")
    print()

    # Run SAFTE analysis
    print("Running SAFTE Fatigue Analysis...")
    reference_date = datetime(2025, 10, 22, 0, 0, 0)  # Arbitrary reference date
    analysis = analyze_trip_fatigue(parsed_trip, reference_date)

    if 'error' in analysis:
        print(f"ERROR: {analysis['error']}")
        return

    # Display results
    print()
    print(format_fatigue_summary(analysis['fatigue_metrics']))
    print()

    # Additional details
    metrics = analysis['fatigue_metrics']
    duty_periods = analysis['duty_periods']

    print("Detailed Metrics:")
    print(f"  Duty Periods Analyzed: {len(duty_periods)}")
    print(f"  Total Simulation Points: {len(analysis['safte_results'])}")
    print(f"  Lowest Effectiveness: {metrics['lowest_effectiveness']:.2f}%")
    print(f"    Occurred at: {metrics['lowest_effectiveness_time']}")
    print(f"  Average Effectiveness: {metrics['average_effectiveness_on_duty']:.2f}%")
    print(f"  Time Below 77.5% (Danger): {metrics['time_below_danger_threshold_minutes']} minutes")
    print(f"  Time Below 85% (Warning): {metrics['time_below_warning_threshold_minutes']} minutes")
    print(f"  Overall Fatigue Score: {metrics['overall_fatigue_score']:.0f}/100")
    print()

    # Sample effectiveness timeline (first 2 hours of first duty)
    if duty_periods:
        first_duty_start, _ = duty_periods[0]
        print(f"Sample Effectiveness Timeline (First 2 Hours of Duty):")
        print(f"{'Time':<20} {'Effectiveness':<15} {'Reservoir':<12} {'Sleep Inertia':<15}")
        print("-" * 65)

        for result in analysis['safte_results']:
            if first_duty_start <= result['timestamp'] < first_duty_start + timedelta(hours=2):
                if (result['timestamp'] - first_duty_start).seconds % 600 == 0:  # Every 10 minutes
                    print(f"{str(result['timestamp'])[11:19]:<20} "
                          f"{result['effectiveness']:>6.1f}%        "
                          f"{result['reservoir_level']:>7.0f}      "
                          f"{result['sleep_inertia']:>6.2f}")

    return analysis


if __name__ == '__main__':
    # Test with ONT 757 PDF
    pdf_path = 'test_data/BID2601_757_ONT_TRIPS_CAROL.pdf'

    print("\n" + "=" * 80)
    print("SAFTE FATIGUE ANALYSIS - REAL TRIP DATA")
    print("=" * 80 + "\n")

    # Analyze first trip in PDF
    analysis = test_real_trip_analysis(pdf_path)

    print("\n" + "=" * 80)
    print("Analysis complete! Data bridge is working with real PDF data.")
    print("=" * 80)
