# Bid Sorter Implementation Plan

## Goal
Transform the existing bid-line and pairing parsers into a unified bid-sorting workflow. The sorter will let pilots combine their line assignments with pairing-level intelligence, then filter or prioritize results by criteria such as layovers, credit/block, EDW exposure, and custom day vs night flying rules.

---

## Current Inputs & Capabilities

### Bid Line Parser (`parse_bid_lines`)
- Extracts line-level metrics (Line, CT, BT, DO, DD) with per-pay-period details.
- Detects reserve lines and buy-up style lines via CT/BT patterns.
- Leaves the comment block (daily schedule text) unparsed.

### Pairing Parser / EDW Analyzer (`parse_pairings`, `parse_trip_for_table`)
- Splits pairing PDFs into individual trip texts keyed by Trip ID.
- Provides duty-day breakdowns with local departure/arrival times, block, credit, rest (layover) data, leg lists, EDW flags, and trip summaries.
- Already maps Trip ID → raw text for downstream display.

### Key Insight
We already have the trip-level metadata needed for sorting (times, layovers, duty-day structure). The missing link is parsing the bid-line daily schedule so we can map each line to the Trip IDs it contains, then join on the trip catalog.

---

## Target Data Model

### Entities
1. **Trip Catalog** (per pairing PDF)
   - `trip_id`, `frequency`, `edw_flag`, `duty_days[]`, `layovers[]` (location + duration), `credit_hours`, `block_hours`, `duty_hours`, `leg_count`, `hot_standby`, `safte_metrics` (already produced), plus cached local departure/arrival times per leg.
2. **Line Assignments** (per bid-line PDF)
   - One record per line, per pay period segment:
     - `line_id`, `pay_period`, `ct_hours`, `bt_hours`, `do_days`, `dd_days`, reserve flags, comment text.
   - **New child table:** `line_days`
     - `line_id`, `pay_period`, `day_index` (within PP), `status` (`trip`, `day_off`, `training`, `reserve`, etc.), `trip_id` (if trip day), `position` (Captain/FO slots when available), `raw_label` (e.g., “OFF”, “DH GT”, “ATC”), `is_layover_bridge` (when a trip spans multiple days but the line shows layover text).
3. **Merged Line Summary**
   - `line_id`, aggregated metrics referenced for sorting: total credit/block, credit-to-block ratio, EDW duty count, day/night block totals under user-configurable thresholds, longest layover, preferred layover city flags, consecutive duty stretches, percent reserve, etc.

### Matching Rules
- Require shared bid identifier (e.g., `ONT2507`) between the uploaded pairing and bid-line PDFs. Reject mismatches early.
- Map Trip IDs from line schedules to the Trip Catalog; if missing, flag diagnostics for UI display.
- Allow multiple Trip IDs per line day (e.g., split duties) while keeping order for future prioritization logic.

---

## Parser Enhancements Needed

### Bid Line Parser
1. **Comment Block Extraction**
   - Extend `_parse_block_text` (or add helper) to capture the schedule section following `Comment:` up to the next line header.
   - Normalize whitespace and fix OCR artifacts similar to existing numeric cleanups.
2. **Line-Day Tokenizer**
   - Detect day markers (`01`, `02`, etc.) and status codes (OFF, AL, VAC, TRNG, RES, trip numbers).
   - Support overlapping fonts/spacing by using regex tolerant of extra spaces and broken words.
3. **Trip Identification**
   - Recognize trip references (`T1234`, raw numeric `1234`, or `TRIP 1234`) consistent with pairing PDF Trip IDs.
   - Handle suffixes (e.g., `-A`, `-B`) if present.
4. **Status Classification**
   - Tag days as `trip`, `off`, `reserve`, `training`, `vacation`, etc., using code dictionaries.
   - Capture partial-day annotations (e.g., `1/2 OFF`, `GT`, `DH`). These feed future prioritization.
5. **Output Structure**
   - Return `line_days` alongside existing summary DataFrame; include in diagnostics for UI debugging.

### Pairing Parser / Trip Catalog
1. **Expose Layover Metadata**
   - From `parse_trip_for_table`, extract location and rest duration per duty transition into a normalized `layovers[]` list.
2. **Leg-Level Time Buckets**
   - Ensure each flight record uses both local departure and arrival times (already parsed). Provide helper to convert to `datetime` placeholders (HH:MM + local offset) so the UI can compare against user day/night thresholds.
3. **Auxiliary Flags**
   - Compute per-duty-day attributes: first departure local hour, last arrival hour, overnight rest length. Store in Trip Catalog for quick summarization.
4. **Caching**
   - Consider caching parsed trip data (in session state) to avoid reprocessing when the user adjusts filters.

---

## Data Fusion Pipeline

1. **Bid Identifier Validation**
   - Extract `bid_period`, `domicile`, `fleet` from both PDFs (already implemented) and confirm they match.
2. **Parse Inputs**
   - Run pairing parser → Trip Catalog.
   - Run bid-line parser → line summary + `line_days` frame + diagnostics.
3. **Map Line Days to Trips**
   - For each `line_day` tagged as `trip`, look up Trip ID in catalog; if not found, log mismatch with raw token for UI.
   - Track multi-day trips by linking consecutive days until the trip end (use trip frequency + duty day count to validate completeness).
4. **Aggregate Metrics**
   - Compute per-line totals using Trip Catalog data:
     - Credit/Block sums (respect pay-period splits).
     - Day/Night hours using user-defined local time thresholds on flight legs or duty windows.
     - EDW duty counts based on existing `edw_flag` per trip day.
     - Layover stats (longest duration, list of cities, short-rest flags).
     - Consecutive day-off windows, duty stretches, reserve-day counts.
5. **Prioritization Scaffolding**
   - Store multi-criteria score fields (initialized later) so future “prioritize multiple options” logic can assign weights.
6. **Outputs**
   - `line_summary` DataFrame (one row per line) ready for sorting/filtering.
   - `line_days` detail view for transparency.
   - Diagnostics object noting unmatched trips, ambiguous codes, odd CT/BT discrepancies.

---

## Bid Sorting UI & UX

1. **Upload Flow**
   - Require two files: Pairing PDF + Bid Line PDF. Validate matching headers before enabling parsing.
2. **Configuration Panel**
   - User inputs for day/night thresholds (e.g., Day begins HH:MM, Day ends HH:MM).
   - Toggle for EDW vs Non-EDW lines (filter by EDW duty count > 0).
   - Additional filters: minimum days off, target layover duration, exclude specific layover cities, credit/block ranges (reuse existing sliders).
3. **Sorting Controls**
   - Columns clickable for sorting; provide preset buttons (e.g., “Long layovers first”, “High credit day-flying”).
   - Leave hook for multi-criteria prioritization (e.g., choose priority order of metrics) to tackle later.
4. **Results Display**
   - Summary table with expandable rows showing matched trips and day-level breakdown.
   - Diagnostics badge when trips are missing or ambiguous.
   - Download options (CSV/PDF) reflecting the new metrics.
5. **Performance Considerations**
   - Cache parsed catalogs while only reapplying filters when thresholds change.
   - Use progress indicators similar to existing tabs.

---

## Validation & Testing Strategy

1. **Unit Tests**
   - New fixtures derived from sample PDFs (scrubbed text snippets) for bid-line comment parsing.
   - Tests for day/night classification helper functions.
   - Trip linkage tests ensuring known lines map to expected Trip IDs.
2. **Integration Tests**
   - Script that runs end-to-end parse + merge on provided `test_data` PDFs, asserting line counts, basic metrics, and absence of missing Trip IDs.
3. **Manual QA**
   - Spot-check: select representative lines (day-heavy, night-heavy, reserve-heavy) against source PDFs via raw text view.
   - Validate day/night thresholds by toggling UI values and verifying counts adjust predictably.
4. **Regression Guardrails**
   - Add diagnostics panel in UI showing unmatched trips/reserve anomalies so issues surface quickly.

---

## Milestones

1. **Parser Foundation** (Bid-line comment parser + Trip catalog exposure).
2. **Data Model & Merge Layer** (line_days table, trip linkage, aggregate metrics).
3. **UI Rollout** (dual upload workflow, filter controls, results table).
4. **Testing & QA** (unit/integration tests, documentation updates).
5. **Prioritization Enhancements** (multi-option scoring, presets) — scheduled after core functionality proves stable.

---

## Future Enhancements (Post-MVP)
- Multi-criteria prioritization engine (weighted scoring, tie-breakers).
- User-defined layover city preferences and avoid lists.
- Calendar export for selected lines/trips.
- Persist user filter presets via optional Supabase integration.
- Deeper analytics: fatigue scoring overlays, SAFTÉ insights per line.

