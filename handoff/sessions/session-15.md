# Session 15 - SAFTE Fatigue Analysis Integration

**Date:** October 22, 2025
**Focus:** Complete SAFTE (Sleep, Activity, Fatigue, Task Effectiveness) Fatigue Model Implementation

---

## Session Overview

This session implemented a complete, scientifically-validated fatigue analysis system using the SAFTE model. The system analyzes pilot cognitive effectiveness over the duration of a pairing, predicts sleep periods, and identifies high-risk trips. This adds critical safety analysis capabilities to the EDW Pairing Analyzer.

**Branch:** `Bid_Sorter`

---

## Major Accomplishments

### 1. **Core SAFTE Model Implementation** ✅

Built pure Python implementation of the SAFTE fatigue model based on published research and mathematical specifications.

#### **Mathematical Components Implemented:**

1. **Homeostatic Reservoir Process**
   - Reservoir capacity: 2,880 units (4 days without sleep)
   - Performance depletion: 0.5 units/minute during wakefulness
   - Sleep accumulation: Variable rate, capped at 3.4 units/minute
   - Sleep debt factor: 0.00312

2. **Dual-Oscillator Circadian Rhythm Model**
   - 24-hour phase (acrophase at 18:00 / 6 PM)
   - 12-hour harmonic with 3-hour offset
   - Amplitude: 0.5 for 12-hour component
   - Sleep propensity amplitude: 0.55

3. **Sleep Inertia Process**
   - Maximum inertia: -5% (impairs performance)
   - Time constant: 15.0 (2-hour decay period)
   - Exponential decay from awakening
   - Represents post-sleep grogginess

4. **AutoSleep Prediction Algorithm**
   - Rule 1: Work ending 00:00-11:59 → sleep immediately after commute
   - Rule 2: Work ending 12:00-23:59 → delay sleep until 23:00 (forbidden zone avoidance)
   - Default commute time: 1 hour
   - Maximum sleep per day: 8 hours
   - Minimum sleep period: 1 hour

**Files Created:**
- `safte_model.py` (260 lines) - Complete SAFTE implementation

---

### 2. **Data Integration Bridge** ✅

Created integration layer to convert parsed pairing data into SAFTE-compatible format.

#### **Key Functions:**

1. **`parse_local_time()`**
   - Extracts hour/minute/second from "(HH)MM:SS" format
   - Handles local time zone notation from PDF data

2. **`trip_to_duty_periods()`**
   - Converts parsed trip structure to datetime tuples
   - Handles midnight crossings automatically
   - Advances calendar dates for multi-day trips
   - Returns: `[(duty_start, duty_end), ...]`

3. **`analyze_trip_fatigue()`**
   - Main orchestration function
   - Runs full SAFTE simulation pipeline
   - Returns: duty periods, results, metrics, trip ID

4. **`calculate_fatigue_metrics()`**
   - Computes summary statistics from simulation
   - Identifies lowest effectiveness point
   - Calculates time below danger/warning thresholds
   - Generates 0-100 fatigue risk score

5. **`format_fatigue_summary()`**
   - Creates human-readable text summary
   - Includes risk assessment labels

**Files Created:**
- `safte_integration.py` (279 lines) - Data bridge module

---

### 3. **Comprehensive Test Suite** ✅

Built 25 passing tests across 3 test files to ensure scientific accuracy.

#### **Validation Tests (test_safte_validation.py):**

1. **88-Hour Sleep Deprivation Scenario**
   - Validates continuous wakefulness pattern
   - Confirms decline below danger threshold (77.5%)
   - Verifies circadian oscillation overlay

2. **Circadian Rhythm Verification**
   - Confirms peak at 6 PM (acrophase)
   - Confirms nadir at 6 AM
   - Validates dual-oscillator mathematics

3. **Danger Threshold Detection**
   - 77.5% threshold (equivalent to 0.05% BAC)
   - Tracks time spent in danger zone
   - High-risk identification

4. **Sleep Recovery Validation**
   - Confirms reservoir replenishment during sleep
   - Validates effectiveness restoration
   - Verifies 8-hour sleep recovery

5. **Sleep Inertia Effects**
   - Confirms -5% impairment at awakening
   - Validates 2-hour exponential decay
   - Proper grogginess modeling

6. **Edge Cases**
   - Empty duty periods
   - Very short duty periods (< 1 hour)
   - Overlapping duty periods
   - Out-of-order duty periods

**Test Results:**
- `test_safte_model.py`: 4/4 tests passing (basic functionality)
- `test_safte_validation.py`: 12/12 tests passing (scientific validation)
- `test_safte_integration.py`: 9/9 tests passing (data integration)
- **Total: 25/25 tests passing** ✅

**Files Created:**
- `test_safte_model.py` (73 lines) - Basic unit tests
- `test_safte_validation.py` (267 lines) - Scientific validation tests
- `test_safte_integration.py` (241 lines) - Integration tests

---

### 4. **User Interface Integration** ✅

Added interactive fatigue analysis to EDW Pairing Analyzer tab with professional visualizations.

#### **UI Components:**

1. **"Run Fatigue Analysis" Button**
   - Located in trip details section (after trip table)
   - Triggers SAFTE simulation for selected trip
   - Results cached in session state

2. **3 Key Metrics Display**
   - **Lowest Effectiveness:** Minimum cognitive performance (%)
   - **Time in Danger Zone:** Hours below 77.5% threshold
   - **Fatigue Score:** 0-100 risk score with color-coded label
   - Risk levels: LOW, MODERATE, HIGH, VERY HIGH

3. **Interactive Effectiveness Timeline Chart**
   - Full trip timeline (duty periods + layovers/sleep)
   - Blue shaded areas: On-duty periods
   - White areas: Layover/sleep recovery periods
   - Red dashed line: Danger threshold (77.5% = 0.05% BAC)
   - Orange dashed line: Warning threshold (85%)
   - X-axis: Date + Time (multi-day format)
   - Interactive tooltips: Time, effectiveness, duty status, sleep status

4. **Detailed Statistics Expander**
   - Effectiveness stats (lowest, average, timing)
   - Time below thresholds breakdown
   - Duty period count
   - Explanatory notes about SAFTE predictions

**Visual Enhancements:**
- Duty periods shaded in light blue (15% opacity)
- Recovery periods (layovers) clearly visible as white gaps
- Sawtooth effectiveness pattern shows decline during duty, recovery during rest
- Color-coded risk metrics (red for inverse/high risk, green for normal/low risk)

**Files Modified:**
- `app.py` (lines 665-859) - Added 195 lines of SAFTE UI code

---

## Technical Implementation Details

### **Bug Fixes from Initial Implementation:**

1. **Sleep Accumulation Rate Uncapped** (safte_model.py:237)
   - **Problem:** Sleep intensity used directly without cap
   - **Solution:** Capped at `MAX_SLEEP_ACCUMULATION_RATE = 3.4` units/min
   - **Impact:** Prevents over-replenishment of reservoir

2. **Effectiveness Clamping Too Restrictive** (safte_model.py:98)
   - **Problem:** Clamped to 0-100%, but SAFTE can exceed 100%
   - **Solution:** Only clamp lower bound (0%), allow >100% for peak performance
   - **Impact:** Correctly models well-rested peak performance

3. **Sleep Inertia Sign Error** (safte_model.py:95)
   - **Problem:** Positive value instead of negative (impairment)
   - **Solution:** Return negative value (-5% to 0%)
   - **Impact:** Properly reduces effectiveness after waking

4. **Sleep Inertia Decay Too Fast** (safte_model.py:45)
   - **Problem:** Time constant 0.04 caused instant decay
   - **Solution:** Increased to 15.0 for realistic 2-hour duration
   - **Impact:** Matches SAFTE specification for grogginess duration

5. **Chart Display Missing Layovers** (app.py:749-770)
   - **Problem:** Only showed duty periods, hid sleep recovery
   - **Solution:** Display full trip timeline including layovers
   - **Impact:** Users can now see effectiveness recovery during rest

---

## Real-World Validation

### **Test Case: Trip 100 (ONT 757)**

**Trip Details:**
- Duty Start: 23:07:40 (11:07 PM)
- Duty End: 15:24:00 next day (3:24 PM)
- Route: ONT→BFI→ONT
- Duty Time: 7h44

**SAFTE Analysis Results:**
- Lowest Effectiveness: **59.4%** ⚠️
- Time Below Danger (<77.5%): **8.1 hours**
- Average Effectiveness: **63.2%**
- Fatigue Score: **96/100**
- Risk Assessment: **VERY HIGH RISK**

**Why High Risk:**
Starting duty at 11 PM conflicts with circadian low point (midnight-6 AM), causing effectiveness to drop far below the 77.5% danger threshold (equivalent to 0.05% blood alcohol content).

### **Multi-Day Trip Validation: Pairing 86**

**Observable Patterns:**
- **Sawtooth effectiveness curve:** Decline during duty, recovery during layovers
- **Blue shaded areas:** Duty periods show declining effectiveness
- **White gaps:** Layover periods show effectiveness recovery during predicted sleep
- **Visual confirmation:** SAFTE correctly models sleep opportunities between duty days

---

## Key Metrics & Thresholds

### **Effectiveness Thresholds:**

| Threshold | Meaning | Color Code |
|-----------|---------|------------|
| **>90%** | Optimal performance | Green |
| **85-90%** | Acceptable | Yellow |
| **77.5-85%** | Warning zone | Orange |
| **<77.5%** | Danger zone (0.05% BAC equivalent) | Red |
| **<70%** | Very high risk | Dark Red |

### **Fatigue Score Scale:**

| Score | Risk Level | Base Cause |
|-------|------------|------------|
| **0-40** | LOW | Lowest effectiveness ≥85% |
| **40-60** | MODERATE | Lowest effectiveness 77.5-85% |
| **60-80** | HIGH | Lowest effectiveness 70-77.5% |
| **80-100** | VERY HIGH | Lowest effectiveness <70% |

**Additional Penalty:** +2 points per hour in danger zone (max +20)

---

## Files Summary

### **New Files Created:**

| File | Lines | Purpose |
|------|-------|---------|
| `safte_model.py` | 260 | Core SAFTE fatigue model |
| `safte_integration.py` | 279 | Data bridge for pairing data |
| `test_safte_model.py` | 73 | Basic unit tests |
| `test_safte_validation.py` | 267 | Scientific validation tests |
| `test_safte_integration.py` | 241 | Integration tests |

**Total New Code:** ~1,120 lines

### **Modified Files:**

| File | Lines Changed | Purpose |
|------|---------------|---------|
| `app.py` | +195 (lines 665-859) | SAFTE UI integration |

---

## Scientific Validation

### **Published Research Basis:**

The SAFTE model is based on peer-reviewed research:

1. **Federal Railroad Administration Studies**
   - 89% variance explained in performance degradation over 72 hours
   - 98% variance explained across 54 hours of sleep deprivation
   - Strong correlation with accident risk ratios

2. **U.S. Army Research**
   - Original SAFTE development (pre-2004, public domain)
   - Validation against military operations data

3. **Academic Validation**
   - Psychomotor Vigilance Task (PVT) performance prediction
   - Subjective sleepiness correlation
   - Real-world operational performance studies

### **Implementation Fidelity:**

All mathematical formulas match published specifications:
- ✅ Reservoir capacity: 2,880 units
- ✅ Performance use rate: 0.5 units/min
- ✅ Sleep accumulation cap: 3.4 units/min
- ✅ Circadian acrophase: 18:00 (6 PM)
- ✅ Sleep inertia max: 5%
- ✅ Danger threshold: 77.5% (0.05% BAC equivalent)

---

## User Experience Enhancements

### **Session State Caching:**

Analysis results are cached per trip:
```python
st.session_state[f"fatigue_analysis_{selected_trip_id}"] = analysis
```

**Benefits:**
- No re-computation when toggling expanders
- Fast navigation between trips
- Preserves analysis across page interactions

### **Visual Design:**

1. **Chart Improvements:**
   - Date + time format on x-axis for multi-day clarity
   - Duty period shading for context
   - Two threshold lines (danger + warning)
   - Comprehensive tooltips

2. **Metric Cards:**
   - Color-coded risk indicators
   - Delta labels for risk level
   - Helpful hover tooltips
   - Clear units (%, hours, score/100)

3. **Progressive Disclosure:**
   - Key metrics always visible
   - Detailed stats in collapsible section
   - Educational notes about SAFTE

---

## Known Limitations & Future Enhancements

### **Current Limitations:**

1. **No Time Zone Adjustment**
   - Transmeridian travel (crossing time zones) not yet implemented
   - Circadian rhythm adjustment algorithm planned for Phase 4
   - Current implementation assumes local time remains constant

2. **Generic Sleep Prediction**
   - Uses default AutoSleep algorithm
   - No user customization for personal sleep patterns
   - Default commute time: 1 hour (not customizable)

3. **Individual Variation**
   - SAFTE predicts group averages, not individuals
   - No adjustment for age, health, experience
   - No historical data integration

### **Planned Future Enhancements:**

1. **Phase 4: Transmeridian Adjustment** (from original plan)
   - Implement circadian phase shift algorithm
   - Account for eastward/westward travel
   - Adjust sleep predictions for time zone changes

2. **User Customization:**
   - Custom commute time input
   - Personal sleep/wake time preferences
   - Adjustable sleep quality parameters

3. **Batch Analysis:**
   - Analyze all trips at once
   - Sort trips by fatigue score
   - Filter high-risk pairings

4. **Trip Comparison:**
   - Side-by-side fatigue comparison
   - Highlight safer alternatives
   - Export comparison reports

5. **PDF Report Integration:**
   - Add fatigue charts to downloadable PDFs
   - Include SAFTE summary in trip reports
   - Comprehensive safety documentation

---

## Testing Completed

### **Unit Tests:**
- ✅ Circadian oscillator mathematics
- ✅ Sleep period prediction (Rule 1 & 2)
- ✅ Basic simulation execution

### **Validation Tests:**
- ✅ 88-hour sleep deprivation pattern
- ✅ Circadian peak/nadir timing
- ✅ Sleep recovery replenishment
- ✅ Effectiveness exceeds 100%
- ✅ Danger threshold detection
- ✅ Sleep inertia decay
- ✅ Reservoir capacity limits
- ✅ Performance use rate consistency

### **Integration Tests:**
- ✅ Local time parsing
- ✅ Simple single-duty trips
- ✅ Midnight crossing handling
- ✅ Multi-day trip conversion
- ✅ Missing data handling
- ✅ Full analysis pipeline
- ✅ Metrics calculation
- ✅ Realistic EDW trip analysis

### **Real-World Testing:**
- ✅ ONT 757 PDF (272 trips, Trip 100 validated)
- ✅ Multi-day pairings show recovery patterns
- ✅ Early morning trips correctly flagged as high-risk
- ✅ Chart displays full timeline with layovers

---

## Commands for Reference

### **Run Tests:**
```bash
source .venv/bin/activate

# Basic tests
python test_safte_model.py

# Validation tests
python test_safte_validation.py

# Integration tests
python test_safte_integration.py

# All tests
python test_safte_model.py && python test_safte_validation.py && python test_safte_integration.py
```

### **Start Application:**
```bash
source .venv/bin/activate
streamlit run app.py
```

### **Access Application:**
- Local: http://localhost:8501
- Network: http://192.168.50.122:8501

### **Test Fatigue Analysis:**
1. Navigate to "📊 EDW Pairing Analyzer" tab
2. Upload PDF: `test_data/BID2601_757_ONT_TRIPS_CAROL.pdf`
3. Click "🚀 Run Analysis"
4. Select Trip 100 from dropdown
5. Scroll to "😴 SAFTE Fatigue Analysis"
6. Click "🧠 Run Fatigue Analysis"

---

## Session Statistics

- **Files Created:** 5
- **Files Modified:** 1
- **Total New Code:** ~1,120 lines
- **Tests Written:** 25
- **Tests Passing:** 25/25 (100%)
- **Functions Implemented:** 15
- **Mathematical Models:** 4 (Reservoir, Circadian, Sleep Inertia, AutoSleep)
- **Charts Added:** 1 (Effectiveness Timeline)
- **Metrics Displayed:** 3 (Lowest Effectiveness, Danger Time, Fatigue Score)

---

## Key Learnings

1. **Scientific Validation is Critical:** Cannot deploy a fatigue model without rigorous testing against published research. The 25-test suite ensures mathematical accuracy before real-world use.

2. **Visual Context Matters:** Initial chart showing only duty periods was misleading. Full timeline with layover shading makes recovery patterns obvious and builds user trust.

3. **Sawtooth Pattern is Key:** Multi-day trips should show decline-recovery-decline pattern. This visual confirmation validates that SAFTE is working correctly.

4. **Sleep Prediction Complexity:** The AutoSleep algorithm's "forbidden zone" concept (avoiding 12:00-20:00 sleep starts) is crucial for realistic predictions.

5. **Time Zone Challenges:** Current implementation works well for single-base operations but needs transmeridian adjustment for international routes.

6. **Threshold Communication:** Using "0.05% BAC equivalent" for 77.5% threshold makes the danger concrete and relatable for pilots.

---

## Repository Information

**Repository:** https://github.com/Kibutznik1978/edw_streamlit_starter
**Branch:** `Bid_Sorter` (uncommitted changes to app.py)
**Previous Session:** Session 14 - Brand Integration & PDF Layout Refinements
**Next Steps:**
1. Test with various trip types (international, overnight, EDW)
2. Consider transmeridian time zone adjustment (Phase 4)
3. User feedback on fatigue metrics
4. Potential integration into PDF reports

---

## Reference Documentation

### **SAFTE Research:**
- Federal Railroad Administration validation studies
- U.S. Army DTIC Report ADA452991
- Academic papers on biomathematical fatigue modeling

### **Internal Documentation:**
- `docs/SAFTE.md` - Comprehensive technical specification
- `docs/SAFTE_IMPLEMENTATION_PLAN.md` - Updated implementation plan with 3-step approach

### **Related Code:**
- `edw_reporter.py` - Trip parsing (provides duty times)
- `app.py` - Main Streamlit UI
- `safte_model.py` - Core fatigue model
- `safte_integration.py` - Data bridge

---

## Contact / Support

For questions about SAFTE implementation:
- Review scientific validation tests in `test_safte_validation.py`
- Check `docs/SAFTE.md` for mathematical formulas
- Consult `safte_integration.py` for data format requirements
- See Session 15 handoff (this document) for overview

**Important Safety Note:** SAFTE provides risk assessment based on generic sleep/wake patterns. Individual pilot fatigue may vary. This tool is for informational purposes and should not replace crew scheduling regulations or pilot judgment.

---

**End of Session 15 Handoff**
