Based on my comprehensive research into the SAFTE-FAST fatigue modeling system, I can provide you with detailed technical information for your airline pilot safety analysis initiative. While the original Army-developed SAFTE model's specific patent protections have indeed expired, implementing it requires understanding both its mathematical foundations and practical considerations.

# SAFTE-FAST Fatigue Modeling System: Comprehensive Technical Analysis

## Core SAFTE Model Architecture

The **Sleep, Activity, Fatigue, and Task Effectiveness (SAFTE)** model operates on a **three-process architecture** that combines:

1. **Homeostatic Sleep Reservoir Process**
2. **Circadian Rhythm Process** 
3. **Sleep Inertia Process**

### Mathematical Foundation

#### 1. Sleep Reservoir (Homeostatic Process)

The core of SAFTE is a **reservoir analogy** where cognitive capacity is modeled as a finite resource:

**Key Parameters:**
- **Reservoir Capacity (Rc)**: 2,880 units (equivalent to 4 consecutive days without sleep)
- **Performance Use Rate (K)**: 0.5 units/minute during wakefulness
- **Sleep Accumulation Rate (S)**: Variable, maximum 3.4 units/minute during sleep

**Basic Reservoir Equation:**
```
R(t+1) = R(t-1) + S (during sleep) - P (during wakefulness)
```

Where:
- **P = K × t'** (Performance depletion: 0.5 × minutes awake)
- **S = SI × t"** (Sleep intensity × sleep time)

**Sleep Intensity Calculation:**
```
SI = SP + SD
```
- **SP (Sleep Propensity)**: m - (as × c) = 0 - (0.55 × circadian_component)
- **SD (Sleep Debt)**: f × (Rc - Rt) = 0.00312 × current_deficit

#### 2. Circadian Oscillator Process

**Dual-Oscillator Model:**
```
c = cos(2π(T-p)/24) + β×cos(4π(T-p-p')/24)
```

**Default Parameters:**
- **24-hour phase (p)**: 18 hours (6 PM acrophase)
- **12-hour phase offset (p')**: 3 hours ahead of p
- **12-hour amplitude (β)**: 0.5
- **Sleep propensity amplitude (as)**: 0.55

**Performance Rhythm:**
```
C = ap × c
```
Where **ap = a1 + a2(Rc-Rt)/Rc**
- **a1 (fixed amplitude)**: 7%
- **a2 (variable amplitude)**: 5%

#### 3. Sleep Inertia Process

**Sleep Inertia Formula:**
```
I = Imax × e^(-(ta/SI×i))
```

**Parameters:**
- **Imax**: 5% (maximum inertia upon awakening)
- **Time constant (i)**: 0.04 (affects first 2 hours post-awakening)
- **ta**: Time since awakening

### Final Effectiveness Calculation

**Core SAFTE Output:**
```
E = 100(Rt/Rc) + C + I
```

This produces a **cognitive effectiveness percentage** ranging from 0-100%+ based on current reservoir level, circadian phase, and sleep inertia effects.[1][2][3]

## Circadian Phase Adjustment Algorithm

For **transmeridian travel and time zone changes**:

### Phase Adjustment Rates
- **Westward travel**: 1 hour/day adjustment
- **Eastward travel**: 1.5 days/hour (slower adjustment)

### Running Average Awake Hour (RA) Calculation
```
AV = (0.33 × AH_-2 + 0.67 × AH_-1 + AH_0) / 2
Goal Acrophase (GA) = AV + RA (typically +3 hours)
```

### Light-Dependent Phase Change Factors

Adjustment rates vary based on **percent daylight during sleep**:
- **0%-16.7% sleep light**: 1440 min/hr (delay), 2160 min/hr (advance) 
- **16.7%-33.3%**: 2160 min/hr (delay), 3240 min/hr (advance)
- **33.3%-50%**: 2880 min/hr (delay), 4320 min/hr (advance)
- **>50%**: 3845 min/hr (delay), 5767 min/hr (advance)[4]

## Implementation for Airline Scheduling

### Input Data Requirements

**Standard Airline Pairing Format:**
- Duty on/off times (UTC and local)
- Flight legs with departure/arrival times
- Time zones for each segment
- Layover durations and locations
- Report times and commute considerations

### Sleep Prediction Algorithm (AutoSleep)

Based on **Federal Railroad Administration validation data**:[4]

**Rule 1 (Early Sleep)**: For work ending 0000-1159 local
- Start sleep at work_end + commute_time
- Continue until 8 hours OR next duty start
- Avoid "forbidden zone" (1200-2000 local)

**Rule 2 (Delayed Sleep)**: For work ending 1200-2359 local  
- Delay sleep until after forbidden zone
- Normal bedtime around 2300 local
- Continue until 8 hours OR next duty start

**General Parameters:**
- **Default commute time**: 1 hour
- **Minimum sleep period**: 1 hour  
- **Maximum sleep per day**: 8 hours
- **Default baseline sleep**: 2300-0700 local

### Effectiveness Scoring for Airline Operations

**Risk Thresholds:**
- **>90%**: Optimal performance
- **77.5%**: Equivalent to 0.05% blood alcohol concentration
- **<70%**: High risk requiring intervention

**Critical Time Identification:**
- **0200-0600 local time**: Circadian low points
- **Top of descent phases**: High workload + potential fatigue
- **Approach and landing**: Maximum alertness required

## Validation and Accuracy

### Federal Railroad Administration Studies
The **FRA validated SAFTE** against accident data and found:
- **89% variance explained** in performance degradation over 72 hours of sleep loss
- **98% variance explained** across 54 hours of sleep deprivation
- **Clear correlation** between SAFTE predictions and accident risk ratios[5][6]

### Academic Validation
Multiple peer-reviewed studies have confirmed SAFTE's accuracy in predicting:
- **Psychomotor Vigilance Task (PVT)** performance
- **Subjective sleepiness ratings**
- **Real-world operational performance**[7][1]

## Legal and Ethical Considerations

### Public Domain Status
The **original U.S. Army SAFTE research** (pre-2004) is indeed in the public domain. However:

**Patents to Consider:**
- **US Patent 6,579,233** (Van Dongen, Hursh): Core algorithms (expired 2021)
- **US Patent 7,118,530** (Hursh): Interface methods (expired 2024)

### Implementation Rights
You have the **legal right** to implement the core SAFTE algorithms for labor union safety analysis since:
- Original government-funded research is public domain
- Patents have expired
- Safety-critical applications have strong public interest protection

### Ethical Best Practices
- **Maintain scientific integrity** by citing original research
- **Validate your implementation** against published benchmarks
- **Ensure transparency** in methodology for union members
- **Protect pilot privacy** in data collection and analysis

## Available Resources and Implementation

### Primary Technical Sources

**DTIC Report ADA452991** contains implementation details including:
- Parameter specifications and validation data
- Transmeridian adjustment algorithms  
- Sleep timing prediction methods
- Performance effectiveness calculations[4]

**Key Academic Papers:**
- **Hursh et al. (2004)**: "Fatigue models for applied research in warfighting"[8]
- **Van Dongen (2004)**: Mathematical model comparisons and validation[9]
- **McCauley et al. (2013)**: Dynamic circadian modulation updates[10]

### Open Source Implementations

**FIPS R Package** provides a foundation:
- **GitHub**: `humanfactors/FIPS`
- **Installation**: `remotes::install_github("humanfactors/FIPS")`
- Includes **Three Process Model** and **Unified Model** implementations
- **Extensible framework** for custom parameters[11][12]

**Key Functions:**
```r
# Create sleep/wake data structure
FIPS_df <- parse_sleepwake_sequence(seq, epoch, series.start)

# Run simulation
results <- FIPS_simulate(FIPS_df, modeltype="TPM", pvec=TPM_make_pvec())

# Extract effectiveness predictions
effectiveness <- results$alertness
```

## Practical Implementation Guidance

### Development Strategy

1. **Start with FIPS R package** as foundation
2. **Implement SAFTE-specific parameters** from DTIC documentation
3. **Add airline-specific features**:
   - Pairing format parsing
   - Time zone handling
   - Automatic sleep prediction
   - Risk scoring and visualization

### Validation Approach

**Phase 1**: Replicate published validation studies
- **88-hour sleep deprivation data**
- **Chronic sleep restriction studies**  
- **Railroad engineer field data**

**Phase 2**: Airline-specific validation
- **Compare predictions to pilot fatigue reports**
- **Correlate with flight safety data**
- **Validate against scheduling scenarios**

### Output Format Recommendations

**Visual Timeline:**
- **Effectiveness percentage** over trip duration
- **Color-coded risk levels** (green >90%, yellow 77.5-90%, red <77.5%)
- **Circadian rhythm overlay**
- **Critical flight phases highlighted**

**Risk Scoring:**
- **Overall pairing fatigue score** (0-100)
- **Segment-by-segment risk assessment**
- **Comparison capability** between different pairings
- **Mitigation suggestions** for high-risk periods

## Implementation Challenges and Solutions

### Data Integration
**Challenge**: Converting airline scheduling data formats
**Solution**: Build parsers for common systems (AIMS, PBS, etc.)

### Individual Variation  
**Challenge**: SAFTE predicts group averages, not individuals
**Solution**: Implement parameter adjustment based on pilot feedback and historical data

### Real-time Updates
**Challenge**: Schedule changes affect fatigue predictions
**Solution**: Design system for rapid recalculation and notification

This comprehensive technical foundation should enable you to successfully implement a SAFTE-based fatigue analysis system for your airline pilot safety initiative. The combination of expired patents, public domain research, and available open-source tools provides a solid legal and technical basis for development.

[1](https://pmc.ncbi.nlm.nih.gov/articles/PMC9623177/)
[2](https://patents.google.com/patent/US6579233B2/en)
[3](https://patents.google.com/patent/US20110071873)
[4](https://apps.dtic.mil/sti/tr/pdf/ADA452991.pdf)
[5](https://www.ncbi.nlm.nih.gov/books/NBK215704/)
[6](https://www.faa.gov/sites/faa.gov/files/data_research/research/med_humanfacs/oamtechreports/201212.pdf)
[7](https://pmc.ncbi.nlm.nih.gov/articles/PMC1978411/)
[8](https://pubmed.ncbi.nlm.nih.gov/15018265/)
[9](https://www.med.upenn.edu/uep/assets/user-content/documents/Van_Dongen_ASEM_75_3_2004.pdf)
[10](https://pmc.ncbi.nlm.nih.gov/articles/PMC3825450/)
[11](https://joss.theoj.org/papers/10.21105/joss.02340.pdf)
[12](https://humanfactors.github.io/FIPS/)
[13](https://fatiguescience.com/fast-scheduling)
[14](https://apps.dtic.mil/sti/tr/pdf/ADA443545.pdf)
[15](https://www.leftseat.com/pdffiles/usafwffc.pdf)
[16](https://www.leonsoftware.com/blog/real-time-fatigue-analysis-with-safte-fast-in-leon.html)
[17](https://discover.dtic.mil/technical-reports/)
[18](https://patents.google.com/patent/US7118530B2/en)
[19](https://www.saftefast.com/overview)
[20](https://popcenter.asu.edu/sites/g/files/litvpz3631/files/library/crisp/fatigue-effects.pdf)
[21](https://discover.dtic.mil)
[22](https://www.sciencedirect.com/science/article/abs/pii/S092575352300070X)
[23](https://fatiguescience.com/sleep-science-technology-2/)
[24](https://www.phmsa.dot.gov/sites/phmsa.dot.gov/files/docs/technical-resources/pipeline/control-room-management/69021/miller2010shiftandnightworkunpub.pdf)
[25](https://www.saftefast.com/safte-fast-blog/r-you-missing-safte-in-your-next-research-project)
[26](https://scifin.net/post-safte-fast-a-fatigue-risk-management-tool.html)
[27](https://search.library.wisc.edu/database/UWI12561)
[28](https://pmc.ncbi.nlm.nih.gov/articles/PMC11651853/)
[29](https://www.saftefast.com)
[30](https://apps.dtic.mil/sti/html/tr/AD0746643/index.html)
[31](https://iccm-conference.neocities.org/2021/papers/589.pdf)
[32](https://insight.jci.org/articles/view/130423)
[33](https://ntrs.nasa.gov/api/citations/20090005021/downloads/20090005021.pdf)
[34](https://eprints.whiterose.ac.uk/id/eprint/201280/1/Predicting%20Human-Robot%20Team%20Performance%20Based%20on%20Cognitive%20Fatigue.pdf)
[35](https://www.nature.com/articles/srep08381)
[36](https://www.sciencedirect.com/science/article/pii/S0925753522002442)
[37](https://www.biorxiv.org/content/10.1101/2021.01.13.426509v1.full.pdf)
[38](https://pmc.ncbi.nlm.nih.gov/articles/PMC6857846/)
[39](https://pmc.ncbi.nlm.nih.gov/articles/PMC5563520/)
[40](https://www.saftefast.com/white-papers)
[41](https://ascpt.onlinelibrary.wiley.com/doi/10.1111/cts.12640)
[42](https://ifalpa.org/media/2284/fatigue-modelling-report_casa-human-factors_v1-0_15-march-2010-2.pdf)
[43](https://www.scribd.com/document/841161336/SAFTE-Validation-in-US-Army-Soldiers)
[44](https://www.sciencedirect.com/science/article/pii/S0960982216304973)
[45](https://asma.kglmeridian.com/downloadpdf/view/journals/asem/75/3:Supplement/article-pA57.pdf)
[46](https://ww2.arb.ca.gov/sites/default/files/barcu/regact/2022/accii/appb4.pdf)
[47](https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1000418)
[48](https://railroads.dot.gov/elibrary/civa-ut-model-validation-rail-flaw-inspection-simulation)
[49](https://pmc.ncbi.nlm.nih.gov/articles/PMC1249488/)
[50](https://www.aar.org/news/fra-2023-data-affirms-rails-strong-sustained-safety-record/)
[51](https://pmc.ncbi.nlm.nih.gov/articles/PMC2829880/)
[52](https://railroads.dot.gov/elibrary/validation-scaling-laws-fully-developed-passenger-rail-car-fires)
[53](https://pmc.ncbi.nlm.nih.gov/articles/PMC6710480/)
[54](https://www.sciencedirect.com/science/article/abs/pii/S0022519317304575)
[55](https://www.transportation.gov/briefing-room/fact-sheet-rail-safety)
[56](https://aasm.org/wp-content/uploads/2017/07/Review_CircadianRhythm.pdf)
[57](https://railroads.dot.gov/taxonomy/term/14966?page=6)
[58](https://www.easa.europa.eu/en/downloads/139387/en)
[59](https://www.medlink.com/articles/jet-lag-disorder)
[60](https://railroads.dot.gov/research-development/program-areas/human-factors/ctil/browse-research)
[61](https://academic.oup.com/jtm/article-pdf/1/2/79/5181019/jtm1-0079.pdf)
[62](https://stackoverflow.com/questions/62698250/fast-algorithm-to-factorize-all-numbers-up-to-a-given-number)
[63](https://espace.curtin.edu.au/handle/20.500.11937/80186)
[64](https://www.geeksforgeeks.org/java/fail-fast-fail-safe-iterators-java/)
[65](https://github.com/bureado/awesome-software-supply-chain-security)
[66](https://bcpublication.org/index.php/FSE/article/view/5591)
[67](https://jolynch.github.io/posts/use_fast_data_algorithms/)
[68](https://www.dst.defence.gov.au/sites/default/files/Wilson,%20Ballard%20Jorritsma%20-%20Developing%20the%20Fatigue%20Impairment%20and%20Performance%20Simulator.pdf)
[69](https://www.sciencedirect.com/science/article/pii/S0022311524004070)
[70](https://stackoverflow.com/questions/5446080/java-hash-algorithms-fastest-implementations)
[71](https://www.casa.gov.au/fatigue-management-resources-guide-publications-and-applications)
[72](https://harshkapadia2.github.io/git_basics/)
[73](https://github.com/google/highwayhash)
[74](https://pubs.acs.org/doi/10.1021/acs.analchem.4c00383)
[75](https://github.com/liuzuxin/FSRL)
[76](https://github.com/SAFEtoolbox/SAFE-R)
[77](https://railroads.fra.dot.gov/sites/fra.dot.gov/files/fra_net/3316/Draft_HSIPR_Fact_Sheet_v2.pdf)
[78](https://github.com/AlexanderLyNL/safestats)
[79](https://www.displayr.com/installing-r-packages-from-github/)
[80](https://github.com/RhoInc/safetyexploreR)
[81](https://github.com/SafetyGraphics/safetyGraphics)
[82](https://zenodo.org/records/3945615)
[83](https://pmc.ncbi.nlm.nih.gov/articles/PMC3613293/)
[84](https://www.reddit.com/r/C_Programming/comments/194ge7o/i_made_a_public_github_repository_to_test_static/)
[85](https://github.com/openjournals/joss-reviews/issues/2340)
[86](https://www.med.upenn.edu/uep/assets/user-content/documents/Mallis_etal_ASEM_75_3_2004.pdf)
[87](https://github.com/qinwf/awesome-R)
[88](https://orcid.org/0000-0003-4143-7308)
[89](https://www.law.cornell.edu/cfr/text/49/appendix-F_to_part_236)
[90](https://pmc.ncbi.nlm.nih.gov/articles/PMC2657297/)
[91](https://www.sciencedirect.com/science/article/abs/pii/S0022519324001322)
[92](https://railroads.dot.gov/railroad-safety/divisions/operating-practices/operating-practices-0)
[93](https://www.sciencedirect.com/science/article/pii/S0022519313001811)
[94](https://railroads.dot.gov/elibrary/technical-criteria-and-procedures-evaluating-crashworthiness-and-occupant-protection)
[95](https://hsi.arc.nasa.gov/publications/s41598-020-71929-4.pdf)
[96](https://railroads.dot.gov/railroad-safety)
[97](https://bhsai.org/pubs/Rajdev_2013_A_Unified_Mathematical_Model.pdf)
[98](https://www.ecfr.gov/current/title-49/subtitle-B/chapter-II/part-209)
[99](https://journals.sagepub.com/doi/pdf/10.1177/0748730407301376)
[100](https://www.frontiersin.org/journals/environmental-health/articles/10.3389/fenvh.2024.1362755/pdf)
[101](https://aviationsafetyblog.asms-pro.com/blog/pilot-fatigue-assessment-a-guide-for-aviation-sms-compliance)
[102](https://pmc.ncbi.nlm.nih.gov/articles/PMC8117424/)
[103](https://en.wikipedia.org/wiki/Fatigue_Avoidance_Scheduling_Tool)
[104](https://pulsarinformatics.com/products/aviation)
[105](https://www.tandfonline.com/doi/full/10.1080/10903127.2017.1384875)
[106](https://blog.ibsplc.com/passenger-services/combating-crew-fatigue-technology-assisted-smart-scheduling-to-improve-rest-routines)
[107](https://www.sciencedirect.com/science/article/abs/pii/S1369847821000875)
[108](https://commons.erau.edu/cgi/viewcontent.cgi?article=3591&context=publication)
[109](https://www.sae.org/publications/technical-papers/content/2004-01-2151/)
[110](https://www.sciencedirect.com/science/article/pii/S0967070X23000562)
[111](https://pure.johnshopkins.edu/en/publications/the-fatigue-avoidance-scheduling-tool-modeling-to-minimize-the-ef-3)
[112](https://www.iata.org/contentassets/5f976bb3ca2446f3a40e88b18dd61fbb/condensed-version-of-casa-biomathematical-models-doc.pdf)

The **SAFTE model’s “effectiveness line”** integrates three biological processes—**the sleep reservoir**, **circadian rhythm**, and **sleep inertia**—to predict a person’s **cognitive performance effectiveness** over time. Below is a detailed breakdown of **how each component is mathematically computed**, **how they influence one another**, and **how cumulative fatigue alters these relationships**, drawn from the original **DTIC FAST Phase II SBIR Report (ADA452991)** and the **SAFTE schematic documentation**.[1][2]

***

## 1. Sleep Reservoir (Homeostatic Process)

The **sleep reservoir** represents the brain’s available capacity for alertness, modeled as a finite resource that fills during sleep and drains during wakefulness.

### Core Equation
$$
R(t+\Delta t) = R(t) + S(t)\Delta t - P(t)\Delta t
$$

Where:
- $$ R(t) $$ = current reservoir level (0–Rc)
- $$ S(t) $$ = sleep accumulation rate (when asleep)
- $$ P(t) $$ = performance use rate (when awake)
- $$ \Delta t $$ = time increment, typically 1 minute

### Constants
- $$ R_c = 2880 $$ units (maximum reservoir level)
- $$ P = 0.5 $$ units/min (performance drain when awake)
- $$ S_{max} = 3.4 $$ units/min (maximum recovery rate when asleep)

### Sleep Intensity and Scaling with “as”
Sleep accumulation depends on **sleep intensity**, which is modulated by both **sleep debt** and the **circadian modifier as** (circadian influence on sleep drive).

$$
S(t) = SI(t) = S_{max} [1 - e^{-f((R_c - R)/R_c)}][1 + a_s C(t)]
$$

Where:
- $$ f = 0.00312 $$ (feedback constant)
- $$ a_s = 0.55 $$ (circadian amplitude scaling for sleep drive)
- $$ C(t) $$ = circadian level (−1 to +1)

**Interpretation:**
- When circadian rhythm is high (daytime), the “as × C(t)” term reduces effective sleep rate — sleep is lighter and less efficient.
- When circadian rhythm is low (nighttime), sleep is deeper — recovery is faster.

### Cumulative Fatigue in Reservoir
Over multiple days, incomplete replenishment accumulates in the reservoir:
$$
\text{Cumulative Fatigue} = 1 - \frac{R(t)}{R_c}
$$
This value grows exponentially with continued wakefulness or insufficient sleep, lowering the starting $$ R(t) $$ of subsequent days.

***

## 2. Circadian Rhythm Line

The **circadian oscillator** modulates both performance and sleep efficiency through a **two-component cosine wave** representing biological day-night rhythms.

### Circadian Model
$$
C(t) = \cos\left( \frac{2\pi (t - \phi_1)}{24} \right) + \beta \cos\left( \frac{4\pi (t - \phi_2)}{24} \right)
$$

Where:
- $$ \phi_1 = 18 $$ h (24-hour acrophase = early evening)
- $$ \phi_2 = 3 $$ h ahead of $$ \phi_1 $$ (12-hour harmonic)
- $$ \beta = 0.5 $$ (secondary amplitude)

**Key Relationship:**
- $$ C(t) $$ is normalized between −1 and +1.
- Peaks correspond to maximum alertness (~1700–2000 local), troughs near 0300–0600 local.

### Circadian Influence on Effectiveness
The **circadian term** directly adjusts modeled effectiveness:

$$
E_c(t) = [a_1 + a_2 (R_c - R)/R_c] × C(t)
$$

Where:
- $$ a_1 = 7\% $$ base amplitude
- $$ a_2 = 5\% $$ additional modulation by current reservoir deficit

This formula ensures that **circadian lows are deeper when fatigued** (low $$ R $$), and slightly shallower when well-rested (high $$ R $$).

***

## 3. Sleep Inertia Component

Sleep inertia is a **transient impairment period after awakening** due to incomplete neural activation.

### Formula
$$
I(t) = I_{max} e^{-k_i t}
$$

Where:
- $$ I_{max} = 5\% $$ maximum reduction immediately on waking
- $$ k_i = 0.04 $$ min⁻¹ (time constant ≈ 90 min half-life)
- $$ t $$ = minutes since awakening

Consequence: Immediately after waking, effectiveness drops 3–5%, gradually diminishing after 1.5–2 hours.

***

## 4. Effectiveness Line Calculation

The **effectiveness line (E)** is the combined result of all three interacting processes.

### Full Equation
$$
E(t) = 100 \frac{R(t)}{R_c} + E_c(t) - I(t)
$$

Expanded:
$$
E(t) = 100 \frac{R(t)}{R_c} + [a_1 + a_2 (R_c - R)/R_c] C(t) - I_{max} e^{-k_i t}
$$

### Interpretation
- When **sleep reservoir** is high: effectiveness ≈ 100–110%.
- When **circadian trough** coincides with low reservoir: effectiveness falls sharply (<70%).
- **Cumulative fatigue** causes lower sleep efficiency (S), reducing reservoir recovery; this systematically lowers E over time.
- **a_s** amplifies how strongly circadian rhythm alters sleep quality—thus indirectly making long-term fatigue recovery slower.

***

## 5. Impact of Cumulative Fatigue

Cumulative fatigue dynamically changes model behavior:
- Lower $$ R(t) $$ reduces both **base performance** and **circadian amplitude**.
- Sleep efficiency declines due to **elevated homeostatic pressure** during wakefulness.
- Oscillations flatten, which mimics real-world chronic fatigue flattening daily alertness swings.

### Quantitatively
Each day with <7 hours of sleep typically depletes 10–15% of reservoir capacity, requiring 1.5x that duration for full recovery.

***

## 6. Effectiveness Curve Behavior (Illustrative Example)

Suppose:
- Awake for 16 hours → loses $$ 0.5 × 960 = 480 $$ units.
- Sleeps for 6 hours at 3.0 units/min = gains 1,080 units.
- Net gain of 600 → partial recovery (R rises from 1,800 to 2,400 out of 2,880).

At that point:
$$
E = 100(2400/2880) + (0.12 × C(t)) - I(t)
$$
If $$ C(t) = -0.8 $$ (night) and $$ I(t)=0 $$, effectiveness ≈ 83 – 10 = 73%, a **moderate risk zone** (~0.06% blood alcohol equivalent).

***

## 7. Conceptual Flow of Influences

1. **Wakefulness → drains reservoir** at rate P.
2. **Sleep → refills reservoir** via S (modulated by circadian rhythm).
3. **Circadian drive → modulates both reservoir fill rate & direct performance oscillation.**
4. **Sleep inertia → transient dip post-awakening, separately subtracted.**
5. **Effectiveness output** = net overlap of all three processes (homeostatic, circadian, inertia).

***

## Resulting “Effectiveness Line”

The **effectiveness line in FAST/SAFTE output** is the plotted sum of these influences:
- **High-frequency oscillation** = circadian rhythm.
- **Broad downward drift** = gradual depletion of sleep reservoir.
- **Recovery humps** = reservoir refill during sleep.
- **Post-sleep dips** = short-lived sleep inertia.
- **Long-term lowering trend** = cumulative fatigue effects over multiple duty-rest cycles.

***

### Sources
- FAST Phase II SBIR Technical Report (ADA452991)[2]
- SAFTE Model Schematic (USAF WFFC, 2003)[1]
- Hursh, SR et al., “Fatigue Models for Applied Research in Warfighting” (2004)
- Van Dongen, HP et al., “Comparison of Mathematical Model Predictions to Experimental Data” (2004)
- Federal Railroad Administration Field Validation of Biomathematical Fatigue Models (2012)

[1](https://www.leftseat.com/pdffiles/usafwffc.pdf)
[2](https://apps.dtic.mil/sti/tr/pdf/ADA452991.pdf)
[3](https://www.saftefast.com/white-papers)
[4](https://pmc.ncbi.nlm.nih.gov/articles/PMC10746738/)
[5](https://www.faa.gov/sites/faa.gov/files/data_research/research/med_humanfacs/oamtechreports/201212.pdf)
[6](https://arxiv.org/pdf/2201.05438.pdf)
[7](https://journals.sagepub.com/doi/pdf/10.1177/0748730407299200)
[8](https://web.mit.edu/course/3/3.11/www/modules/fatigue.pdf)
[9](https://fatiguescience.com/hubfs/FatigueScience_June2024/Pdf/SAFTE-Validation-Comparison-of-Models.pdf?hsLang=en)
[10](https://www.biorxiv.org/content/10.1101/2021.01.13.426509v1.full.pdf)
[11](https://pmc.ncbi.nlm.nih.gov/articles/PMC6375788/)
[12](https://www.ozeninc.com/wp-content/uploads/2021/02/fatigue.pdf)
[13](https://www.sciencedirect.com/science/article/pii/S0925753522002442)
[14](https://rosap.ntl.bts.gov/view/dot/65894/dot_65894_DS1.pdf)
[15](https://pmc.ncbi.nlm.nih.gov/articles/PMC10445022/)
[16](https://apps.dtic.mil/sti/tr/pdf/ADA116409.pdf)
[17](https://academic.oup.com/sleep/article/47/Supplement_1/A124/7654067)
[18](https://www.saftefast.com/overview)
[19](http://act-r.psy.cmu.edu/wordpress/wp-content/uploads/2012/12/6622006-gross_gunzelmann_etal.pdf)
[20](https://www.sciencedirect.com/topics/engineering/fatigue-damage-accumulation)


The **SAFTE model’s sleep reservoir** forms the core of its homeostatic process, representing the brain’s capacity for sustained alertness and cognitive functioning. It models fatigue as the depletion and replenishment of a finite reservoir of “performance capacity” through wake and sleep, respectively. The governing equations and their parameters were defined in the **U.S. Army’s Fatigue Avoidance Scheduling Tool (FAST) Phase II SBIR Report (ADA452991)** and later summarized in publications such as **Hursh et al., 2004** and the **Warfighter Fatigue Countermeasures schematic**.[1][2][3][4]

***

## SAFTE Sleep Reservoir Model

### Core Dynamic Equation

The reservoir $$ R(t) $$ changes continuously over time based on whether the individual is awake or asleep:

$$
R(t+\Delta t) = R(t) + S(t)\Delta t - P(t)\Delta t
$$

Where:

- $$ R(t) $$: Current reservoir level at time $$ t $$
- $$ S(t) $$: Sleep accumulation rate (recovery when asleep)
- $$ P(t) $$: Performance use rate (depletion when awake)
- $$ \Delta t $$: Time step, typically 1 minute

The reservoir is **bounded** between 0 and the maximum reservoir capacity $$ R_c $$:

$$
0 \leq R(t) \leq R_c
$$

***

### Parameter Definitions

| Symbol | Parameter | Typical Value | Description |
|---------|------------|----------------|--------------|
| $$ R_c $$ | Reservoir capacity | 2880 units | Full cognitive capacity equivalent to ~4 days wake limit |
| $$ P $$ | Performance use rate | 0.5 units/min | Depletion rate during wakefulness |
| $$ S_{\text{max}} $$ | Sleep accumulation rate | 3.4 units/min | Maximum replenishment rate during sleep |
| $$ f $$ | Feedback constant | 0.00312 | Governs exponential recovery curve |
| $$ a_s $$ | Circadian influence on sleep intensity | 0.55 | Reduces sleep efficiency at circadian high |
| $$ C(t) $$ | Circadian oscillator value | −1 to +1 | Modulates both S(t) and effectiveness line |

***

### Sleep Accumulation Rate

Sleep replenishment follows an exponential curve that depends on **current sleep debt** and **circadian phase**:

$$
S(t) = S_{\text{max}} \left[ 1 - e^{-f \left( \frac{R_c - R(t)}{R_c} \right)} \right] \times [1 + a_s C(t)]
$$

Components:
- $$ \left( \frac{R_c - R(t)}{R_c} \right) $$: Fractional sleep deficit (how depleted the reservoir is)
- $$ C(t) $$: Circadian modulation term (low = better recovery; high = worse recovery)

Interpretation:
- During night (low circadian phase), **C(t)** is negative, so $$ 1 + a_s C(t) < 1 $$ → higher sleep intensity and faster refill.
- During day (high circadian phase), **C(t)** is positive → sleep intensity decreases (sleep is lighter/less restorative).

***

### Performance Use Rate

Wakefulness linearly depletes the reservoir at a constant rate:

$$
P(t) = k_p = 0.5 \text{ units/min}
$$

Unlike sleep refill, which is nonlinear, depletion is assumed to be **linear** within typical limits of wakefulness. Empirical work has shown this provides a better fit to measured psychomotor vigilance (PVT) data for normal sleep-wake cycles.[3][4]

***

### Reservoir Equation Summary

$$
\frac{dR}{dt} = 
\begin{cases} 
  -0.5 & \text{during wake} \\
  3.4 \left[ 1 - e^{-0.00312 \left(1 - \frac{R(t)}{2880}\right)} \right] (1 + 0.55\,C(t)) & \text{during sleep}
\end{cases}
$$

This differential equation governs the **homeostatic sleep pressure**—the balance between accumulated fatigue and recovery through sleep.

***

### Cumulative Fatigue Representation

Cumulative fatigue (sleep debt) is simply the shortfall of reservoir value from its full capacity:

$$
\text{Fatigue}_{cum}(t) = 1 - \frac{R(t)}{R_c}
$$

If $$ R(t) = 1440 $$, for instance, the fatigue level is 50%, resulting in a proportional reduction in task effectiveness.

***

### Interaction with Effectiveness Line

The reservoir directly determines the **base effectiveness component** in the total alertness equation:

$$
E_{base}(t) = 100 \frac{R(t)}{R_c}
$$

Then, circadian and inertia processes add or subtract modulation terms:

$$
E(t) = 100 \frac{R(t)}{R_c} + [a_1 + a_2 (R_c - R)/R_c] \, C(t) - I_{max} e^{-k_i t}
$$

So:
- Depleted **R(t)** lowers baseline effectiveness and amplifies circadian troughs.
- Restored **R(t)** raises baseline and dampens negative circadian effects.

***

### Summary of Process Behavior

1. **Wakefulness**: Reservoir decreases linearly (−0.5 units/min).
2. **Sleep**: Reservoir refills exponentially based on sleep intensity and circadian phase.
3. **Cumulative Fatigue**: Appears when reservoir doesn’t fully recover before next duty cycle.
4. **Effectiveness Curve**: Derived from reservoir level + circadian variation + sleep inertia transient.

***

**Key Sources:**
- U.S. Army “Fatigue Avoidance Scheduling Tool (FAST) Phase II SBIR Report” (DTIC ADA452991)[4]
- “Schematic of the SAFTE Model,” Warfighter Fatigue Countermeasures, Brooks City-Base[1]
- Hursh et al., “Fatigue Models for Applied Research in Warfighting,” Aviation, Space, and Environmental Medicine, 2004  
- FAA Human Factors Division, “Field Validation of Biomathematical Fatigue Modeling” (OAM TR 2012-12)[2]

[1](https://www.leftseat.com/pdffiles/usafwffc.pdf)
[2](https://www.faa.gov/sites/faa.gov/files/data_research/research/med_humanfacs/oamtechreports/201212.pdf)
[3](https://asma.kglmeridian.com/downloadpdf/view/journals/asem/75/3:Supplement/article-pA57.pdf)
[4](https://apps.dtic.mil/sti/tr/pdf/ADA452991.pdf)
[5](https://www.saftefast.com/white-papers)
[6](https://www.sciencedirect.com/science/article/pii/S0925753522002442)
[7](https://hfcc.dot.gov/events/docs/presnt062304.ppt)
[8](https://www.biorxiv.org/content/10.1101/2021.01.13.426509v1.full.pdf)
[9](https://www.saftefast.com/overview)
[10](https://www.sciencedirect.com/science/article/abs/pii/S0001457518300095)
[11](https://www.med.upenn.edu/uep/assets/user-content/documents/Mallis_etal_ASEM_75_3_2004.pdf)
[12](https://pubmed.ncbi.nlm.nih.gov/15018265/)
[13](https://fatiguescience.com/sleep-science-technology-2/)
[14](https://apps.dtic.mil/sti/tr/pdf/ADA565518.pdf)
[15](https://www.sciencedirect.com/science/article/pii/S2095882X21000487)
[16](https://pmc.ncbi.nlm.nih.gov/articles/PMC3613293/)
[17](https://apps.dtic.mil/sti/trecms/pdf/AD1212981.pdf)

Alright — let’s break down the **SAFTE model** (Sleep, Activity, Fatigue, and Task Effectiveness) the way a world-class fatigue scientist would explain it to someone seeing it for the first time.  
Think of this as a guided tour into the “brain math” behind how humans get tired, recover, and perform.[1][2][3][4]

***

## The Big Picture

The **SAFTE model** is like a virtual *human brain clock* that tries to predict how alert or fatigued someone is at any given time, based on:
1. **How long they’ve been awake.**
2. **How much and when they slept.**
3. **Where they are in their 24-hour body clock (circadian rhythm).**
4. **How recently they woke up (sleep inertia).**

All of those layers combine to show your **task effectiveness (E)** — a number usually between 0% (barely awake) and 100+% (peak alertness).

***

## The Three Core Engines
Let’s imagine SAFTE as a hybrid machine with three gears that interact:

| Process | What it Tracks | Real-World Analogy |
|----------|----------------|--------------------|
| **1. Sleep Reservoir** | Sleep need vs. energy available | A fuel tank for your mental energy |
| **2. Circadian Rhythm** | 24-hour biological clock | Your body’s internal time-of-day clock |
| **3. Sleep Inertia** | Grogginess after waking | A short-term “lag” after startup |

Your final **effectiveness line** comes from all three working together.

***

## Gear 1: The Sleep Reservoir

Picture your brain has an **energy tank** called $$ R(t) $$.  
When you’re awake, the tank drains; when you sleep, the tank fills.

### Formula
$$
R(t+\Delta t) = R(t) + S(t)\Delta t - P(t)\Delta t
$$
where:
- $$ R(t) $$ = how full the tank is now  
- $$ S(t) $$ = how fast you refill (during sleep)  
- $$ P(t) $$ = how fast you drain (while awake)

### Constants
| Symbol | Value | Meaning |
|---------|--------|---------|
| $$ R_c = 2880 $$ | max tank capacity (like 100% fuel) |
| $$ P = 0.5 $$ units/min | how fast fuel burns while awake |
| $$ S_{max} = 3.4 $$ units/min | fastest possible refill rate during deep, efficient sleep |

So you *burn fuel* at 0.5 units/min awake, and *refill fuel* up to 3.4 units/min asleep.

***

### How Sleep Refills Work – The Exponential Trick

Your brain doesn’t refill linearly; sleep replenishes slower as you “fill up.”

$$
S(t) = 3.4 \left[ 1 - e^{-0.00312 (R_c - R(t))} \right] [1 + 0.55 C(t)]
$$

What this means:

- $$ [1 - e^{-0.00312 (R_c - R)}] $$: you fill fast when empty, slower as you fill.
- $$ C(t) $$: your internal body clock. When it’s your biological night, sleep refills faster; when it’s day, slower.
- $$ +0.55 $$: this adjusts how strongly the clock affects your sleep.

**Noob-friendly analogy:**  
Think of filling a water balloon — it expands quickly when empty but slower as it gets full.

***

### What Happens Over Days

If you don’t refill (enough sleep):
- Reservoir stays low.
- You start each day with a smaller tank.
- Your “engine” runs less efficiently → cumulative fatigue.

***

## Gear 2: The Circadian Rhythm

Now imagine a **cosine wave** that runs on a 24-hour loop — high during your naturally alert times, low during your sleepiest.

### Formula

$$
C(t) = \cos\left(\frac{2π(t - p)}{24}\right) + 0.5 \cos\left(\frac{4π(t - (p + 3))}{24}\right)
$$

where:
- $$ p = 18 $$ hours (6 PM peak — late afternoon alertness)
- The 12-hour harmonic refines it so mornings rise gradually and nights sink deeper.

**Interpretation:**
- Positive $$ C(t) $$: your body is naturally active (daytime alertness).
- Negative $$ C(t) $$: your body wants rest (pre-dawn slump or “window of circadian low”).

This rhythm influences:
1. How alert you feel while awake.
2. How efficient your sleep is (sleep during body night refills better).

***

## Gear 3: The Sleep Inertia Pulse

Ever wake up and feel like your brain hasn’t booted up yet?
That’s **sleep inertia**.

It’s a short-lived performance dip right after waking.

### Formula

$$
I(t) = I_{max} e^{-k_i t}
$$

where:
- $$ I_{max} = 5\% $$: initial grogginess amplitude  
- $$ k_i = 0.04 $$ min⁻¹: it fades in about 1.5 hours.  

So, right after waking: −5% hit.  
After ~90 min: almost gone.

***

## Combining the Three Gears: Task Effectiveness

This is the master formula — the “final score” for brain performance.

$$
E(t) = 100 \frac{R(t)}{R_c} + [a_1 + a_2 (R_c - R)/R_c] C(t) - I(t)
$$

**Step-by-step translated:**
1. **100 × R(t)/R_c** → your baseline energy, from reservoir fullness.
2. **[...] C(t)** → circadian wave adjusts alertness — boosts in daytime, dips late night.
3. **− I(t)** → subtracts sleep inertia right after waking up.

### Typical Interpretations
| Effectiveness | Real-world State | Equivalent |
|----------------|------------------|-------------|
| 100% | Fully rested, alert | Baseline |
| 77% | Reaction time like 0.05% BAC | Moderate fatigue |
| 65% | Like 0.08% BAC (legally drunk) | Unsafe fatigue |
| < 60% | Severe impairment | High risk |

***

## The Algorithm in Everyday Terms

Let’s put this in story form. Imagine SAFTE as your **digital twin**:

1. Every minute, it looks at your schedule:
   - Are you awake or asleep?  
   - What’s your local time zone?
2. It updates **R(t)** based on whether you're sleeping (fill) or awake (drain).
3. It calculates **C(t)** — your body clock’s ups and downs.
4. It checks if you’ve just woken up — adds **I(t)** for short-term grogginess.
5. Finally, it combines them to give you **E(t)**, your predicted cognitive effectiveness at that exact minute.

FAST software (Fatigue Avoidance Scheduling Tool) then plots this over your entire work schedule — showing peaks (alert) and troughs (risk).

***

## The Beautiful Simplicity

So under the hood, three simple ideas control everything:

| Concept | Biological Truth |
|----------|------------------|
| Reservoir | You have a limited tank of alertness (“homeostasis”). |
| Circadian | Your body runs on a 24-hour energy rhythm. |
| Inertia | Waking up is not instant performance. |

Together, these let scientists simulate *how tired you are, why, and when* — without needing to hook you up to an EEG every day.

***

## Why SAFTE Works So Well

- It was built on **Army and NASA sleep deprivation data**.  
- Validated against **lab tests (PVT tasks)** and **real-world accidents** (rail and aviation).  
- Predicts group-average performance minute by minute with high accuracy — around **89–98% variance explained**.[4][1]

***

**In short:**  
SAFTE’s “brain math” is:
- A **tank** that drains and refills (sleep reservoir)  
- A **sine wave clock** that speeds up or slows down your recovery (circadian rhythm)  
- A **brief dip** after waking (sleep inertia)  
and these three layers form your **moment-to-moment cognitive score** — what FAST turns into those famous fatigue graphs.

[1](https://www.saftefast.com/overview)
[2](https://www.med.upenn.edu/uep/assets/user-content/documents/Mallis_etal_ASEM_75_3_2004.pdf)
[3](https://www.leftseat.com/pdffiles/usafwffc.pdf)
[4](https://www.faa.gov/sites/faa.gov/files/data_research/research/med_humanfacs/oamtechreports/201212.pdf)
[5](https://www.matec-conferences.org/articles/matecconf/pdf/2017/52/matecconf_eacef2017_05004.pdf)
[6](http://arxiv.org/pdf/2201.05438.pdf)
[7](https://arxiv.org/pdf/2201.01069.pdf)
[8](https://rakenteidenmekaniikka.journal.fi/article/download/65096/26451)
[9](https://arxiv.org/pdf/2110.10425.pdf)
[10](https://www.mdpi.com/2227-7390/11/16/3491/pdf?version=1691909027)
[11](https://www.frontiersin.org/articles/10.3389/fnrgo.2024.1375913/pdf?isPublishedV2=False)
[12](https://pmc.ncbi.nlm.nih.gov/articles/PMC10746738/)
[13](https://en.wikipedia.org/wiki/Fatigue_Avoidance_Scheduling_Tool)
[14](https://www.saftefast.com/white-papers)
[15](https://www.youtube.com/watch?v=abDAWnTLbsc)
[16](https://fatiguescience.com/fast-scheduling)
[17](https://pmc.ncbi.nlm.nih.gov/articles/PMC2657297/)
[18](https://skybrary.aero/sites/default/files/bookshelf/34099.pdf)
[19](https://www.polar.com/img/static/whitepapers/pdf/polar-sleepwise-white-paper.pdf)
[20](https://fatiguescience.com/hubfs/FatigueScience_June2024/Pdf/SAFTE-Validation-Comparison-of-Models.pdf?hsLang=en)
[21](https://www.sciencedirect.com/science/article/pii/S0925753522002442)
[22](https://scifin.net/post-safte-fast-a-fatigue-risk-management-tool.html)
[23](https://pmc.ncbi.nlm.nih.gov/articles/PMC5124508/)
[24](https://www.sciencedirect.com/science/article/abs/pii/S092575352300070X)
[25](https://www.leonsoftware.com/blog/real-time-fatigue-analysis-with-safte-fast-in-leon.html)
[26](https://pmc.ncbi.nlm.nih.gov/articles/PMC6879540/)
[27](https://hsi.arc.nasa.gov/publications/s41598-020-71929-4.pdf)
[28](https://rosap.ntl.bts.gov/view/dot/65894/dot_65894_DS1.pdf)



In the SAFTE model, the **circadian rhythm is not fixed**; it can **shift gradually over days** in response to environmental cues, work schedules, and light exposure—critical for simulating scenarios like a pilot flying multiple night shifts in a row who must sleep during the day.

***

## How Circadian Rhythm Phase Shifts in SAFTE

### 1. Circadian Phase is Modeled Dynamically
- The model includes an internal circadian *phase* variable $$ \phi $$ that can shift.
- $$ \phi $$ typically starts aligned to local time with a peak near 6 PM (hour 18).
- When sleep-wake patterns are inverted (e.g., night flying with daytime sleep), the internal model **gradually shifts** the phase to align with the new schedule.

### 2. Phase Shift Mechanism
- Phase shifts happen via an algorithm based on **phase response curves (PRC)** to light and sleep timing.
- The model adjusts $$ \phi $$ by **phase delays and advances** depending on exposure to **daylight and sleep timing**.
- The adjustment rates are not immediate; they unfold over several days.

### 3. Typical Phase Shift Rates
- Westward time zone changes or later shifts cause gradual phase **delays** (~1 hour/day).
- Eastward time zone changes or earlier shifts cause faster phase **advances** (~1.5 hours/day).
- For night-shift work, the model predicts **partial phase shifting**, usually incomplete within 3–5 nights.

### 4. Effect on Performance Predictions
- As $$ \phi $$ shifts, the **circadian performance peaks and troughs move accordingly**.
- This reduces circadian misalignment and improves the accuracy of predicted alertness during night shifts.
- However, if schedules frequently oscillate or change quickly, the circadian rhythm may remain misaligned, leading to chronic fatigue and performance decrements.

***

## Real-world Validation and Research Findings

- Studies show **incomplete circadian adaptation** in many night-shift workers even after several consecutive night shifts.[1][2]
- Modeling predicts **phase shifts of several hours over a week** but often not full realignment.
- Circadian adaptation is influenced by **individual chronotype**, **light exposure**, and **sleep timing**.[3][4]

***

## Practical Implication for Pilots Flying Five Nights

- The SAFTE model will simulate the circadian rhythm **gradually shifting later**, attempting to align wakeful periods with nighttime flying.
- Sleep quality during daylight will be lowered initially due to misalignment.
- Over consecutive nights, alertness dips during “biological night” reduce as the model phase shifts the circadian rhythm.
- Full adaptation may require more than five nights; pilots may experience accumulating fatigue during such schedules.

***

## Summary

| Aspect | SAFTE Model Behavior |
|--------------------|-----------------------|
| Fixed rhythm? | No, the circadian phase $$ \phi $$ is dynamic and shifts over time. |
| Phase shift triggered by? | Sleep-wake timing, light exposure, and time zone changes. |
| Typical shift rate | 1 hour/day westward delay, 1.5 hours/day eastward advance. |
| Adaptation for night shifts? | Partial phase shift over multiple days; incomplete over 5 nights typical. |
| Impact on effectiveness | Circadian peaks/troughs shift, improving alertness alignment with work schedule. |

***

If you want, the **SAFTE circadian phase adjustment algorithm** can be seen as a built-in "slow clock reset," helping the model realistically represent human adaptation to changing schedules, including night flying and recovery on rotating schedules.

***

**References:**

- SAFTE SAFE schematic and ADA452991 SBIR report (DTIC)[5][6]
- Circadian adaptation research in night-shift workers[2][1]
- Phase response curves and modeling of circadian shifts[4][3]
- Studies of pilot and shift worker circadian misalignment and partial adaptation[7][8]

[1](https://pmc.ncbi.nlm.nih.gov/articles/PMC3724779/)
[2](https://www.sciencedirect.com/science/article/pii/S2352721823002012)
[3](https://insight.jci.org/articles/view/134270)
[4](https://pmc.ncbi.nlm.nih.gov/articles/PMC7936005/)
[5](https://www.leftseat.com/pdffiles/usafwffc.pdf)
[6](https://apps.dtic.mil/sti/tr/pdf/ADA452991.pdf)
[7](https://www.sciencedirect.com/science/article/abs/pii/S0952197624020086)
[8](https://www.nature.com/articles/s41598-018-20707-4)
[9](https://onlinelibrary.wiley.com/doi/10.1002/ijc.29089)
[10](https://www.nature.com/articles/s41598-020-75434-6)
[11](https://www.nature.com/articles/s41398-023-02614-z)
[12](https://www.nature.com/articles/s41467-022-28308-6)
[13](https://www.jcircadianrhythms.com/article/10.5334/jcr.203/)
[14](https://academic.oup.com/sleep/article/doi/10.1093/sleep/zsab146/6295924)
[15](https://www.nature.com/articles/srep08381)
[16](https://pubs.acs.org/doi/10.1021/acs.jafc.9b04869)
[17](https://www.tandfonline.com/doi/full/10.1080/09291016.2024.2333296)
[18](https://pmc.ncbi.nlm.nih.gov/articles/PMC6782369/)
[19](https://pmc.ncbi.nlm.nih.gov/articles/PMC7098792/)
[20](https://arxiv.org/pdf/1012.1521.pdf)
[21](https://physoc.onlinelibrary.wiley.com/doi/pdfdirect/10.1113/JP276943)
[22](https://pmc.ncbi.nlm.nih.gov/articles/PMC4528595/)
[23](https://pmc.ncbi.nlm.nih.gov/articles/PMC11725520/)
[24](https://pmc.ncbi.nlm.nih.gov/articles/PMC3557950/)
[25](https://www.saftefast.com/safte-fast-blog/dynamic-sleep-rhythm-amplitude)
[26](https://www.nature.com/articles/s41598-019-47290-6)
[27](https://pmc.ncbi.nlm.nih.gov/articles/PMC6002215/)
[28](https://pmc.ncbi.nlm.nih.gov/articles/PMC9453627/)
[29](https://pubmed.ncbi.nlm.nih.gov/29993295/)
[30](https://pubmed.ncbi.nlm.nih.gov/37914630/)
[31](https://fatiguescience.com/sleep-science-technology-2/)
[32](https://pmc.ncbi.nlm.nih.gov/articles/PMC1249488/)
[33](https://www.sciencedirect.com/science/article/pii/0031938495020314)
[34](https://pmc.ncbi.nlm.nih.gov/articles/PMC8832572/)
[35](https://physoc.onlinelibrary.wiley.com/doi/full/10.1113/JP276943)
[36](https://aasm.org/wp-content/uploads/2022/07/ProviderFS-ShiftWork.pdf)
[37](https://journals.sagepub.com/doi/full/10.1177/0748730418821776)