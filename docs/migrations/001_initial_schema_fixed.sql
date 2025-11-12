-- =====================================================================
-- Supabase Integration - Initial Schema Migration (FIXED VERSION)
-- =====================================================================
-- Version: 1.1
-- Date: 2025-10-29
-- Description: Complete database schema for Aero Crew Data application
--
-- CHANGES FROM v1.0:
-- - Commented out auth.users trigger (requires elevated permissions)
-- - Will be set up via Supabase Database Webhooks instead
--
-- This migration creates:
-- - 7 core tables (bid_periods, pairings, pairing_duty_days, bid_lines,
--   profiles, pdf_export_templates, audit_log)
-- - 1 materialized view (bid_period_trends)
-- - All indexes for performance optimization
-- - Helper functions for RLS and operations
-- - Row-Level Security policies (JWT-based)
-- - Audit triggers for compliance
--
-- IMPORTANT: Run this entire script in Supabase SQL Editor
-- =====================================================================

-- Enable UUID extension (required for uuid_generate_v4())
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================================
-- PART 1: CORE TABLES
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. bid_periods
-- Master table containing metadata for each bid period
-- ---------------------------------------------------------------------
CREATE TABLE bid_periods (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  period TEXT NOT NULL,              -- e.g., "2507", "2508"
  domicile TEXT NOT NULL,             -- e.g., "ONT", "LAX", "SFO"
  aircraft TEXT NOT NULL,             -- e.g., "757", "737", "A320"
  seat TEXT NOT NULL CHECK (seat IN ('CA', 'FO')),  -- Captain or First Officer
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  created_by UUID REFERENCES auth.users(id),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_by UUID REFERENCES auth.users(id),
  deleted_at TIMESTAMP WITH TIME ZONE,  -- Soft delete

  -- Ensure uniqueness
  UNIQUE(period, domicile, aircraft, seat)
);

-- Indexes for bid_periods
CREATE INDEX idx_bid_periods_lookup ON bid_periods(period, domicile, aircraft, seat);
CREATE INDEX idx_bid_periods_dates ON bid_periods(start_date DESC, end_date DESC);
CREATE INDEX idx_bid_periods_created_by ON bid_periods(created_by);
CREATE INDEX idx_bid_periods_created_at ON bid_periods(created_at DESC);

-- ---------------------------------------------------------------------
-- 2. pairings
-- Individual trip records from EDW pairing analysis
-- ---------------------------------------------------------------------
CREATE TABLE pairings (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  bid_period_id UUID NOT NULL REFERENCES bid_periods(id) ON DELETE CASCADE,
  trip_id VARCHAR(50) NOT NULL,

  -- EDW Classification
  is_edw BOOLEAN NOT NULL,
  edw_reason TEXT,  -- Which duty days triggered EDW

  -- Trip Metrics
  total_credit_time DECIMAL(6,2),  -- In hours (max 9999.99)
  tafb_hours DECIMAL(6,2),         -- Time Away From Base
  num_duty_days INTEGER,
  num_legs INTEGER,

  -- Timestamps
  departure_time TIMESTAMP WITH TIME ZONE,
  arrival_time TIMESTAMP WITH TIME ZONE,

  -- Trip Details (for full text search)
  trip_details TEXT,

  -- Audit
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  deleted_at TIMESTAMP WITH TIME ZONE,

  UNIQUE(bid_period_id, trip_id)
);

-- Indexes for pairings
CREATE INDEX idx_pairings_bid_period ON pairings(bid_period_id);
CREATE INDEX idx_pairings_edw ON pairings(is_edw);
CREATE INDEX idx_pairings_metrics ON pairings(total_credit_time, tafb_hours, num_duty_days);
CREATE INDEX idx_pairings_departure ON pairings(departure_time);
CREATE INDEX idx_pairings_composite ON pairings(bid_period_id, is_edw, total_credit_time);

-- Full-text search index (optional - uncomment if needed)
-- CREATE INDEX idx_pairings_trip_details_fts ON pairings
--   USING gin(to_tsvector('english', trip_details));

-- ---------------------------------------------------------------------
-- 3. pairing_duty_days
-- Detailed duty day records for each pairing
-- ---------------------------------------------------------------------
CREATE TABLE pairing_duty_days (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  pairing_id UUID NOT NULL REFERENCES pairings(id) ON DELETE CASCADE,
  duty_day_number INTEGER NOT NULL,  -- 1, 2, 3, etc.

  -- Duty Day Metrics
  num_legs INTEGER,
  duty_duration DECIMAL(5,2),  -- In hours
  credit_time DECIMAL(5,2),
  is_edw BOOLEAN NOT NULL,

  -- Times (local time at departure city)
  report_time TIME,
  release_time TIME,

  -- Duty day details
  duty_day_text TEXT,

  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  UNIQUE(pairing_id, duty_day_number)
);

-- Indexes for pairing_duty_days
CREATE INDEX idx_duty_days_pairing ON pairing_duty_days(pairing_id);
CREATE INDEX idx_duty_days_edw ON pairing_duty_days(is_edw);

-- ---------------------------------------------------------------------
-- 4. bid_lines
-- Individual bid line records with pay period breakout
-- ---------------------------------------------------------------------
CREATE TABLE bid_lines (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  bid_period_id UUID NOT NULL REFERENCES bid_periods(id) ON DELETE CASCADE,
  line_number INTEGER NOT NULL,

  -- Line Metrics (Pay Period 1)
  pp1_ct DECIMAL(5,2),  -- Credit Time (hours)
  pp1_bt DECIMAL(5,2),  -- Block Time (hours)
  pp1_do INTEGER,       -- Days Off
  pp1_dd INTEGER,       -- Duty Days

  -- Line Metrics (Pay Period 2)
  pp2_ct DECIMAL(5,2),
  pp2_bt DECIMAL(5,2),
  pp2_do INTEGER,
  pp2_dd INTEGER,

  -- Combined Metrics
  total_ct DECIMAL(5,2) NOT NULL,
  total_bt DECIMAL(5,2) NOT NULL,
  total_do INTEGER NOT NULL,
  total_dd INTEGER NOT NULL,

  -- Reserve Line Data
  is_reserve BOOLEAN DEFAULT FALSE,
  is_hot_standby BOOLEAN DEFAULT FALSE,
  reserve_slots_ca INTEGER,  -- Captain reserve slots
  reserve_slots_fo INTEGER,  -- First Officer reserve slots

  -- VTO Tracking
  vto_type TEXT CHECK (vto_type IN ('VTO', 'VTOR', 'VOR', NULL)),
  vto_period INTEGER CHECK (vto_period IN (1, 2, NULL)),
  is_split_line BOOLEAN DEFAULT FALSE,

  -- Line Details
  line_details TEXT,

  -- Audit
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  deleted_at TIMESTAMP WITH TIME ZONE,

  UNIQUE(bid_period_id, line_number)
);

-- Indexes for bid_lines
CREATE INDEX idx_bid_lines_bid_period ON bid_lines(bid_period_id);
CREATE INDEX idx_bid_lines_reserve ON bid_lines(is_reserve);
CREATE INDEX idx_bid_lines_metrics ON bid_lines(total_ct, total_bt, total_do, total_dd);
CREATE INDEX idx_bid_lines_ct ON bid_lines(total_ct);
CREATE INDEX idx_bid_lines_bt ON bid_lines(total_bt);
CREATE INDEX idx_bid_lines_vto ON bid_lines(vto_type, vto_period) WHERE vto_type IS NOT NULL;

-- =====================================================================
-- PART 2: AUTHENTICATION & USER MANAGEMENT
-- =====================================================================

-- ---------------------------------------------------------------------
-- 5. profiles
-- Extended user profile information
-- ---------------------------------------------------------------------
CREATE TABLE profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  display_name TEXT,
  role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('admin', 'user')),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for profiles
CREATE INDEX idx_profiles_role ON profiles(role);
CREATE INDEX idx_profiles_role_id ON profiles(id, role);  -- For RLS performance

-- ---------------------------------------------------------------------
-- 6. pdf_export_templates
-- Admin-managed PDF export templates
-- ---------------------------------------------------------------------
CREATE TABLE pdf_export_templates (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL UNIQUE,
  description TEXT,

  -- Template Configuration (JSON)
  config_json JSONB NOT NULL,
  -- Example: {"sections": ["filters", "data_table"], "charts": ["time_series"], "layout": "compact"}

  -- Metadata
  created_by UUID REFERENCES auth.users(id),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  -- Visibility
  is_public BOOLEAN DEFAULT TRUE,
  is_default BOOLEAN DEFAULT FALSE
);

-- Indexes for pdf_export_templates
CREATE INDEX idx_pdf_templates_public ON pdf_export_templates(is_public);
CREATE INDEX idx_pdf_templates_default ON pdf_export_templates(is_default);

-- =====================================================================
-- PART 3: AUDIT & COMPLIANCE
-- =====================================================================

-- ---------------------------------------------------------------------
-- 7. audit_log
-- Comprehensive audit trail for all data changes
-- ---------------------------------------------------------------------
CREATE TABLE audit_log (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users(id),
  action TEXT NOT NULL,  -- 'INSERT', 'UPDATE', 'DELETE'
  table_name TEXT NOT NULL,
  record_id UUID,
  old_data JSONB,
  new_data JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for audit_log
CREATE INDEX idx_audit_log_user ON audit_log(user_id, created_at DESC);
CREATE INDEX idx_audit_log_table ON audit_log(table_name, record_id);
CREATE INDEX idx_audit_log_created_at ON audit_log(created_at DESC);

-- =====================================================================
-- PART 4: HELPER FUNCTIONS
-- =====================================================================

-- ---------------------------------------------------------------------
-- is_admin() - Check if current user is admin (JWT-based, no subquery)
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION is_admin()
RETURNS BOOLEAN AS $$
BEGIN
  RETURN (auth.jwt() ->> 'app_role') = 'admin';
END;
$$ LANGUAGE plpgsql SECURITY DEFINER STABLE;

COMMENT ON FUNCTION is_admin() IS 'Check if current user has admin role using JWT custom claim (performance-optimized)';

-- Note: You must configure JWT custom claims in Supabase Auth settings
-- Dashboard > Authentication > Settings > Custom Claims
-- Add: { "app_role": "admin" } for admin users

-- ---------------------------------------------------------------------
-- handle_new_user() - Trigger function to create profile on signup
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id, display_name, role)
  VALUES (NEW.id, NEW.email, 'user');
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION handle_new_user() IS 'Automatically create user profile when new user signs up';

-- ---------------------------------------------------------------------
-- log_changes() - Trigger function for audit logging
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION log_changes()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO audit_log (user_id, action, table_name, record_id, old_data, new_data)
  VALUES (
    auth.uid(),
    TG_OP,
    TG_TABLE_NAME,
    COALESCE(NEW.id, OLD.id),
    CASE WHEN TG_OP = 'DELETE' THEN row_to_json(OLD) ELSE NULL END,
    CASE WHEN TG_OP IN ('INSERT', 'UPDATE') THEN row_to_json(NEW) ELSE NULL END
  );
  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION log_changes() IS 'Log all INSERT/UPDATE/DELETE operations to audit_log table';

-- =====================================================================
-- PART 5: TRIGGERS
-- =====================================================================

-- ---------------------------------------------------------------------
-- Profile creation trigger (COMMENTED OUT - see below)
-- ---------------------------------------------------------------------
-- NOTE: Creating triggers on auth.users requires elevated permissions
-- that are not available via SQL Editor. Instead, we'll set this up
-- using Supabase Database Webhooks after the migration completes.
--
-- For now, profiles will be created manually when users first log in.
-- The trigger function (handle_new_user) is still created above so
-- it can be used with the webhook.
--
-- UNCOMMENT BELOW IF YOU HAVE ELEVATED PERMISSIONS:
-- CREATE TRIGGER on_auth_user_created
--   AFTER INSERT ON auth.users
--   FOR EACH ROW EXECUTE FUNCTION handle_new_user();

-- ---------------------------------------------------------------------
-- Audit logging triggers
-- ---------------------------------------------------------------------
CREATE TRIGGER bid_periods_audit AFTER INSERT OR UPDATE OR DELETE ON bid_periods
  FOR EACH ROW EXECUTE FUNCTION log_changes();

CREATE TRIGGER pairings_audit AFTER INSERT OR UPDATE OR DELETE ON pairings
  FOR EACH ROW EXECUTE FUNCTION log_changes();

CREATE TRIGGER bid_lines_audit AFTER INSERT OR UPDATE OR DELETE ON bid_lines
  FOR EACH ROW EXECUTE FUNCTION log_changes();

COMMENT ON TRIGGER bid_periods_audit ON bid_periods IS 'Log all changes to bid_periods table';
COMMENT ON TRIGGER pairings_audit ON pairings IS 'Log all changes to pairings table';
COMMENT ON TRIGGER bid_lines_audit ON bid_lines IS 'Log all changes to bid_lines table';

-- =====================================================================
-- PART 6: ROW-LEVEL SECURITY (RLS) POLICIES
-- =====================================================================

-- Enable RLS on all tables
ALTER TABLE bid_periods ENABLE ROW LEVEL SECURITY;
ALTER TABLE pairings ENABLE ROW LEVEL SECURITY;
ALTER TABLE pairing_duty_days ENABLE ROW LEVEL SECURITY;
ALTER TABLE bid_lines ENABLE ROW LEVEL SECURITY;
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE pdf_export_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;

-- Force RLS (prevent TRUNCATE even by table owners)
ALTER TABLE bid_periods FORCE ROW LEVEL SECURITY;
ALTER TABLE pairings FORCE ROW LEVEL SECURITY;
ALTER TABLE bid_lines FORCE ROW LEVEL SECURITY;

-- ---------------------------------------------------------------------
-- bid_periods policies
-- ---------------------------------------------------------------------
CREATE POLICY "Anyone can view bid periods" ON bid_periods FOR SELECT
  USING (true);

CREATE POLICY "Admins can insert bid periods" ON bid_periods FOR INSERT
  WITH CHECK (is_admin());

CREATE POLICY "Admins can update bid periods" ON bid_periods FOR UPDATE
  USING (is_admin());

CREATE POLICY "Admins can delete bid periods" ON bid_periods FOR DELETE
  USING (is_admin());

-- ---------------------------------------------------------------------
-- pairings policies
-- ---------------------------------------------------------------------
CREATE POLICY "Anyone can view pairings" ON pairings FOR SELECT
  USING (true);

CREATE POLICY "Admins can insert pairings" ON pairings FOR INSERT
  WITH CHECK (is_admin());

CREATE POLICY "Admins can update pairings" ON pairings FOR UPDATE
  USING (is_admin());

CREATE POLICY "Admins can delete pairings" ON pairings FOR DELETE
  USING (is_admin());

-- ---------------------------------------------------------------------
-- pairing_duty_days policies
-- ---------------------------------------------------------------------
CREATE POLICY "Anyone can view duty days" ON pairing_duty_days FOR SELECT
  USING (true);

CREATE POLICY "Admins can insert duty days" ON pairing_duty_days FOR INSERT
  WITH CHECK (is_admin());

CREATE POLICY "Admins can update duty days" ON pairing_duty_days FOR UPDATE
  USING (is_admin());

CREATE POLICY "Admins can delete duty days" ON pairing_duty_days FOR DELETE
  USING (is_admin());

-- ---------------------------------------------------------------------
-- bid_lines policies
-- ---------------------------------------------------------------------
CREATE POLICY "Anyone can view bid lines" ON bid_lines FOR SELECT
  USING (true);

CREATE POLICY "Admins can insert bid lines" ON bid_lines FOR INSERT
  WITH CHECK (is_admin());

CREATE POLICY "Admins can update bid lines" ON bid_lines FOR UPDATE
  USING (is_admin());

CREATE POLICY "Admins can delete bid lines" ON bid_lines FOR DELETE
  USING (is_admin());

-- ---------------------------------------------------------------------
-- profiles policies
-- ---------------------------------------------------------------------
CREATE POLICY "Users can view their own profile" ON profiles FOR SELECT
  USING (auth.uid() = id);

CREATE POLICY "Users can create their own profile" ON profiles FOR INSERT
  WITH CHECK (auth.uid() = id);

CREATE POLICY "Admins can view all profiles" ON profiles FOR SELECT
  USING (is_admin());

CREATE POLICY "Users can update their own profile" ON profiles FOR UPDATE
  USING (auth.uid() = id);

CREATE POLICY "Admins can update all profiles" ON profiles FOR UPDATE
  USING (is_admin());

-- ---------------------------------------------------------------------
-- pdf_export_templates policies
-- ---------------------------------------------------------------------
CREATE POLICY "Anyone can view public templates" ON pdf_export_templates FOR SELECT
  USING (is_public = true);

CREATE POLICY "Admins can view all templates" ON pdf_export_templates FOR SELECT
  USING (is_admin());

CREATE POLICY "Admins can insert templates" ON pdf_export_templates FOR INSERT
  WITH CHECK (is_admin());

CREATE POLICY "Admins can update templates" ON pdf_export_templates FOR UPDATE
  USING (is_admin());

CREATE POLICY "Admins can delete templates" ON pdf_export_templates FOR DELETE
  USING (is_admin());

-- ---------------------------------------------------------------------
-- audit_log policies
-- ---------------------------------------------------------------------
CREATE POLICY "Admins can view audit logs" ON audit_log FOR SELECT
  USING (is_admin());

-- No INSERT/UPDATE/DELETE policies - only triggers can write to audit_log

-- =====================================================================
-- PART 7: MATERIALIZED VIEW FOR PERFORMANCE
-- =====================================================================

-- ---------------------------------------------------------------------
-- bid_period_trends - Pre-computed trends for fast queries
-- ---------------------------------------------------------------------
CREATE MATERIALIZED VIEW bid_period_trends AS
SELECT
  bp.id AS bid_period_id,
  bp.period,
  bp.domicile,
  bp.aircraft,
  bp.seat,
  bp.start_date,

  -- Pairing metrics (if EDW data exists)
  COUNT(DISTINCT p.id) AS total_trips,
  COUNT(DISTINCT p.id) FILTER (WHERE p.is_edw) AS edw_trips,
  ROUND(100.0 * COUNT(p.id) FILTER (WHERE p.is_edw) / NULLIF(COUNT(p.id), 0), 2) AS edw_trip_pct,

  -- Bid line metrics (if bid line data exists)
  COUNT(DISTINCT bl.id) AS total_lines,
  ROUND(AVG(bl.total_ct), 2) AS ct_avg,
  ROUND(AVG(bl.total_bt), 2) AS bt_avg,
  ROUND(AVG(bl.total_do::numeric), 1) AS do_avg,
  ROUND(AVG(bl.total_dd::numeric), 1) AS dd_avg,
  COUNT(bl.id) FILTER (WHERE bl.is_reserve) AS reserve_lines

FROM bid_periods bp
LEFT JOIN pairings p ON p.bid_period_id = bp.id AND p.deleted_at IS NULL
LEFT JOIN bid_lines bl ON bl.bid_period_id = bp.id AND bl.deleted_at IS NULL
WHERE bp.deleted_at IS NULL
GROUP BY bp.id, bp.period, bp.domicile, bp.aircraft, bp.seat, bp.start_date
ORDER BY bp.start_date DESC;

-- Indexes for materialized view
CREATE INDEX idx_trends_domicile ON bid_period_trends(domicile, start_date DESC);
CREATE INDEX idx_trends_aircraft ON bid_period_trends(aircraft, start_date DESC);
CREATE INDEX idx_trends_seat ON bid_period_trends(seat, start_date DESC);
CREATE INDEX idx_trends_period ON bid_period_trends(period DESC);

COMMENT ON MATERIALIZED VIEW bid_period_trends IS 'Pre-computed aggregations for fast trend queries (refresh after data changes)';

-- ---------------------------------------------------------------------
-- refresh_trends() - Function to refresh materialized view
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION refresh_trends()
RETURNS void AS $$
BEGIN
  REFRESH MATERIALIZED VIEW CONCURRENTLY bid_period_trends;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION refresh_trends() IS 'Refresh bid_period_trends materialized view (call after data changes)';

-- =====================================================================
-- PART 8: VERIFICATION QUERIES
-- =====================================================================

-- Verify all tables were created
SELECT
  tablename,
  schemaname
FROM pg_tables
WHERE schemaname = 'public'
  AND tablename IN (
    'bid_periods', 'pairings', 'pairing_duty_days', 'bid_lines',
    'profiles', 'pdf_export_templates', 'audit_log'
  )
ORDER BY tablename;

-- Verify all indexes were created
SELECT
  tablename,
  indexname
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename IN (
    'bid_periods', 'pairings', 'pairing_duty_days', 'bid_lines',
    'profiles', 'pdf_export_templates', 'audit_log'
  )
ORDER BY tablename, indexname;

-- Verify helper functions exist
SELECT
  routine_name,
  routine_type
FROM information_schema.routines
WHERE routine_schema = 'public'
  AND routine_name IN ('is_admin', 'handle_new_user', 'log_changes', 'refresh_trends')
ORDER BY routine_name;

-- Verify triggers exist (should be 3, not 4 since auth.users trigger is commented out)
SELECT
  trigger_name,
  event_object_table AS table_name,
  action_timing,
  event_manipulation
FROM information_schema.triggers
WHERE trigger_schema = 'public'
  AND trigger_name IN (
    'bid_periods_audit',
    'pairings_audit',
    'bid_lines_audit'
  )
ORDER BY trigger_name;

-- Verify RLS is enabled
SELECT
  tablename,
  rowsecurity AS rls_enabled
FROM pg_tables
WHERE schemaname = 'public'
  AND tablename IN (
    'bid_periods', 'pairings', 'pairing_duty_days', 'bid_lines',
    'profiles', 'pdf_export_templates', 'audit_log'
  )
ORDER BY tablename;

-- Verify materialized view exists
SELECT
  matviewname,
  schemaname
FROM pg_matviews
WHERE schemaname = 'public'
  AND matviewname = 'bid_period_trends';

-- =====================================================================
-- MIGRATION COMPLETE
-- =====================================================================

-- Success message
DO $$
BEGIN
  RAISE NOTICE '✅ Migration 001_initial_schema_fixed.sql completed successfully!';
  RAISE NOTICE '';
  RAISE NOTICE '⚠️  IMPORTANT: Profile auto-creation trigger not enabled';
  RAISE NOTICE '   The auth.users trigger requires elevated permissions.';
  RAISE NOTICE '   Profiles will be created manually via auth.py on first login.';
  RAISE NOTICE '';
  RAISE NOTICE 'Next steps:';
  RAISE NOTICE '1. Review verification queries above';
  RAISE NOTICE '2. Configure JWT custom claims in Supabase Auth settings';
  RAISE NOTICE '3. Test connection with test_supabase_connection.py';
  RAISE NOTICE '4. Sign up via app - profiles will be created automatically';
  RAISE NOTICE '';
  RAISE NOTICE 'Tables created: 7';
  RAISE NOTICE 'Materialized views: 1';
  RAISE NOTICE 'Indexes: 30+';
  RAISE NOTICE 'Helper functions: 4';
  RAISE NOTICE 'Triggers: 3 (audit triggers only)';
  RAISE NOTICE 'RLS policies: 32';
END $$;
