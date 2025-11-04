#!/usr/bin/env python3
"""Test script to parse SDF bid line PDF and diagnose issues."""

import sys
from bid_parser import parse_bid_lines, extract_bid_line_header_info

def main():
    pdf_path = "/Users/giladswerdlow/Desktop/2601/SDF/BidLinePrint_BID2601_757_SDF.pdf"

    print("=" * 80)
    print("Testing SDF Bid Line PDF Parsing")
    print("=" * 80)

    # Extract header info
    print("\n1. Extracting header info...")
    with open(pdf_path, 'rb') as pdf_file:
        header_info = extract_bid_line_header_info(pdf_file)
    if header_info:
        print(f"   Bid Period: {header_info.get('bid_period', 'N/A')}")
        print(f"   Domicile: {header_info.get('domicile', 'N/A')}")
        print(f"   Aircraft: {header_info.get('aircraft', 'N/A')}")
        print(f"   Date Range: {header_info.get('date_range', 'N/A')}")
    else:
        print("   ⚠️  Failed to extract header info")

    # Parse bid lines
    print("\n2. Parsing bid lines...")
    with open(pdf_path, 'rb') as pdf_file:
        df, diagnostics = parse_bid_lines(pdf_file)

    print(f"   ✓ Parsed {len(df)} lines")

    # Check for missing data
    print("\n3. Analyzing missing data...")
    for col in ['CT', 'BT', 'DO', 'DD']:
        missing_count = df[col].isna().sum()
        if missing_count > 0:
            print(f"   ⚠️  {col}: {missing_count} missing values")
            # Show which lines are missing this data
            missing_lines = df[df[col].isna()]['Line'].tolist()
            print(f"      Missing in lines: {missing_lines[:10]}{'...' if len(missing_lines) > 10 else ''}")

    # Check reserve lines
    print("\n4. Checking reserve line detection...")
    reserve_lines = diagnostics.reserve_lines
    print(f"   Found {len(reserve_lines)} reserve lines:")
    for reserve in reserve_lines[:5]:  # Show first 5
        print(f"      Line {reserve['line_number']}: "
              f"Captain slots: {reserve.get('captain_slots', 'N/A')}, "
              f"FO slots: {reserve.get('fo_slots', 'N/A')}, "
              f"Hot Standby: {reserve.get('is_hot_standby', False)}")

    # Check if reserve lines appear in main DataFrame
    if reserve_lines:
        reserve_line_numbers = [r['line_number'] for r in reserve_lines]
        lines_in_df = df[df['Line'].isin(reserve_line_numbers)]
        if len(lines_in_df) > 0:
            print(f"\n   ⚠️  WARNING: {len(lines_in_df)} reserve lines are in main DataFrame!")
            print(f"      These should be in diagnostics only, not parsed data:")
            for _, row in lines_in_df.iterrows():
                print(f"         Line {row['Line']}: CT={row['CT']}, BT={row['BT']}, DO={row['DO']}, DD={row['DD']}")

    # Show sample of parsed data
    print("\n5. Sample parsed data (first 10 lines):")
    print(df[['Line', 'CT', 'BT', 'DO', 'DD', 'VTOType']].head(10).to_string(index=False))

    # Show pay period breakdown
    print("\n6. Pay period analysis...")
    pay_periods = diagnostics.pay_periods
    print(f"   Found {len(pay_periods)} pay period entries")
    if pay_periods:
        import pandas as pd
        pp_df = pd.DataFrame(pay_periods)
        print(f"   Columns: {pp_df.columns.tolist()}")
        if 'PayPeriod' in pp_df.columns:
            print(f"   PP1 entries: {len(pp_df[pp_df['PayPeriod'] == 'PP1'])}")
            print(f"   PP2 entries: {len(pp_df[pp_df['PayPeriod'] == 'PP2'])}")

if __name__ == "__main__":
    main()
