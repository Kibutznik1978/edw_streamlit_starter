-- POC 4: Test Table with RLS Policies
-- This creates a simple test table to validate JWT/RLS integration

-- Create test table
CREATE TABLE IF NOT EXISTS public.poc_test_data (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL,
    title TEXT NOT NULL,
    content TEXT,
    is_public BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE public.poc_test_data ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist
DROP POLICY IF EXISTS "Users can view their own data" ON public.poc_test_data;
DROP POLICY IF EXISTS "Users can insert their own data" ON public.poc_test_data;
DROP POLICY IF EXISTS "Users can update their own data" ON public.poc_test_data;
DROP POLICY IF EXISTS "Users can delete their own data" ON public.poc_test_data;
DROP POLICY IF EXISTS "Admins can view all data" ON public.poc_test_data;

-- Policy 1: Users can view their own data
CREATE POLICY "Users can view their own data"
ON public.poc_test_data
FOR SELECT
USING (auth.uid() = user_id);

-- Policy 2: Users can insert their own data
CREATE POLICY "Users can insert their own data"
ON public.poc_test_data
FOR INSERT
WITH CHECK (auth.uid() = user_id);

-- Policy 3: Users can update their own data
CREATE POLICY "Users can update their own data"
ON public.poc_test_data
FOR UPDATE
USING (auth.uid() = user_id);

-- Policy 4: Users can delete their own data
CREATE POLICY "Users can delete their own data"
ON public.poc_test_data
FOR DELETE
USING (auth.uid() = user_id);

-- Policy 5: Admins can view all data
-- This policy checks for a custom claim in the JWT
CREATE POLICY "Admins can view all data"
ON public.poc_test_data
FOR SELECT
USING (
    (auth.jwt() ->> 'user_role')::text = 'admin'
);

-- Insert sample data for testing
-- NOTE: Replace these UUIDs with actual user IDs from your Supabase Auth users
-- You can get user IDs from: Supabase Dashboard > Authentication > Users

-- Sample data for user 1 (replace with real user ID)
INSERT INTO public.poc_test_data (user_id, title, content, is_public)
VALUES
    ('00000000-0000-0000-0000-000000000001', 'User 1 - Private Post', 'This is a private post for user 1', false),
    ('00000000-0000-0000-0000-000000000001', 'User 1 - Public Post', 'This is a public post for user 1', true);

-- Sample data for user 2 (replace with real user ID)
INSERT INTO public.poc_test_data (user_id, title, content, is_public)
VALUES
    ('00000000-0000-0000-0000-000000000002', 'User 2 - Private Post', 'This is a private post for user 2', false),
    ('00000000-0000-0000-0000-000000000002', 'User 2 - Public Post', 'This is a public post for user 2', true);

-- Verify RLS is enabled
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public' AND tablename = 'poc_test_data';

-- View all policies
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual, with_check
FROM pg_policies
WHERE schemaname = 'public' AND tablename = 'poc_test_data';
