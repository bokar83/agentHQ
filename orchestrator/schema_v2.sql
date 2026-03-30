-- schema_v2.sql
-- Migration to add Lead Management (CRM) tables for the First 3 Deals Engine

-- 1. Create the 'leads' table
CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    company TEXT,
    title TEXT,
    industry TEXT,
    revenue_est TEXT,
    employee_count INTEGER,
    location TEXT,
    linkedin_url TEXT,
    email TEXT,
    phone TEXT,
    source TEXT DEFAULT 'apollo',
    status TEXT DEFAULT 'new' CHECK (status IN ('new', 'messaged', 'replied', 'booked', 'paid')),
    last_reply_at TIMESTAMP WITH TIME ZONE,
    next_action_due TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Create the 'lead_interactions' table
CREATE TABLE IF NOT EXISTS lead_interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
    agent_name TEXT,
    interaction_type TEXT NOT NULL, -- 'outreach', 'reply', 'note', 'call'
    content TEXT,
    sentiment TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Create indices for performance
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
CREATE INDEX IF NOT EXISTS idx_leads_location ON leads(location);
CREATE INDEX IF NOT EXISTS idx_interactions_lead_id ON lead_interactions(lead_id);

-- 4. Simple trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_leads_updated_at
    BEFORE UPDATE ON leads
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
