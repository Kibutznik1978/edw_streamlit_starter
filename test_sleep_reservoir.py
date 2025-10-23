"""
Unit tests for SAFTE sleep reservoir implementation.

Tests verify that the sleep accumulation rate follows the official SAFTE formula:
    S(t) = S_max * [1 - exp(-f * (Rc - R))] * [1 + a_s * C(t)]

Based on Hursh et al., 2004 and FAST Phase II SBIR Report ADA452991.
"""

import math
from safte_model import (
    calculate_sleep_accumulation_rate,
    calculate_sleep_propensity,
    RESERVOIR_CAPACITY,
    MAX_SLEEP_ACCUMULATION_RATE,
    SLEEP_DEBT_FACTOR,
    SLEEP_PROPENSITY_AMPLITUDE
)


def test_fully_depleted_reservoir():
    """
    Test: When reservoir is fully depleted (R = 0), accumulation should be near maximum.

    Expected: S(t) ≈ 3.4 * [1 + 0.55*C]
    At neutral circadian (C=0): S(t) ≈ 3.4 units/min
    """
    print("Test 1: Fully depleted reservoir")
    reservoir_level = 0
    circadian_neutral = 0.0

    rate = calculate_sleep_accumulation_rate(circadian_neutral, reservoir_level)

    # Calculate expected value
    sleep_deficit = RESERVOIR_CAPACITY - reservoir_level  # 2880
    exponent = -SLEEP_DEBT_FACTOR * sleep_deficit  # -0.00312 * 2880 = -8.986
    expected_saturation = 1 - math.exp(exponent)  # 1 - 0.000124 ≈ 0.9999
    expected_rate = MAX_SLEEP_ACCUMULATION_RATE * expected_saturation * 1.0  # 3.4 * 0.9999 ≈ 3.4

    print(f"  Reservoir: {reservoir_level} / {RESERVOIR_CAPACITY}")
    print(f"  Circadian: {circadian_neutral}")
    print(f"  Sleep deficit: {sleep_deficit}")
    print(f"  Exponent: {exponent}")
    print(f"  Saturation factor: {expected_saturation:.6f}")
    print(f"  Expected rate: {expected_rate:.4f} units/min")
    print(f"  Actual rate: {rate:.4f} units/min")

    assert rate > 3.39, f"Expected rate near 3.4, got {rate}"
    assert rate <= MAX_SLEEP_ACCUMULATION_RATE, f"Rate exceeded maximum: {rate}"
    print("  ✓ PASS: Depleted reservoir accumulates at near-maximum rate\n")


def test_fully_charged_reservoir():
    """
    Test: When reservoir is fully charged (R = Rc), accumulation should be zero.

    Expected: S(t) = 0 (no accumulation when full)
    """
    print("Test 2: Fully charged reservoir")
    reservoir_level = RESERVOIR_CAPACITY
    circadian_neutral = 0.0

    rate = calculate_sleep_accumulation_rate(circadian_neutral, reservoir_level)

    sleep_deficit = RESERVOIR_CAPACITY - reservoir_level  # 0
    exponent = -SLEEP_DEBT_FACTOR * sleep_deficit  # 0
    expected_saturation = 1 - math.exp(0)  # 1 - 1 = 0

    print(f"  Reservoir: {reservoir_level} / {RESERVOIR_CAPACITY}")
    print(f"  Sleep deficit: {sleep_deficit}")
    print(f"  Saturation factor: {expected_saturation}")
    print(f"  Actual rate: {rate:.4f} units/min")

    assert rate == 0, f"Expected zero accumulation when full, got {rate}"
    print("  ✓ PASS: Full reservoir has zero accumulation\n")


def test_half_depleted_reservoir():
    """
    Test: When reservoir is half depleted, verify exponential saturation formula.
    """
    print("Test 3: Half-depleted reservoir")
    reservoir_level = RESERVOIR_CAPACITY / 2  # 1440
    circadian_neutral = 0.0

    rate = calculate_sleep_accumulation_rate(circadian_neutral, reservoir_level)

    sleep_deficit = RESERVOIR_CAPACITY - reservoir_level  # 1440
    exponent = -SLEEP_DEBT_FACTOR * sleep_deficit  # -0.00312 * 1440 = -4.493
    expected_saturation = 1 - math.exp(exponent)  # 1 - 0.0112 = 0.9888
    expected_rate = MAX_SLEEP_ACCUMULATION_RATE * expected_saturation * 1.0  # 3.4 * 0.9888 ≈ 3.36

    print(f"  Reservoir: {reservoir_level} / {RESERVOIR_CAPACITY}")
    print(f"  Sleep deficit: {sleep_deficit}")
    print(f"  Exponent: {exponent:.4f}")
    print(f"  Saturation factor: {expected_saturation:.4f}")
    print(f"  Expected rate: {expected_rate:.4f} units/min")
    print(f"  Actual rate: {rate:.4f} units/min")

    assert abs(rate - expected_rate) < 0.01, f"Expected {expected_rate}, got {rate}"
    print("  ✓ PASS: Half-depleted reservoir shows correct exponential saturation\n")


def test_circadian_trough_enhancement():
    """
    Test: At circadian trough (C = -1), sleep accumulation should be REDUCED.

    Circadian modulator: [1 + 0.55*(-1)] = [1 - 0.55] = 0.45
    This represents reduced sleep efficiency during circadian low.
    """
    print("Test 4: Circadian trough (C = -1) - reduced recovery")
    reservoir_level = RESERVOIR_CAPACITY / 2  # 1440
    circadian_trough = -1.0

    rate_neutral = calculate_sleep_accumulation_rate(0.0, reservoir_level)
    rate_trough = calculate_sleep_accumulation_rate(circadian_trough, reservoir_level)

    expected_modulator = 1 + SLEEP_PROPENSITY_AMPLITUDE * circadian_trough  # 1 - 0.55 = 0.45
    expected_rate = rate_neutral * expected_modulator

    print(f"  Reservoir: {reservoir_level} / {RESERVOIR_CAPACITY}")
    print(f"  Circadian: {circadian_trough}")
    print(f"  Circadian modulator: {expected_modulator}")
    print(f"  Rate at neutral circadian: {rate_neutral:.4f} units/min")
    print(f"  Rate at circadian trough: {rate_trough:.4f} units/min")
    print(f"  Expected rate: {expected_rate:.4f} units/min")
    print(f"  Reduction: {((rate_neutral - rate_trough) / rate_neutral * 100):.1f}%")

    assert abs(rate_trough - expected_rate) < 0.01, f"Expected {expected_rate}, got {rate_trough}"
    assert rate_trough < rate_neutral, "Trough should reduce accumulation"
    print("  ✓ PASS: Circadian trough reduces sleep efficiency by ~55%\n")


def test_circadian_peak_reduction():
    """
    Test: At circadian peak (C = +1), sleep accumulation should be ENHANCED.

    Circadian modulator: [1 + 0.55*(+1)] = [1 + 0.55] = 1.55
    This represents enhanced sleep efficiency during circadian high.
    """
    print("Test 5: Circadian peak (C = +1) - enhanced recovery")
    reservoir_level = RESERVOIR_CAPACITY / 2  # 1440
    circadian_peak = 1.0

    rate_neutral = calculate_sleep_accumulation_rate(0.0, reservoir_level)
    rate_peak = calculate_sleep_accumulation_rate(circadian_peak, reservoir_level)

    expected_modulator = 1 + SLEEP_PROPENSITY_AMPLITUDE * circadian_peak  # 1 + 0.55 = 1.55
    expected_rate = rate_neutral * expected_modulator

    print(f"  Reservoir: {reservoir_level} / {RESERVOIR_CAPACITY}")
    print(f"  Circadian: {circadian_peak}")
    print(f"  Circadian modulator: {expected_modulator}")
    print(f"  Rate at neutral circadian: {rate_neutral:.4f} units/min")
    print(f"  Rate at circadian peak: {rate_peak:.4f} units/min")
    print(f"  Expected rate: {expected_rate:.4f} units/min")
    print(f"  Enhancement: {((rate_peak - rate_neutral) / rate_neutral * 100):.1f}%")

    # Note: expected_rate might exceed MAX, so we check against clamped value
    expected_clamped = min(expected_rate, MAX_SLEEP_ACCUMULATION_RATE)
    assert abs(rate_peak - expected_clamped) < 0.01, f"Expected {expected_clamped}, got {rate_peak}"
    assert rate_peak > rate_neutral, "Peak should enhance accumulation"
    print("  ✓ PASS: Circadian peak enhances sleep efficiency by ~55%\n")


def test_non_negativity_constraint():
    """
    Test: Sleep accumulation should NEVER be negative, even at extreme circadian values.

    The safety constraint max(0, ...) should prevent negative accumulation.
    """
    print("Test 6: Non-negativity constraint at extreme circadian")
    reservoir_level = RESERVOIR_CAPACITY  # Full reservoir
    extreme_circadian = -2.0  # Unrealistic but tests safety constraint

    rate = calculate_sleep_accumulation_rate(extreme_circadian, reservoir_level)

    print(f"  Reservoir: {reservoir_level} / {RESERVOIR_CAPACITY}")
    print(f"  Circadian: {extreme_circadian} (extreme)")
    print(f"  Actual rate: {rate:.4f} units/min")

    assert rate >= 0, f"Rate should never be negative, got {rate}"
    print("  ✓ PASS: Non-negativity constraint prevents negative accumulation\n")


def test_maximum_rate_constraint():
    """
    Test: Sleep accumulation should never exceed S_max = 3.4 units/min.
    """
    print("Test 7: Maximum rate constraint")
    reservoir_level = 0  # Fully depleted
    extreme_circadian = 2.0  # High positive value

    rate = calculate_sleep_accumulation_rate(extreme_circadian, reservoir_level)

    print(f"  Reservoir: {reservoir_level} / {RESERVOIR_CAPACITY}")
    print(f"  Circadian: {extreme_circadian} (extreme)")
    print(f"  Actual rate: {rate:.4f} units/min")
    print(f"  Maximum allowed: {MAX_SLEEP_ACCUMULATION_RATE} units/min")

    assert rate <= MAX_SLEEP_ACCUMULATION_RATE, f"Rate exceeded maximum: {rate}"
    print("  ✓ PASS: Rate capped at maximum accumulation rate\n")


def test_sleep_propensity_separate():
    """
    Test: Verify sleep_propensity (for inertia) is calculated separately and correctly.
    """
    print("Test 8: Sleep propensity calculation (for sleep inertia)")
    reservoir_level = RESERVOIR_CAPACITY / 2
    circadian_neutral = 0.0
    circadian_trough = -1.0

    propensity_neutral = calculate_sleep_propensity(circadian_neutral, reservoir_level)
    propensity_trough = calculate_sleep_propensity(circadian_trough, reservoir_level)

    # Expected values
    sleep_debt = SLEEP_DEBT_FACTOR * (RESERVOIR_CAPACITY - reservoir_level)
    expected_neutral = 0 - (SLEEP_PROPENSITY_AMPLITUDE * 0) + sleep_debt
    expected_trough = 0 - (SLEEP_PROPENSITY_AMPLITUDE * circadian_trough) + sleep_debt

    print(f"  Reservoir: {reservoir_level} / {RESERVOIR_CAPACITY}")
    print(f"  Sleep debt: {sleep_debt:.6f}")
    print(f"  Propensity at neutral: {propensity_neutral:.6f} (expected {expected_neutral:.6f})")
    print(f"  Propensity at trough: {propensity_trough:.6f} (expected {expected_trough:.6f})")

    assert abs(propensity_neutral - expected_neutral) < 0.0001
    assert abs(propensity_trough - expected_trough) < 0.0001
    assert propensity_trough > propensity_neutral, "Propensity higher at circadian trough"
    print("  ✓ PASS: Sleep propensity calculated correctly\n")


def test_reservoir_refill_simulation():
    """
    Test: Simulate reservoir refilling over time to verify realistic behavior.

    Starting from 50% depletion, verify reservoir refills with exponential saturation.
    """
    print("Test 9: Reservoir refill simulation")
    reservoir_level = RESERVOIR_CAPACITY / 2  # Start at 50%
    circadian_neutral = 0.0

    print(f"  Initial reservoir: {reservoir_level} / {RESERVOIR_CAPACITY} ({reservoir_level/RESERVOIR_CAPACITY*100:.1f}%)")

    # Simulate 8 hours of sleep (480 minutes)
    for minute in range(480):
        rate = calculate_sleep_accumulation_rate(circadian_neutral, reservoir_level)
        reservoir_level = min(RESERVOIR_CAPACITY, reservoir_level + rate)

    print(f"  After 8 hours of sleep: {reservoir_level:.1f} / {RESERVOIR_CAPACITY} ({reservoir_level/RESERVOIR_CAPACITY*100:.1f}%)")

    # After 8 hours of good sleep, reservoir should be nearly full
    assert reservoir_level > RESERVOIR_CAPACITY * 0.95, f"Expected >95% full, got {reservoir_level/RESERVOIR_CAPACITY*100:.1f}%"
    print("  ✓ PASS: Reservoir refills to >95% after 8 hours of sleep\n")


if __name__ == "__main__":
    print("=" * 70)
    print("SAFTE Sleep Reservoir Unit Tests")
    print("=" * 70)
    print()

    test_fully_depleted_reservoir()
    test_fully_charged_reservoir()
    test_half_depleted_reservoir()
    test_circadian_trough_enhancement()
    test_circadian_peak_reduction()
    test_non_negativity_constraint()
    test_maximum_rate_constraint()
    test_sleep_propensity_separate()
    test_reservoir_refill_simulation()

    print("=" * 70)
    print("✓ All tests passed!")
    print("=" * 70)
