"""
Debug script to investigate duplicate trip parsing.

This script will:
1. Parse a PDF and show all trip IDs found
2. Identify which trip IDs are duplicated
3. Show the full text of each duplicate to compare them
"""

import sys
from pathlib import Path
from collections import Counter
from edw.parser import parse_pairings, parse_trip_id

def debug_duplicates(pdf_path: str):
    """
    Analyze a PDF for duplicate trip IDs and show the differences.

    Args:
        pdf_path: Path to the pairing PDF file
    """
    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        print(f"❌ Error: File not found: {pdf_path}")
        return

    print(f"🔍 Analyzing: {pdf_path.name}")
    print("=" * 80)

    # Parse all trips
    print("\n📄 Parsing PDF...")
    trips = parse_pairings(pdf_path)
    print(f"✅ Found {len(trips)} trip blocks\n")

    # Extract trip IDs
    trip_ids = []
    trip_map = {}  # Map trip_id to list of trip texts

    for i, trip_text in enumerate(trips):
        trip_id = parse_trip_id(trip_text)
        if trip_id:
            trip_ids.append(trip_id)
            if trip_id not in trip_map:
                trip_map[trip_id] = []
            trip_map[trip_id].append((i, trip_text))

    # Count occurrences
    trip_counts = Counter(trip_ids)

    print(f"📊 Trip ID Statistics:")
    print(f"   Total trip blocks: {len(trips)}")
    print(f"   Unique trip IDs: {len(trip_counts)}")
    print(f"   Total parsed IDs: {len(trip_ids)}")
    print(f"   Duplicates: {len(trips) - len(trip_counts)}\n")

    # Find duplicates
    duplicates = {tid: count for tid, count in trip_counts.items() if count > 1}

    if not duplicates:
        print("✅ No duplicates found!")
        return

    print(f"⚠️  Found {len(duplicates)} trip IDs with duplicates:")
    for trip_id, count in sorted(duplicates.items()):
        print(f"   Trip {trip_id}: appears {count} times")

    print("\n" + "=" * 80)
    print("🔍 DETAILED DUPLICATE ANALYSIS")
    print("=" * 80)

    # Show detailed comparison for each duplicate
    for trip_id in sorted(duplicates.keys()):
        occurrences = trip_map[trip_id]
        print(f"\n{'='*80}")
        print(f"Trip ID: {trip_id} (appears {len(occurrences)} times)")
        print(f"{'='*80}")

        for idx, (original_idx, trip_text) in enumerate(occurrences, 1):
            print(f"\n--- Occurrence #{idx} (Block #{original_idx + 1}) ---")

            # Show first 20 lines to see the key differences
            lines = trip_text.split('\n')[:25]

            # Highlight if "Lines:" appears
            has_lines_marker = any('Lines:' in line for line in lines)
            if has_lines_marker:
                print("🔔 Contains 'Lines:' marker")

            # Show the text
            for line_num, line in enumerate(lines, 1):
                # Highlight Lines: pattern
                if 'Lines:' in line:
                    print(f"  {line_num:2d}: >>> {line} <<<")
                else:
                    print(f"  {line_num:2d}: {line}")

            total_lines = len(trip_text.split('\n'))
            if total_lines > 25:
                remaining = total_lines - 25
                print(f"  ... ({remaining} more lines)")

    print("\n" + "=" * 80)
    print("💡 RECOMMENDATIONS:")
    print("=" * 80)

    # Check if "Lines:" pattern correlates with duplicates
    lines_marker_count = 0
    for trip_id in duplicates.keys():
        for _, trip_text in trip_map[trip_id]:
            if 'Lines:' in trip_text:
                lines_marker_count += 1

    if lines_marker_count > 0:
        print(f"\n✓ {lines_marker_count} duplicate occurrences contain 'Lines:' marker")
        print("  → Consider filtering out trips with 'Lines:' pattern")
        print("  → OR extract line assignment info and store separately")
    else:
        print("\n✓ No 'Lines:' markers found in duplicates")
        print("  → Duplication likely caused by something else")
        print("  → Check for page breaks or report sections")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python debug_duplicate_trips.py <path_to_pdf>")
        print("\nExample:")
        print("  python debug_duplicate_trips.py ~/Downloads/2507_ONT_757_CA.pdf")
        sys.exit(1)

    pdf_path = sys.argv[1]
    debug_duplicates(pdf_path)
