# Supabase Setup Guide

This guide will walk you through setting up a Supabase project for the Pairing Analyzer Tool.

---

## Table of Contents

1. [Create Supabase Project](#1-create-supabase-project)
2. [Get API Credentials](#2-get-api-credentials)
3. [Run Database Migrations](#3-run-database-migrations)
4. [Configure Local Environment](#4-configure-local-environment)
5. [Test Connection](#5-test-connection)
6. [Troubleshooting](#troubleshooting)

---

## 1. Create Supabase Project

### Step 1.1: Sign Up / Log In

1. Go to [https://supabase.com](https://supabase.com)
2. Click "Start your project" or "Sign In"
3. Sign in with GitHub (recommended) or email

### Step 1.2: Create New Project

1. Click "New Project" from your dashboard
2. Fill in project details:
   - **Name:** `pairing-analyzer` (or your preferred name)
   - **Database Password:** Generate a strong password (save this!)
   - **Region:** Choose closest to you (e.g., `us-west-1`)
   - **Pricing Plan:** Free (sufficient for testing)
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

⚠️ **Save these values** - you'll need them in Step 4.

💡 **Security Note:** The `anon` key is safe to use in client-side code, but never commit it to public repos. We'll use `.env` files.

---

## 3. Run Database Migrations

### Step 3.1: Open SQL Editor

1. In your Supabase project dashboard, click "SQL Editor" in the left sidebar
2. Click "New query" button

### Step 3.2: Run Migration Script

Copy and paste the following SQL script into the editor:

```sql
-- ============================================
-- PAIRING ANALYZER DATABASE SCHEMA
-- Version: 1.0
-- Date: 2025-10-19
-- ============================================

-- Enable UUID extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- TABLE 1: bid_periods
-- Master reference table for all bid periods
-- ============================================

CREATE TABLE bid_periods (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  domicile VARCHAR(10) NOT NULL,
  aircraft VARCHAR(10) NOT NULL,
  bid_period VARCHAR(10) NOT NULL,
  upload_date TIMESTAMP DEFAULT NOW(),
  created_at TIMESTAMP DEFAULT NOW(),

  -- Ensure no duplicate bid periods
  CONSTRAINT unique_bid_period UNIQUE(domicile, aircraft, bid_period)
);

-- Index for fast lookups
CREATE INDEX idx_bid_periods_lookup ON bid_periods(domicile, aircraft, bid_period);

COMMENT ON TABLE bid_periods IS 'Master table tracking all uploaded bid periods';

-- ============================================
-- TABLE 2: trips
-- Individual pairing/trip details from EDW analyzer
-- ============================================

CREATE TABLE trips (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  bid_period_id UUID NOT NULL REFERENCES bid_periods(id) ON DELETE CASCADE,

  -- Trip identification
  trip_id VARCHAR(50) NOT NULL,

  -- EDW analysis results
  is_edw BOOLEAN NOT NULL,
  edw_reason TEXT,

  -- Metrics
  tafb_hours DECIMAL(6,2),
  duty_days INTEGER,
  credit_time_hours DECIMAL(6,2),

  -- Raw trip text for debugging/audit trail
  raw_text TEXT,

  created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for common queries
CREATE INDEX idx_trips_bid_period ON trips(bid_period_id);
CREATE INDEX idx_trips_edw ON trips(is_edw);
CREATE INDEX idx_trips_trip_id ON trips(trip_id);

COMMENT ON TABLE trips IS 'Granular trip/pairing data with EDW analysis';

-- ============================================
-- TABLE 3: edw_summary_stats
-- Aggregated EDW statistics per bid period
-- ============================================

CREATE TABLE edw_summary_stats (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  bid_period_id UUID NOT NULL REFERENCES bid_periods(id) ON DELETE CASCADE,

  -- Trip counts
  total_trips INTEGER NOT NULL,
  edw_trips INTEGER NOT NULL,
  non_edw_trips INTEGER NOT NULL,

  -- Trip-weighted percentage
  trip_weighted_pct DECIMAL(5,2),

  -- TAFB-weighted metrics
  total_tafb_hours DECIMAL(8,2),
  edw_tafb_hours DECIMAL(8,2),
  tafb_weighted_pct DECIMAL(5,2),

  -- Duty-day-weighted metrics
  total_duty_days INTEGER,
  edw_duty_days INTEGER,
  duty_day_weighted_pct DECIMAL(5,2),

  created_at TIMESTAMP DEFAULT NOW(),

  -- One summary per bid period
  CONSTRAINT unique_edw_summary UNIQUE(bid_period_id)
);

CREATE INDEX idx_edw_summary_bid_period ON edw_summary_stats(bid_period_id);

COMMENT ON TABLE edw_summary_stats IS 'Pre-computed EDW summary statistics per bid period';

-- ============================================
-- TABLE 4: bid_lines
-- Individual line details from Bid Line analyzer
-- ============================================

CREATE TABLE bid_lines (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  bid_period_id UUID NOT NULL REFERENCES bid_periods(id) ON DELETE CASCADE,

  -- Line identification
  line_number INTEGER NOT NULL,

  -- Metrics (stored in minutes for precision)
  credit_time_minutes INTEGER NOT NULL,
  block_time_minutes INTEGER NOT NULL,
  days_off INTEGER NOT NULL,
  duty_days INTEGER NOT NULL,

  -- Analysis flag
  is_buy_up BOOLEAN,

  created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_bid_lines_bid_period ON bid_lines(bid_period_id);
CREATE INDEX idx_bid_lines_buy_up ON bid_lines(is_buy_up);
CREATE INDEX idx_bid_lines_line_number ON bid_lines(line_number);

COMMENT ON TABLE bid_lines IS 'Granular bid line data with credit/block time metrics';

-- ============================================
-- TABLE 5: bid_line_summary_stats
-- Aggregated line statistics per bid period
-- ============================================

CREATE TABLE bid_line_summary_stats (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  bid_period_id UUID NOT NULL REFERENCES bid_periods(id) ON DELETE CASCADE,

  -- Counts
  total_lines INTEGER NOT NULL,
  buy_up_lines INTEGER NOT NULL,

  -- Credit Time stats (in minutes)
  ct_min INTEGER,
  ct_max INTEGER,
  ct_avg DECIMAL(8,2),
  ct_median DECIMAL(8,2),
  ct_stddev DECIMAL(8,2),

  -- Block Time stats (in minutes)
  bt_min INTEGER,
  bt_max INTEGER,
  bt_avg DECIMAL(8,2),
  bt_median DECIMAL(8,2),
  bt_stddev DECIMAL(8,2),

  -- Days Off stats
  do_min INTEGER,
  do_max INTEGER,
  do_avg DECIMAL(5,2),
  do_median DECIMAL(5,2),

  -- Duty Days stats
  dd_min INTEGER,
  dd_max INTEGER,
  dd_avg DECIMAL(5,2),
  dd_median DECIMAL(5,2),

  created_at TIMESTAMP DEFAULT NOW(),

  -- One summary per bid period
  CONSTRAINT unique_line_summary UNIQUE(bid_period_id)
);

CREATE INDEX idx_bid_line_summary_bid_period ON bid_line_summary_stats(bid_period_id);

COMMENT ON TABLE bid_line_summary_stats IS 'Pre-computed bid line summary statistics';

-- ============================================
-- VERIFICATION QUERIES
-- ============================================

-- Verify all tables created
SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;

-- Check table row counts (should all be 0)
SELECT
  (SELECT COUNT(*) FROM bid_periods) as bid_periods,
  (SELECT COUNT(*) FROM trips) as trips,
  (SELECT COUNT(*) FROM edw_summary_stats) as edw_summary_stats,
  (SELECT COUNT(*) FROM bid_lines) as bid_lines,
  (SELECT COUNT(*) FROM bid_line_summary_stats) as bid_line_summary_stats;
```

### Step 3.3: Execute Migration

1. Click "Run" button (or press Cmd/Ctrl + Enter)
2. You should see success message: "Success. No rows returned"
3. Scroll down to see verification query results showing all 5 tables

### Step 3.4: Verify Tables

In the Supabase sidebar, click "Table Editor". You should see:
- ✅ `bid_periods`
- ✅ `trips`
- ✅ `edw_summary_stats`
- ✅ `bid_lines`
- ✅ `bid_line_summary_stats`

All tables should be empty (0 rows).

---

## 4. Configure Local Environment

### Step 4.1: Create .env File

In your project root directory, create a new file called `.env`:

```bash
# From project root
touch .env
```

### Step 4.2: Add Credentials

Open `.env` in your text editor and add:

```env
# Supabase Configuration
SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3...

# Optional: Service Role Key (for admin operations)
# SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3...
```

Replace the values with your actual credentials from Step 2.

### Step 4.3: Verify .gitignore

Make sure `.env` is in your `.gitignore` file:

```bash
# Check if .env is ignored
grep -q "^\.env$" .gitignore && echo "✅ .env is ignored" || echo "❌ Add .env to .gitignore"
```

If not present, add it:

```bash
echo ".env" >> .gitignore
```

### Step 4.4: Install Dependencies

```bash
# Activate virtual environment
source .venv/bin/activate

# Install new dependencies
pip install supabase python-dotenv plotly

# Update requirements.txt
pip freeze > requirements.txt
```

---

## 5. Test Connection

### Step 5.1: Create Test Script

Create a file `test_supabase.py` in your project root:

```python
#!/usr/bin/env python3
"""
Test Supabase connection
"""
from supabase import create_client
from dotenv import load_dotenv
import os

def test_connection():
    """Test Supabase connection and query tables."""

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
        print("📊 Querying bid_periods table...")
        response = supabase.table('bid_periods').select('*', count='exact').execute()

        print(f"✅ Connection successful!")
        print(f"   Tables accessible: bid_periods, trips, edw_summary_stats, bid_lines, bid_line_summary_stats")
        print(f"   Current bid_periods count: {len(response.data)}")

        return True

    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_connection()
    exit(0 if success else 1)
```

### Step 5.2: Run Test

```bash
python test_supabase.py
```

**Expected output:**
```
🔌 Connecting to Supabase...
📊 Querying bid_periods table...
✅ Connection successful!
   Tables accessible: bid_periods, trips, edw_summary_stats, bid_lines, bid_line_summary_stats
   Current bid_periods count: 0
```

### Step 5.3: Test Insert (Optional)

Add this function to `test_supabase.py`:

```python
def test_insert():
    """Test inserting a sample bid period."""
    load_dotenv()
    supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_ANON_KEY"))

    try:
        # Insert test bid period
        print("📝 Inserting test bid period...")
        data = {
            "domicile": "TEST",
            "aircraft": "777",
            "bid_period": "9999"
        }
        response = supabase.table('bid_periods').insert(data).execute()

        print(f"✅ Insert successful! ID: {response.data[0]['id']}")

        # Delete test data
        print("🗑️  Cleaning up test data...")
        supabase.table('bid_periods').delete().eq('bid_period', '9999').execute()
        print("✅ Cleanup complete!")

        return True
    except Exception as e:
        print(f"❌ Insert failed: {str(e)}")
        return False

# Add to main
if __name__ == "__main__":
    success = test_connection()
    if success:
        test_insert()
    exit(0 if success else 1)
```

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

### Error: "Row Level Security" (RLS) policy violation

**Cause:** RLS enabled on tables (we haven't enabled it yet).

**Solution:**
For now, we're not using RLS. If this error appears:
1. Go to Table Editor in Supabase
2. Click on the table name
3. Uncheck "Enable RLS"

---

## Next Steps

✅ Supabase project created
✅ Database schema deployed
✅ Environment configured
✅ Connection tested

**You're ready to integrate with the Streamlit app!**

Next, we'll:
1. Create `database.py` module
2. Add save functionality to analyzer pages
3. Build historical trends viewer

Refer to `IMPLEMENTATION_PLAN.md` for full roadmap.

---

## Useful Supabase Resources

- **Dashboard:** https://app.supabase.com
- **Docs:** https://supabase.com/docs
- **Python Client:** https://supabase.com/docs/reference/python/introduction
- **SQL Editor:** Direct SQL query interface
- **Table Editor:** GUI for viewing/editing data
- **Database Logs:** Monitor queries and errors

---

## Security Best Practices

1. ✅ **Never commit `.env`** to git
2. ✅ **Use `anon` key** for client-side operations (safe to expose)
3. ⚠️ **Protect `service_role` key** (admin access, never expose)
4. 💡 **Enable RLS later** for multi-user access control
5. 💡 **Rotate keys periodically** in production
6. 💡 **Use environment-specific projects** (dev, staging, prod)

---

**Setup complete! 🎉**
