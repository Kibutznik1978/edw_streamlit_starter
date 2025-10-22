# SAFTE Fatigue Model Implementation Plan

## Project Goal

To implement the SAFTE fatigue model to analyze each pairing from an uploaded bid packet. The system will predict pilot cognitive effectiveness over the duration of a trip, visualize the results, and provide a fatigue risk score for each pairing, allowing pilots to make safer scheduling decisions.

## Core Strategy: Python Re-implementation

The `SAFTE.md` document references an R package, `FIPS`. However, to maintain a clean, single-language architecture and simplify deployment, the best path forward is to **re-implement the core SAFTE model in pure Python**. The provided `SAFTE.md` contains all the necessary mathematical formulas and algorithms to do this, making it a feasible and superior long-term solution.

---

## Current Status (Updated: October 22, 2025)

**Git Branch:** `Bid_Sorter`

**Overall Progress:** Phase 1 approximately 60% complete with critical issues identified.

### ✅ Completed Work

**Core SAFTE Engine (`safte_model.py`):**
- Homeostatic reservoir process implemented
- Dual-oscillator circadian rhythm model implemented
- Sleep inertia calculation implemented
- Performance rhythm calculation implemented
- Final effectiveness scoring formula implemented
- AutoSleep prediction algorithm (Rule 1 and Rule 2) implemented
- Simulation runner with minute-by-minute timeline
- Basic unit tests created and passing (4/4 tests in `test_safte_model.py`)

### ⚠️ Critical Issues Identified

1. **Sleep Accumulation Rate Bug** (safte_model.py:237)
   - Currently: `sleep_accumulation_rate = sleep_intensity` (uncapped)
   - Should be: Capped at maximum 3.4 units/minute per SAFTE specification
   - Impact: Over-replenishment of reservoir during sleep

2. **Effectiveness Clamping** (safte_model.py:98)
   - Currently: `max(0, min(100, effectiveness))` restricts output to 0-100%
   - Issue: SAFTE can legitimately exceed 100% during peak circadian performance
   - Decision needed: Keep restriction or allow >100% values

3. **No Scientific Validation**
   - No validation against published SAFTE studies
   - Missing: 88-hour sleep deprivation scenario replication
   - Missing: FRA railroad data validation
   - **Critical:** Cannot proceed to integration without proving model accuracy

4. **No Integration**
   - No connection to PDF parser or pairing data (Phase 2: 0% complete)
   - No UI/visualization components (Phase 3: 0% complete)
   - No transmeridian time zone adjustments (Phase 4: 0% complete)

### 🎯 Revised Implementation Strategy

Based on assessment, switching to a **focused 3-step approach** for rapid, validated progress:

**Step 1: Fix & Validate Core Model** ⬅️ START HERE
- Fix sleep accumulation rate capping
- Fix/document effectiveness clamping decision
- Create validation test replicating published study (88-hour scenario)
- Add comprehensive edge case unit tests
- **Gate:** Do not proceed until validation passes

**Step 2: Minimal Data Integration**
- Create data bridge: trip data → `duty_periods` format
- Extract time zones from pairing data
- Test with ONE real pairing from PDF
- Verify output makes intuitive sense
- **Gate:** Effectiveness timeline should show expected patterns

**Step 3: Minimal UI Integration**
- Add "Run Fatigue Analysis" button to existing EDW Pairing Analyzer
- Display effectiveness timeline chart (using Altair)
- Show 3 key metrics: lowest score, time in danger zone, overall risk score
- **Gate:** User can analyze one pairing and see actionable data

---

## Original Four-Phase Implementation Plan

The original plan is preserved below for reference. The revised 3-step approach above takes precedence.

### Original Phases Overview

The project was originally broken down into four distinct phases. We will complete and validate each phase before moving to the next, ensuring a high-quality outcome.

### Phase 1: Build the Core SAFTE Engine

**Objective:** Create a standalone, testable Python module that accurately implements the SAFTE model. This is the "brains" of the operation.

1.  **New Module (`safte_model.py`):**
    *   Create a new file, `safte_model.py`, to house all the core logic. This keeps the fatigue model separate from the web app's UI code.

2.  **Implement the Three Processes:**
    *   Translate the mathematical formulas for the **Homeostatic Reservoir**, **Circadian Oscillator**, and **Sleep Inertia** from `SAFTE.md` into Python functions. All constants will be clearly defined.

3.  **Implement the Sleep Prediction (`AutoSleep`) Algorithm:**
    *   Create a function that takes a pilot's duty schedule and automatically predicts sleep periods based on the rules in `SAFTE.md` (e.g., delaying sleep if work ends in the afternoon "forbidden zone"). This is critical as we don't have actual sleep logs.

4.  **Develop the Simulation Runner:**
    *   Create a primary function that takes a schedule (duty on/off times), runs the `AutoSleep` prediction, and then iterates through the entire trip timeline (e.g., minute by minute) to calculate the pilot's effectiveness score at each point.
    *   **Output:** This function will produce a timeseries of effectiveness scores for the full duration of a pairing.

5.  **Crucial Validation:**
    *   Write unit tests to verify the mathematical correctness of each component.
    *   Replicate a known scientific validation study (e.g., the 88-hour sleep deprivation scenario mentioned in the documentation) to prove our Python model matches published SAFTE results.

### Phase 2: Integrate Pairing Data

**Objective:** Connect the SAFTE engine to the data being extracted from the user's uploaded PDFs.

1.  **Enhance the PDF Parser (`edw_reporter.py`):**
    *   Analyze and upgrade the existing PDF parser to ensure it reliably extracts all data points required for the fatigue model:
        *   Duty start and end times (in UTC).
        *   Layover locations and durations.
        *   Time zones for every departure, arrival, and layover.

2.  **Develop a Data "Bridge":**
    *   Create a function that takes the parsed pairing data from the PDF and converts it into the clean, simple schedule format that the `safte_model.py` engine requires.

3.  **Run Simulations in the Background:**
    *   Modify the app's workflow so that after the PDF is parsed, it automatically runs the SAFTE simulation for each unique pairing. The resulting fatigue data will be stored and ready for visualization.

### Phase 3: Visualize Fatigue Risk (UI/UX)

**Objective:** Display the complex fatigue data in a simple, intuitive, and actionable way for the pilot.

1.  **New "Fatigue Analysis" Section:**
    *   Add a new tab or a prominent section within the **EDW Pairing Analyzer** dedicated to fatigue analysis.

2.  **Create the Effectiveness Timeline Chart:**
    *   This will be the central visualization: a line chart showing the effectiveness score over the entire trip.
    *   The chart will be color-coded to instantly show risk levels (Green for safe, Yellow for caution, Red for high-risk).
    *   It will also overlay the predicted sleep periods, making the cause-and-effect of sleep on performance obvious.

3.  **Display Key Fatigue Metrics:**
    *   For each pairing, we will calculate and display simple, powerful metrics:
        *   **Lowest Effectiveness Score:** The worst fatigue point in the trip.
        *   **Time in Red Zone:** The total time spent in a high-risk state (<77.5% effectiveness).
        *   **Overall Fatigue Score:** A single number to make it easy to sort and compare pairings.

### Phase 4: Advanced Features & Final Polish

**Objective:** Incorporate advanced SAFTE features and user customizations.

1.  **Transmeridian (Time Zone) Adjustment:**
    *   Implement the circadian rhythm adjustment algorithm from `SAFTE.md`. This is essential for accurately modeling fatigue on trips that cross multiple time zones.

2.  **User-Configurable Settings:**
    *   Add an "options" area where pilots can input their personal `commute time` and `normal sleep/wake times` to get a more personalized fatigue prediction.

3.  **PDF Report Integration:**
    *   Add the new fatigue charts and summary scores to the downloadable PDF report, creating a comprehensive safety and schedule document.

### Project Risks & Mitigation

*   **Risk:** The mathematical model is implemented incorrectly.
    *   **Mitigation:** The validation step in Phase 1, where we replicate a published study, is specifically designed to prevent this.
*   **Risk:** The PDF parser cannot extract all required time zone data.
    *   **Mitigation:** I will start with a deep analysis of the parser. If data is missing, I will use the most reasonable assumption (e.g., last known time zone) and clearly communicate this assumption in the UI.
*   **Risk:** Running simulations is too slow.
    *   **Mitigation:** The architecture is designed to run the simulation only once per *unique* pairing, not for every single trip in the bid packet, which will significantly improve performance.
