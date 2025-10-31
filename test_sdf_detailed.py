#!/usr/bin/env python3
"""Detailed analysis of SDF parsing - VTO and Reserve line handling."""

from bid_parser import parse_bid_lines
import pandas as pd

pdf_path = "/Users/giladswerdlow/Desktop/2601/SDF/BidLinePrint_BID2601_757_SDF.pdf"

print("Parsing SDF PDF...")
with open(pdf_path, 'rb') as pdf_file:
    df, diagnostics = parse_bid_lines(pdf_file)

print(f"\n{'='*80}")
print(f"PARSED DATA ANALYSIS")
print(f"{'='*80}")

print(f"\nTotal lines in parsed DataFrame: {len(df)}")
print(f"Line number range: {df['Line'].min()} - {df['Line'].max()}")

# Check for VTO lines in parsed data
if 'VTOType' in df.columns:
    vto_lines = df[df['VTOType'].notna()]
    print(f"\nVTO/VOR lines in parsed data: {len(vto_lines)}")
    if len(vto_lines) > 0:
        print(f"VTO line numbers: {vto_lines['Line'].tolist()[:10]}...")
        print(f"VTO types: {vto_lines['VTOType'].unique().tolist()}")
else:
    print("\n⚠️  No VTOType column in parsed data")

# Check line number gaps
all_lines = sorted(df['Line'].unique())
print(f"\nLine number analysis:")
print(f"  Unique lines: {len(all_lines)}")
print(f"  First 10: {all_lines[:10]}")
print(f"  Last 10: {all_lines[-10:]}")

# Find gaps in line numbers
gaps = []
for i in range(len(all_lines) - 1):
    if all_lines[i+1] - all_lines[i] > 1:
        gap_start = all_lines[i] + 1
        gap_end = all_lines[i+1] - 1
        gaps.append((gap_start, gap_end))

if gaps:
    print(f"\n⚠️  Line number gaps found:")
    for gap_start, gap_end in gaps[:5]:  # Show first 5 gaps
        print(f"     Missing lines {gap_start}-{gap_end} ({gap_end - gap_start + 1} lines)")

print(f"\n{'='*80}")
print(f"RESERVE LINE ANALYSIS")
print(f"{'='*80}")

if diagnostics.reserve_lines is not None:
    reserve_df = diagnostics.reserve_lines

    # Actual reserve lines (IsReserve=True)
    actual_reserves = reserve_df[reserve_df['IsReserve'] == True]
    print(f"\nReserve lines detected (IsReserve=True): {len(actual_reserves)}")
    print(f"Reserve line numbers: {sorted(actual_reserves['Line'].tolist())}")

    # Check if reserve lines are in main DataFrame
    reserve_line_nums = set(actual_reserves['Line'].tolist())
    lines_in_df = df[df['Line'].isin(reserve_line_nums)]

    print(f"\nReserve lines in main DataFrame: {len(lines_in_df)}")
    if len(lines_in_df) > 0:
        print(f"❌ PROBLEM: Reserve lines should NOT be in main DataFrame!")
        print(f"   These will be included in averages!")
        print(f"   First 5 reserve lines in data:")
        print(lines_in_df[['Line', 'CT', 'BT', 'DO', 'DD']].head())

print(f"\n{'='*80}")
print(f"SAMPLE DATA")
print(f"{'='*80}")

print(f"\nFirst 5 lines:")
print(df[['Line', 'CT', 'BT', 'DO', 'DD']].head())

print(f"\nLast 5 lines:")
print(df[['Line', 'CT', 'BT', 'DO', 'DD']].tail())

# Check if line 264 (first VTO) is in data
if 264 in df['Line'].values:
    print(f"\nLine 264 (first VTO line):")
    print(df[df['Line'] == 264][['Line', 'CT', 'BT', 'DO', 'DD', 'VTOType']])
else:
    print(f"\n✓ Line 264 (VTO) is NOT in parsed data (correct)")

# Check if line 347 (first Reserve) is in data
if 347 in df['Line'].values:
    print(f"\nLine 347 (first Reserve line):")
    print(df[df['Line'] == 347][['Line', 'CT', 'BT', 'DO', 'DD']])
else:
    print(f"\n✓ Line 347 (Reserve) is NOT in parsed data (correct)")
