"""
Create Test User for Multi-User Access Testing
===============================================

This script creates a regular (non-admin) test user for testing
multi-user access and RLS policies.

Usage:
    python create_test_user.py
"""

import os
from dotenv import load_dotenv
from database import get_supabase_client

# Load environment variables
load_dotenv()

def create_test_user(email: str, password: str, display_name: str):
    """
    Create a test user account.

    Args:
        email: User email address
        password: User password (min 8 characters)
        display_name: Display name for the user

    Returns:
        True if successful, False otherwise
    """
    print("\n" + "=" * 70)
    print("CREATE TEST USER")
    print("=" * 70)

    supabase = get_supabase_client()

    try:
        # Create user via Supabase Auth
        print(f"\n📝 Creating user: {email}")
        print(f"   Display name: {display_name}")
        print(f"   Password length: {len(password)} characters")

        response = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "display_name": display_name
                }
            }
        })

        if response.user:
            user_id = response.user.id
            print(f"\n✅ User created successfully!")
            print(f"   User ID: {user_id}")
            print(f"   Email: {response.user.email}")

            # Check if email confirmation is required
            if response.session:
                print(f"\n✅ User session created (no email confirmation required)")
            else:
                print(f"\n⚠️  Email confirmation required")
                print(f"   Check {email} for confirmation link")

            # Check the profile was created automatically
            print(f"\n📊 Checking profile creation...")
            profile_response = supabase.table('profiles').select('*').eq('id', user_id).execute()

            if profile_response.data and len(profile_response.data) > 0:
                profile = profile_response.data[0]
                print(f"✅ Profile created automatically")
                print(f"   Display name: {profile.get('display_name')}")
                print(f"   Role: {profile.get('role')}")

                if profile.get('role') == 'user':
                    print(f"\n✅ User has 'user' role (non-admin)")
                else:
                    print(f"\n⚠️  User has '{profile.get('role')}' role")
            else:
                print(f"⚠️  Profile not found - may need to be created manually")

            return True

        else:
            print(f"\n❌ User creation failed - no user returned")
            return False

    except Exception as e:
        print(f"\n❌ Error creating user: {e}")

        # Check if user already exists
        if "already registered" in str(e).lower() or "already exists" in str(e).lower():
            print(f"\n⚠️  User {email} already exists")
            print(f"   You can use this account for testing")

            # Try to find the existing user
            try:
                print(f"\n📊 Looking up existing user...")
                # We can't query auth.users directly, but we can check profiles
                profile_response = supabase.table('profiles').select('*').execute()

                for profile in profile_response.data:
                    if profile.get('display_name') == display_name:
                        print(f"✅ Found existing profile:")
                        print(f"   User ID: {profile.get('id')}")
                        print(f"   Display name: {profile.get('display_name')}")
                        print(f"   Role: {profile.get('role')}")
                        return True

            except Exception as lookup_error:
                print(f"   Could not look up existing user: {lookup_error}")

        return False


def list_all_users():
    """List all users in the database."""
    print("\n" + "=" * 70)
    print("EXISTING USERS")
    print("=" * 70)

    supabase = get_supabase_client()

    try:
        response = supabase.table('profiles').select('*').order('created_at', desc=True).execute()

        if response.data:
            print(f"\n✅ Found {len(response.data)} user(s):\n")

            for i, profile in enumerate(response.data, 1):
                role_emoji = "👑" if profile.get('role') == 'admin' else "👤"
                print(f"   {role_emoji} User {i}:")
                print(f"      ID: {profile.get('id')}")
                print(f"      Display name: {profile.get('display_name')}")
                print(f"      Role: {profile.get('role').upper()}")
                print(f"      Created: {profile.get('created_at')}")
                print()
        else:
            print("\n⚠️  No users found in database")

    except Exception as e:
        print(f"\n❌ Error listing users: {e}")


def main():
    """Main function."""
    print("\n" + "=" * 70)
    print("TEST USER CREATION SCRIPT")
    print("=" * 70)
    print("\nThis script creates a regular (non-admin) test user for testing")
    print("multi-user access and Row Level Security (RLS) policies.")
    print("=" * 70)

    # List existing users first
    list_all_users()

    # Create test user
    print("\n" + "=" * 70)
    print("CREATING NEW TEST USER")
    print("=" * 70)

    test_email = "testuser@aerocrew.local"
    test_password = "TestPassword123!"
    test_display_name = "Test User (Regular)"

    print(f"\nTest user credentials:")
    print(f"   Email: {test_email}")
    print(f"   Password: {test_password}")
    print(f"   Display name: {test_display_name}")
    print(f"   Expected role: user (non-admin)")

    input("\nPress Enter to create this user (or Ctrl+C to cancel)...")

    success = create_test_user(test_email, test_password, test_display_name)

    # List users again to show the new user
    if success:
        list_all_users()

    # Summary
    print("\n" + "=" * 70)
    print("NEXT STEPS FOR TESTING")
    print("=" * 70)

    if success:
        print("\n✅ Test user created successfully!")
        print("\nYou can now test multi-user access:")
        print(f"\n1. Log out of the Streamlit app")
        print(f"2. Log in with: {test_email} / {test_password}")
        print(f"3. Try to save data to the database (should fail - regular users cannot insert)")
        print(f"4. Verify you can still view existing data")
        print(f"\n5. Log back in as admin (giladswerdlow@gmail.com)")
        print(f"6. Try to save data to the database (should succeed)")

        print(f"\n📚 Expected behavior:")
        print(f"   ✅ Regular users: Can SELECT (view) all data")
        print(f"   ❌ Regular users: Cannot INSERT/UPDATE/DELETE data")
        print(f"   ✅ Admin users: Full access to all operations")
    else:
        print("\n❌ Test user creation failed")
        print("\nAlternative approach:")
        print("1. Open the Streamlit app")
        print("2. Log out if logged in")
        print("3. Click 'Sign Up' tab")
        print(f"4. Create account with email: {test_email}")
        print(f"5. The account will automatically have 'user' role (non-admin)")

    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
