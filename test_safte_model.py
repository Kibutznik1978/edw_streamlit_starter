import unittest
from datetime import datetime, timedelta
from safte_model import (
    calculate_circadian_oscillator,
    predict_sleep_periods,
    run_safte_simulation,
    RESERVOIR_CAPACITY
)

class TestSafteModel(unittest.TestCase):

    def test_calculate_circadian_oscillator(self):
        # At hour 18 (acrophase), cos(0) + 0.5*cos(0) = 1.5 (this is not the formula)
        # c = cos(2π(T-p)/24) + β*cos(4π(T-p-p')/24)
        # T = 18, p = 18, p' = 3, B = 0.5
        # c = cos(0) + 0.5*cos(4*pi*(18-18-3)/24) = 1 + 0.5*cos(-pi/2) = 1
        # The formula for `c` is not just `1.5`. Let's re-calculate based on the code.
        # At T=18, p=18: term1 is cos(0) = 1.
        # term2 is 0.5 * cos(4*pi*(18-18-3)/24) = 0.5 * cos(-12*pi/24) = 0.5 * cos(-pi/2) = 0.
        # So c should be 1.
        self.assertAlmostEqual(calculate_circadian_oscillator(18), 1.0, places=5)
        # At T=6, p=18: term1 is cos(2*pi*(-12)/24) = cos(-pi) = -1
        # term2 is 0.5 * cos(4*pi*(6-18-3)/24) = 0.5 * cos(-60*pi/24) = 0.5*cos(-2.5*pi) = 0
        # This is not quite right. Let's re-read the formula.
        # p' is 3 hours ahead of p. The formula uses (T-p-p'). Let's assume p' is just 3.
        # At T=6, p=18, p'=3: term2 = 0.5 * cos(4*pi*(6-18-3)/24) = 0.5 * cos(4*pi*(-15)/24) = 0.5 * cos(-2.5*pi)
        # cos(-2.5pi) is cos(-0.5pi) which is 0. So c should be -1.
        self.assertAlmostEqual(calculate_circadian_oscillator(6), -1.0, places=5)

    def test_predict_sleep_periods_rule1(self):
        # Work ends at 8am (Rule 1)
        duty_end = datetime(2025, 10, 22, 8, 0)
        duty_start = duty_end - timedelta(hours=8)
        duty_periods = [(duty_start, duty_end)]
        
        sleep_periods = predict_sleep_periods(duty_periods)
        
        self.assertEqual(len(sleep_periods), 1)
        # Commute is 1 hour, so sleep starts at 9am
        self.assertEqual(sleep_periods[0][0], datetime(2025, 10, 22, 9, 0))
        # Max sleep is 8 hours, so sleep ends at 5pm (17:00)
        self.assertEqual(sleep_periods[0][1], datetime(2025, 10, 22, 17, 0))

    def test_predict_sleep_periods_rule2(self):
        # Work ends at 8pm (20:00) (Rule 2)
        duty_end = datetime(2025, 10, 22, 20, 0)
        duty_start = duty_end - timedelta(hours=8)
        duty_periods = [(duty_start, duty_end)]
        
        sleep_periods = predict_sleep_periods(duty_periods)
        
        self.assertEqual(len(sleep_periods), 1)
        # Bedtime is 23:00
        self.assertEqual(sleep_periods[0][0], datetime(2025, 10, 22, 23, 0))
        # Max sleep is 8 hours, so sleep ends at 7am next day
        self.assertEqual(sleep_periods[0][1], datetime(2025, 10, 23, 7, 0))

    def test_run_safte_simulation_basic(self):
        duty_start = datetime(2025, 10, 22, 8, 0)
        duty_end = datetime(2025, 10, 22, 16, 0)
        duty_periods = [(duty_start, duty_end)]

        results = run_safte_simulation(duty_periods)
        
        # Check that the simulation runs and produces results
        self.assertTrue(len(results) > 0)
        # Check that effectiveness is generally decreasing during wakefulness
        # and increasing during sleep.
        # This is a more complex test to write, for now just check it runs.

if __name__ == '__main__':
    unittest.main()
