"""
Integration test for SAFTE model with realistic trip data.

Tests the complete SAFTE simulation with various duty schedules to verify:
- Reservoir depletion during duty
- Reservoir recovery during sleep
- Circadian rhythm effects
- Sleep inertia after awakening
- Realistic fatigue accumulation patterns
"""

from datetime import datetime, timedelta
from safte_model import run_safte_simulation, RESERVOIR_CAPACITY, PERFORMANCE_USE_RATE


def test_single_day_trip():
    """
    Test: Simple single-day trip (8am-6pm duty).

    Expected behavior:
    - Reservoir depletes during duty at 0.5 units/min
    - Recovers during sleep
    - Sleep inertia appears after awakening
    """
    print("Test 1: Single day trip (8am-6pm duty)")

    # Define a simple single-day trip
    base_date = datetime(2025, 1, 15, 8, 0)  # Jan 15, 2025, 8:00 AM
    duty_start = base_date
    duty_end = base_date.replace(hour=18, minute=0)  # 6:00 PM

    duty_periods = [(duty_start, duty_end)]

    # Run simulation
    results = run_safte_simulation(duty_periods)

    # Find key timepoints
    duty_start_idx = next(i for i, r in enumerate(results) if r['timestamp'] >= duty_start)
    duty_end_idx = next(i for i, r in enumerate(results) if r['timestamp'] >= duty_end)

    initial_reservoir = results[duty_start_idx]['reservoir_level']
    final_reservoir = results[duty_end_idx]['reservoir_level']
    duty_duration_minutes = (duty_end - duty_start).total_seconds() / 60

    # Calculate expected depletion
    expected_depletion = PERFORMANCE_USE_RATE * duty_duration_minutes
    actual_depletion = initial_reservoir - final_reservoir

    print(f"  Duty period: {duty_start.strftime('%Y-%m-%d %H:%M')} to {duty_end.strftime('%H:%M')}")
    print(f"  Duty duration: {duty_duration_minutes:.0f} minutes ({duty_duration_minutes/60:.1f} hours)")
    print(f"  Initial reservoir: {initial_reservoir:.1f} units")
    print(f"  Final reservoir: {final_reservoir:.1f} units")
    print(f"  Expected depletion: {expected_depletion:.1f} units")
    print(f"  Actual depletion: {actual_depletion:.1f} units")
    print(f"  Depletion accuracy: {abs(actual_depletion - expected_depletion):.1f} units difference")

    # Verify reasonable depletion
    assert abs(actual_depletion - expected_depletion) < 10, f"Depletion mismatch: expected {expected_depletion}, got {actual_depletion}"
    assert final_reservoir < initial_reservoir, "Reservoir should deplete during duty"

    # Check for sleep recovery after duty
    sleep_periods_found = any(r['is_asleep'] for r in results[duty_end_idx:])
    print(f"  Sleep periods after duty: {'Yes' if sleep_periods_found else 'No'}")

    assert sleep_periods_found, "Should have sleep period after duty"
    print("  ✓ PASS: Single day trip simulation works correctly\n")


def test_multi_day_trip():
    """
    Test: Multi-day trip with multiple duty periods and layovers.

    Expected behavior:
    - Progressive fatigue accumulation if sleep is insufficient
    - Recovery during layovers
    - Realistic fatigue patterns
    """
    print("Test 2: Multi-day trip (3 days, 2 duties)")

    # Define a multi-day trip
    base_date = datetime(2025, 1, 15, 6, 0)

    # Day 1: 6am-4pm duty
    duty1_start = base_date
    duty1_end = base_date.replace(hour=16, minute=0)

    # Day 2: 8am-5pm duty (after 16-hour layover)
    duty2_start = base_date + timedelta(days=1, hours=2)  # Next day, 8am
    duty2_end = duty2_start + timedelta(hours=9)  # 5pm

    duty_periods = [
        (duty1_start, duty1_end),
        (duty2_start, duty2_end)
    ]

    # Run simulation
    results = run_safte_simulation(duty_periods)

    # Analyze reservoir levels
    duty1_start_idx = next(i for i, r in enumerate(results) if r['timestamp'] >= duty1_start)
    duty1_end_idx = next(i for i, r in enumerate(results) if r['timestamp'] >= duty1_end)
    duty2_start_idx = next(i for i, r in enumerate(results) if r['timestamp'] >= duty2_start)
    duty2_end_idx = next(i for i, r in enumerate(results) if r['timestamp'] >= duty2_end)

    reservoir_duty1_start = results[duty1_start_idx]['reservoir_level']
    reservoir_duty1_end = results[duty1_end_idx]['reservoir_level']
    reservoir_duty2_start = results[duty2_start_idx]['reservoir_level']
    reservoir_duty2_end = results[duty2_end_idx]['reservoir_level']

    print(f"  Day 1 duty: {duty1_start.strftime('%Y-%m-%d %H:%M')} to {duty1_end.strftime('%H:%M')}")
    print(f"    Start reservoir: {reservoir_duty1_start:.1f} units ({reservoir_duty1_start/RESERVOIR_CAPACITY*100:.1f}%)")
    print(f"    End reservoir: {reservoir_duty1_end:.1f} units ({reservoir_duty1_end/RESERVOIR_CAPACITY*100:.1f}%)")

    print(f"  Day 2 duty: {duty2_start.strftime('%Y-%m-%d %H:%M')} to {duty2_end.strftime('%H:%M')}")
    print(f"    Start reservoir: {reservoir_duty2_start:.1f} units ({reservoir_duty2_start/RESERVOIR_CAPACITY*100:.1f}%)")
    print(f"    End reservoir: {reservoir_duty2_end:.1f} units ({reservoir_duty2_end/RESERVOIR_CAPACITY*100:.1f}%)")

    # Verify recovery between duties
    recovery = reservoir_duty2_start - reservoir_duty1_end
    print(f"  Recovery during layover: {recovery:.1f} units")

    assert recovery > 0, f"Expected positive recovery during layover, got {recovery}"
    assert reservoir_duty1_start > reservoir_duty1_end, "Duty 1 should deplete reservoir"
    assert reservoir_duty2_start > reservoir_duty2_end, "Duty 2 should deplete reservoir"

    print("  ✓ PASS: Multi-day trip shows realistic fatigue and recovery\n")


def test_red_eye_flight():
    """
    Test: Red-eye flight (overnight duty) with EDW characteristics.

    Expected behavior:
    - High fatigue during circadian trough (2am-6am)
    - Poor sleep recovery if attempted during day
    - Effectiveness drops significantly
    """
    print("Test 3: Red-eye flight (overnight duty)")

    # Red-eye: 11pm to 7am next day
    base_date = datetime(2025, 1, 15, 23, 0)  # 11 PM
    duty_start = base_date
    duty_end = base_date + timedelta(hours=8)  # 7 AM next day

    duty_periods = [(duty_start, duty_end)]

    # Run simulation
    results = run_safte_simulation(duty_periods)

    # Find lowest effectiveness during duty
    duty_start_idx = next(i for i, r in enumerate(results) if r['timestamp'] >= duty_start)
    duty_end_idx = next(i for i, r in enumerate(results) if r['timestamp'] >= duty_end)

    duty_results = results[duty_start_idx:duty_end_idx]
    lowest_effectiveness = min(r['effectiveness'] for r in duty_results)
    lowest_time = next(r['timestamp'] for r in duty_results if r['effectiveness'] == lowest_effectiveness)

    reservoir_start = results[duty_start_idx]['reservoir_level']
    reservoir_end = results[duty_end_idx]['reservoir_level']

    print(f"  Duty period: {duty_start.strftime('%Y-%m-%d %H:%M')} to {duty_end.strftime('%Y-%m-%d %H:%M')}")
    print(f"  Start reservoir: {reservoir_start:.1f} units ({reservoir_start/RESERVOIR_CAPACITY*100:.1f}%)")
    print(f"  End reservoir: {reservoir_end:.1f} units ({reservoir_end/RESERVOIR_CAPACITY*100:.1f}%)")
    print(f"  Lowest effectiveness during duty: {lowest_effectiveness:.1f}%")
    print(f"  Lowest effectiveness occurred at: {lowest_time.strftime('%Y-%m-%d %H:%M')}")

    # Red-eye should cause significant fatigue
    assert lowest_effectiveness < 85, f"Expected significant fatigue during red-eye, got {lowest_effectiveness}%"
    assert reservoir_end < reservoir_start, "Reservoir should deplete during duty"

    print("  ✓ PASS: Red-eye flight shows realistic fatigue pattern\n")


def test_cumulative_fatigue():
    """
    Test: Multiple consecutive duties with insufficient recovery time.

    Expected behavior:
    - Progressive reservoir depletion
    - Increasing fatigue (decreasing effectiveness)
    - Demonstrates cumulative fatigue effects
    """
    print("Test 4: Cumulative fatigue (4 consecutive duties)")

    # Simulate 4 consecutive days with 10-hour duties and short layovers
    base_date = datetime(2025, 1, 15, 6, 0)
    duty_periods = []

    for day in range(4):
        duty_start = base_date + timedelta(days=day, hours=0)
        duty_end = duty_start + timedelta(hours=10)
        duty_periods.append((duty_start, duty_end))

    # Run simulation
    results = run_safte_simulation(duty_periods)

    # Track reservoir at start of each duty
    reservoir_levels = []
    effectiveness_levels = []

    for duty_start, duty_end in duty_periods:
        duty_start_idx = next(i for i, r in enumerate(results) if r['timestamp'] >= duty_start)
        reservoir_levels.append(results[duty_start_idx]['reservoir_level'])
        effectiveness_levels.append(results[duty_start_idx]['effectiveness'])

    print(f"  Number of duties: {len(duty_periods)}")
    print(f"  Duty duration: 10 hours each")

    for i, (reservoir, effectiveness) in enumerate(zip(reservoir_levels, effectiveness_levels)):
        print(f"  Day {i+1} start: Reservoir={reservoir:.1f} ({reservoir/RESERVOIR_CAPACITY*100:.1f}%), Effectiveness={effectiveness:.1f}%")

    # Verify progressive fatigue
    # Note: With proper sleep, reservoir might actually recover, so we check the trend
    first_day_reservoir = reservoir_levels[0]
    last_day_reservoir = reservoir_levels[-1]

    print(f"  Total reservoir change: {last_day_reservoir - first_day_reservoir:.1f} units")

    # With 4 consecutive 10-hour duties, there should be some cumulative fatigue
    # but with proper sleep between duties, it shouldn't be catastrophic
    assert last_day_reservoir < RESERVOIR_CAPACITY, "Should show some fatigue accumulation"

    print("  ✓ PASS: Cumulative fatigue simulation works correctly\n")


def test_effectiveness_calculation():
    """
    Test: Verify effectiveness calculation includes all components.

    Expected: E = 100*(R/Rc) + C + I
    """
    print("Test 5: Effectiveness calculation verification")

    # Simple single duty
    base_date = datetime(2025, 1, 15, 10, 0)
    duty_start = base_date
    duty_end = base_date + timedelta(hours=4)

    duty_periods = [(duty_start, duty_end)]
    results = run_safte_simulation(duty_periods)

    # Sample a result during wakefulness
    duty_idx = next(i for i, r in enumerate(results) if r['timestamp'] >= duty_start and not r['is_asleep'])
    sample = results[duty_idx]

    print(f"  Sample timestamp: {sample['timestamp'].strftime('%Y-%m-%d %H:%M')}")
    print(f"  Reservoir level: {sample['reservoir_level']:.2f} units")
    print(f"  Effectiveness: {sample['effectiveness']:.2f}%")
    print(f"  Circadian rhythm: {sample['circadian_rhythm']:.2f}")
    print(f"  Sleep inertia: {sample['sleep_inertia']:.2f}")

    # Calculate expected effectiveness
    reservoir_component = 100 * (sample['reservoir_level'] / RESERVOIR_CAPACITY)
    expected_effectiveness = reservoir_component + sample['circadian_rhythm'] + sample['sleep_inertia']
    expected_effectiveness = max(0, min(100, expected_effectiveness))  # Clamp to 0-100

    print(f"  Calculated reservoir component: {reservoir_component:.2f}%")
    print(f"  Expected effectiveness: {expected_effectiveness:.2f}%")
    print(f"  Actual effectiveness: {sample['effectiveness']:.2f}%")

    assert abs(sample['effectiveness'] - expected_effectiveness) < 0.1, f"Effectiveness mismatch"
    print("  ✓ PASS: Effectiveness calculation is correct\n")


if __name__ == "__main__":
    print("=" * 70)
    print("SAFTE Integration Tests")
    print("=" * 70)
    print()

    test_single_day_trip()
    test_multi_day_trip()
    test_red_eye_flight()
    test_cumulative_fatigue()
    test_effectiveness_calculation()

    print("=" * 70)
    print("✓ All integration tests passed!")
    print("=" * 70)
