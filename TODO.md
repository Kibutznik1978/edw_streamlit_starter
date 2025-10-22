# Feature Development To-Do List

Here is a list of planned features to enhance the Pilot Scheduling Tools application.

## Phase 1: Core Analytics & Usability

- [ ] **Pay and Efficiency Metrics**
    - [ ] Add user input for hourly pay rate.
    - [ ] Calculate and display estimated monthly pay for each bid line.
    - [ ] Calculate and display per diem estimates for pairings.
    - [ ] Add "Credit-to-Block Ratio" (C/B Ratio) to pairings and lines.
    - [ ] Add "Pay-per-Duty-Day" (Credit/DD) to bid lines.

- [ ] **Layover Analysis**
    - [ ] Extract layover (rest) duration for each leg of a pairing.
    - [ ] Display layover statistics (min, max, average) for each pairing.
    - [ ] Add flags for "short rest" (<12h) and "long rest" (>24h) layovers.
    - [ ] Add flag for international or special layovers (if data is available).

- [ ] **Correlation Analysis**
    - [ ] Add an interactive scatter plot to the "Visuals" tab of the Bid Line Analyzer.
    - [ ] Allow users to select the X and Y axes from available metrics (e.g., CT vs. DO).

## Phase 2: Advanced Calendar & Pattern Analysis

- [ ] **Weekend and Holiday Analysis**
    - [ ] Enhance PDF parser to extract specific dates for all duty days and days off.
    - [ ] Add UI for users to define their weekend days (e.g., Sat/Sun).
    - [ ] Add UI for users to input key holiday dates.
    - [ ] Calculate and display "Weekends Off" for each bid line.
    - [ ] Flag lines that have specified holidays off.

- [ ] **Line Pattern and Rhythm Analysis**
    - [ ] Analyze the sequence of work days and days off for each line.
    - [ ] Calculate statistics on consecutive days on and off (max, average).
    - [ ] Develop a "Pattern" metric (e.g., "Regular", "Irregular", "Front-loaded", "Back-loaded").
