#!/usr/bin/env python3
"""Check what values are in IsReserve column."""

from bid_parser import parse_bid_lines

pdf_path = "/Users/giladswerdlow/Desktop/2601/SDF/BidLinePrint_BID2601_757_SDF.pdf"

print("Parsing PDF (this may take a minute)...")
with open(pdf_path, 'rb') as pdf_file:
    df, diagnostics = parse_bid_lines(pdf_file)

print(f"Parsed {len(df)} lines")

if diagnostics.reserve_lines is not None:
    reserve_df = diagnostics.reserve_lines

    print(f"\nReserve DataFrame shape: {reserve_df.shape}")
    print(f"Columns: {reserve_df.columns.tolist()}")

    # Check first 10 values in IsReserve column
    print(f"\nFirst 10 IsReserve values:")
    for i, val in enumerate(reserve_df['IsReserve'].head(10)):
        print(f"  {i}: {val} (type: {type(val).__name__})")

    # Check data types
    print(f"\nIsReserve dtype: {reserve_df['IsReserve'].dtype}")

    # Count value types
    print(f"\nValue type breakdown:")
    type_counts = {}
    for val in reserve_df['IsReserve']:
        type_name = type(val).__name__
        type_counts[type_name] = type_counts.get(type_name, 0) + 1
    for type_name, count in type_counts.items():
        print(f"  {type_name}: {count}")

    # Try to count True/False values
    print(f"\nAttempting to count booleans...")
    true_count = sum(1 for val in reserve_df['IsReserve'] if val is True)
    false_count = sum(1 for val in reserve_df['IsReserve'] if val is False)
    print(f"  True: {true_count}")
    print(f"  False: {false_count}")
