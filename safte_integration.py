"""
SAFTE Integration Module

Bridges parsed pairing data from edw_reporter.py to the SAFTE fatigue model.
Converts duty day schedules into the format required by run_safte_simulation().
"""

from datetime import datetime, timedelta
import re
from typing import List, Tuple, Dict, Optional


def parse_local_time(time_str: str) -> Optional[Tuple[int, int, int]]:
    """
    Parse a time string in format "(LOCAL_HH)ZULU_HH:ZULU_MM".

    The format combines local and zulu times where:
    - (LOCAL_HH) is the local hour in parentheses
    - ZULU_HH:ZULU_MM is the UTC/Zulu time
    - Local minutes = Zulu minutes (timezone offset only affects hours)

    Args:
        time_str: Time string like "(03)08:28" or "(14)19:40"

    Returns:
        Tuple of (local_hour, local_minute, local_second) or None if parsing fails

    Examples:
        "(03)08:28" -> (3, 28, 0)  # Local time is 03:28, Zulu is 08:28
        "(14)19:40" -> (14, 40, 0)  # Local time is 14:40, Zulu is 19:40
    """
    if not time_str:
        return None

    # Pattern: (LOCAL_HH)ZULU_HH:ZULU_MM
    match = re.match(r'\((\d+)\)(\d{2}):(\d{2})', time_str)
    if not match:
        return None

    local_hour = int(match.group(1))    # Local hour from parentheses
    zulu_hour = int(match.group(2))     # Zulu hour (not used for local time)
    minute = int(match.group(3))        # Minutes (same for local and zulu)
    second = 0                           # Seconds not provided in this format

    return (local_hour, minute, second)


def trip_to_duty_periods(
    parsed_trip: Dict,
    reference_date: Optional[datetime] = None
) -> List[Tuple[datetime, datetime]]:
    """
    Convert a parsed trip structure to a list of duty periods for SAFTE simulation.

    Args:
        parsed_trip: Trip structure from parse_trip_for_table()
                    Expected keys: 'trip_id', 'duty_days', 'date_freq', 'trip_summary'
                    Each duty_day has: 'duty_start', 'duty_end', 'flights', etc.
        reference_date: Starting date for the trip. If None, uses current date.

    Returns:
        List of (duty_start_datetime, duty_end_datetime) tuples

    Notes:
        - Uses local times from the parsed trip data
        - Assumes duty days are sequential (day 1, day 2, etc.)
        - If duty spans midnight, automatically handles date rollover
        - Time zone information is implicit in the local hour notation (HH)
    """
    if reference_date is None:
        reference_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    duty_days = parsed_trip.get('duty_days', [])
    duty_periods = []

    # Track the last duty end time to determine when next duty should start
    last_duty_end = None
    current_date = reference_date

    for duty_day in duty_days:
        duty_start_str = duty_day.get('duty_start')
        duty_end_str = duty_day.get('duty_end')

        if not duty_start_str or not duty_end_str:
            # Skip duty days with missing start/end times
            continue

        # Parse start time
        start_parts = parse_local_time(duty_start_str)
        if not start_parts:
            continue
        start_hour, start_min, start_sec = start_parts

        # Parse end time
        end_parts = parse_local_time(duty_end_str)
        if not end_parts:
            continue
        end_hour, end_min, end_sec = end_parts

        # Create duty start datetime on current_date
        duty_start = current_date.replace(
            hour=start_hour,
            minute=start_min,
            second=start_sec,
            microsecond=0
        )

        # If we have a previous duty, check if this start time makes sense
        if last_duty_end is not None:
            # If duty_start would be before or too close to last_duty_end, advance to next day
            # (Minimum 2 hours between duties for rest/commute)
            if duty_start <= last_duty_end + timedelta(hours=2):
                current_date += timedelta(days=1)
                duty_start = current_date.replace(
                    hour=start_hour,
                    minute=start_min,
                    second=start_sec,
                    microsecond=0
                )

        # Create duty end datetime
        duty_end = current_date.replace(
            hour=end_hour,
            minute=end_min,
            second=end_sec,
            microsecond=0
        )

        # If end time is before start time, duty spans midnight
        if duty_end <= duty_start:
            duty_end += timedelta(days=1)

        duty_periods.append((duty_start, duty_end))
        last_duty_end = duty_end

    return duty_periods


def analyze_trip_fatigue(
    parsed_trip: Dict,
    reference_date: Optional[datetime] = None,
    initial_reservoir_level: Optional[float] = None
) -> Dict:
    """
    Run full SAFTE fatigue analysis on a parsed trip.

    Args:
        parsed_trip: Trip structure from parse_trip_for_table()
        reference_date: Starting date for the trip simulation
        initial_reservoir_level: Starting reservoir level (defaults to full: 2880)

    Returns:
        Dictionary containing:
            - 'duty_periods': List of (start, end) datetime tuples
            - 'safte_results': Full minute-by-minute simulation results
            - 'fatigue_metrics': Summary metrics (lowest effectiveness, time in danger, etc.)
            - 'trip_id': Trip identifier
    """
    from safte_model import run_safte_simulation, RESERVOIR_CAPACITY

    # Convert trip to duty periods
    duty_periods = trip_to_duty_periods(parsed_trip, reference_date)

    if not duty_periods:
        return {
            'duty_periods': [],
            'safte_results': [],
            'fatigue_metrics': None,
            'trip_id': parsed_trip.get('trip_id'),
            'error': 'No valid duty periods found in trip'
        }

    # Run SAFTE simulation
    if initial_reservoir_level is None:
        initial_reservoir_level = RESERVOIR_CAPACITY

    safte_results = run_safte_simulation(duty_periods, initial_reservoir_level)

    # Calculate fatigue metrics
    fatigue_metrics = calculate_fatigue_metrics(safte_results, duty_periods)

    # Also extract the predicted sleep periods from SAFTE model
    from safte_model import predict_sleep_periods
    sleep_periods = predict_sleep_periods(duty_periods)

    return {
        'duty_periods': duty_periods,
        'sleep_periods': sleep_periods,
        'safte_results': safte_results,
        'fatigue_metrics': fatigue_metrics,
        'trip_id': parsed_trip.get('trip_id')
    }


def calculate_fatigue_metrics(safte_results: List[Dict], duty_periods: List[Tuple[datetime, datetime]]) -> Dict:
    """
    Calculate summary fatigue metrics from SAFTE simulation results.

    Args:
        safte_results: Output from run_safte_simulation()
        duty_periods: List of duty period tuples

    Returns:
        Dictionary with key fatigue metrics:
            - lowest_effectiveness: Minimum effectiveness score during duty
            - lowest_effectiveness_time: When minimum occurred
            - time_below_danger_threshold: Minutes spent below 77.5%
            - time_below_warning_threshold: Minutes spent below 85%
            - average_effectiveness_on_duty: Mean effectiveness during duty periods
            - overall_fatigue_score: 0-100 score (higher = more fatigued)
    """
    if not safte_results:
        return None

    # Filter to only results during duty periods (not layovers)
    duty_results = []
    for result in safte_results:
        timestamp = result['timestamp']
        # Check if this timestamp falls within any duty period
        for duty_start, duty_end in duty_periods:
            if duty_start <= timestamp <= duty_end:
                duty_results.append(result)
                break

    if not duty_results:
        duty_results = safte_results  # Fallback to all results

    # Find minimum effectiveness
    lowest_result = min(duty_results, key=lambda r: r['effectiveness'])
    lowest_effectiveness = lowest_result['effectiveness']
    lowest_effectiveness_time = lowest_result['timestamp']

    # Calculate time below thresholds (industry standard from SAFTE-FAST)
    danger_threshold = 70.0  # Danger: significant impairment
    warning_threshold = 82.0  # Warning: entering impairment zone

    time_below_danger = sum(1 for r in duty_results if r['effectiveness'] < danger_threshold)
    time_below_warning = sum(1 for r in duty_results if r['effectiveness'] < warning_threshold)

    # Average effectiveness on duty
    avg_effectiveness = sum(r['effectiveness'] for r in duty_results) / len(duty_results)

    # Overall fatigue score (0-100, higher = worse)
    # Based on: lowest effectiveness, time in danger zone, average effectiveness
    # Scoring logic aligned with industry thresholds:
    #   - If lowest < 60: very high risk (80-100 score) - severe impairment
    #   - If lowest < 70: high risk (60-80 score) - significant impairment
    #   - If lowest < 82: moderate risk (40-60 score) - entering impairment
    #   - If lowest >= 82: low risk (0-40 score) - optimal performance
    if lowest_effectiveness < 60:
        base_score = 80
    elif lowest_effectiveness < 70:
        base_score = 60
    elif lowest_effectiveness < 82:
        base_score = 40
    else:
        base_score = 20

    # Add points for time spent in danger zone (up to 20 points)
    danger_hours = time_below_danger / 60.0
    danger_penalty = min(20, danger_hours * 2)  # 2 points per hour in danger

    overall_fatigue_score = min(100, base_score + danger_penalty)

    return {
        'lowest_effectiveness': lowest_effectiveness,
        'lowest_effectiveness_time': lowest_effectiveness_time,
        'time_below_danger_threshold_minutes': time_below_danger,
        'time_below_warning_threshold_minutes': time_below_warning,
        'average_effectiveness_on_duty': avg_effectiveness,
        'overall_fatigue_score': overall_fatigue_score,
        'danger_threshold': danger_threshold,
        'warning_threshold': warning_threshold
    }


def format_fatigue_summary(fatigue_metrics: Dict) -> str:
    """
    Format fatigue metrics into a human-readable summary string.

    Args:
        fatigue_metrics: Output from calculate_fatigue_metrics()

    Returns:
        Formatted summary string
    """
    if not fatigue_metrics:
        return "No fatigue metrics available"

    lines = []
    lines.append("=== SAFTE Fatigue Analysis Summary ===")
    lines.append(f"Lowest Effectiveness: {fatigue_metrics['lowest_effectiveness']:.1f}%")
    lines.append(f"  Occurred at: {fatigue_metrics['lowest_effectiveness_time']}")

    danger_hours = fatigue_metrics['time_below_danger_threshold_minutes'] / 60.0
    warning_hours = fatigue_metrics['time_below_warning_threshold_minutes'] / 60.0

    lines.append(f"Time Below Danger Threshold (<{fatigue_metrics['danger_threshold']}%): {danger_hours:.1f} hours")
    lines.append(f"Time Below Warning Threshold (<{fatigue_metrics['warning_threshold']}%): {warning_hours:.1f} hours")
    lines.append(f"Average Effectiveness on Duty: {fatigue_metrics['average_effectiveness_on_duty']:.1f}%")
    lines.append(f"Overall Fatigue Score: {fatigue_metrics['overall_fatigue_score']:.0f}/100")

    # Risk assessment
    score = fatigue_metrics['overall_fatigue_score']
    if score >= 80:
        risk_level = "VERY HIGH RISK - Significant safety concerns"
    elif score >= 60:
        risk_level = "HIGH RISK - Safety mitigation recommended"
    elif score >= 40:
        risk_level = "MODERATE RISK - Monitor closely"
    else:
        risk_level = "LOW RISK - Within acceptable range"

    lines.append(f"Risk Assessment: {risk_level}")

    return "\n".join(lines)
