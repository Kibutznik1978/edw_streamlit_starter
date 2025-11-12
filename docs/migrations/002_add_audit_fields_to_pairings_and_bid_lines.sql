-- Migration: Add audit fields (created_by, updated_by) to pairings and bid_lines tables
-- Date: 2025-10-29
-- Description: Add created_by and updated_by columns to support RLS policies

-- Add audit fields to pairings table
ALTER TABLE public.pairings
  ADD COLUMN created_by uuid REFERENCES auth.users(id),
  ADD COLUMN updated_by uuid REFERENCES auth.users(id);

-- Add audit fields to bid_lines table
ALTER TABLE public.bid_lines
  ADD COLUMN created_by uuid REFERENCES auth.users(id),
  ADD COLUMN updated_by uuid REFERENCES auth.users(id);

-- Add indexes for performance
CREATE INDEX idx_pairings_created_by ON public.pairings(created_by);
CREATE INDEX idx_pairings_updated_by ON public.pairings(updated_by);
CREATE INDEX idx_bid_lines_created_by ON public.bid_lines(created_by);
CREATE INDEX idx_bid_lines_updated_by ON public.bid_lines(updated_by);

-- Update RLS policies to use the new audit fields

-- Pairings table policies
DROP POLICY IF EXISTS "pairings_select_policy" ON public.pairings;
DROP POLICY IF EXISTS "pairings_insert_policy" ON public.pairings;
DROP POLICY IF EXISTS "pairings_update_policy" ON public.pairings;
DROP POLICY IF EXISTS "pairings_delete_policy" ON public.pairings;

CREATE POLICY "pairings_select_policy" ON public.pairings
  FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "pairings_insert_policy" ON public.pairings
  FOR INSERT
  TO authenticated
  WITH CHECK (
    created_by = (current_setting('request.jwt.claims', true)::json->>'sub')::uuid
  );

CREATE POLICY "pairings_update_policy" ON public.pairings
  FOR UPDATE
  TO authenticated
  USING (
    created_by = (current_setting('request.jwt.claims', true)::json->>'sub')::uuid
    OR public.is_admin()
  )
  WITH CHECK (
    updated_by = (current_setting('request.jwt.claims', true)::json->>'sub')::uuid
  );

CREATE POLICY "pairings_delete_policy" ON public.pairings
  FOR DELETE
  TO authenticated
  USING (
    created_by = (current_setting('request.jwt.claims', true)::json->>'sub')::uuid
    OR public.is_admin()
  );

-- Bid lines table policies
DROP POLICY IF EXISTS "bid_lines_select_policy" ON public.bid_lines;
DROP POLICY IF EXISTS "bid_lines_insert_policy" ON public.bid_lines;
DROP POLICY IF EXISTS "bid_lines_update_policy" ON public.bid_lines;
DROP POLICY IF EXISTS "bid_lines_delete_policy" ON public.bid_lines;

CREATE POLICY "bid_lines_select_policy" ON public.bid_lines
  FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "bid_lines_insert_policy" ON public.bid_lines
  FOR INSERT
  TO authenticated
  WITH CHECK (
    created_by = (current_setting('request.jwt.claims', true)::json->>'sub')::uuid
  );

CREATE POLICY "bid_lines_update_policy" ON public.bid_lines
  FOR UPDATE
  TO authenticated
  USING (
    created_by = (current_setting('request.jwt.claims', true)::json->>'sub')::uuid
    OR public.is_admin()
  )
  WITH CHECK (
    updated_by = (current_setting('request.jwt.claims', true)::json->>'sub')::uuid
  );

CREATE POLICY "bid_lines_delete_policy" ON public.bid_lines
  FOR DELETE
  TO authenticated
  USING (
    created_by = (current_setting('request.jwt.claims', true)::json->>'sub')::uuid
    OR public.is_admin()
  );

-- Refresh schema cache
NOTIFY pgrst, 'reload schema';
