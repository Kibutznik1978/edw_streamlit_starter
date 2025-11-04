#!/usr/bin/env python3
"""Test reserve line detection logic on SDF PDF."""

import pandas as pd
from bid_parser import parse_bid_lines

pdf_path = "/Users/giladswerdlow/Desktop/2601/SDF/BidLinePrint_BID2601_757_SDF.pdf"

with open(pdf_path, 'rb') as pdf_file:
    df, diagnostics = parse_bid_lines(pdf_file)

print(f"Total lines parsed: {len(df)}")
print(f"\nFirst 10 lines of parsed data:")
print(df[['Line', 'CT', 'BT', 'DO', 'DD']].head(10))

if diagnostics.reserve_lines is not None:
    reserve_df = diagnostics.reserve_lines

    print(f"\nReserve lines DataFrame has {len(reserve_df)} rows")
    print(f"Columns: {reserve_df.columns.tolist()}")

    # Count actual reserve lines
    if 'IsReserve' in reserve_df.columns:
        actual_reserve_count = reserve_df['IsReserve'].sum()
        print(f"\nActual reserve lines (IsReserve=True): {actual_reserve_count}")

        # Show some examples of IsReserve=True
        actual_reserves = reserve_df[reserve_df['IsReserve'] == True]
        if len(actual_reserves) > 0:
            print(f"\nFirst 5 actual reserve lines:")
            print(actual_reserves[['Line', 'IsReserve', 'IsHotStandby', 'CaptainSlots', 'FOSlots']].head())

        # Show some examples of IsReserve=False
        non_reserves = reserve_df[reserve_df['IsReserve'] == False]
        if len(non_reserves) > 0:
            print(f"\nFirst 5 NON-reserve lines (IsReserve=False):")
            print(non_reserves[['Line', 'IsReserve', 'IsHotStandby', 'CaptainSlots', 'FOSlots']].head())

            # Check if non-reserve lines have CT/BT data in main df
            print(f"\nChecking CT/BT values for first 5 non-reserve lines in main DataFrame:")
            for line_num in non_reserves['Line'].head(5):
                line_data = df[df['Line'] == line_num]
                if len(line_data) > 0:
                    ct = line_data['CT'].values[0]
                    bt = line_data['BT'].values[0]
                    print(f"   Line {line_num}: CT={ct}, BT={bt}")
