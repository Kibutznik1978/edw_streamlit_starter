# POC 4: JWT Authentication with Supabase

## Overview

This POC tests JWT session handling and RLS (Row Level Security) policy enforcement in Reflex with Supabase Auth.

## Critical Requirements

1. ✅ Login with Supabase Auth (email/password)
2. ✅ JWT custom claims propagation (user_role)
3. ✅ RLS policy enforcement (admin vs regular user)
4. ✅ Session persistence across page reloads
5. ✅ Secure JWT storage

## Success Criteria

- [ ] Supabase login functional
- [ ] JWT token stored securely in Reflex State
- [ ] Custom claims accessible (user_id, user_role)
- [ ] RLS policies enforced correctly (admin can see all, users see own data)
- [ ] Session persists on page reload
- [ ] JWT expiration/refresh works

## Setup

### Prerequisites

1. **Supabase Project Setup**:
   - Create Supabase project at https://supabase.com
   - Note your `SUPABASE_URL` and `SUPABASE_ANON_KEY`
   - Create test users (admin + regular user)

2. **Database Setup**:
   - Run the SQL migration in `sql/poc_test_table.sql`
   - This creates a `poc_test_data` table with RLS policies

3. **Environment Configuration**:
   ```bash
   # Copy .env.example to .env and fill in credentials
   cp ../../.env.example .env

   # Edit .env with your Supabase credentials
   SUPABASE_URL=https://xxxxx.supabase.co
   SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Initialize Reflex (first time only)
reflex init

# Run the POC
reflex run
```

The app will be available at http://localhost:3000

## Testing Instructions

### Test 1: Admin Login
1. Login with admin email (set in Supabase)
2. Verify JWT token appears
3. Verify user_role shows "admin"
4. Check RLS results: ✅ Can query all data, ✅ Can query own data

### Test 2: Regular User Login
1. Logout and login with regular user email
2. Verify JWT token appears
3. Verify user_role shows "user"
4. Check RLS results: ❌ Cannot query all data, ✅ Can query own data

### Test 3: Session Persistence
1. Login as any user
2. Refresh the browser page
3. Verify user remains logged in
4. Verify JWT token persists

### Test 4: JWT Expiration
1. Login and note the expiration time
2. Wait for token to expire (or simulate)
3. Verify automatic refresh or re-authentication

## Critical Questions

- ❓ How to pass JWT to Supabase client in Reflex?
- ❓ Does Supabase-py work with Reflex's async state?
- ❓ How to persist JWT across page reloads?
- ❓ Can we use cookies or local storage for JWT?

## Risk Assessment

**Risk Level**: 🟡 MEDIUM

**Known Issues**:
- Reflex State is server-side only - JWT persistence may require client-side storage
- Cookie-based session management may be needed
- JWT refresh logic needs careful implementation

## Files

- `poc_jwt_auth.py` - Main POC implementation
- `rxconfig.py` - Reflex configuration
- `requirements.txt` - Python dependencies
- `sql/poc_test_table.sql` - Database schema and RLS policies
- `README.md` - This file

## Expected Outcome

**PASS Criteria**:
- All 4 test scenarios work correctly
- JWT propagates to Supabase client
- RLS policies enforce based on JWT claims
- Session persists across page reloads

**FAIL Criteria**:
- Cannot extract JWT custom claims
- RLS policies don't enforce correctly
- Session lost on page reload with no viable fix
- Security vulnerabilities in JWT handling

## Next Steps After POC

If POC passes:
- ✅ Proceed to final GO/NO-GO decision (Day 5 EOD)
- ✅ Document findings in `docs/phase0_poc4_findings.md`
- ✅ Update migration plan with any adjustments

If POC has issues:
- Document blockers and mitigation strategies
- Assess risk to overall migration
- Escalate to stakeholders if critical
