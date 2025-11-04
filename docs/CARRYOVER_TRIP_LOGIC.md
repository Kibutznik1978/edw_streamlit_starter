# Carryover Trip Logic

**Purpose**: Documents how carryover trips (trips spanning pay period boundaries) are handled in bid line PDFs.

**Source**: Article 12.B.3.h. and Article 12.B.3.i. of the collective bargaining agreement.

---

## Definition

A **carryover trip** (also called a **transition trip**) is a trip that begins in one bid period and ends in the following bid period.

---

## Credit Time (CT) and Block Time (BT) Splitting

The methodology for splitting pay and credit depends on the crewmember's **status at the exact start time of the new pay period**:

### Scenario 1: On Layover Rest at Transition

If the trip is on layover rest at the start time of the next pay period:

- **Departing Pay Period**: Pay and credit for the portion of the trip in the departing pay period will be calculated in accordance with the Agreement.
- **Inbound Pay Period**: The remaining pay and credit of the trip will be applied to the next (inbound) pay period.

### Scenario 2: Duty Period in Progress at Transition

If a duty period within the trip is in progress at the start time of the next pay period:

- **Departing Pay Period**: Pay and credit for the portion of the trip in the departing pay period will be calculated up to the point the crewmember is released for rest.
- **Inbound Pay Period**: Remaining pay and credit for the trip will be applied to the next (inbound) pay period.

### Guarantee Protection

In both scenarios above, pay and credit applied for the trip to the departing pay period will in no event be less than what was scheduled to be paid and credited.

---

## Duty Day (DD) Calculation

The calculation for splitting the associated duty days across the bid periods is as follows:

1. **Departing Bid Period**: The number of duty days applied will be the sum of the duty days plus any partial duty day calculated up to the start time of the next bid period.

2. **Next (Inbound) Bid Period**: The number of duty days applied will be the total number of duty days in the trip less the number of duty days applied to the prior (departing) bid period.

---

## Days Off (DO) Calculation

Days off are assigned to the pay period in which they occur based on the calendar dates.

---

## Parser Implementation

### ✅ Pre-Calculated Values in PDF

**CRITICAL**: The bid line PDF already shows the pre-calculated split credits for carryover trips in each pay period summary.

The parser does **NOT** need to:
- Identify carryover trips
- Access full pairing details
- Apply Article 12.B.3 rules to calculate the split

The parser **DOES** need to:
- Extract the displayed CT, BT, DO, DD values from each pay period summary as-is
- Trust that the scheduling system has already applied the carryover split logic

### Example Carryover Trip on Bid Line

```
Line 2015 (Captain)

PP1 2513 Calendar:
28 | 29 | 30 | 31
   |    |    | Trip 156 (starts 31st, 1830 report)
                14:28 credit
                LAS

PP1 Summary:
CT: 14:28, BT: 11:15, DO: 27, DD: 1

PP2 2601 Calendar:
1  | 2  | 3  | 4
156|    |    |    (trip continues from PP1)
LAS|    |    |

PP2 Summary:
CT: 10:32, BT: 8:45, DO: 1, DD: 3
```

In this example:
- Trip 156 starts on Dec 31 (PP1) and ends on Jan 3 (PP2)
- PP1 gets: 14:28 CT, 11:15 BT, 1 DD (partial day on Dec 31)
- PP2 gets: 10:32 CT, 8:45 BT, 3 DD (Jan 1-3)
- Total trip credit: 25:00 (14:28 + 10:32)
- Parser extracts values as shown, no calculation needed

---

## Related Documentation

- `PAIRING_AND_LINE_REFERENCE.md` - Main parsing reference
- `EXCLUSION_LOGIC.md` - Reserve and VTO exclusion logic
- `bid_parser.py` - Bid line parser implementation
- Article 12.B.3.h. and 12.B.3.i. - Collective bargaining agreement

---

## Version History

- **v1.0** (November 3, 2025): Initial documentation based on contract Article 12.B.3
  - Documented credit time splitting rules (layover rest vs duty in progress)
  - Documented duty day calculation rules
  - Clarified that PDF shows pre-calculated values (parser doesn't calculate)
