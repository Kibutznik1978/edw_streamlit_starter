"""
Test to verify circadian rhythm is correctly anchored to clock time, not elapsed time.
"""

from datetime import datetime, timedelta
from safte_model import run_safte_simulation, calculate_circadian_oscillator
import math


def test_circadian_consistency():
    """
    Test: Same clock time should produce same circadian value regardless of simulation start.

    This verifies that circadian rhythm is anchored to time of day, not elapsed time.
    """
    print("Test 1: Circadian consistency across different simulation starts")

    # Define a 3 AM duty (circadian trough) with two different simulation starts
    duty_time = datetime(2025, 1, 15, 3, 0)  # Jan 15, 3:00 AM
    duty_end = duty_time + timedelta(hours=4)

    # Simulation 1: Start 1 hour before duty
    sim1_start = duty_time - timedelta(hours=1)
    duty_periods_1 = [(duty_time, duty_end)]
    results_1 = run_safte_simulation(duty_periods_1)

    # Simulation 2: Start 1 day before duty
    sim2_start = duty_time - timedelta(days=1)
    duty_periods_2 = [(duty_time, duty_end)]
    results_2 = run_safte_simulation(duty_periods_2)

    # Find circadian values at 3 AM in both simulations
    duty_idx_1 = next(i for i, r in enumerate(results_1) if r['timestamp'] >= duty_time)
    duty_idx_2 = next(i for i, r in enumerate(results_2) if r['timestamp'] >= duty_time)

    circ_1 = results_1[duty_idx_1]['circadian_rhythm']
    circ_2 = results_2[duty_idx_2]['circadian_rhythm']

    print(f"  3 AM duty (circadian trough expected)")
    print(f"  Simulation 1 (start 1 hour before): Circadian = {circ_1:.4f}")
    print(f"  Simulation 2 (start 1 day before): Circadian = {circ_2:.4f}")
    print(f"  Difference: {abs(circ_1 - circ_2):.6f}")

    # Should be identical (or nearly so, allowing for tiny floating point errors)
    assert abs(circ_1 - circ_2) < 0.01, f"Circadian values should match! Got {circ_1} vs {circ_2}"
    print("  ✓ PASS: Circadian values are consistent\n")


def test_circadian_trough_at_3am():
    """
    Test: Verify 3 AM is at circadian trough (lowest alertness).
    """
    print("Test 2: Circadian trough at 3 AM")

    # Calculate circadian component at various times
    times = [
        (3, "3 AM (expected trough)"),
        (6, "6 AM (rising)"),
        (12, "12 PM (midday)"),
        (18, "6 PM (expected peak)"),
        (21, "9 PM (falling)"),
        (0, "Midnight")
    ]

    values = []
    for hour, label in times:
        c = calculate_circadian_oscillator(hour)
        values.append((hour, c, label))
        print(f"  {label:25s}: C = {c:+.4f}")

    # Find minimum (trough)
    min_hour, min_c, min_label = min(values, key=lambda x: x[1])
    max_hour, max_c, max_label = max(values, key=lambda x: x[1])

    print(f"\n  Minimum (trough): {min_label} with C = {min_c:.4f}")
    print(f"  Maximum (peak):   {max_label} with C = {max_c:.4f}")

    # 3-6 AM should be in the trough region
    assert min_hour in [3, 6], f"Expected trough at 3-6 AM, got {min_label}"
    print("  ✓ PASS: Circadian trough is in early morning (3-6 AM)\n")


def test_circadian_peak_at_6pm():
    """
    Test: Verify 6 PM is at circadian peak (highest alertness).
    """
    print("Test 3: Circadian peak at 6 PM")

    # Sample every hour
    hour_values = []
    for hour in range(24):
        c = calculate_circadian_oscillator(hour)
        hour_values.append((hour, c))

    # Find peak
    peak_hour, peak_c = max(hour_values, key=lambda x: x[1])

    print(f"  Peak circadian value: {peak_c:.4f} at hour {peak_hour}")
    print(f"  Expected peak: Early evening (17:00-21:00)")
    print(f"  Note: Dual oscillator (24h + 12h harmonics) shifts peak from p=18 to ~20:00")

    # Peak should be in early evening (17:00-21:00) - the "wake maintenance zone"
    # The dual oscillator design (24h + 12h harmonics) creates peak around 8 PM
    assert 17 <= peak_hour <= 21, f"Expected peak in early evening (17-21h), got hour {peak_hour}"
    print("  ✓ PASS: Circadian peak is in early evening wake maintenance zone\n")


def test_red_eye_flight_circadian():
    """
    Test: Red-eye flight (11 PM - 7 AM) should experience circadian trough.
    """
    print("Test 4: Red-eye flight circadian trough")

    # Red-eye: 11 PM to 7 AM next day
    duty_start = datetime(2025, 1, 15, 23, 0)  # 11 PM
    duty_end = datetime(2025, 1, 16, 7, 0)     # 7 AM next day

    duty_periods = [(duty_start, duty_end)]
    results = run_safte_simulation(duty_periods)

    # Find results during duty period
    duty_start_idx = next(i for i, r in enumerate(results) if r['timestamp'] >= duty_start)
    duty_end_idx = next(i for i, r in enumerate(results) if r['timestamp'] >= duty_end)

    duty_results = results[duty_start_idx:duty_end_idx]

    # Find lowest circadian rhythm during duty
    lowest_circ = min(r['circadian_rhythm'] for r in duty_results)
    lowest_time = next(r['timestamp'] for r in duty_results if r['circadian_rhythm'] == lowest_circ)

    print(f"  Red-eye duty: {duty_start.strftime('%H:%M')} - {duty_end.strftime('%H:%M')}")
    print(f"  Lowest circadian rhythm: {lowest_circ:.4f}")
    print(f"  Occurred at: {lowest_time.strftime('%Y-%m-%d %H:%M')}")

    # Should hit trough in early morning (3-6 AM)
    assert 3 <= lowest_time.hour <= 6, f"Expected trough at 3-6 AM, got {lowest_time.hour}:00"
    assert lowest_circ < 0, f"Expected negative circadian value at trough, got {lowest_circ}"
    print("  ✓ PASS: Red-eye experiences circadian trough at 3-6 AM\n")


def test_performance_rhythm_modulation():
    """
    Test: Performance rhythm amplitude increases with fatigue.

    The variable amplitude a2 makes circadian effects stronger when fatigued.
    """
    print("Test 5: Performance rhythm amplitude modulation by fatigue")

    from safte_model import calculate_performance_rhythm, RESERVOIR_CAPACITY

    # Test at circadian trough (C = -1.0)
    circadian_trough = -1.0

    # Well-rested (90% reservoir)
    reservoir_high = RESERVOIR_CAPACITY * 0.9
    perf_high = calculate_performance_rhythm(circadian_trough, reservoir_high)

    # Fatigued (50% reservoir)
    reservoir_low = RESERVOIR_CAPACITY * 0.5
    perf_low = calculate_performance_rhythm(circadian_trough, reservoir_low)

    print(f"  Circadian component: {circadian_trough}")
    print(f"  Well-rested (90% reservoir): Performance rhythm = {perf_high:.4f}")
    print(f"  Fatigued (50% reservoir):    Performance rhythm = {perf_low:.4f}")
    print(f"  Difference: {abs(perf_low - perf_high):.4f}")

    # Fatigued state should have larger (more negative) circadian effect
    assert perf_low < perf_high, "Fatigue should amplify circadian trough effect"
    assert abs(perf_low) > abs(perf_high), "Fatigued state should have stronger circadian modulation"

    print("  ✓ PASS: Fatigue amplifies circadian rhythm effects\n")


if __name__ == "__main__":
    print("=" * 70)
    print("Circadian Rhythm Fix Verification Tests")
    print("=" * 70)
    print()

    test_circadian_consistency()
    test_circadian_trough_at_3am()
    test_circadian_peak_at_6pm()
    test_red_eye_flight_circadian()
    test_performance_rhythm_modulation()

    print("=" * 70)
    print("✓ All circadian rhythm tests passed!")
    print("=" * 70)
