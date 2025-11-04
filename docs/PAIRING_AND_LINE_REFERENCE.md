# Pairing and Line Reference Guide

**Purpose**: This document provides detailed explanations of pairing and bid line structures to aid parser development and debugging.

**Source**: Based on "CREW RESOURCES Pairing and Line Examples.pdf"

---

## Table of Contents

1. [Pairing Structure](#pairing-structure)
2. [Bid Line Structure](#bid-line-structure)
3. [Special Line Types](#special-line-types)
4. [Parsing Considerations](#parsing-considerations)
5. [Common Patterns](#common-patterns)

---

## Pairing Structure

### Key Components

#### Header Information
- **Trip Id**: Unique pairing identifier (e.g., Trip Id: 2, Trip Id: 246)
- **Lines**: Comma-separated list of bid lines containing this pairing (e.g., "Lines: 2000")
- **Operates**: Date range for pairing operation (e.g., "Only on Tue 08Sep2020")

#### Flight Details
- **Day**: Day of week (e.g., "1 (Tu)Tu" = Day 1, Tuesday-Tuesday)
- **Flight**: Flight number or special code
  - Regular flights: "UPS9707", "UPS 328"
  - **Deadhead (DH)**: Non-revenue positioning (e.g., "DH AA5277-2")
  - **Ground Transport**: "GT N/A BUS G" = ground shuttle/bus
- **Departure-Arrival**: City pairs (e.g., "SDF-JFK", "ORD-PHL")
- **Start/End Times**: Local times with timezone indicator
  - Format: "(HH)MM:SS" where HH in parentheses is local hour
  - Example: "(02)06:49" = 2:06:49 AM local time
- **Block Time**: Actual flight time (e.g., "1h52", "2h11")
- **A/C**: Aircraft type (e.g., "A30", "73W")

#### Connection and Ground Time
- **Cxn**: Connection/ground time between segments
- **Briefing**: Report time before first flight (e.g., "1h00")
- **Debriefing**: Release time after last flight (e.g., "0h15", "0h30")

#### Crew Requirements
- **Leg Need**: Crew complement needed
  - Format: "X/Y/Z" = Captain/First Officer/Flight Engineer
  - Example: "1/1/0" = 1 Captain, 1 FO, 0 FE
  - "0/0/0" = Deadhead or ground transport (no crew needed)

#### Special Indicators
- **(C)**: Catered segment (meal service provided) - **being phased out**
- **GS** or **GT N/A BUS G**: Ground shuttle/transport

### Duty Summary (Per Duty Period)

Each duty period has its own summary:
- **Duty**: Total duty time (report to release)
- **Block**: Sum of block times for all segments
- **Rest**: Rest period before next duty (e.g., "23h10 S1" = 23:10 Split Duty 1)
- **Credit**: Credit for THIS DUTY PERIOD ONLY
  - Could be actual block time
  - Could be MPDP (Minimum Pay Per Duty Period) = 4h00
  - Could be duty rig calculation (e.g., "4h28D" = duty rig, "4h00M" = minimum)

### Trip Summary (Entire Pairing)

Summary for the complete trip across all duty days:
- **Crew**: Crew complement for trip (e.g., "1/1/0")
- **Domicile**: Home base (e.g., "SDF", "ONT")
- **Duty Time**: Total duty time across all duty periods
- **Block Time**: Total block time
- **Credit Time**: **FINAL PAY CREDIT FOR ENTIRE TRIP**
  - Sum of all duty period credits OR trip rig, whichever is higher
  - This is the value used for pay calculation
- **TAFB**: Time Away From Base (total elapsed time)
- **Premium**: Additional pay (e.g., international, special duty)
- **per Diem**: Per diem payment
- **LDGS**: Number of landings

---

## Bid Line Structure

### Line Header Format

```
SDF 2002 | Sun | Mon | Tue | Wed | Thu | Fri | Sat
1/1/0/   | 6   | 7   | 8   | 9   | 10  | 11  | 12  ...
```

- **Domicile**: Base airport (SDF, ONT, etc.)
- **Line Number**: Unique bid line identifier
- **Seat/Crew**: Seat position and times awarded (e.g., "1/1/0/" = Captain/FO/FE)
- **Calendar Grid**: Days of the month with pairing assignments

### Pay Period Summary

Each line shows two pay periods:

**PP1 (2010)** - First pay period:
- **CT**: Credit Time for entire pay period
- **BT**: Block Time for entire pay period
- **DO**: Days Off
- **DD**: Duty Days

**PP2 (2011)** - Second pay period:
- Same metrics as PP1

### Calendar Details

For each pairing instance on the calendar:
- **Pairing Number**: Trip ID (e.g., "179")
- **Report Time**: Local report time for first day (e.g., "0244" = 02:44)
- **Credit Time**: Credit for this pairing (e.g., "25:19")
- **Layover Cities**: Where crew stays overnight (e.g., "LAS", "TPA", "BOI")

### Comment Section

Special notes about the line (e.g., "Shiftable Reserve", "VTO Line", "VTOR Line")

---

## Special Line Types

### 1. Reserve Lines

**Types** (based on availability/report times):
- **RA, RB, RC, RD**: Regular reserve with different availability windows (A, B, C, D)
- **SA, SB, SC, SD**: Shiftable reserve (can be moved per contract rules)

**Characteristics**:
- **CT**: 0.00 (no guaranteed credit)
- **BT**: 0.00 (no block time)
- **DO**: 14 (typically half month off)
- **DD**: 14 (typically half month on reserve)
- Calendar shows "RA", "SA", etc. on reserve days

**Parser Implications**:
- Reserve lines should be **excluded from main DataFrame** (skews averages)
- Track in diagnostics for Captain/FO slot counts
- Check for: `(CT == 0) AND (BT == 0) AND (DD == 14)` AND NOT VTO line

### 2. VTO / VTOR / VOR Lines

**VTO (Vacation, Training, Other)**:
- Built from leftover trips due to vacation/training/other events
- Can ONLY contain regular flying trips
- **CT/BT**: Varies based on trips assigned
- **DO**: 0 (no guaranteed days off)
- **DD**: 28 (or full month)
- Calendar shows "VTO" on all days

**VTOR / VOR (Vacation, Training, Other, or Reserve)**:
- Same as VTO but can ALSO include reserve days
- More flexible - mix of trips and reserve assignments
- **CT/BT**: Varies
- **DO**: 0
- **DD**: 28
- Calendar shows "VTOR" or "VOR" on all days

**Split VTO/VTOR Lines** (COMMON in final bid packets):
- One pay period: Regular flying (normal CT, BT, DO, DD)
- Other pay period: VTO/VTOR (CT:0, BT:0, DO:0, DD:28)
- **Parser Logic**: Include regular pay period in averages, exclude VTO period
- Example:
  ```
  PP1: CT:72.23, BT:54.20, DO:11, DD:12 (REGULAR - include)
  PP2: CT:0.00, BT:0.00, DO:0, DD:28 (VTO - exclude)
  ```

### 3. Gateway Airport Standby (Hot Standby)

**SBG1 (Stand By Gateway 1)**:
- Hot standby at non-domicile airport (e.g., PHL for SDF crew)
- Part of longer trip requiring positioning to/from gateway
- Has defined start and end times (like regular hot standby)
- Requires deadhead flights to reach gateway and return home

**Structure**:
- Day 1: Deadhead to gateway (e.g., SDF-PHL)
- Days 2-7: Hot standby duty at gateway ("SBG1" shown on calendar)
- Day 8: Deadhead return (e.g., PHL-SDF)

**Credit Calculation**:
- Each standby duty period: Often credited at minimum (e.g., "5h30M")
- Rest periods between standby days (e.g., "15h00", "16h00", "22h40")
- Total trip credit: Sum of all duty credits

---

## Parsing Considerations

### EDW (Early/Day/Window) Detection

**Current Logic**: Trip is EDW if ANY duty day touches 02:30-05:00 local time (inclusive)

**Examples from PDF**:

1. **EDW Turn Example (Trip Id: 2)**:
   - Briefing: (02)06:49 - BEFORE window close
   - First flight departure: (03)07:43 - WITHIN EDW window
   - Result: **EDW trip**

2. **EDW Layover Example (Trip Id: 246)**:
   - Day 1 briefing: (18)22:55 - outside window
   - Day 1 last flight: (20)01:05 - outside window
   - Day 2 briefing: (21)02:00 - outside window
   - Day 2 first flight: (22)03:00 - WITHIN EDW window
   - Result: **EDW trip** (Day 2 touches window)

3. **International Example (Trip Id: 1238)**:
   - Day 1: (13)17:55 to (19)23:26 - outside window
   - Day 2: (19)23:12 to (01)05:21 - outside window
   - Result: **NOT EDW** (neither duty day touches 02:30-05:00)

### Credit Time Parsing

**Two Different Values to Parse**:

1. **Duty Summary → Credit**: Credit for single duty period
   - Format: "4h28D" (duty rig), "4h00M" (minimum), "6h41" (actual)
   - Location: Under each duty day

2. **Trip Summary → Credit Time**: FINAL TRIP PAY CREDIT
   - Format: "6h00M", "9h27T", "8h10" (hours:minutes + optional rig indicator)
   - Location: Right column, "Trip Summary" section
   - **This is the value to use for pay calculations**

**Rig Indicators**:
- **M**: Minimum (MPDP = 4h00 for duty, varies for trip)
- **D**: Duty rig calculation
- **T**: Trip rig calculation
- **L**: Likely another rig type
- **No suffix**: Actual block time or sum of duty credits

### Header Extraction

**Key Fields to Extract**:
- **Bid Period**: From "Operates: Only on [date]" or explicit header
- **Domicile**: From line header (e.g., "SDF 2002")
- **Fleet/Aircraft**: From A/C column (e.g., "A30", "73W", "757")
- **Date Range**: From "Operates" field or pay period headers

**Multi-Page Headers**:
- Header may appear on page 1, 2, 3, 4, or 5 (cover pages common)
- Parser should check up to 5 pages to find header
- Look for patterns: "Bid Period", "Domicile", "Fleet", date ranges

### Reserve Line Detection

**Boolean Logic Fix** (Session 32):
- Always wrap boolean expressions in `bool()` to prevent `None` propagation
- **Incorrect**: `ct_zero and dd_fourteen` (returns None if ct_zero is None)
- **Correct**: `bool(ct_zero and dd_fourteen)` (returns False if ct_zero is None)

**Detection Logic**:
1. Check for VTO/VTOR first (early return to avoid false positives)
2. Check for reserve pattern: `(CT == 0) AND (BT == 0) AND (DD == 14)`
3. Extract reserve type from Comment field or calendar cells
4. Count Captain vs FO slots based on seat column

**Exclusion Logic**:
- Regular reserve lines (RA, RB, RC, RD, SA, SB, SC, SD): **Exclude from main data**
- Hot standby lines (HSBY): **Include in main data** (has real CT/BT/DO/DD)
- Track reserve lines in diagnostics only

### VTO/VTOR Split Line Handling

**Detection Logic**:
1. Parse both pay periods independently
2. Check each period for VTO keywords in Comment or calendar
3. Determine which period is regular vs VTO
4. Include regular period data in main DataFrame
5. Set VTOType and VTOPeriod fields for tracking

**Example Split Line**:
```python
{
  'Line': 2008,
  'PP1_CT': 72.23, 'PP1_BT': 54.20, 'PP1_DO': 11, 'PP1_DD': 12,  # Regular
  'PP2_CT': 0.00, 'PP2_BT': 0.00, 'PP2_DO': 0, 'PP2_DD': 28,      # VTO
  'VTOType': 'Split - PP2 VTO',
  'VTOPeriod': 'PP2'
}
```

**Aggregated Values** (what goes in main data):
- **CT**: 72.23 (from PP1 only)
- **BT**: 54.20 (from PP1 only)
- **DO**: 11 (from PP1 only)
- **DD**: 12 (from PP1 only)

---

## Common Patterns

### Turn Trip (Single Day Trip)

**Example**: Trip Id: 2 (EDW Turn Example)
- **Days**: 1 duty day
- **Structure**: SDF → JFK → SDF (out and back same day)
- **Timing**: Early morning departure (02:06 brief, 03:07 departure)
- **TAFB**: Short (6h41 - same as duty time)
- **Characteristics**:
  - Single duty period
  - No layover/rest period
  - Duty time = TAFB
  - Common for EDW detection (early briefing times)

### Multi-Day Layover Trip

**Example**: Trip Id: 246 (EDW Layover Example)
- **Days**: 3 duty days across 4 calendar days (Su, Mo, Tu, Tu)
- **Structure**:
  - Day 1: SDF → MDW → ORD (layover in ORD)
  - Day 2: ORD → PHL (layover in PHL)
  - Day 3: PHL → MHT → SDF (return home)
- **Rest Periods**: 23h10 S1 (split duty rest)
- **TAFB**: 37h32 (much longer than duty time)
- **Characteristics**:
  - Multiple duty periods with layovers
  - Rest periods between duties
  - May include ground shuttles or deadheads
  - Higher per diem due to overnights

### International Trip

**Example**: Trip Id: 1238 (International Example)
- **Days**: 2 duty days (Th, Fr)
- **Structure**:
  - Day 1: SDF → SJU (international) - layover
  - Day 2: SJU → SDF (return)
- **Characteristics**:
  - "(C)" catered segments (being phased out)
  - Longer TAFB (35h26)
  - Higher premium pay (102.30)
  - Higher per diem (125.76)
  - May cross multiple time zones

### Hot Standby Trip

**Example**: Trip Id: 9000 (Gateway Airport Standby)
- **Days**: 8 duty days
- **Structure**:
  - Day 1: DH to gateway (SDF → PHL)
  - Days 2-7: Standby duty ("SBG1") at PHL
  - Day 8: DH return (PHL → SDF)
- **Credit**: Minimum pay per standby period (5h30M each)
- **Rest**: Regular rest periods between standbys (15h00-22h40)
- **Characteristics**:
  - Requires positioning flights (deadheads)
  - Fixed duty windows at non-domicile airport
  - Crew on-call during standby windows
  - May be used to cover irregular operations

---

## Quick Reference Tables

### Reserve Line Patterns

| Type | Prefix | Meaning | Characteristics |
|------|--------|---------|----------------|
| RA   | R      | Regular Reserve A | Fixed availability window A |
| RB   | R      | Regular Reserve B | Fixed availability window B |
| RC   | R      | Regular Reserve C | Fixed availability window C |
| RD   | R      | Regular Reserve D | Fixed availability window D |
| SA   | S      | Shiftable Reserve A | Movable window A |
| SB   | S      | Shiftable Reserve B | Movable window B |
| SC   | S      | Shiftable Reserve C | Movable window C |
| SD   | S      | Shiftable Reserve D | Movable window D |

**Common Values**: CT:0.00, BT:0.00, DO:14, DD:14

### VTO Line Patterns

| Type | Full Name | Can Include Regular Trips? | Can Include Reserve? | Common in Final Bid? |
|------|-----------|---------------------------|---------------------|---------------------|
| VTO  | Vacation/Training/Other | Yes | No | Yes (split lines common) |
| VTOR | Vacation/Training/Other/Reserve | Yes | Yes | Yes (split lines common) |
| VOR  | Same as VTOR | Yes | Yes | Yes (split lines common) |

**Split Line Values** (one period regular, one VTO):
- Regular period: Normal CT/BT/DO/DD → **Include in averages**
- VTO period: CT:0, BT:0, DO:0, DD:28 → **Exclude from averages**

### Credit Time Suffixes

| Suffix | Meaning | Context |
|--------|---------|---------|
| M | Minimum | Minimum pay guarantee applied |
| D | Duty Rig | Duty rig calculation used |
| T | Trip Rig | Trip rig calculation used |
| L | (Unknown) | Likely another rig type |
| (none) | Actual | Actual block/sum of credits |

---

## Parser Testing Checklist

When testing parser improvements, verify:

### Pairing Parsing
- [ ] EDW detection works for turn trips (early briefing)
- [ ] EDW detection works for layover trips (any duty day in window)
- [ ] Non-EDW international trips excluded correctly
- [ ] Deadhead (DH) flights parsed correctly
- [ ] Ground shuttles (GT N/A BUS G) parsed correctly
- [ ] Credit Time extracted from Trip Summary (not Duty Summary)
- [ ] TAFB, Premium, per Diem extracted correctly
- [ ] Multiple duty periods handled (rest periods tracked)
- [ ] Local time extraction works (parentheses around hour)
- [ ] Catered segment indicator "(C)" handled

### Bid Line Parsing
- [ ] Header extraction works with cover pages (checks up to 5 pages)
- [ ] Both pay periods parsed correctly (PP1 and PP2)
- [ ] Reserve lines detected and excluded from main data
- [ ] Reserve slots counted correctly (Captain vs FO)
- [ ] VTO/VTOR full-month lines excluded
- [ ] Split VTO lines handled (regular period included, VTO excluded)
- [ ] VTOType and VTOPeriod fields populated
- [ ] Hot standby lines (HSBY) included in main data
- [ ] Boolean logic uses `bool()` wrapper (no None propagation)
- [ ] Comment section parsed for special line notes

### Data Validation
- [ ] No NaN values in distribution charts (causes memory errors)
- [ ] CT/BT averages exclude reserve and VTO periods
- [ ] DO/DD counts exclude reserve and VTO periods
- [ ] Line counts accurate (regular lines only)
- [ ] Pay period breakdown shows correct distributions

---

## Version History

- **v1.0** (October 31, 2025): Initial version based on CREW RESOURCES PDF
  - Documented pairing structure, bid line structure, special line types
  - Added reserve detection logic and VTO/VTOR handling
  - Included parsing considerations and common patterns
  - Added quick reference tables and testing checklist

---

## Related Documentation

- `CLAUDE.md` - Main project documentation
- `EXCLUSION_LOGIC.md` - Reserve and VTO exclusion logic details
- `handoff/sessions/session-32.md` - Reserve line detection bug fixes
- `handoff/sessions/session-31.md` - Older PDF format compatibility
- `edw/parser.py` - EDW pairing parser implementation
- `bid_parser.py` - Bid line parser implementation
