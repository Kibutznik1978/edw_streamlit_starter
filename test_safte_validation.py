"""
SAFTE Model Validation Tests

This module validates the SAFTE implementation against published scientific studies
and known behavioral patterns. These tests ensure the model produces scientifically
accurate predictions before integration with real-world data.

Key validation scenarios:
1. 88-hour sleep deprivation (from SAFTE research literature)
2. Circadian rhythm patterns (peak at 6PM, nadir at 6AM)
3. Sleep debt accumulation and recovery
4. Critical performance thresholds (77.5% = 0.05% BAC)
"""

import unittest
from datetime import datetime, timedelta
from safte_model import (
    run_safte_simulation,
    calculate_circadian_oscillator,
    calculate_effectiveness,
    RESERVOIR_CAPACITY,
    CIRCADIAN_PHASE_24H,
)


class TestSafteValidation(unittest.TestCase):
    """
    Validation tests against published SAFTE research and expected patterns.
    """

    def test_88_hour_sleep_deprivation_pattern(self):
        """
        Test continuous 88-hour wakefulness scenario.

        Expected behavior from SAFTE literature:
        - Steady decline in effectiveness
        - Effectiveness should drop below 77.5% (danger threshold)
        - Pattern should show circadian oscillations overlaid on declining trend
        - Should reach critically low levels by hour 88
        """
        # Create scenario: 88 consecutive hours of wakefulness
        start_time = datetime(2025, 10, 22, 8, 0)  # Start at 8 AM
        end_time = start_time + timedelta(hours=88)

        # Single continuous duty period (unrealistic but tests core math)
        duty_periods = [(start_time, end_time)]

        results = run_safte_simulation(duty_periods, initial_reservoir_level=RESERVOIR_CAPACITY)

        # Filter to just the duty period
        duty_results = [r for r in results if start_time <= r['timestamp'] <= end_time]

        # Validation checks
        self.assertTrue(len(duty_results) > 5000, "Should have minute-by-minute data")

        # Check 1: Effectiveness should decline over time
        first_hour_avg = sum(r['effectiveness'] for r in duty_results[:60]) / 60
        last_hour_avg = sum(r['effectiveness'] for r in duty_results[-60:]) / 60
        self.assertLess(last_hour_avg, first_hour_avg,
                       "Effectiveness should decline over 88 hours of wakefulness")

        # Check 2: Should drop below danger threshold (77.5%)
        min_effectiveness = min(r['effectiveness'] for r in duty_results)
        self.assertLess(min_effectiveness, 77.5,
                       "Should drop below 77.5% danger threshold during 88-hour deprivation")

        # Check 3: Reservoir should be significantly depleted
        final_reservoir = duty_results[-1]['reservoir_level']
        self.assertLess(final_reservoir, RESERVOIR_CAPACITY * 0.3,
                       "Reservoir should be heavily depleted after 88 hours")

        # Check 4: Should show circadian oscillation (not just linear decline)
        # Extract effectiveness values at 24-hour intervals
        effectiveness_at_24h = duty_results[24 * 60]['effectiveness']
        effectiveness_at_48h = duty_results[48 * 60]['effectiveness']
        effectiveness_at_72h = duty_results[72 * 60]['effectiveness']

        # Despite overall decline, circadian rhythm should cause daily variation
        # Check that we have variation, not just monotonic decline
        differences = [
            abs(effectiveness_at_48h - effectiveness_at_24h),
            abs(effectiveness_at_72h - effectiveness_at_48h)
        ]
        avg_daily_change = sum(differences) / len(differences)
        self.assertGreater(avg_daily_change, 1.0,
                          "Should show circadian variation, not pure linear decline")

    def test_circadian_rhythm_peak_and_nadir(self):
        """
        Test that circadian rhythm peaks at 6 PM (18:00) and has nadir at 6 AM.

        CIRCADIAN_PHASE_24H is set to 18 (6 PM acrophase per SAFTE spec).
        """
        # At acrophase (hour 18), circadian component should be at maximum
        c_at_peak = calculate_circadian_oscillator(18)

        # At nadir (6 hours after peak, which is 6 AM = hour 6), should be at minimum
        c_at_nadir = calculate_circadian_oscillator(6)

        self.assertGreater(c_at_peak, c_at_nadir,
                          "Circadian component should peak at 6 PM and be lowest at 6 AM")

        # Peak should be close to +1 (cosine at phase = 1)
        self.assertAlmostEqual(c_at_peak, 1.0, places=1,
                              msg="Peak circadian component should be approximately 1.0")

    def test_sleep_recovery_replenishes_reservoir(self):
        """
        Test that sleep properly replenishes the reservoir after depletion.

        Expected: 8 hours of sleep should significantly restore effectiveness.
        """
        # Deplete reservoir with 24 hours of wakefulness
        start_time = datetime(2025, 10, 22, 8, 0)
        duty_end = start_time + timedelta(hours=24)

        duty_periods = [(start_time, duty_end)]

        results = run_safte_simulation(duty_periods, initial_reservoir_level=RESERVOIR_CAPACITY)

        # Find effectiveness at end of duty period
        duty_results = [r for r in results if r['timestamp'] <= duty_end]
        effectiveness_before_sleep = duty_results[-1]['effectiveness']

        # Get actual predicted sleep end time
        from safte_model import predict_sleep_periods
        sleep_periods = predict_sleep_periods(duty_periods)
        self.assertGreater(len(sleep_periods), 0, "Should predict sleep period")

        sleep_end_time = sleep_periods[0][1]

        # Check effectiveness 2 hours after waking (to let sleep inertia dissipate)
        check_time = sleep_end_time + timedelta(hours=2)
        check_results = [r for r in results if r['timestamp'] <= check_time]
        effectiveness_after_recovery = check_results[-1]['effectiveness']

        # Sleep should restore effectiveness
        self.assertGreater(effectiveness_after_recovery, effectiveness_before_sleep,
                          "Sleep should restore effectiveness")

        # After 8 hours of sleep + 2 hours awake, should be reasonably recovered
        # (accounting for sleep inertia wearing off)
        self.assertGreater(effectiveness_after_recovery, 84.0,
                          "Should be reasonably recovered after 8 hours of sleep + recovery time")

    def test_effectiveness_can_exceed_100_percent(self):
        """
        Test that effectiveness can exceed 100% during peak circadian phase when well-rested.

        This is a valid SAFTE behavior - peak performance exceeds baseline.
        """
        # Start fully rested at circadian peak
        reservoir_level = RESERVOIR_CAPACITY
        circadian_c = 1.0  # Peak circadian rhythm

        # Performance rhythm calculation
        from safte_model import calculate_performance_rhythm
        performance_rhythm = calculate_performance_rhythm(circadian_c, reservoir_level)

        # Calculate effectiveness (no sleep inertia)
        effectiveness = calculate_effectiveness(reservoir_level, performance_rhythm, 0)

        # At peak circadian phase with full reservoir, effectiveness can exceed 100%
        self.assertGreaterEqual(effectiveness, 100.0,
                               "Effectiveness should be able to reach/exceed 100% at peak performance")

    def test_danger_threshold_77_5_percent(self):
        """
        Test that we can identify when effectiveness drops below the 77.5% danger threshold.

        77.5% effectiveness = 0.05% blood alcohol concentration equivalent (per SAFTE research).
        """
        # Create scenario with significant sleep deprivation
        start_time = datetime(2025, 10, 22, 8, 0)
        duty_end = start_time + timedelta(hours=48)  # 48 hours continuous duty

        duty_periods = [(start_time, duty_end)]
        results = run_safte_simulation(duty_periods)

        # Find all times when effectiveness is below danger threshold
        danger_zone_results = [r for r in results if r['effectiveness'] < 77.5]

        # Should have some time in danger zone after 48 hours
        self.assertGreater(len(danger_zone_results), 0,
                          "Should enter danger zone (<77.5%) during 48-hour deprivation")

        # Calculate total time in danger zone
        time_in_danger = len(danger_zone_results)  # minutes

        # Should spend significant time in danger zone
        self.assertGreater(time_in_danger, 60,  # More than 1 hour
                          "Should spend substantial time in danger zone during 48-hour deprivation")

    def test_sleep_inertia_effect_after_waking(self):
        """
        Test that sleep inertia temporarily reduces effectiveness immediately after waking.

        Expected: Brief dip in effectiveness for ~2 hours after waking (grogginess).
        """
        # Short duty period followed by sleep
        start_time = datetime(2025, 10, 22, 8, 0)
        duty_end = start_time + timedelta(hours=8)

        duty_periods = [(start_time, duty_end)]

        # Get predicted sleep periods to find actual wake time
        from safte_model import predict_sleep_periods
        sleep_periods = predict_sleep_periods(duty_periods)

        self.assertGreater(len(sleep_periods), 0, "Should predict at least one sleep period")

        sleep_end_time = sleep_periods[0][1]

        results = run_safte_simulation(duty_periods)

        # Find effectiveness right after waking (use actual predicted wake time)
        wake_time_results = [r for r in results
                            if sleep_end_time <= r['timestamp'] <= sleep_end_time + timedelta(minutes=30)]

        self.assertGreater(len(wake_time_results), 0, "Should have results after wake time")

        # Check that sleep inertia component is present
        has_sleep_inertia = any(r['sleep_inertia'] < 0 for r in wake_time_results)
        self.assertTrue(has_sleep_inertia,
                      "Should have sleep inertia (negative) effect after waking")

    def test_reservoir_cannot_exceed_capacity(self):
        """
        Test that the reservoir never exceeds maximum capacity (2880 units).
        """
        # Even with extended sleep, reservoir should be capped
        start_time = datetime(2025, 10, 22, 8, 0)
        duty_end = start_time + timedelta(hours=1)  # Very short duty

        duty_periods = [(start_time, duty_end)]
        results = run_safte_simulation(duty_periods, initial_reservoir_level=RESERVOIR_CAPACITY)

        # Check all reservoir levels
        max_reservoir = max(r['reservoir_level'] for r in results)

        self.assertLessEqual(max_reservoir, RESERVOIR_CAPACITY,
                            "Reservoir should never exceed maximum capacity")

    def test_performance_use_rate_consistency(self):
        """
        Test that reservoir depletes at expected rate during wakefulness.

        Expected: 0.5 units/minute = 30 units/hour = 720 units/day
        """
        # Start with full reservoir, stay awake for exactly 24 hours
        start_time = datetime(2025, 10, 22, 8, 0)
        duty_end = start_time + timedelta(hours=24)

        duty_periods = [(start_time, duty_end)]
        results = run_safte_simulation(duty_periods, initial_reservoir_level=RESERVOIR_CAPACITY)

        # Get initial and final reservoir levels during duty
        initial_result = [r for r in results if r['timestamp'] == start_time][0]
        final_result = [r for r in results if r['timestamp'] <= duty_end][-1]

        depletion = initial_result['reservoir_level'] - final_result['reservoir_level']

        # Expected depletion: 0.5 units/min * 60 min/hr * 24 hr = 720 units
        expected_depletion = 0.5 * 60 * 24

        # Allow 10% tolerance due to simulation timing
        self.assertAlmostEqual(depletion, expected_depletion, delta=expected_depletion * 0.1,
                              msg=f"Reservoir should deplete ~{expected_depletion} units over 24 hours")


class TestEdgeCases(unittest.TestCase):
    """
    Test edge cases and boundary conditions.
    """

    def test_empty_duty_periods(self):
        """Test that empty duty periods list doesn't crash."""
        results = run_safte_simulation([])
        self.assertEqual(results, [])

    def test_very_short_duty_period(self):
        """Test handling of very short duty periods (< 1 hour)."""
        start = datetime(2025, 10, 22, 8, 0)
        end = start + timedelta(minutes=30)

        results = run_safte_simulation([(start, end)])
        self.assertGreater(len(results), 0, "Should handle short duty periods")

    def test_overlapping_duty_periods(self):
        """Test that overlapping duty periods don't crash the simulation."""
        start1 = datetime(2025, 10, 22, 8, 0)
        end1 = start1 + timedelta(hours=8)
        start2 = start1 + timedelta(hours=4)  # Overlaps with first
        end2 = start2 + timedelta(hours=8)

        # Should not crash
        results = run_safte_simulation([(start1, end1), (start2, end2)])
        self.assertGreater(len(results), 0)

    def test_out_of_order_duty_periods(self):
        """Test that duty periods get sorted properly even if provided out of order."""
        start1 = datetime(2025, 10, 22, 8, 0)
        end1 = start1 + timedelta(hours=8)
        start2 = datetime(2025, 10, 23, 8, 0)
        end2 = start2 + timedelta(hours=8)

        # Provide in reverse order
        results = run_safte_simulation([(start2, end2), (start1, end1)])
        self.assertGreater(len(results), 0, "Should handle out-of-order duty periods")


if __name__ == '__main__':
    # Run with verbose output
    unittest.main(verbosity=2)
