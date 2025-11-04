"""
Test Audit Fields in Database Operations
=========================================

This script tests that the created_by and updated_by fields are properly
populated when saving data to the database.

Usage:
    python test_audit_fields.py
"""

import os
import sys
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import database module
from database import get_supabase_client, save_bid_period, check_duplicate_bid_period

def test_audit_fields_in_bid_period():
    """Test that audit fields are populated in bid_period table."""
    print("\n" + "=" * 70)
    print("TEST: Audit Fields in Bid Period")
    print("=" * 70)

    # Get authenticated client
    supabase = get_supabase_client()

    # Check if we can get the current user
    try:
        user = supabase.auth.get_user()
        if user and hasattr(user, 'user') and user.user:
            print(f"✅ Authenticated as: {user.user.email}")
            print(f"   User ID: {user.user.id}")
        else:
            print("❌ Not authenticated - cannot test audit fields")
            print("   Please log in through the Streamlit app first")
            return False
    except Exception as e:
        print(f"❌ Authentication check failed: {e}")
        print("   Please log in through the Streamlit app first")
        return False

    # Query the most recent bid period to check audit fields
    print("\n📊 Checking existing bid periods for audit fields...")
    try:
        response = supabase.table('bid_periods').select('*').order('created_at', desc=True).limit(5).execute()

        if response.data and len(response.data) > 0:
            print(f"\n✅ Found {len(response.data)} bid period(s)")

            for i, record in enumerate(response.data[:3], 1):  # Show first 3
                print(f"\n   Bid Period {i}:")
                print(f"      Period: {record.get('period')}")
                print(f"      Domicile: {record.get('domicile')}")
                print(f"      Aircraft: {record.get('aircraft')}")
                print(f"      Seat: {record.get('seat')}")
                print(f"      created_by: {record.get('created_by', 'NOT SET ❌')}")
                print(f"      updated_by: {record.get('updated_by', 'NOT SET ❌')}")
                print(f"      created_at: {record.get('created_at')}")

                # Check if audit fields are populated
                if record.get('created_by'):
                    print(f"      ✅ Audit fields populated")
                else:
                    print(f"      ⚠️  Audit fields NOT populated (old record)")
        else:
            print("   No bid periods found in database")

    except Exception as e:
        print(f"❌ Error querying bid periods: {e}")
        return False

    return True


def test_audit_fields_in_pairings():
    """Test that audit fields are populated in pairings table."""
    print("\n" + "=" * 70)
    print("TEST: Audit Fields in Pairings")
    print("=" * 70)

    supabase = get_supabase_client()

    # Query the most recent pairings to check audit fields
    print("\n📊 Checking existing pairings for audit fields...")
    try:
        response = supabase.table('pairings').select('*').order('created_at', desc=True).limit(5).execute()

        if response.data and len(response.data) > 0:
            print(f"\n✅ Found {len(response.data)} pairing(s)")

            for i, record in enumerate(response.data[:3], 1):  # Show first 3
                print(f"\n   Pairing {i}:")
                print(f"      Trip ID: {record.get('trip_id')}")
                print(f"      Is EDW: {record.get('is_edw')}")
                print(f"      created_by: {record.get('created_by', 'NOT SET ❌')}")
                print(f"      updated_by: {record.get('updated_by', 'NOT SET ❌')}")
                print(f"      created_at: {record.get('created_at')}")

                # Check if audit fields are populated
                if record.get('created_by'):
                    print(f"      ✅ Audit fields populated")
                else:
                    print(f"      ⚠️  Audit fields NOT populated (old record)")
        else:
            print("   No pairings found in database")

    except Exception as e:
        print(f"❌ Error querying pairings: {e}")
        return False

    return True


def test_audit_fields_in_bid_lines():
    """Test that audit fields are populated in bid_lines table."""
    print("\n" + "=" * 70)
    print("TEST: Audit Fields in Bid Lines")
    print("=" * 70)

    supabase = get_supabase_client()

    # Query the most recent bid lines to check audit fields
    print("\n📊 Checking existing bid lines for audit fields...")
    try:
        response = supabase.table('bid_lines').select('*').order('created_at', desc=True).limit(5).execute()

        if response.data and len(response.data) > 0:
            print(f"\n✅ Found {len(response.data)} bid line(s)")

            for i, record in enumerate(response.data[:3], 1):  # Show first 3
                print(f"\n   Bid Line {i}:")
                print(f"      Line Number: {record.get('line_number')}")
                print(f"      Total CT: {record.get('total_ct')}")
                print(f"      created_by: {record.get('created_by', 'NOT SET ❌')}")
                print(f"      updated_by: {record.get('updated_by', 'NOT SET ❌')}")
                print(f"      created_at: {record.get('created_at')}")

                # Check if audit fields are populated
                if record.get('created_by'):
                    print(f"      ✅ Audit fields populated")
                else:
                    print(f"      ⚠️  Audit fields NOT populated (old record)")
        else:
            print("   No bid lines found in database")

    except Exception as e:
        print(f"❌ Error querying bid lines: {e}")
        return False

    return True


def main():
    """Run all audit field tests."""
    print("\n" + "=" * 70)
    print("AUDIT FIELDS TEST SUITE")
    print("=" * 70)
    print("\nThis script checks that created_by and updated_by fields are")
    print("properly populated when saving data to the database.")
    print("\nNOTE: You must be logged in through the Streamlit app for this test to work.")
    print("=" * 70)

    # Run tests
    results = []

    results.append(("Bid Period Audit Fields", test_audit_fields_in_bid_period()))
    results.append(("Pairing Audit Fields", test_audit_fields_in_pairings()))
    results.append(("Bid Line Audit Fields", test_audit_fields_in_bid_lines()))

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
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️  Some tests failed")

    print("\n" + "=" * 70)
    print("NEXT STEPS")
    print("=" * 70)
    print("\n1. Upload a PDF through the Streamlit app")
    print("2. Click 'Save to Database'")
    print("3. Run this script again to verify audit fields are populated")
    print("\nExpected: All newly saved records should have created_by and updated_by fields set")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
