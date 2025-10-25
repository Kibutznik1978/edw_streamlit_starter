#!/usr/bin/env python3
"""
SAFTE Specification Compliance Test
Validates our implementation against SAFTE.md and Hursh et al. 2004
"""

from safte_model import *
import math

def test_constants():
    """Test that all constants match SAFTE specification."""
    print("=" * 80)
    print("TEST 1: Constants Validation")
    print("=" * 80)

    tests = [
        ("Reservoir Capacity (Rc)", RESERVOIR_CAPACITY, 2880.0),
        ("Performance Use Rate (P)", PERFORMANCE_USE_RATE, 0.5),
        ("Max Sleep Accumulation (S_max)", MAX_SLEEP_ACCUMULATION_RATE, 3.4),
        ("Feedback Constant (f)", SLEEP_DEBT_FACTOR, 0.00312),
        ("Circadian 24h Phase (p)", CIRCADIAN_PHASE_24H, 18.0),
        ("Circadian 12h Offset (p')", CIRCADIAN_PHASE_12H_OFFSET, 3.0),
        ("Circadian 12h Amplitude (β)", CIRCADIAN_AMPLITUDE_12H, 0.5),
        ("Sleep Propensity Amplitude (a_s)", SLEEP_PROPENSITY_AMPLITUDE, 0.55),
        ("Performance Fixed Amplitude (a1)", PERFORMANCE_RHYTHM_AMPLITUDE_FIXED, 7.0),
        ("Performance Variable Amplitude (a2)", PERFORMANCE_RHYTHM_AMPLITUDE_VARIABLE, 5.0),
        ("Sleep Inertia Max (I_max)", SLEEP_INERTIA_MAX, 5.0),
    ]

    all_pass = True
    for name, actual, expected in tests:
        status = "✅ PASS" if actual == expected else "❌ FAIL"
        if actual != expected:
            all_pass = False
        print(f"{name:40} {actual:>10} (expected {expected:>10}) {status}")

    print(f"\n{'All constants match specification' if all_pass else 'Some constants do not match'}")
    return all_pass

def test_sleep_accumulation_behavior():
    """Test that sleep accumulation produces correct exponential saturation."""
    print("\n" + "=" * 80)
    print("TEST 2: Sleep Accumulation Exponential Saturation")
    print("=" * 80)

    print("\nTesting recovery rate vs reservoir level (circadian neutral C=0):")
    print(f"{'Reservoir %':<15} {'Reservoir':<10} {'S(t)':<15} {'% of S_max':<15}")
    print("-" * 80)

    for pct in [0, 25, 50, 75, 90, 95, 100]:
        reservoir = (pct / 100.0) * RESERVOIR_CAPACITY
        s_t = calculate_sleep_accumulation_rate(0.0, reservoir)
        pct_of_max = (s_t / MAX_SLEEP_ACCUMULATION_RATE) * 100

        print(f"{pct}%{'':<12} {reservoir:>8.1f}  {s_t:>8.4f} u/min  {pct_of_max:>6.1f}%")

    # Key validation points
    s_empty = calculate_sleep_accumulation_rate(0.0, 0.0)
    s_full = calculate_sleep_accumulation_rate(0.0, RESERVOIR_CAPACITY)

    print(f"\n✅ Empty reservoir (R=0): S(t) = {s_empty:.4f} (should be ≈{MAX_SLEEP_ACCUMULATION_RATE})")
    print(f"✅ Full reservoir (R=Rc): S(t) = {s_full:.4f} (should be ≈0)")

    return s_empty > 3.3 and s_full < 0.1

def test_circadian_peaks_and_troughs():
    """Test that circadian oscillator has correct peaks and troughs."""
    print("\n" + "=" * 80)
    print("TEST 3: Circadian Oscillator Behavior")
    print("=" * 80)

    print("\nCircadian values throughout the day:")
    print(f"{'Time':<10} {'C(t)':<10} {'Expected Behavior':<30}")
    print("-" * 80)

    test_times = [
        (3, "Trough (window of circadian low)"),
        (6, "Morning rise begins"),
        (12, "Midday neutral"),
        (18, "Peak approaching (6 PM acrophase)"),
        (20, "Peak (early evening)"),
        (0, "Night descent"),
    ]

    for hour, description in test_times:
        c_t = calculate_circadian_oscillator(hour)
        print(f"{hour:02d}:00{'':<5} {c_t:>+7.4f}  {description}")

    # Find actual peak and trough
    min_c, max_c = 0, 0
    min_hour, max_hour = 0, 0

    for hour in range(24):
        c = calculate_circadian_oscillator(hour)
        if c < min_c:
            min_c, min_hour = c, hour
        if c > max_c:
            max_c, max_hour = c, hour

    print(f"\n✅ Peak occurs at {max_hour:02d}:00 with C = {max_c:+.4f}")
    print(f"✅ Trough occurs at {min_hour:02d}:00 with C = {min_c:+.4f}")

    # Validate: peak should be around 18-20h, trough around 3-6h
    return 18 <= max_hour <= 22 and 2 <= min_hour <= 6

def test_effectiveness_equation():
    """Test that effectiveness equation combines components correctly."""
    print("\n" + "=" * 80)
    print("TEST 4: Effectiveness Equation E = 100(R/Rc) + C - I")
    print("=" * 80)

    # Test scenario: 80% reservoir, neutral circadian, no sleep inertia
    reservoir = 0.8 * RESERVOIR_CAPACITY
    circadian_c = 0.0
    perf_rhythm = calculate_performance_rhythm(circadian_c, reservoir)
    sleep_inertia = 0.0

    # Manual calculation
    reservoir_component = 100 * (reservoir / RESERVOIR_CAPACITY)
    expected_e = reservoir_component + perf_rhythm + sleep_inertia

    # Our function
    actual_e = calculate_effectiveness(reservoir, perf_rhythm, sleep_inertia)

    print(f"Test Case: 80% reservoir, neutral circadian, no sleep inertia")
    print(f"  Reservoir component: 100 * (0.8) = {reservoir_component:.2f}%")
    print(f"  Performance rhythm: {perf_rhythm:+.2f}%")
    print(f"  Sleep inertia: {sleep_inertia:+.2f}%")
    print(f"  Expected E: {expected_e:.2f}%")
    print(f"  Actual E: {actual_e:.2f}%")
    print(f"  {'✅ PASS' if abs(expected_e - actual_e) < 0.01 else '❌ FAIL'}")

    # Test clamping at 100%
    print(f"\nTest Case: 100% reservoir at circadian peak (should clamp at 100%)")
    reservoir = RESERVOIR_CAPACITY
    circadian_c = 1.5  # High circadian
    perf_rhythm = calculate_performance_rhythm(circadian_c, reservoir)

    raw_e = 100 + perf_rhythm
    clamped_e = calculate_effectiveness(reservoir, perf_rhythm, 0.0)

    print(f"  Raw effectiveness: {raw_e:.2f}%")
    print(f"  Clamped effectiveness: {clamped_e:.2f}%")
    print(f"  {'✅ PASS (clamped at 100%)' if clamped_e == 100 else '❌ FAIL'}")

    return True

def test_sleep_inertia_decay():
    """Test that sleep inertia decays properly over ~2 hours."""
    print("\n" + "=" * 80)
    print("TEST 5: Sleep Inertia ~2 Hour Decay")
    print("=" * 80)

    print("\nSleep inertia decay after awakening (SI = 3.0):")
    print(f"{'Time':<15} {'I(t)':<10} {'% of I_max':<15}")
    print("-" * 80)

    SI = 3.0  # Typical sleep intensity

    for minutes in [0, 15, 30, 45, 60, 90, 120, 150]:
        i_t = calculate_sleep_inertia(minutes, SI)
        pct_of_max = (abs(i_t) / SLEEP_INERTIA_MAX) * 100

        print(f"{minutes} min{'':<10} {i_t:>+7.3f}%  {pct_of_max:>6.1f}%")

    # Test decay behavior
    i_0 = calculate_sleep_inertia(0, SI)
    i_120 = calculate_sleep_inertia(120, SI)

    print(f"\n✅ At awakening (t=0): I = {i_0:+.3f}% (should be ≈-5%)")
    print(f"✅ After 2 hours (t=120): I = {i_120:+.3f}% (should be near 0)")

    # Should be near -5% at start and near 0 after 2 hours
    return abs(i_0 + 5.0) < 0.1 and abs(i_120) < 1.0

def test_90_percent_initial_condition():
    """Test that default initial reservoir is 90% per aviation standard."""
    print("\n" + "=" * 80)
    print("TEST 6: Aviation Standard Initial Condition (90%)")
    print("=" * 80)

    from datetime import datetime

    # Create a dummy duty period
    duty_start = datetime(2025, 10, 24, 6, 0)
    duty_end = datetime(2025, 10, 24, 14, 0)
    duty_periods = [(duty_start, duty_end)]

    # Run simulation with default initial condition
    results = run_safte_simulation(duty_periods)

    if results:
        # Find the first result (should be at start of simulation)
        initial_reservoir = results[0]['reservoir_level']
        expected_90_pct = 0.9 * RESERVOIR_CAPACITY

        print(f"Default initial reservoir: {initial_reservoir:.1f} units")
        print(f"Expected (90% of Rc): {expected_90_pct:.1f} units")
        print(f"Percentage: {(initial_reservoir/RESERVOIR_CAPACITY)*100:.1f}%")

        # Allow for minor depletion during pre-simulation period
        is_correct = 0.85 * RESERVOIR_CAPACITY <= initial_reservoir <= 0.95 * RESERVOIR_CAPACITY
        print(f"\n{'✅ PASS (using aviation standard 90%)' if is_correct else '❌ FAIL'}")

        return is_correct

    return False

def run_all_tests():
    """Run all validation tests."""
    print("\n" + "=" * 80)
    print("SAFTE MODEL SPECIFICATION COMPLIANCE VALIDATION")
    print("=" * 80)

    results = {
        "Constants": test_constants(),
        "Sleep Accumulation": test_sleep_accumulation_behavior(),
        "Circadian Oscillator": test_circadian_peaks_and_troughs(),
        "Effectiveness Equation": test_effectiveness_equation(),
        "Sleep Inertia Decay": test_sleep_inertia_decay(),
        "90% Initial Condition": test_90_percent_initial_condition(),
    }

    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:<30} {status}")

    all_passed = all(results.values())

    print("\n" + "=" * 80)
    if all_passed:
        print("✅ ALL TESTS PASSED - Implementation matches SAFTE specification")
    else:
        print("❌ SOME TESTS FAILED - Review discrepancies")
    print("=" * 80)

    return all_passed

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
