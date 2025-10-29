#!/usr/bin/env python3
"""
Test Supabase Connection Script
================================

This script verifies that your Supabase connection is working correctly
and that all tables from the migration have been created.

Usage:
    python test_supabase_connection.py

Requirements:
    - .env file with SUPABASE_URL and SUPABASE_ANON_KEY
    - supabase-py package installed
    - Database migration (001_initial_schema.sql) already run
"""

from database import get_supabase_client, test_connection
from dotenv import load_dotenv
import os
import sys

def verify_environment():
    """Check if .env file exists and contains required variables."""
    print("🔍 Checking environment variables...")
    
    load_dotenv()
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")
    
    if not url or not key:
        print("❌ Error: Missing Supabase credentials")
        print("\nPlease create a .env file with:")
        print("  SUPABASE_URL=your_project_url")
        print("  SUPABASE_ANON_KEY=your_anon_key")
        print("\nSee .env.example for template")
        return False
    
    print(f"✅ Found SUPABASE_URL: {url[:30]}...")
    print(f"✅ Found SUPABASE_ANON_KEY: {key[:20]}...")
    return True

def verify_tables():
    """Verify all required tables exist."""
    print("\n🔍 Verifying database schema...")
    
    expected_tables = [
        'bid_periods',
        'pairings',
        'pairing_duty_days',
        'bid_lines',
        'profiles',
        'pdf_export_templates',
        'audit_log'
    ]
    
    try:
        supabase = get_supabase_client()
        
        for table in expected_tables:
            try:
                response = supabase.table(table).select('*', count='exact').limit(0).execute()
                print(f"✅ Table '{table}' exists (found {response.count} records)")
            except Exception as e:
                print(f"❌ Table '{table}' error: {str(e)}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        return False

def verify_materialized_view():
    """Verify materialized view exists."""
    print("\n🔍 Verifying materialized view...")
    
    try:
        supabase = get_supabase_client()
        
        response = supabase.table('bid_period_trends').select('*', count='exact').limit(0).execute()
        print(f"✅ Materialized view 'bid_period_trends' exists")
        return True
        
    except Exception as e:
        print(f"❌ Materialized view error: {str(e)}")
        print("   Note: This is expected if you haven't run the migration yet")
        return False

def verify_functions():
    """Verify helper functions exist (best effort check)."""
    print("\n🔍 Verifying helper functions...")
    
    try:
        supabase = get_supabase_client()
        
        # Try to call refresh_trends function
        try:
            supabase.rpc('refresh_trends').execute()
            print(f"✅ Function 'refresh_trends()' exists and works")
        except Exception as e:
            if "does not exist" in str(e):
                print(f"❌ Function 'refresh_trends()' not found")
                return False
            else:
                # Function exists but might fail for other reasons (e.g., empty view)
                print(f"✅ Function 'refresh_trends()' exists (may have failed due to empty data)")
        
        return True
        
    except Exception as e:
        print(f"❌ Function verification failed: {str(e)}")
        return False

def main():
    """Run all verification tests."""
    print("=" * 70)
    print("Supabase Connection Test")
    print("=" * 70)
    
    # Step 1: Verify environment
    if not verify_environment():
        print("\n❌ Setup incomplete: Missing environment variables")
        sys.exit(1)
    
    # Step 2: Test basic connection
    print("\n🔍 Testing basic connection...")
    if not test_connection():
        print("\n❌ Setup incomplete: Cannot connect to Supabase")
        print("\nPossible issues:")
        print("  1. Invalid credentials in .env")
        print("  2. Supabase project is paused")
        print("  3. Network connectivity issue")
        sys.exit(1)
    
    # Step 3: Verify tables
    tables_ok = verify_tables()
    
    # Step 4: Verify materialized view
    view_ok = verify_materialized_view()
    
    # Step 5: Verify functions
    functions_ok = verify_functions()
    
    # Summary
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    
    if tables_ok and view_ok and functions_ok:
        print("✅ All checks passed! Your Supabase integration is ready.")
        print("\nNext steps:")
        print("  1. Run: streamlit run app.py")
        print("  2. Sign up for an account")
        print("  3. Promote your first admin user (see SUPABASE_SETUP.md)")
        print("  4. Start uploading bid packets!")
    else:
        print("⚠️  Some checks failed.")
        print("\nIf tables are missing, run the migration:")
        print("  1. Open Supabase SQL Editor")
        print("  2. Copy contents of docs/migrations/001_initial_schema.sql")
        print("  3. Execute the SQL")
        print("  4. Run this test script again")
        
        if not functions_ok:
            print("\nNote: Function checks may fail if migration hasn't been run yet.")

if __name__ == "__main__":
    main()
