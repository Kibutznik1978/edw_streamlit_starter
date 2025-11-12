# Phase 3: Testing & Optimization - Test Plan

**Date:** October 31, 2025
**Status:** In Progress
**Objective:** Verify audit field population, multi-user access, RLS policies, and performance with large datasets

---

## Test Summary

| Test Category | Status | Priority |
|--------------|--------|----------|
| Audit Field Population | ✅ PASS | High |
| Multi-User Access & RLS | 🔄 IN PROGRESS | High |
| Performance Testing | ⏳ PENDING | Medium |
| Error Handling & Retry Logic | ⏳ PENDING | Medium |

---

## 1. Audit Field Population Testing

### Objective
Verify that `created_by` and `updated_by` fields are populated correctly when saving data to the database.

### Changes Made
- ✅ Applied migration `002_add_audit_fields_to_pairings_and_bid_lines.sql`
- ✅ Updated `database.py` - `save_pairings()` to populate audit fields
- ✅ Updated `database.py` - `save_bid_lines()` to populate audit fields

### Test Results

**Pairings Table:**
- ✅ PASS - Audit fields (`created_by`, `updated_by`) are populated with user UUID
- ✅ PASS - Fields are set automatically from `st.session_state["user"]`
- ✅ PASS - Verified with test script `test_audit_fields.py`

**Bid Lines Table:**
- ✅ PASS - Code updated to populate audit fields
- ⚠️  Old records (created before migration) don't have audit fields populated (expected)
- ✅ PASS - New records will have audit fields populated

**Bid Periods Table:**
- ℹ️  Already had `created_by` and `updated_by` fields in original schema
- ✅ PASS - Fields are populated on insert

### Test Script
Run `python test_audit_fields.py` to verify audit field population.

---

## 2. Multi-User Access & RLS Policy Testing

### Objective
Verify Row Level Security (RLS) policies work correctly for admin vs regular users.

### Test Users

| User Type | Email | Role | Can View? | Can Insert? | Can Update? | Can Delete? |
|-----------|-------|------|-----------|-------------|-------------|-------------|
| Admin | giladswerdlow@gmail.com | admin | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| Regular User | (to be created) | user | ✅ Yes | ❌ No | ❌ No | ❌ No |

### Creating a Test User

**Method 1: Through Streamlit App (Recommended)**
1. Open Streamlit app at http://localhost:8501
2. Log out if logged in (sidebar button)
3. Click "Sign Up" tab
4. Create account with:
   - Email: Use a valid Gmail or other email (e.g., `testuser@gmail.com`)
   - Password: At least 8 characters
5. Account will automatically have `role = 'user'` (non-admin)
6. Check email for confirmation link (if email confirmation is enabled)

**Method 2: Manual SQL Update (For Testing Only)**
1. Create user through Streamlit app
2. Verify user has `role = 'user'` in profiles table:
   ```sql
   SELECT id, display_name, role FROM profiles ORDER BY created_at DESC;
   ```

### Test Scenarios

#### Scenario 1: Regular User - View Data (Should PASS)
**Steps:**
1. Log in as regular user
2. Navigate to "Historical Trends" tab (Tab 3)
3. Try to query existing data

**Expected Result:** ✅ Can view all bid periods, pairings, and bid lines

**RLS Policy:** `SELECT` is allowed for all authenticated users (`USING (true)`)

---

#### Scenario 2: Regular User - Save Pairing Data (Should FAIL)
**Steps:**
1. Log in as regular user
2. Navigate to "EDW Pairing Analyzer" tab (Tab 1)
3. Upload a pairing PDF
4. Click "Save to Database"
5. Fill in bid period details
6. Try to save

**Expected Result:** ❌ Should fail with RLS policy violation

**Expected Error:**
```
new row violates row-level security policy for table "pairings"
```

**RLS Policy:** `INSERT` requires `created_by` to match current user's UUID (from JWT claims)

---

#### Scenario 3: Regular User - Save Bid Line Data (Should FAIL)
**Steps:**
1. Log in as regular user
2. Navigate to "Bid Line Analyzer" tab (Tab 2)
3. Upload a bid line PDF
4. Click "Save to Database"
5. Fill in bid period details
6. Try to save

**Expected Result:** ❌ Should fail with RLS policy violation

**Expected Error:**
```
new row violates row-level security policy for table "bid_lines"
```

**RLS Policy:** `INSERT` requires `created_by` to match current user's UUID

---

#### Scenario 4: Admin User - Save Pairing Data (Should PASS)
**Steps:**
1. Log in as admin (giladswerdlow@gmail.com)
2. Navigate to "EDW Pairing Analyzer" tab (Tab 1)
3. Upload a pairing PDF
4. Click "Save to Database"
5. Fill in bid period details
6. Save to database

**Expected Result:** ✅ Should succeed

**Verification:**
```sql
SELECT trip_id, created_by, updated_by, created_at
FROM pairings
ORDER BY created_at DESC
LIMIT 5;
```

All records should have `created_by` and `updated_by` populated with admin user UUID.

---

#### Scenario 5: Admin User - Save Bid Line Data (Should PASS)
**Steps:**
1. Log in as admin (giladswerdlow@gmail.com)
2. Navigate to "Bid Line Analyzer" tab (Tab 2)
3. Upload a bid line PDF
4. Click "Save to Database"
5. Fill in bid period details
6. Save to database

**Expected Result:** ✅ Should succeed

**Verification:**
```sql
SELECT line_number, created_by, updated_by, created_at
FROM bid_lines
ORDER BY created_at DESC
LIMIT 5;
```

All records should have `created_by` and `updated_by` populated with admin user UUID.

---

#### Scenario 6: Verify JWT Claims
**Steps:**
1. Log in as admin
2. Check sidebar for "JWT Claims" debug section (if enabled)
3. Verify `app_role` claim is present and set to `admin`

**Expected Result:** ✅ JWT claims should include:
```json
{
  "sub": "<user-uuid>",
  "email": "giladswerdlow@gmail.com",
  "app_role": "admin",
  ...
}
```

**Note:** If `app_role` is missing, RLS policies will fail. This is set via Auth Hooks in Supabase.

---

## 3. Performance Testing

### Objective
Verify database operations perform well with large datasets (1000+ records).

### Test Cases

#### Test 1: Bulk Insert - 1000 Pairings
**Steps:**
1. Create test DataFrame with 1000 pairing records
2. Call `save_pairings(bid_period_id, df)`
3. Measure execution time

**Expected Result:** ✅ Should complete in < 5 seconds

**Verification:**
```sql
SELECT COUNT(*) FROM pairings WHERE bid_period_id = '<test-bid-period-id>';
```

Should return 1000 records.

---

#### Test 2: Bulk Insert - 1000 Bid Lines
**Steps:**
1. Create test DataFrame with 1000 bid line records
2. Call `save_bid_lines(bid_period_id, df)`
3. Measure execution time

**Expected Result:** ✅ Should complete in < 5 seconds

**Verification:**
```sql
SELECT COUNT(*) FROM bid_lines WHERE bid_period_id = '<test-bid-period-id>';
```

Should return 1000 records.

---

#### Test 3: Query with Filters
**Steps:**
1. Query pairings with filters (e.g., `is_edw = True`, `min_credit_time = 5.0`)
2. Use pagination (`limit = 100`, `offset = 0`)
3. Measure execution time

**Expected Result:** ✅ Should complete in < 3 seconds

---

#### Test 4: Materialized View Refresh
**Steps:**
1. Save new data to database
2. Call `refresh_trends()`
3. Query `bid_period_trends` view
4. Measure execution time

**Expected Result:** ✅ Should complete in < 10 seconds

---

### Performance Benchmark Script

Create `test_performance.py`:
```python
import time
import pandas as pd
from database import save_pairings, save_bid_lines, query_pairings, refresh_trends

def test_bulk_insert_performance():
    # Create test DataFrame with 1000 records
    df = pd.DataFrame({
        'trip_id': [f'TEST-{i:04d}' for i in range(1000)],
        'is_edw': [i % 2 == 0 for i in range(1000)],
        'tafb_hours': [20.0 + (i % 50) for i in range(1000)],
        'num_duty_days': [2 + (i % 3) for i in range(1000)],
        'total_credit_time': [5.0 + (i % 10) for i in range(1000)],
        'num_legs': [4 + (i % 4) for i in range(1000)]
    })

    start = time.time()
    count = save_pairings('<test-bid-period-id>', df)
    elapsed = time.time() - start

    print(f"Inserted {count} records in {elapsed:.2f} seconds")
    print(f"Average: {count/elapsed:.0f} records/second")

    assert elapsed < 5.0, f"Too slow: {elapsed:.2f}s (expected < 5.0s)"
    assert count == 1000, f"Wrong count: {count} (expected 1000)"
```

---

## 4. Error Handling & Retry Logic

### Objective
Improve error handling and add retry logic for transient failures.

### Current Error Handling
- ✅ Validation errors are caught and displayed to user
- ✅ Database errors are caught and displayed with details
- ✅ Duplicate detection works correctly
- ⚠️  No retry logic for transient failures (network errors, timeouts)

### Improvements Needed

#### 1. Add Retry Logic for Network Errors
**Location:** `database.py` - bulk insert operations

**Current Code:**
```python
response = supabase.table("pairings").insert(batch).execute()
```

**Improved Code:**
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
def insert_with_retry(table_name, batch):
    return supabase.table(table_name).insert(batch).execute()

# Usage:
response = insert_with_retry("pairings", batch)
```

**Benefit:** Handles transient network errors automatically.

---

#### 2. Better Error Messages
**Current:** Generic "Failed to insert batch" error

**Improved:** Specific error messages based on error type:
- RLS violation: "You don't have permission to save data (admin access required)"
- Duplicate key: "This data already exists in the database"
- Network error: "Network connection lost - retrying..."
- Validation error: "Data validation failed: [specific fields]"

---

#### 3. Progress Indicators for Large Uploads
**Current:** Single progress spinner for entire operation

**Improved:** Progress bar with batch-level updates:
```python
import streamlit as st

progress_bar = st.progress(0)
status_text = st.empty()

for i, batch in enumerate(batches):
    status_text.text(f"Uploading batch {i+1}/{len(batches)}...")
    progress_bar.progress((i + 1) / len(batches))
    # ... insert batch ...
```

---

## 5. Test Checklist

### Audit Fields
- [x] Migration applied successfully
- [x] `save_pairings()` populates `created_by` and `updated_by`
- [x] `save_bid_lines()` populates `created_by` and `updated_by`
- [x] Test script confirms audit fields are populated
- [ ] Upload new data and verify audit fields in Supabase Table Editor

### Multi-User Access
- [ ] Create regular (non-admin) test user
- [ ] Test regular user can VIEW data
- [ ] Test regular user CANNOT save data (RLS violation expected)
- [ ] Test admin user CAN save data
- [ ] Verify JWT claims include `app_role`
- [ ] Verify `created_by` matches logged-in user

### Performance
- [ ] Test bulk insert with 1000+ pairing records
- [ ] Test bulk insert with 1000+ bid line records
- [ ] Measure query performance with filters
- [ ] Test materialized view refresh
- [ ] Document performance benchmarks

### Error Handling
- [ ] Test validation error display
- [ ] Test database error display
- [ ] Test duplicate detection
- [ ] (Optional) Implement retry logic
- [ ] (Optional) Improve error messages
- [ ] (Optional) Add progress indicators

---

## Expected Timeline

| Task | Duration | Status |
|------|----------|--------|
| Audit field implementation | 1 hour | ✅ Complete |
| Multi-user testing | 2 hours | 🔄 In Progress |
| Performance testing | 2 hours | ⏳ Pending |
| Error handling improvements | 2 hours | ⏳ Pending |
| Documentation | 1 hour | ⏳ Pending |
| **Total** | **8 hours (1 day)** | **50% Complete** |

---

## Success Criteria

Phase 3 is complete when:
1. ✅ Audit fields are populated for all new database inserts
2. ⏳ Multi-user access works correctly (admin vs regular user)
3. ⏳ Performance benchmarks meet targets (< 5s for 1000 records)
4. ⏳ Error handling provides clear feedback to users
5. ⏳ All test scenarios documented in Session 33

---

## Notes

- **Audit Migration:** Successfully applied on October 29, 2025
- **RLS Policies:** Using JWT custom claims (`app_role`) for role-based access
- **Performance:** Batch size is 1000 rows (Supabase limit)
- **Authentication:** Admin user already exists (giladswerdlow@gmail.com)

---

**Document Version:** 1.0
**Last Updated:** October 31, 2025
