#!/usr/bin/env python3
"""Test reserve detection on a single block of text from the SDF PDF."""

from bid_parser import _detect_reserve_line

# This is the text from Line 1 in the SDF PDF (a regular bid line)
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

print("Testing reserve detection on Line 1 (regular bid line):")
print("="*80)
print(f"Block text:\n{sample_block}")
print("="*80)

is_reserve, is_hot_standby, captain_slots, fo_slots = _detect_reserve_line(sample_block)

print(f"\nResults:")
print(f"  is_reserve: {is_reserve}")
print(f"  is_hot_standby: {is_hot_standby}")
print(f"  captain_slots: {captain_slots}")
print(f"  fo_slots: {fo_slots}")

print(f"\n❌ PROBLEM: This should be False (not a reserve line) but got: {is_reserve}")

# Now test an actual reserve line (if we can find one in the PDF)
# For now, let's create a synthetic reserve line
reserve_block = """
SDF 999
1/2/0/
RA RA RA RA RA RA RA RA RA RA RA RA RA RA
CT: 0:00
BT: 0:00
DO: 17
DD: 14
"""

print(f"\n\nTesting reserve detection on synthetic reserve line:")
print("="*80)
print(f"Block text:\n{reserve_block}")
print("="*80)

is_reserve2, is_hot_standby2, captain_slots2, fo_slots2 = _detect_reserve_line(reserve_block)

print(f"\nResults:")
print(f"  is_reserve: {is_reserve2}")
print(f"  is_hot_standby: {is_hot_standby2}")
print(f"  captain_slots: {captain_slots2}")
print(f"  fo_slots: {fo_slots2}")

print(f"\n✓ This should be True (reserve line): {is_reserve2}")
