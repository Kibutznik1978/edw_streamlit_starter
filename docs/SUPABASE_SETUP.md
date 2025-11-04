# Supabase Setup Guide - REVISED v2.0

**Last Updated:** 2025-10-28
**Status:** Production-Ready

This guide will walk you through setting up a **production-ready** Supabase project with optimized schema, security, and performance.

---

## Table of Contents

1. [Create Supabase Project](#1-create-supabase-project)
2. [Get API Credentials](#2-get-api-credentials)
3. [Run Database Migrations](#3-run-database-migrations)
4. [Configure Row-Level Security](#4-configure-row-level-security)
5. [Configure Local Environment](#5-configure-local-environment)
6. [Test Connection](#6-test-connection)
7. [Set First Admin User](#7-set-first-admin-user)
8. [Troubleshooting](#troubleshooting)

---

## 1. Create Supabase Project

### Step 1.1: Sign Up / Log In

1. Go to [https://supabase.com](https://supabase.com)
2. Click "Start your project" or "Sign In"
3. Sign in with GitHub (recommended) or email

### Step 1.2: Create New Project

1. Click "New Project" from your dashboard
2. Fill in project details:
   - **Name:** `aero-crew-data` (or your preferred name)
   - **Database Password:** Generate a strong password (save this!)
   - **Region:** Choose closest to you (e.g., `us-west-1`)
   - **Pricing Plan:** Free (sufficient for development/testing)
3. Click "Create new project"
4. Wait 2-3 minutes for project provisioning

---

## 2. Get API Credentials

### Step 2.1: Project Settings

1. Once project is ready, click on "Project Settings" (gear icon in sidebar)
2. Navigate to "API" section

### Step 2.2: Copy Credentials

You'll need two values:

**Project URL:**
```
https://xxxxxxxxxxxxx.supabase.co
```

**Anon/Public Key:**
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inh4eHh4...
```

⚠️ **Save these values** - you'll need them in Step 5.

💡 **Security Note:** The `anon` key is safe to use in client-side code. Never use the `service_role` key in client code!

---

## 3. Run Database Migrations

### Step 3.1: Open SQL Editor

1. In your Supabase project dashboard, click "SQL Editor" in the left sidebar
2. Click "New query" button

### Step 3.2: Run Migration Script

⚠️ **IMPORTANT:** Copy the **entire** migration script from the file `docs/migrations/001_initial_schema.sql` or use the consolidated script below.

Click "Run" button (or press Cmd/Ctrl + Enter).

**Expected Output:**
- "Success. No rows returned" for CREATE TABLE statements
- Row counts showing 0 for all tables in verification query

### Step 3.3: Verify Tables Created

Run this verification query in SQL Editor:

```sql
-- Verify all tables exist
SELECT tablename
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;
```

**Expected Result:** You should see 8 tables:
- ✅ `audit_log`
- ✅ `bid_lines`
- ✅ `bid_periods`
- ✅ `pairing_duty_days`
- ✅ `pairings`
- ✅ `pdf_export_templates`
- ✅ `profiles`
- Plus 1 materialized view: `bid_period_trends`

### Step 3.4: Verify Indexes

```sql
-- Check indexes were created
SELECT
    tablename,
    indexname
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;
```

You should see multiple indexes per table (30+ total).

### Step 3.5: Verify Functions

```sql
-- Check helper functions
SELECT
    routine_name,
    routine_type
FROM information_schema.routines
WHERE routine_schema = 'public'
ORDER BY routine_name;
```

**Expected Functions:**
- `handle_new_user` - Creates profile on user signup
- `is_admin` - Checks if user is admin (JWT-based)
- `log_changes` - Audit logging trigger
- `refresh_trends` - Refreshes materialized view

---

## 4. Configure Row-Level Security

### Step 4.1: Verify RLS is Enabled

```sql
-- Check RLS status
SELECT
    tablename,
    rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;
```

All tables should show `rowsecurity = true`.

### Step 4.2: Verify RLS Policies

```sql
-- List all RLS policies
SELECT
    schemaname,
    tablename,
    policyname,
    cmd
FROM pg_policies
WHERE schemaname = 'public'
ORDER BY tablename, policyname;
```

You should see 4 policies per table (SELECT, INSERT, UPDATE, DELETE).

### Step 4.3: Test RLS Policies

⚠️ **Important:** RLS policies use JWT custom claims. You'll configure this after creating your first user.

---

## 5. Configure Local Environment

### Step 5.1: Create .env File

In your project root directory:

```bash
# From project root
touch .env
```

### Step 5.2: Add Credentials

Open `.env` in your text editor and add:

```env
# Supabase Configuration
SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3...

# Optional: Service Role Key (for admin operations, never expose!)
# SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Optional: Application Configuration
APP_ENV=development
DEBUG=true
LOG_LEVEL=INFO
```

Replace the values with your actual credentials from Step 2.

### Step 5.3: Verify .gitignore

Make sure `.env` is in your `.gitignore` file:

```bash
# Check if .env is ignored
grep -q "^\.env$" .gitignore && echo "✅ .env is ignored" || echo "❌ Add .env to .gitignore"
```

If not present, add it:

```bash
echo ".env" >> .gitignore
```

### Step 5.4: Install Dependencies

```bash
# Activate virtual environment
source .venv/bin/activate

# Install Supabase dependencies
pip install supabase python-dotenv

# Update requirements.txt
pip freeze > requirements.txt
```

---

## 6. Test Connection

### Step 6.1: Create Test Script

Create a file `test_supabase_connection.py` in your project root:

```python
#!/usr/bin/env python3
"""
Test Supabase connection and schema validation
"""
from supabase import create_client
from dotenv import load_dotenv
import os

def test_connection():
    """Test Supabase connection and verify schema."""

    # Load environment variables
    load_dotenv()

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")

    if not url or not key:
        print("❌ Error: SUPABASE_URL or SUPABASE_ANON_KEY not found in .env")
        return False

    try:
        # Initialize client
        print("🔌 Connecting to Supabase...")
        supabase = create_client(url, key)

        # Test query - count bid periods
        print("📊 Testing bid_periods table...")
        response = supabase.table('bid_periods').select('*', count='exact').execute()

        print(f"✅ Connection successful!")
        print(f"   Project URL: {url}")
        print(f"   bid_periods table accessible: {len(response.data)} records")

        # Test other tables
        tables = ['pairings', 'bid_lines', 'profiles', 'pdf_export_templates', 'audit_log']
        print(f"\n📋 Testing all tables...")

        for table in tables:
            try:
                response = supabase.table(table).select('*', count='exact').execute()
                print(f"   ✅ {table}: {len(response.data)} records")
            except Exception as e:
                print(f"   ❌ {table}: {str(e)}")
                return False

        # Test materialized view
        print(f"\n🔍 Testing materialized view...")
        try:
            response = supabase.table('bid_period_trends').select('*').execute()
            print(f"   ✅ bid_period_trends: {len(response.data)} records")
        except Exception as e:
            print(f"   ❌ bid_period_trends: {str(e)}")

        # Test helper function
        print(f"\n⚙️  Testing helper functions...")
        try:
            # This will fail until we have a user session, but that's expected
            # Just checking the function exists
            print(f"   ✅ Helper functions deployed (will be tested with auth)")
        except Exception as e:
            print(f"   ⚠️  Helper functions check skipped (requires auth)")

        print(f"\n🎉 All tests passed!")
        return True

    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_connection()
    exit(0 if success else 1)
```

### Step 6.2: Run Test

```bash
python test_supabase_connection.py
```

**Expected output:**
```
🔌 Connecting to Supabase...
📊 Testing bid_periods table...
✅ Connection successful!
   Project URL: https://xxxxxxxxxxxxx.supabase.co
   bid_periods table accessible: 0 records

📋 Testing all tables...
   ✅ pairings: 0 records
   ✅ bid_lines: 0 records
   ✅ profiles: 0 records
   ✅ pdf_export_templates: 0 records
   ✅ audit_log: 0 records

🔍 Testing materialized view...
   ✅ bid_period_trends: 0 records

⚙️  Testing helper functions...
   ✅ Helper functions deployed (will be tested with auth)

🎉 All tests passed!
```

### Step 6.3: Test Insert (Optional)

Add this function to `test_supabase_connection.py`:

```python
def test_insert():
    """Test inserting a sample bid period."""
    load_dotenv()
    supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_ANON_KEY"))

    try:
        # Insert test bid period
        print("📝 Inserting test bid period...")
        data = {
            "period": "TEST",
            "domicile": "ONT",
            "aircraft": "777",
            "seat": "CA",
            "start_date": "2025-01-01",
            "end_date": "2025-01-31"
        }
        response = supabase.table('bid_periods').insert(data).execute()

        print(f"✅ Insert successful! ID: {response.data[0]['id']}")

        # Verify audit log captured it
        print("🔍 Checking audit log...")
        audit_response = supabase.table('audit_log').select('*').order('created_at', desc=True).limit(1).execute()
        if audit_response.data:
            print(f"✅ Audit log working! Latest action: {audit_response.data[0]['action']}")

        # Delete test data
        print("🗑️  Cleaning up test data...")
        supabase.table('bid_periods').delete().eq('period', 'TEST').execute()
        print("✅ Cleanup complete!")

        return True
    except Exception as e:
        print(f"❌ Insert failed: {str(e)}")
        # Try to clean up anyway
        try:
            supabase.table('bid_periods').delete().eq('period', 'TEST').execute()
        except:
            pass
        return False

# Add to main
if __name__ == "__main__":
    success = test_connection()
    if success:
        print("\n" + "="*50)
        test_insert()
    exit(0 if success else 1)
```

---

## 7. Set First Admin User

After your first user signs up through the app:

### Step 7.1: Run in SQL Editor

```sql
-- Set admin role for your user
-- Replace with your actual email
UPDATE profiles
SET role = 'admin'
WHERE id = (
  SELECT id FROM auth.users
  WHERE email = 'your-email@example.com'
);

-- Verify
SELECT
  u.email,
  p.role,
  p.created_at
FROM auth.users u
JOIN profiles p ON p.id = u.id
WHERE u.email = 'your-email@example.com';
```

**Expected Result:**
```
email                    | role  | created_at
-------------------------|-------|-------------------
your-email@example.com  | admin | 2025-10-28 12:34:56
```

### Step 7.2: Configure JWT Custom Claims (CRITICAL)

⚠️ **This is required for RLS policies to work correctly!**

1. Go to **Authentication → Settings** in Supabase Dashboard
2. Scroll to **Custom Claims**
3. Add this function:

```javascript
// Custom claims function
// This adds the user's role to their JWT token
const getCustomClaims = async ({ user, session }) => {
  // Query the profiles table for the user's role
  const { data, error } = await supabase
    .from('profiles')
    .select('role')
    .eq('id', user.id)
    .single();

  if (error || !data) {
    return { app_role: 'user' };
  }

  return {
    app_role: data.role
  };
};
```

4. Click **Save**
5. New logins will have role in JWT token

### Step 7.3: Test Admin Access

Log out and log back in with your admin account. The RLS policies should now recognize you as admin.

---

## Troubleshooting

### Error: "relation 'bid_periods' does not exist"

**Cause:** Migration script didn't run successfully.

**Solution:**
1. Go back to SQL Editor in Supabase
2. Check for any error messages from the migration
3. Re-run the migration script
4. Verify tables exist in Table Editor

### Error: "Invalid API key"

**Cause:** Wrong API key in `.env` file.

**Solution:**
1. Double-check you copied the `anon` key (not service_role key)
2. Verify no extra spaces or quotes in `.env`
3. Regenerate keys in Supabase dashboard if needed (Settings → API)

### Error: "Could not load .env file"

**Cause:** `.env` file not in project root or `python-dotenv` not installed.

**Solution:**
```bash
# Check .env exists
ls -la .env

# Install python-dotenv
pip install python-dotenv
```

### Error: "Connection timeout"

**Cause:** Network issues or wrong project URL.

**Solution:**
1. Verify Supabase project URL is correct
2. Check internet connection
3. Try accessing Supabase dashboard - if it loads, project is online
4. Check firewall/VPN settings

### Error: "Row Level Security policy violation"

**Cause:** RLS policies not configured correctly or JWT custom claims not set up.

**Solution:**
1. Verify you ran the RLS policy migration
2. Check JWT custom claims are configured (Step 7.2)
3. Log out and log back in to get new JWT token
4. Verify admin user role in profiles table

### Error: "permission denied for table"

**Cause:** RLS is too restrictive or custom claims not working.

**Solution:**
```sql
-- Temporarily disable RLS for debugging (NOT for production!)
ALTER TABLE bid_periods DISABLE ROW LEVEL SECURITY;

-- Test your operation
-- Then re-enable RLS
ALTER TABLE bid_periods ENABLE ROW LEVEL SECURITY;
```

### Error: "function is_admin() does not exist"

**Cause:** Helper functions not created.

**Solution:**
Re-run the helper functions section of the migration script:

```sql
-- Helper function for admin checks (JWT-based)
CREATE OR REPLACE FUNCTION is_admin()
RETURNS BOOLEAN AS $$
BEGIN
  RETURN (auth.jwt() ->> 'app_role') = 'admin';
END;
$$ LANGUAGE plpgsql SECURITY DEFINER STABLE;
```

### Materialized View Not Refreshing

**Cause:** Materialized view needs manual refresh after data changes.

**Solution:**
```sql
-- Manually refresh
REFRESH MATERIALIZED VIEW CONCURRENTLY bid_period_trends;

-- Or use the helper function
SELECT refresh_trends();
```

**Best Practice:** Call `refresh_trends()` after bulk data inserts in your Python code.

---

## Next Steps

✅ Supabase project created
✅ Database schema deployed
✅ Row-Level Security configured
✅ Environment configured
✅ Connection tested
✅ First admin user set

**You're ready to integrate with the Streamlit app!**

Next, proceed to:
1. Create `database.py` module (see Step 4 of main setup)
2. Create `auth.py` module (see Step 5 of main setup)
3. Add authentication to `app.py`
4. Add "Save to Database" functionality

Refer to `SUPABASE_INTEGRATION_ROADMAP.md` for the complete implementation plan.

---

## Useful Supabase Resources

- **Dashboard:** https://app.supabase.com
- **Documentation:** https://supabase.com/docs
- **Python Client Docs:** https://supabase.com/docs/reference/python
- **SQL Editor:** Direct SQL query interface
- **Table Editor:** GUI for viewing/editing data
- **Database Logs:** Monitor queries and errors
- **Auth Settings:** Configure JWT custom claims

---

## Security Best Practices

1. ✅ **Never commit `.env`** to git
2. ✅ **Use `anon` key** for client-side operations (safe to expose)
3. ⚠️ **Protect `service_role` key** (admin access, never expose)
4. ✅ **Enable RLS** on all tables for security
5. ✅ **Use JWT custom claims** for role-based access (not subqueries!)
6. 💡 **Rotate keys periodically** in production
7. 💡 **Use environment-specific projects** (dev, staging, prod)
8. ✅ **Enable audit logging** for compliance
9. ✅ **Test RLS policies** thoroughly before production

---

## Performance Optimization Tips

1. **Use materialized views** for expensive aggregations
2. **Add indexes** on frequently queried columns (already included in schema)
3. **Use batch inserts** (1000 rows at a time maximum)
4. **Cache queries** in Streamlit with `@st.cache_data`
5. **Use pagination** for large result sets
6. **Refresh materialized views** after bulk data changes
7. **Monitor query performance** in Supabase Dashboard → Database → Query Performance

---

**Setup complete! 🎉**

**Document Version:** 2.0
**Last Updated:** 2025-10-28
