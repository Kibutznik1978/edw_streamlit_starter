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


def calculate_sleep_intensity(circadian_component, current_reservoir_level):
    """
    Calculates the sleep intensity (SI) based on sleep propensity and sleep debt.
    """
    # Sleep Propensity (SP) = m - (as * c) where m = 0
    sleep_propensity = 0 - (SLEEP_PROPENSITY_AMPLITUDE * circadian_component)

    # Sleep Debt (SD) = f * (Rc - Rt)
    sleep_debt = SLEEP_DEBT_FACTOR * (RESERVOIR_CAPACITY - current_reservoir_level)

    return sleep_propensity + sleep_debt

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

    Note: SAFTE effectiveness can legitimately exceed 100% during peak circadian
    performance when well-rested. We only clamp the lower bound at 0.
    """
    # E = 100(Rt/Rc) + C + I
    reservoir_component = 100 * (reservoir_level / RESERVOIR_CAPACITY)
    effectiveness = reservoir_component + performance_rhythm + sleep_inertia
    return max(0, effectiveness)  # Only clamp lower bound

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

    for i in range(len(sorted_duties)):
        duty_end = sorted_duties[i][1]
        layover_start = duty_end + commute_time

        # Determine the start of the next duty period
        next_duty_start = None
        if i + 1 < len(sorted_duties):
            next_duty_start = sorted_duties[i+1][0] - commute_time

        # Rule 1: Work ends between 00:00 and 11:59
        if 0 <= duty_end.hour < 12:
            sleep_start = layover_start
            sleep_end = sleep_start + MAX_SLEEP_PER_DAY

            # Ensure sleep doesn't overlap with the next duty
            if next_duty_start and sleep_end > next_duty_start:
                sleep_end = next_duty_start

            # Ensure sleep period is of a minimum duration
            if sleep_end - sleep_start >= MIN_SLEEP_PERIOD:
                sleep_periods.append((sleep_start, sleep_end))

        # Rule 2: Work ends between 12:00 and 23:59
        else:
            # Delay sleep until after the forbidden zone
            potential_sleep_start = duty_end.replace(hour=NORMAL_BEDTIME_HOUR, minute=0, second=0)

            # If bedtime has already passed for that day, move to the next day
            if potential_sleep_start < layover_start:
                potential_sleep_start += timedelta(days=1)

            sleep_start = max(layover_start, potential_sleep_start)
            sleep_end = sleep_start + MAX_SLEEP_PER_DAY

            # Ensure sleep doesn't overlap with the next duty
            if next_duty_start and sleep_end > next_duty_start:
                sleep_end = next_duty_start

            if sleep_end - sleep_start >= MIN_SLEEP_PERIOD:
                sleep_periods.append((sleep_start, sleep_end))

    return sleep_periods

def run_safte_simulation(duty_periods, initial_reservoir_level=RESERVOIR_CAPACITY):
    """
    Runs the full SAFTE simulation over a series of duty periods.

    Args:
        duty_periods (list): A list of tuples, each representing a duty
                             period with a start and end datetime object.
        initial_reservoir_level (float): The starting level of the sleep reservoir.

    Returns:
        list: A list of dictionaries, where each dictionary contains the
              timestamp, effectiveness, and other SAFTE components.
    """
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

    event_index = 0

    while current_time < sim_end_time:
        # Process any events at the current time
        while event_index < len(events) and events[event_index][0] == current_time:
            event_time, event_type = events[event_index]
            if event_type == 'sleep_start':
                is_asleep = True
            elif event_type == 'sleep_end':
                is_asleep = False
                time_since_awakening = 0
            event_index += 1

        # Calculate SAFTE components for the current minute
        time_hours = (current_time - sim_start_time).total_seconds() / 3600.0

        circadian_c = calculate_circadian_oscillator(time_hours)
        performance_rhythm_c = calculate_performance_rhythm(circadian_c, reservoir_level)

        sleep_intensity = calculate_sleep_intensity(circadian_c, reservoir_level)

        if is_asleep:
            # Replenish reservoir
            # Sleep intensity is capped at MAX_SLEEP_ACCUMULATION_RATE (3.4 units/min)
            sleep_accumulation_rate = min(sleep_intensity, MAX_SLEEP_ACCUMULATION_RATE)
            reservoir_level = min(RESERVOIR_CAPACITY, reservoir_level + sleep_accumulation_rate)
            sleep_inertia_i = 0
        else:
            # Deplete reservoir
            reservoir_level = max(0, reservoir_level - PERFORMANCE_USE_RATE)
            sleep_inertia_i = calculate_sleep_inertia(time_since_awakening, sleep_intensity)
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
