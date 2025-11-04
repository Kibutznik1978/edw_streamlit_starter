#!/usr/bin/env python3
"""Debug reserve detection logic."""

import re
from config import RESERVE_DAY_KEYWORDS, SHIFTABLE_RESERVE_KEYWORD

# Build regex patterns from config
_RESERVE_DAY_PATTERN_RE = re.compile(r"\b(" + "|".join(RESERVE_DAY_KEYWORDS) + r")\b", re.IGNORECASE)
_SHIFTABLE_RESERVE_RE = re.compile(re.escape(SHIFTABLE_RESERVE_KEYWORD), re.IGNORECASE)
_HOT_STANDBY_RE = re.compile(r"\b(HSBY|HOT\s*STANDBY|HOTSTANDBY)\b", re.IGNORECASE)

# Test block from Line 1 (regular bid line)
sample_block = """
SDF 1 Sun Mon Tue Wed Thu Fri Sat Sun Mon Tue Wed Thu Fri Sat Sun Mon Tue Wed Thu Fri Sat Sun Mon Tue Wed Thu Fri Sat - Mon
1/1/0/ 30 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 - 29
BL PP1 (2513) 1234 1815 1849 902 898 949 958 983 997 997 997 1059 1094 723 1094 724
CT: 80:01 MHT PDX BIL BHM SAN SAV ONT BHM
1845 1959 0006 2048 0829 0829 0705 0938 0826 0826 0826 0826 0726 0751 0726 0751
BT: 43:12
9:19 31:56 32:46 6:00 6:00 6:00 6:00 6:00 6:00 6:00 6:00 6:10 6:52 6:00 6:52 6:00
DO: 13
DD: 14
"""

print("Debugging reserve detection on Line 1:")
print("="*80)

# Check Hot Standby
is_hot_standby = bool(_HOT_STANDBY_RE.search(sample_block))
print(f"is_hot_standby: {is_hot_standby}")

# Check reserve days
has_reserve_days = bool(_RESERVE_DAY_PATTERN_RE.search(sample_block))
print(f"has_reserve_days: {has_reserve_days}")
if has_reserve_days:
    match = _RESERVE_DAY_PATTERN_RE.search(sample_block)
    print(f"  Matched: '{match.group()}' at position {match.start()}")
    print(f"  Context: '{sample_block[max(0, match.start()-20):match.end()+20]}'")

# Check shiftable reserve
has_shiftable_reserve = bool(_SHIFTABLE_RESERVE_RE.search(sample_block))
print(f"has_shiftable_reserve: {has_shiftable_reserve}")

# Check CT/BT patterns
ct_zero = re.search(r"CT\s*:?\s*0+[:\.]0+", sample_block, re.IGNORECASE)
bt_zero = re.search(r"BT\s*:?\s*0+[:\.]0+", sample_block, re.IGNORECASE)
dd_fourteen = re.search(r"DD\s*:?\s*14\b", sample_block, re.IGNORECASE)

print(f"ct_zero: {ct_zero}")
print(f"bt_zero: {bt_zero}")
print(f"dd_fourteen: {dd_fourteen}")
if dd_fourteen:
    print(f"  DD:14 matched: '{dd_fourteen.group()}'")

has_zero_credit_block = bool(ct_zero and bt_zero)
has_reserve_metrics = has_zero_credit_block or (ct_zero and dd_fourteen) or (bt_zero and dd_fourteen)

print(f"has_zero_credit_block: {has_zero_credit_block}")
print(f"has_reserve_metrics: {has_reserve_metrics}")

# Final calculation
is_reserve = has_reserve_days or has_shiftable_reserve or has_reserve_metrics
print(f"\n>>> is_reserve: {is_reserve} (type: {type(is_reserve)})")

print(f"\n{'='*80}")
print(f"Reserve keywords being checked: {RESERVE_DAY_KEYWORDS}")
