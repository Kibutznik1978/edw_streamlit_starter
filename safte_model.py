# SAFTE Model Implementation
import math
from datetime import datetime, timedelta

# --- Core SAFTE Model Constants ---

# Reservoir Capacity (Rc) in units
RESERVOIR_CAPACITY = 2880.0

# Performance Use Rate (K) in units/minute during wakefulness
PERFORMANCE_USE_RATE = 0.5

# Sleep Accumulation Rate (S) - This is variable, max 3.4 units/minute
# This will be calculated dynamically.
MAX_SLEEP_ACCUMULATION_RATE = 3.4

# --- Circadian Oscillator Constants ---

# 24-hour phase (p) in hours
CIRCADIAN_PHASE_24H = 18.0

# 12-hour phase offset (p') in hours
CIRCADIAN_PHASE_12H_OFFSET = 3.0

# 12-hour amplitude (β)
CIRCADIAN_AMPLITUDE_12H = 0.5

# Sleep propensity amplitude (as)
SLEEP_PROPENSITY_AMPLITUDE = 0.55

# Performance rhythm fixed amplitude (a1)
PERFORMANCE_RHYTHM_AMPLITUDE_FIXED = 7.0

# Performance rhythm variable amplitude (a2)
PERFORMANCE_RHYTHM_AMPLITUDE_VARIABLE = 5.0

# --- Sleep Inertia Constants ---

# Maximum sleep inertia upon awakening (Imax)
SLEEP_INERTIA_MAX = 5.0

# Time constant for sleep inertia (i)
# This controls the decay rate. Higher values = slower decay = longer-lasting sleep inertia
# Adjusted to make sleep inertia last ~2 hours post-awakening as per SAFTE specification
# With SI ~3, this gives a time constant of ~40-60 minutes
SLEEP_INERTIA_TIME_CONSTANT = 15.0

# --- Sleep Intensity Constants ---
SLEEP_DEBT_FACTOR = 0.00312


def calculate_sleep_propensity(circadian_component, current_reservoir_level):
    """
    Calculates sleep propensity (sleep pressure) for use in sleep inertia calculations.

    Sleep propensity represents the "drive to sleep" - a combination of:
    1. Circadian sleep propensity (lower at circadian peaks, higher at troughs)
    2. Homeostatic sleep debt (how depleted the reservoir is)

    This is used to modulate sleep inertia decay rate, NOT for sleep accumulation.

    Formula:
        SP = [m - (a_s * C)] + [f * (Rc - R)]
        where m = 0 (baseline sleep propensity)

    Returns:
        float: Sleep propensity value (can be negative at circadian peaks with full reservoir)
    """
    # Circadian component of sleep propensity
    # Negative at circadian peaks (less sleepy), positive at troughs (more sleepy)
    circadian_propensity = 0 - (SLEEP_PROPENSITY_AMPLITUDE * circadian_component)

    # Homeostatic sleep debt component (always non-negative)
    sleep_debt = SLEEP_DEBT_FACTOR * (RESERVOIR_CAPACITY - current_reservoir_level)

    return circadian_propensity + sleep_debt


def calculate_sleep_accumulation_rate(circadian_component, current_reservoir_level):
    """
    Calculates the sleep accumulation rate S(t) during sleep according to official SAFTE model.

    Formula (Hursh et al., 2004; FAST Phase II SBIR Report ADA452991):
        S(t) = S_max * [1 - exp(-f * (Rc - R))] * [1 + a_s * C(t)]

    Where:
        - S_max = 3.4 units/min (maximum recovery rate)
        - f = 0.00312 (exponential feedback constant)
        - Rc = 2880 (reservoir capacity)
        - R = current reservoir level
        - a_s = 0.55 (circadian modulation amplitude)
        - C(t) = circadian component (-1 to +1)

    Returns:
        float: Sleep accumulation rate in units/minute (always non-negative)

    Behavior:
        - When R = 0 (fully depleted): S(t) ≈ 3.4 units/min (maximum recovery)
        - When R = Rc (fully charged): S(t) = 0 (no accumulation)
        - Circadian lows (C < 0): Enhanced recovery (~45% faster at trough)
        - Circadian highs (C > 0): Reduced recovery (~45% slower at peak)
    """
    # Calculate sleep deficit (how much the reservoir is depleted)
    sleep_deficit = RESERVOIR_CAPACITY - current_reservoir_level

    # Exponential saturation term: provides diminishing returns as reservoir fills
    # When deficit is large: exp(-large) ≈ 0, so [1 - 0] = 1 → maximum accumulation
    # When deficit is zero: exp(0) = 1, so [1 - 1] = 0 → no accumulation
    exponent = -SLEEP_DEBT_FACTOR * sleep_deficit
    exponential_saturation = 1.0 - math.exp(exponent)

    # Circadian modulation: affects sleep efficiency
    # At circadian trough (C = -1): modulator = 1 + 0.55*(-1) = 0.45 (reduced recovery)
    # At circadian peak (C = +1): modulator = 1 + 0.55*(+1) = 1.55 (enhanced recovery)
    # Note: This can theoretically go negative if C < -1.82, so we apply safety constraint
    circadian_modulator = 1.0 + SLEEP_PROPENSITY_AMPLITUDE * circadian_component

    # Full accumulation rate
    accumulation_rate = MAX_SLEEP_ACCUMULATION_RATE * exponential_saturation * circadian_modulator

    # Safety constraints:
    # 1. Never negative (sleep always restores, never depletes)
    # 2. Never exceeds maximum rate (physiological limit)
    return max(0.0, min(MAX_SLEEP_ACCUMULATION_RATE, accumulation_rate))

def calculate_circadian_oscillator(time_hours):
    """
    Calculates the circadian component (c) at a given time.
    Time is in hours from a reference point.
    """
    # c = cos(2π(T-p)/24) + β*cos(4π(T-p-p')/24)
    term1 = math.cos(2 * math.pi * (time_hours - CIRCADIAN_PHASE_24H) / 24)
    term2 = CIRCADIAN_AMPLITUDE_12H * math.cos(4 * math.pi * (time_hours - CIRCADIAN_PHASE_24H - CIRCADIAN_PHASE_12H_OFFSET) / 24)
    return term1 + term2

def calculate_performance_rhythm(circadian_component, current_reservoir_level):
    """
    Calculates the performance rhythm component (C).
    """
    # ap = a1 + a2(Rc-Rt)/Rc
    variable_amplitude = PERFORMANCE_RHYTHM_AMPLITUDE_VARIABLE * (RESERVOIR_CAPACITY - current_reservoir_level) / RESERVOIR_CAPACITY
    total_amplitude = PERFORMANCE_RHYTHM_AMPLITUDE_FIXED + variable_amplitude

    # C = ap * c
    return total_amplitude * circadian_component

def calculate_sleep_inertia(time_since_awakening_minutes, sleep_intensity):
    """
    Calculates the sleep inertia component (I).

    Sleep inertia represents grogginess/impairment immediately after waking.
    Returns a NEGATIVE value (0 to -5%) that reduces effectiveness temporarily.
    Decays exponentially over ~2 hours post-awakening.

    At awakening (ta=0): maximum impairment of -5%
    As time passes: exponentially decays toward 0 (no impairment)
    """
    # I = -Imax * e^(-(ta/SI*i))
    # Negative because it impairs performance
    # At ta=0: e^0 = 1, so I = -5% (maximum grogginess)
    # As ta increases: exponential decay brings I toward 0

    if sleep_intensity <= 0:
        return 0  # Only check sleep_intensity, not time_since_awakening

    exponent = - (time_since_awakening_minutes / (sleep_intensity * SLEEP_INERTIA_TIME_CONSTANT))
    return -SLEEP_INERTIA_MAX * math.exp(exponent)  # Negative: impairs performance

def calculate_effectiveness(reservoir_level, performance_rhythm, sleep_inertia):
    """
    Calculates the final cognitive effectiveness percentage.

    Returns value between 0-100%. Values are clamped at 100% for practical interpretation,
    though the raw SAFTE model can produce values >100% at circadian peaks when well-rested.
    """
    # E = 100(Rt/Rc) + C + I
    reservoir_component = 100 * (reservoir_level / RESERVOIR_CAPACITY)
    effectiveness = reservoir_component + performance_rhythm + sleep_inertia
    return max(0, min(100, effectiveness))  # Clamp to 0-100% range

# --- AutoSleep Constants ---
DEFAULT_COMMUTE_TIME = timedelta(hours=1)
MAX_SLEEP_PER_DAY = timedelta(hours=8)
MIN_SLEEP_PERIOD = timedelta(hours=1)
FORBIDDEN_ZONE_START = 12
FORBIDDEN_ZONE_END = 20
NORMAL_BEDTIME_HOUR = 23

def predict_sleep_periods(duty_periods, commute_time=DEFAULT_COMMUTE_TIME):
    """
    Predicts sleep periods based on a list of duty periods using the AutoSleep algorithm.

    Args:
        duty_periods (list): A list of tuples, where each tuple represents a duty
                             period with a start and end datetime object.
                             e.g., [(duty_start_1, duty_end_1), (duty_start_2, duty_end_2)]
        commute_time (timedelta): The time to account for commuting after a duty period.

    Returns:
        list: A list of tuples, each representing a predicted sleep period
              with a start and end datetime object.
    """
    if not duty_periods:
        return []

    sleep_periods = []
    # Sort duty periods to ensure they are in chronological order
    sorted_duties = sorted(duty_periods, key=lambda x: x[0])

    # Add sleep BEFORE the first duty period (night before trip)
    if sorted_duties:
        first_duty_start = sorted_duties[0][0]
        # Assume wake-up time is: duty start - commute - 1 hour prep
        wake_time = first_duty_start - commute_time - timedelta(hours=1)

        # Sleep starts at 23:00 the night before wake_time
        sleep_start = wake_time.replace(hour=23, minute=0, second=0, microsecond=0) - timedelta(days=1)

        # If wake time is before 23:00, adjust (e.g., wake at 06:00 means sleep from previous day's 23:00)
        # If wake time is after 23:00 same day (e.g., wake at 02:00), sleep from same day's 23:00
        if wake_time.hour >= 23:
            sleep_start += timedelta(days=1)

        # Ensure minimum sleep duration
        if wake_time - sleep_start >= MIN_SLEEP_PERIOD:
            sleep_periods.append((sleep_start, wake_time))

    for i in range(len(sorted_duties)):
        duty_end = sorted_duties[i][1]

        # Allow wind-down time after duty ends (commute + 1 hour to decompress)
        wind_down_buffer = commute_time + timedelta(hours=1)
        sleep_start = duty_end + wind_down_buffer

        # Determine the start of the next duty period
        next_duty_start = None
        if i + 1 < len(sorted_duties):
            next_duty_start = sorted_duties[i+1][0] - commute_time - timedelta(hours=1)  # Wake time before next duty

        # Sleep for up to 8 hours, or until next duty wake time, whichever is shorter
        sleep_end = sleep_start + MAX_SLEEP_PER_DAY

        # Ensure sleep doesn't overlap with the next duty wake time
        if next_duty_start and sleep_end > next_duty_start:
            sleep_end = next_duty_start

        # Only add sleep period if it meets minimum duration (2 hours)
        if sleep_end - sleep_start >= MIN_SLEEP_PERIOD:
            sleep_periods.append((sleep_start, sleep_end))

    return sleep_periods

def run_safte_simulation(duty_periods, initial_reservoir_level=None):
    """
    Runs the full SAFTE simulation over a series of duty periods.

    Args:
        duty_periods (list): A list of tuples, each representing a duty
                             period with a start and end datetime object.
        initial_reservoir_level (float): The starting level of the sleep reservoir.
                             Default is 90% of capacity (0.9 * 2880 = 2592),
                             which is the aviation industry standard per AvORM.
                             Pilots typically do not start missions fully rested.

    Returns:
        list: A list of dictionaries, where each dictionary contains the
              timestamp, effectiveness, and other SAFTE components.
    """
    # Use 90% reservoir as default (aviation standard per AvORM)
    if initial_reservoir_level is None:
        initial_reservoir_level = 0.9 * RESERVOIR_CAPACITY
    if not duty_periods:
        return []

    sleep_periods = predict_sleep_periods(duty_periods)

    # Create a timeline of all events
    events = []
    for start, end in duty_periods:
        events.append((start, 'duty_start'))
        events.append((end, 'duty_end'))
    for start, end in sleep_periods:
        events.append((start, 'sleep_start'))
        events.append((end, 'sleep_end'))

    # Sort events chronologically
    events.sort()

    # Simulation parameters
    sim_start_time = events[0][0] - timedelta(days=1) # Start simulation a day before first event
    sim_end_time = events[-1][0] + timedelta(days=1) # End simulation a day after last event

    results = []
    current_time = sim_start_time
    reservoir_level = initial_reservoir_level
    is_asleep = False
    time_since_awakening = 0
    awakening_sleep_intensity = 0  # Sleep propensity captured at moment of awakening

    event_index = 0

    while current_time < sim_end_time:
        # Calculate SAFTE components for the current minute
        # Use clock time (time of day) for circadian rhythm, not elapsed time
        # Circadian rhythms are entrained to the 24-hour light/dark cycle
        time_hours = current_time.hour + current_time.minute / 60.0 + current_time.second / 3600.0

        circadian_c = calculate_circadian_oscillator(time_hours)
        performance_rhythm_c = calculate_performance_rhythm(circadian_c, reservoir_level)

        # Calculate current sleep propensity (used for sleep accumulation and capturing at awakening)
        sleep_propensity = calculate_sleep_propensity(circadian_c, reservoir_level)

        # Process any events at the current time
        while event_index < len(events) and events[event_index][0] == current_time:
            event_time, event_type = events[event_index]
            if event_type == 'sleep_start':
                is_asleep = True
            elif event_type == 'sleep_end':
                is_asleep = False
                time_since_awakening = 0
                # CRITICAL: Capture sleep propensity at moment of awakening
                # This determines sleep inertia decay rate (constant for ~2 hours post-awakening)
                # Higher sleep intensity at awakening = deeper sleep = longer-lasting grogginess
                awakening_sleep_intensity = sleep_propensity
            event_index += 1

        if is_asleep:
            # Replenish reservoir using official SAFTE exponential saturation formula
            accumulation_rate = calculate_sleep_accumulation_rate(circadian_c, reservoir_level)
            reservoir_level = min(RESERVOIR_CAPACITY, reservoir_level + accumulation_rate)
            sleep_inertia_i = 0
        else:
            # Deplete reservoir during wakefulness
            reservoir_level = max(0, reservoir_level - PERFORMANCE_USE_RATE)
            # Calculate sleep inertia (grogginess after awakening)
            # Use FIXED sleep intensity from moment of awakening (not current sleep propensity)
            # This ensures constant decay rate over ~2 hour period
            sleep_inertia_i = calculate_sleep_inertia(time_since_awakening, awakening_sleep_intensity)
            time_since_awakening += 1

        # Calculate final effectiveness
        effectiveness = calculate_effectiveness(reservoir_level, performance_rhythm_c, sleep_inertia_i)

        results.append({
            'timestamp': current_time,
            'effectiveness': effectiveness,
            'reservoir_level': reservoir_level,
            'circadian_rhythm': performance_rhythm_c,
            'sleep_inertia': sleep_inertia_i,
            'is_asleep': is_asleep
        })

        current_time += timedelta(minutes=1)

    return results
