#!/usr/bin/env python3
"""
Debug script to analyze effectiveness calculation behavior.
Tests whether effectiveness properly tracks reservoir changes.
"""

from safte_model import (
    calculate_effectiveness,
    calculate_performance_rhythm,
    calculate_circadian_oscillator,
    RESERVOIR_CAPACITY
)

def test_effectiveness_proportionality():
    """
    Test if effectiveness changes proportionally with reservoir level
    when circadian rhythm is held constant.
    """
    print("=" * 80)
    print("TEST 1: Effectiveness vs Reservoir (Fixed Circadian)")
    print("=" * 80)

    # Test at different times of day (different circadian values)
    test_times = [
        (3, "3 AM - Circadian Trough"),
        (12, "12 PM - Midday"),
        (20, "8 PM - Circadian Peak")
    ]

    for time_hours, label in test_times:
        print(f"\n{label}:")
        print(f"{'Reservoir %':<15} {'Reservoir':<10} {'Reservoir Comp':<15} {'Perf Rhythm':<15} {'Effectiveness':<15} {'Delta Eff':<10}")
        print("-" * 90)

        circadian_c = calculate_circadian_oscillator(time_hours)
        prev_eff = None

        # Test reservoir levels from 100% down to 50% in 10% increments
        for pct in range(100, 40, -10):
            reservoir = (pct / 100.0) * RESERVOIR_CAPACITY
            reservoir_component = 100 * (reservoir / RESERVOIR_CAPACITY)
            perf_rhythm = calculate_performance_rhythm(circadian_c, reservoir)
            effectiveness = calculate_effectiveness(reservoir, perf_rhythm, 0)

            delta = "" if prev_eff is None else f"{effectiveness - prev_eff:+.2f}%"
            prev_eff = effectiveness

            print(f"{pct}%{'':<12} {reservoir:>8.1f}  {reservoir_component:>8.2f}%{'':<6} "
                  f"{perf_rhythm:>8.2f}%{'':<6} {effectiveness:>8.2f}%{'':<6} {delta}")

    print("\n" + "=" * 80)
    print("TEST 2: Component Breakdown - Why Effectiveness Stays Flat")
    print("=" * 80)

    # Simulate a scenario where reservoir drops but effectiveness stays flat
    print("\nScenario: Reservoir drops from 100% to 80% over time")
    print("Time of Day: Variable (to show circadian compensation)")
    print()
    print(f"{'Time':<10} {'Reservoir %':<12} {'Res Comp':<12} {'Circadian':<12} {'Perf Rhythm':<15} {'Effectiveness':<12}")
    print("-" * 90)

    # Simulate reservoir depletion with changing circadian rhythm
    scenarios = [
        (6, 100, "Start: 6 AM (low circadian)"),
        (8, 98, "2 hours awake"),
        (10, 96, "4 hours awake"),
        (12, 94, "6 hours awake (circadian rising)"),
        (14, 92, "8 hours awake"),
        (16, 90, "10 hours awake"),
        (18, 88, "12 hours awake (circadian peak approaching)"),
        (20, 86, "14 hours awake (circadian peak)"),
    ]

    for time_hours, res_pct, description in scenarios:
        reservoir = (res_pct / 100.0) * RESERVOIR_CAPACITY
        reservoir_component = 100 * (reservoir / RESERVOIR_CAPACITY)
        circadian_c = calculate_circadian_oscillator(time_hours)
        perf_rhythm = calculate_performance_rhythm(circadian_c, reservoir)
        effectiveness = calculate_effectiveness(reservoir, perf_rhythm, 0)

        print(f"{time_hours:02d}:00{'':<5} {res_pct}%{'':<9} {reservoir_component:>8.2f}%  "
              f"{circadian_c:>8.4f}  {perf_rhythm:>8.2f}%{'':<6} {effectiveness:>8.2f}%  {description}")

    print("\n" + "=" * 80)
    print("TEST 3: Initial Conditions Analysis")
    print("=" * 80)

    print("\nCurrent Implementation: Always starts at 100% reservoir")
    print("Question: Should we allow configurable initial reservoir level?")
    print()

    test_initial_conditions = [
        (100, "Fully rested (current default)"),
        (90, "Well-rested but not perfect"),
        (80, "Moderate pre-existing fatigue"),
        (70, "Significant pre-existing fatigue"),
    ]

    start_time = 6  # 6 AM duty start
    circadian_c = calculate_circadian_oscillator(start_time)

    print(f"Duty Start Time: {start_time}:00 AM")
    print(f"Circadian at start: {circadian_c:.4f}")
    print()
    print(f"{'Initial Reservoir':<20} {'Effectiveness at Start':<25} {'Interpretation':<30}")
    print("-" * 90)

    for res_pct, description in test_initial_conditions:
        reservoir = (res_pct / 100.0) * RESERVOIR_CAPACITY
        perf_rhythm = calculate_performance_rhythm(circadian_c, reservoir)
        effectiveness = calculate_effectiveness(reservoir, perf_rhythm, 0)

        print(f"{res_pct}%{'':<17} {effectiveness:>8.2f}%{'':<16} {description}")

if __name__ == "__main__":
    test_effectiveness_proportionality()
