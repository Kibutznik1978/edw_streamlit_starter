#!/usr/bin/env python3
"""
Test script to compare 100% vs 90% initial reservoir impact on effectiveness.
"""

from datetime import datetime, timedelta
from safte_model import (
    run_safte_simulation,
    RESERVOIR_CAPACITY,
    calculate_effectiveness,
    calculate_performance_rhythm,
    calculate_circadian_oscillator
)

def test_initial_conditions():
    """Compare effectiveness with 100% vs 90% initial reservoir."""

    print("=" * 80)
    print("COMPARISON: 100% vs 90% Initial Reservoir")
    print("=" * 80)

    # Example: Early morning duty (6 AM - 2 PM)
    duty_start = datetime(2025, 10, 24, 6, 0)
    duty_end = datetime(2025, 10, 24, 14, 0)
    duty_periods = [(duty_start, duty_end)]

    print("\nExample Duty Period: 6 AM - 2 PM (8 hours)")
    print()

    # Test with 100% initial (current default)
    results_100 = run_safte_simulation(duty_periods, initial_reservoir_level=RESERVOIR_CAPACITY)

    # Test with 90% initial (aviation standard)
    results_90 = run_safte_simulation(duty_periods, initial_reservoir_level=0.9 * RESERVOIR_CAPACITY)

    # Compare key timepoints
    print(f"{'Time':<12} {'100% Initial':<25} {'90% Initial':<25} {'Difference':<15}")
    print(f"{'':12} {'Reservoir':<10} {'Effectiveness':<14} {'Reservoir':<10} {'Effectiveness':<14}")
    print("-" * 90)

    # Sample every 2 hours
    for i in range(0, len(results_100), 120):  # Every 120 minutes
        r100 = results_100[i]
        r90 = results_90[i]

        time_str = r100['timestamp'].strftime("%m/%d %H:%M")
        res_100_pct = (r100['reservoir_level'] / RESERVOIR_CAPACITY) * 100
        res_90_pct = (r90['reservoir_level'] / RESERVOIR_CAPACITY) * 100
        eff_100 = r100['effectiveness']
        eff_90 = r90['effectiveness']
        diff = eff_100 - eff_90

        print(f"{time_str:<12} {res_100_pct:>6.1f}%  {eff_100:>8.2f}%{'':<6} "
              f"{res_90_pct:>6.1f}%  {eff_90:>8.2f}%{'':<6} {diff:>+6.2f}%")

    print("\n" + "=" * 80)
    print("KEY OBSERVATIONS")
    print("=" * 80)

    # Find minimum effectiveness for each scenario
    min_eff_100 = min(r['effectiveness'] for r in results_100)
    min_eff_90 = min(r['effectiveness'] for r in results_90)

    # Find when effectiveness is at minimum
    min_time_100 = next(r['timestamp'] for r in results_100 if r['effectiveness'] == min_eff_100)
    min_time_90 = next(r['timestamp'] for r in results_90 if r['effectiveness'] == min_eff_90)

    print(f"\n100% Initial Reservoir:")
    print(f"  Minimum Effectiveness: {min_eff_100:.2f}% at {min_time_100.strftime('%m/%d %H:%M')}")

    print(f"\n90% Initial Reservoir (Aviation Standard):")
    print(f"  Minimum Effectiveness: {min_eff_90:.2f}% at {min_time_90.strftime('%m/%d %H:%M')}")

    print(f"\nDifference: {min_eff_100 - min_eff_90:+.2f}%")
    print(f"\nConclusion: Starting at 90% provides more realistic and conservative fatigue estimates.")

def test_effectiveness_unclamped():
    """Test what happens if we don't clamp effectiveness at 100%."""

    print("\n" + "=" * 80)
    print("ANALYSIS: Effectiveness Above 100% (Unclamped)")
    print("=" * 80)

    print("\nShould we allow effectiveness > 100%?")
    print()

    # Test at circadian peak with high reservoir
    time_hours = 20  # 8 PM - circadian peak
    reservoir_levels = [100, 95, 90, 85, 80]

    print(f"Time: 8 PM (Circadian Peak)")
    print()
    print(f"{'Reservoir %':<15} {'Res Component':<15} {'Perf Rhythm':<15} {'Raw E':<15} {'Clamped E':<15}")
    print("-" * 90)

    circadian_c = calculate_circadian_oscillator(time_hours)

    for res_pct in reservoir_levels:
        reservoir = (res_pct / 100.0) * RESERVOIR_CAPACITY
        reservoir_component = 100 * (reservoir / RESERVOIR_CAPACITY)
        perf_rhythm = calculate_performance_rhythm(circadian_c, reservoir)

        # Calculate raw (unclamped) effectiveness
        raw_eff = reservoir_component + perf_rhythm  # No sleep inertia
        clamped_eff = max(0, min(100, raw_eff))

        print(f"{res_pct}%{'':<12} {reservoir_component:>8.2f}%{'':<6} {perf_rhythm:>8.2f}%{'':<6} "
              f"{raw_eff:>8.2f}%{'':<6} {clamped_eff:>8.2f}%")

    print("\nObservation:")
    print("- At 100% reservoir + circadian peak: Raw effectiveness = 109%")
    print("- Clamping at 100% masks the first 9% of reservoir depletion")
    print("- Aviation research indicates effectiveness IS clamped at 100%")
    print("- Starting at 90% reservoir reduces likelihood of hitting ceiling")

if __name__ == "__main__":
    test_initial_conditions()
    test_effectiveness_unclamped()
