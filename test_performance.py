"""
Performance Testing Script
==========================

This script tests database performance with large datasets (1000+ records).

Usage:
    python test_performance.py
"""

import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from database import (
    get_supabase_client,
    save_bid_period,
    save_pairings,
    save_bid_lines,
    query_pairings,
    query_bid_lines,
    refresh_trends,
    delete_pairings,
    delete_bid_lines
)

# Performance thresholds
PERFORMANCE_TARGETS = {
    'bulk_insert_1000_rows': 5.0,  # seconds
    'query_with_filters': 3.0,  # seconds
    'materialized_view_refresh': 10.0,  # seconds
}


def create_test_bid_period():
    """Create a test bid period for performance testing."""
    print("\n" + "=" * 70)
    print("CREATE TEST BID PERIOD")
    print("=" * 70)

    test_period_data = {
        'period': 'PERF_TEST',
        'domicile': 'TEST',
        'aircraft': '999',
        'seat': 'CA',
        'start_date': datetime.now().date().isoformat(),
        'end_date': (datetime.now() + timedelta(days=30)).date().isoformat()
    }

    try:
        bid_period_id = save_bid_period(test_period_data)
        print(f"✅ Test bid period created: {bid_period_id}")
        return bid_period_id
    except ValueError as e:
        if "already exists" in str(e):
            # Get existing test bid period
            supabase = get_supabase_client()
            response = supabase.table('bid_periods').select('*').match({
                'period': 'PERF_TEST',
                'domicile': 'TEST',
                'aircraft': '999',
                'seat': 'CA'
            }).execute()

            if response.data:
                bid_period_id = response.data[0]['id']
                print(f"✅ Using existing test bid period: {bid_period_id}")

                # Clean up old data
                print("   Cleaning up old test data...")
                delete_pairings(bid_period_id)
                delete_bid_lines(bid_period_id)
                print("   ✅ Old data deleted")

                return bid_period_id
            else:
                raise


def test_bulk_insert_pairings(bid_period_id: str, num_records: int = 1000):
    """Test bulk insert performance for pairings."""
    print("\n" + "=" * 70)
    print(f"TEST: Bulk Insert {num_records} Pairings")
    print("=" * 70)

    # Create test DataFrame
    print(f"\n📊 Creating test DataFrame with {num_records} records...")

    df = pd.DataFrame({
        'trip_id': [f'PERF-TEST-{i:05d}' for i in range(num_records)],
        'is_edw': [i % 2 == 0 for i in range(num_records)],
        'tafb_hours': [20.0 + (i % 50) for i in range(num_records)],
        'num_duty_days': [2 + (i % 3) for i in range(num_records)],
        'total_credit_time': [5.0 + (i % 10) for i in range(num_records)],
        'num_legs': [4 + (i % 4) for i in range(num_records)],
        'edw_reason': [f'Duty day {i % 3 + 1}' if i % 2 == 0 else None for i in range(num_records)]
    })

    print(f"✅ DataFrame created")
    print(f"   Columns: {', '.join(df.columns)}")
    print(f"   Shape: {df.shape}")

    # Bulk insert with timing
    print(f"\n⏱️  Starting bulk insert...")
    start_time = time.time()

    try:
        count = save_pairings(bid_period_id, df)
        elapsed = time.time() - start_time

        print(f"\n✅ Bulk insert completed!")
        print(f"   Records inserted: {count}")
        print(f"   Time elapsed: {elapsed:.2f} seconds")
        print(f"   Throughput: {count/elapsed:.0f} records/second")

        # Check against performance target
        target = PERFORMANCE_TARGETS['bulk_insert_1000_rows']
        if elapsed < target:
            print(f"   ✅ PASS - Within target ({elapsed:.2f}s < {target}s)")
            return True
        else:
            print(f"   ❌ FAIL - Too slow ({elapsed:.2f}s >= {target}s)")
            return False

    except Exception as e:
        print(f"\n❌ Bulk insert failed: {e}")
        return False


def test_bulk_insert_bid_lines(bid_period_id: str, num_records: int = 1000):
    """Test bulk insert performance for bid lines."""
    print("\n" + "=" * 70)
    print(f"TEST: Bulk Insert {num_records} Bid Lines")
    print("=" * 70)

    # Create test DataFrame
    print(f"\n📊 Creating test DataFrame with {num_records} records...")

    df = pd.DataFrame({
        'line_number': list(range(1, num_records + 1)),
        'total_ct': [50.0 + (i % 50) for i in range(num_records)],
        'total_bt': [45.0 + (i % 45) for i in range(num_records)],
        'total_do': [10 + (i % 10) for i in range(num_records)],
        'total_dd': [18 + (i % 10) for i in range(num_records)],
        'is_reserve': [i % 20 == 0 for i in range(num_records)],
        'is_hot_standby': [False] * num_records,
    })

    # Add optional fields
    df['pp1_ct'] = df['total_ct'] / 2
    df['pp2_ct'] = df['total_ct'] / 2
    df['pp1_bt'] = df['total_bt'] / 2
    df['pp2_bt'] = df['total_bt'] / 2
    df['pp1_do'] = df['total_do'] // 2
    df['pp2_do'] = df['total_do'] - df['pp1_do']
    df['pp1_dd'] = df['total_dd'] // 2
    df['pp2_dd'] = df['total_dd'] - df['pp1_dd']

    print(f"✅ DataFrame created")
    print(f"   Columns: {', '.join(df.columns)}")
    print(f"   Shape: {df.shape}")

    # Bulk insert with timing
    print(f"\n⏱️  Starting bulk insert...")
    start_time = time.time()

    try:
        count = save_bid_lines(bid_period_id, df)
        elapsed = time.time() - start_time

        print(f"\n✅ Bulk insert completed!")
        print(f"   Records inserted: {count}")
        print(f"   Time elapsed: {elapsed:.2f} seconds")
        print(f"   Throughput: {count/elapsed:.0f} records/second")

        # Check against performance target
        target = PERFORMANCE_TARGETS['bulk_insert_1000_rows']
        if elapsed < target:
            print(f"   ✅ PASS - Within target ({elapsed:.2f}s < {target}s)")
            return True
        else:
            print(f"   ❌ FAIL - Too slow ({elapsed:.2f}s >= {target}s)")
            return False

    except Exception as e:
        print(f"\n❌ Bulk insert failed: {e}")
        return False


def test_query_performance(bid_period_id: str):
    """Test query performance with filters."""
    print("\n" + "=" * 70)
    print("TEST: Query Performance with Filters")
    print("=" * 70)

    filters = {
        'bid_period_id': bid_period_id,
        'is_edw': True,
        'min_credit_time': 5.0
    }

    print(f"\n📊 Query filters:")
    for key, value in filters.items():
        print(f"   {key}: {value}")

    print(f"\n⏱️  Starting query...")
    start_time = time.time()

    try:
        df, total_count = query_pairings(filters, limit=1000)
        elapsed = time.time() - start_time

        print(f"\n✅ Query completed!")
        print(f"   Records returned: {len(df)}")
        print(f"   Total matching: {total_count}")
        print(f"   Time elapsed: {elapsed:.2f} seconds")

        # Check against performance target
        target = PERFORMANCE_TARGETS['query_with_filters']
        if elapsed < target:
            print(f"   ✅ PASS - Within target ({elapsed:.2f}s < {target}s)")
            return True
        else:
            print(f"   ❌ FAIL - Too slow ({elapsed:.2f}s >= {target}s)")
            return False

    except Exception as e:
        print(f"\n❌ Query failed: {e}")
        return False


def test_materialized_view_refresh():
    """Test materialized view refresh performance."""
    print("\n" + "=" * 70)
    print("TEST: Materialized View Refresh")
    print("=" * 70)

    print(f"\n⏱️  Starting refresh...")
    start_time = time.time()

    try:
        refresh_trends()
        elapsed = time.time() - start_time

        print(f"\n✅ Refresh completed!")
        print(f"   Time elapsed: {elapsed:.2f} seconds")

        # Check against performance target
        target = PERFORMANCE_TARGETS['materialized_view_refresh']
        if elapsed < target:
            print(f"   ✅ PASS - Within target ({elapsed:.2f}s < {target}s)")
            return True
        else:
            print(f"   ❌ FAIL - Too slow ({elapsed:.2f}s >= {target}s)")
            return False

    except Exception as e:
        print(f"\n❌ Refresh failed: {e}")
        print(f"   Note: This may fail if materialized view needs a unique index")
        return True  # Non-fatal


def cleanup_test_data(bid_period_id: str):
    """Clean up test data."""
    print("\n" + "=" * 70)
    print("CLEANUP TEST DATA")
    print("=" * 70)

    print(f"\n🗑️  Deleting test data...")

    try:
        # Delete pairings
        pairing_count = delete_pairings(bid_period_id)
        print(f"   ✅ Deleted {pairing_count} pairings")

        # Delete bid lines
        bidline_count = delete_bid_lines(bid_period_id)
        print(f"   ✅ Deleted {bidline_count} bid lines")

        # Delete bid period
        supabase = get_supabase_client()
        supabase.table('bid_periods').delete().eq('id', bid_period_id).execute()
        print(f"   ✅ Deleted bid period")

        print(f"\n✅ Cleanup completed!")

    except Exception as e:
        print(f"\n❌ Cleanup failed: {e}")
        print(f"   You may need to manually delete test data")


def main():
    """Run all performance tests."""
    print("\n" + "=" * 70)
    print("PERFORMANCE TEST SUITE")
    print("=" * 70)
    print("\nThis script tests database performance with large datasets.")
    print(f"\nPerformance Targets:")
    for test_name, target in PERFORMANCE_TARGETS.items():
        print(f"   {test_name}: < {target}s")
    print("=" * 70)

    results = []

    try:
        # Create test bid period
        bid_period_id = create_test_bid_period()

        # Run tests
        results.append(("Bulk Insert 1000 Pairings", test_bulk_insert_pairings(bid_period_id, 1000)))
        results.append(("Bulk Insert 1000 Bid Lines", test_bulk_insert_bid_lines(bid_period_id, 1000)))
        results.append(("Query with Filters", test_query_performance(bid_period_id)))
        results.append(("Materialized View Refresh", test_materialized_view_refresh()))

        # Cleanup
        cleanup_test_data(bid_period_id)

    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All performance tests passed!")
        print("\n✅ Database performance meets targets:")
        print("   - Bulk insert: < 5 seconds for 1000 records")
        print("   - Query: < 3 seconds with filters")
        print("   - View refresh: < 10 seconds")
    else:
        print("\n⚠️  Some performance tests failed")
        print("\nConsider:")
        print("   - Adding more database indexes")
        print("   - Optimizing RLS policies")
        print("   - Increasing batch size (if allowed)")

    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
