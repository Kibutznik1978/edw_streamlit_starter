"""
SAFTE Integration Module

Bridges parsed pairing data from edw_reporter.py to the SAFTE fatigue model.
Converts duty day schedules into the format required by run_safte_simulation().
"""

from datetime import datetime, timedelta
import re
from typing import List, Tuple, Dict, Optional
from dateutil import parser as date_parser


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


def parse_layover_duration(layover_str: str) -> Optional[float]:
    """
    Parse layover duration string from L/O field.

    Args:
        layover_str: Layover string like "50h39 S1" or "12h30"

    Returns:
        Duration in hours (float) or None if parsing fails

    Examples:
        "50h39 S1" -> 50.65 (50 hours + 39/60 hours)
        "12h30" -> 12.5
        "24h00" -> 24.0
    """
    if not layover_str:
        return None

    # Pattern: {hours}h{minutes} followed by optional rest type code
    match = re.match(r'(\d+)h(\d+)', layover_str.strip())
    if not match:
        return None

    hours = int(match.group(1))
    minutes = int(match.group(2))

    return hours + (minutes / 60.0)


def trip_to_duty_periods(
    parsed_trip: Dict,
    reference_date: Optional[datetime] = None
) -> List[Tuple[datetime, datetime]]:
    """
    Convert a parsed trip structure to a list of duty periods for SAFTE simulation.

    Args:
        parsed_trip: Trip structure from parse_trip_for_table()
                    Expected keys: 'trip_id', 'duty_days', 'date_freq', 'trip_summary'
                    Each duty_day has: 'duty_start', 'duty_end', 'rest' (L/O), etc.
        reference_date: Starting date for the trip. If None, uses current date.

    Returns:
        List of (duty_start_datetime, duty_end_datetime) tuples

    Notes:
        - Uses local times from the parsed trip data
        - Uses L/O (layover) field from previous duty day to determine exact dates
        - If duty spans midnight, automatically handles date rollover
        - Fallback to heuristic date advancement if L/O field is missing
    """
    if reference_date is None:
        reference_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    duty_days = parsed_trip.get('duty_days', [])
    duty_periods = []

    # Track the last duty end time and use layover duration for accurate date calculation
    last_duty_end = None
    current_date = reference_date

    for duty_idx, duty_day in enumerate(duty_days):
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

        # For duty days after the first, use the L/O field from the PREVIOUS duty day
        if last_duty_end is not None and duty_idx > 0:
            # Get the rest (L/O) field from the previous duty day
            prev_duty_day = duty_days[duty_idx - 1]
            layover_str = prev_duty_day.get('rest')
            layover_duration = parse_layover_duration(layover_str)

            if layover_duration is not None:
                # Use actual layover duration from PDF
                # The layover duration gives us the time from debriefing to briefing
                # Calculate expected briefing time
                calculated_briefing = last_duty_end + timedelta(hours=layover_duration)

                # Extract just the date portion for finding which day the duty starts on
                # We'll use the parsed time (start_hour:start_min) for the actual time
                # First, try using the same date as calculated_briefing
                current_date = calculated_briefing.replace(hour=0, minute=0, second=0, microsecond=0)

                # Create candidate duty start with the parsed local time
                duty_start_candidate = current_date.replace(
                    hour=start_hour,
                    minute=start_min,
                    second=start_sec,
                    microsecond=0
                )

                # If the candidate is before the calculated briefing time,
                # it means the briefing happens the next day (e.g., layover ends at 18:49,
                # but briefing is at 05:15, so it must be the next day)
                if duty_start_candidate < calculated_briefing:
                    current_date += timedelta(days=1)
            else:
                # Fallback: If L/O field is missing, calculate the time difference
                # Advance date until duty_start time makes sense
                duty_start_candidate = current_date.replace(
                    hour=start_hour,
                    minute=start_min,
                    second=start_sec,
                    microsecond=0
                )
                while duty_start_candidate <= last_duty_end + timedelta(hours=2):
                    current_date += timedelta(days=1)
                    duty_start_candidate = current_date.replace(
                        hour=start_hour,
                        minute=start_min,
                        second=start_sec,
                        microsecond=0
                    )

        # Create duty start datetime on current_date
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


def extract_trip_start_date(parsed_trip: Dict) -> Optional[datetime]:
    """
    Extract the actual trip start date from the parsed trip data.

    Parses the 'date_freq' field which contains strings like:
    - "Only on Mon 10Nov2025"
    - "01May2025, 02May2025, ..."
    - "15 trips"

    Returns:
        datetime object for the trip start date, or None if not found
    """
    date_freq = parsed_trip.get('date_freq', '')

    if not date_freq:
        return None

    # Try to parse "Only on Mon 10Nov2025" format
    only_on_match = re.search(r'Only on \w+ (\d{2}\w{3}\d{4})', date_freq, re.IGNORECASE)
    if only_on_match:
        try:
            return date_parser.parse(only_on_match.group(1))
        except:
            pass

    # Try to parse "01May2025" format (first date in comma-separated list)
    date_match = re.search(r'(\d{2}\w{3}\d{4})', date_freq)
    if date_match:
        try:
            return date_parser.parse(date_match.group(1))
        except:
            pass

    return None


def analyze_trip_fatigue(
    parsed_trip: Dict,
    reference_date: Optional[datetime] = None,
    initial_reservoir_level: Optional[float] = None
) -> Dict:
    """
    Run full SAFTE fatigue analysis on a parsed trip.

    Args:
        parsed_trip: Trip structure from parse_trip_for_table()
        reference_date: Starting date for the trip simulation.
                       If None, attempts to extract from trip date_freq field.
        initial_reservoir_level: Starting reservoir level (defaults to 90% per aviation standard)

    Returns:
        Dictionary containing:
            - 'duty_periods': List of (start, end) datetime tuples
            - 'safte_results': Full minute-by-minute simulation results
            - 'fatigue_metrics': Summary metrics (lowest effectiveness, time in danger, etc.)
            - 'trip_id': Trip identifier
    """
    from safte_model import run_safte_simulation

    # If no reference date provided, try to extract from trip data
    if reference_date is None:
        reference_date = extract_trip_start_date(parsed_trip)
        if reference_date is None:
            # Fall back to current date if can't extract
            reference_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

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

    # Run SAFTE simulation (will use 90% default if initial_reservoir_level is None)
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
