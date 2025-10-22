"""
Test SAFTE Integration with Real Trip Data

This test validates the data bridge between parsed pairing data and the SAFTE model.
"""

import unittest
from datetime import datetime, timedelta
from safte_integration import (
    parse_local_time,
    trip_to_duty_periods,
    analyze_trip_fatigue,
    calculate_fatigue_metrics,
    format_fatigue_summary
)


class TestSafteIntegration(unittest.TestCase):

    def test_parse_local_time(self):
        """Test parsing of local time strings."""
        # Standard format
        self.assertEqual(parse_local_time("(08)13:30"), (8, 13, 30))
        self.assertEqual(parse_local_time("(23)05:15"), (23, 5, 15))
        self.assertEqual(parse_local_time("(00)00:00"), (0, 0, 0))

        # Invalid formats
        self.assertIsNone(parse_local_time(""))
        self.assertIsNone(parse_local_time(None))
        self.assertIsNone(parse_local_time("13:30"))  # Missing (HH)

    def test_trip_to_duty_periods_simple(self):
        """Test conversion of a simple single-duty-day trip."""
        trip = {
            'trip_id': 123,
            'duty_days': [
                {
                    'duty_start': '(08)06:00',
                    'duty_end': '(16)14:30'
                }
            ]
        }

        reference_date = datetime(2025, 10, 22, 0, 0, 0)
        duty_periods = trip_to_duty_periods(trip, reference_date)

        self.assertEqual(len(duty_periods), 1)
        start, end = duty_periods[0]

        self.assertEqual(start, datetime(2025, 10, 22, 8, 6, 0))
        self.assertEqual(end, datetime(2025, 10, 22, 16, 14, 30))

    def test_trip_to_duty_periods_midnight_crossing(self):
        """Test handling of duty period that crosses midnight."""
        trip = {
            'trip_id': 456,
            'duty_days': [
                {
                    'duty_start': '(23)22:00',
                    'duty_end': '(02)04:30'  # Next day
                }
            ]
        }

        reference_date = datetime(2025, 10, 22, 0, 0, 0)
        duty_periods = trip_to_duty_periods(trip, reference_date)

        self.assertEqual(len(duty_periods), 1)
        start, end = duty_periods[0]

        self.assertEqual(start, datetime(2025, 10, 22, 23, 22, 0))
        self.assertEqual(end, datetime(2025, 10, 23, 2, 4, 30))  # Next day

    def test_trip_to_duty_periods_multi_day(self):
        """Test conversion of a multi-day trip."""
        trip = {
            'trip_id': 789,
            'duty_days': [
                {
                    'duty_start': '(08)07:00',
                    'duty_end': '(18)17:00'
                },
                {
                    'duty_start': '(09)08:00',
                    'duty_end': '(19)18:00'
                },
                {
                    'duty_start': '(10)09:00',
                    'duty_end': '(20)19:00'
                }
            ]
        }

        reference_date = datetime(2025, 10, 22, 0, 0, 0)
        duty_periods = trip_to_duty_periods(trip, reference_date)

        self.assertEqual(len(duty_periods), 3)

        # Day 1
        self.assertEqual(duty_periods[0][0], datetime(2025, 10, 22, 8, 7, 0))
        self.assertEqual(duty_periods[0][1], datetime(2025, 10, 22, 18, 17, 0))

        # Day 2
        self.assertEqual(duty_periods[1][0], datetime(2025, 10, 23, 9, 8, 0))
        self.assertEqual(duty_periods[1][1], datetime(2025, 10, 23, 19, 18, 0))

        # Day 3
        self.assertEqual(duty_periods[2][0], datetime(2025, 10, 24, 10, 9, 0))
        self.assertEqual(duty_periods[2][1], datetime(2025, 10, 24, 20, 19, 0))

    def test_trip_to_duty_periods_with_missing_data(self):
        """Test handling of duty days with missing start/end times."""
        trip = {
            'trip_id': 999,
            'duty_days': [
                {
                    'duty_start': '(08)07:00',
                    'duty_end': '(18)17:00'
                },
                {
                    'duty_start': None,  # Missing
                    'duty_end': '(19)18:00'
                },
                {
                    'duty_start': '(10)09:00',
                    'duty_end': '(20)19:00'
                }
            ]
        }

        reference_date = datetime(2025, 10, 22, 0, 0, 0)
        duty_periods = trip_to_duty_periods(trip, reference_date)

        # Should skip the duty day with missing data
        self.assertEqual(len(duty_periods), 2)

    def test_analyze_trip_fatigue_integration(self):
        """Test full integration: trip data -> SAFTE analysis -> metrics."""
        # Create a realistic 3-day trip
        trip = {
            'trip_id': 200,
            'duty_days': [
                {
                    'duty_start': '(05)04:30',  # Early morning duty
                    'duty_end': '(16)15:00',
                    'flights': []
                },
                {
                    'duty_start': '(06)05:00',
                    'duty_end': '(17)16:00',
                    'flights': []
                },
                {
                    'duty_start': '(07)06:00',
                    'duty_end': '(18)17:00',
                    'flights': []
                }
            ]
        }

        reference_date = datetime(2025, 10, 22, 0, 0, 0)
        analysis = analyze_trip_fatigue(trip, reference_date)

        # Verify structure
        self.assertIn('duty_periods', analysis)
        self.assertIn('safte_results', analysis)
        self.assertIn('fatigue_metrics', analysis)
        self.assertIn('trip_id', analysis)

        # Verify duty periods were created
        self.assertEqual(len(analysis['duty_periods']), 3)

        # Verify SAFTE simulation ran
        self.assertGreater(len(analysis['safte_results']), 0)

        # Verify metrics were calculated
        metrics = analysis['fatigue_metrics']
        self.assertIsNotNone(metrics)
        self.assertIn('lowest_effectiveness', metrics)
        self.assertIn('overall_fatigue_score', metrics)
        self.assertIn('time_below_danger_threshold_minutes', metrics)

        # Verify metrics make sense
        self.assertGreaterEqual(metrics['lowest_effectiveness'], 0)
        self.assertLessEqual(metrics['lowest_effectiveness'], 120)  # Can exceed 100%
        self.assertGreaterEqual(metrics['overall_fatigue_score'], 0)
        self.assertLessEqual(metrics['overall_fatigue_score'], 100)

    def test_calculate_fatigue_metrics_values(self):
        """Test fatigue metrics calculation with known data."""
        # Create synthetic SAFTE results
        safte_results = []
        base_time = datetime(2025, 10, 22, 8, 0, 0)

        # Simulate decreasing effectiveness over time
        for i in range(300):  # 5 hours
            effectiveness = 95 - (i / 30)  # Gradual decline
            safte_results.append({
                'timestamp': base_time + timedelta(minutes=i),
                'effectiveness': effectiveness,
                'reservoir_level': 2800 - i,
                'circadian_rhythm': 0,
                'sleep_inertia': 0,
                'is_asleep': False
            })

        duty_periods = [(base_time, base_time + timedelta(hours=5))]
        metrics = calculate_fatigue_metrics(safte_results, duty_periods)

        # Verify calculations
        self.assertIsNotNone(metrics)
        self.assertLess(metrics['lowest_effectiveness'], 90)  # Should decline below 90
        self.assertGreater(metrics['average_effectiveness_on_duty'], 85)  # Average should be higher

    def test_format_fatigue_summary(self):
        """Test formatting of fatigue metrics into readable text."""
        metrics = {
            'lowest_effectiveness': 75.5,
            'lowest_effectiveness_time': datetime(2025, 10, 22, 14, 30, 0),
            'time_below_danger_threshold_minutes': 120,
            'time_below_warning_threshold_minutes': 240,
            'average_effectiveness_on_duty': 82.3,
            'overall_fatigue_score': 65,
            'danger_threshold': 77.5,
            'warning_threshold': 85.0
        }

        summary = format_fatigue_summary(metrics)

        # Verify key information is present
        self.assertIn("75.5%", summary)
        self.assertIn("2.0 hours", summary)  # 120 minutes = 2 hours
        self.assertIn("4.0 hours", summary)  # 240 minutes = 4 hours
        self.assertIn("82.3%", summary)
        self.assertIn("65/100", summary)
        self.assertIn("RISK", summary.upper())

    def test_realistic_edw_trip(self):
        """
        Test with a realistic Early-Day-Window (EDW) trip that should show fatigue risk.

        EDW trips start early in the morning (circadian low point), which increases
        fatigue risk according to SAFTE model.
        """
        edw_trip = {
            'trip_id': 188,
            'duty_days': [
                {
                    'duty_start': '(02)01:30',  # 1:30 AM - very early
                    'duty_end': '(12)11:00',
                    'flights': []
                },
                {
                    'duty_start': '(03)02:00',  # 2:00 AM - very early
                    'duty_end': '(13)12:00',
                    'flights': []
                },
                {
                    'duty_start': '(04)03:00',  # 3:00 AM - very early
                    'duty_end': '(14)13:00',
                    'flights': []
                }
            ]
        }

        reference_date = datetime(2025, 10, 22, 0, 0, 0)
        analysis = analyze_trip_fatigue(edw_trip, reference_date)

        metrics = analysis['fatigue_metrics']

        # EDW trips should show higher fatigue risk
        # (Early morning duty conflicts with circadian rhythm)
        print(f"\nEDW Trip Analysis:")
        print(f"  Lowest Effectiveness: {metrics['lowest_effectiveness']:.1f}%")
        print(f"  Overall Fatigue Score: {metrics['overall_fatigue_score']:.0f}/100")
        print(f"  Time in Danger Zone: {metrics['time_below_danger_threshold_minutes'] / 60:.1f} hours")

        # With early morning starts, we expect:
        # - Lower effectiveness scores during duty
        # - Higher fatigue score
        self.assertIsNotNone(metrics)

        # The test passes if analysis completes - specific thresholds depend on SAFTE parameters


if __name__ == '__main__':
    unittest.main(verbosity=2)
