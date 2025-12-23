-- Supabase Schema for Serverless Meal Planner
-- Run this SQL in your Supabase SQL Editor

-- Create meals table
CREATE TABLE IF NOT EXISTS meals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    in_dashboard BOOLEAN DEFAULT false,
    dashboard_added_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_meals_in_dashboard ON meals(in_dashboard);

-- Enable Row Level Security (RLS)
ALTER TABLE meals ENABLE ROW LEVEL SECURITY;

-- Create policy to allow all operations (since this is a personal app)
-- For production, you'd want more restrictive policies
CREATE POLICY "Enable all access for meals" ON meals
    FOR ALL
    USING (true)
    WITH CHECK (true);
