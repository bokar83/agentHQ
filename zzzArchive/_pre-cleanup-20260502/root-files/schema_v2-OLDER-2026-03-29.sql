-- schema_v2.sql — Catalyst Growth Engine CRM
-- This adds the tables needed for lead tracking and pipeline management.

-- 1. Leads Table
-- Stores the core prospect data.
CREATE TABLE IF NOT EXISTS leads (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    company VARCHAR(255) NOT NULL,
    title VARCHAR(255),
    location VARCHAR(255),
    linkedin_url TEXT,
    email VARCHAR(255),
    industry VARCHAR(100),
    status VARCHAR(50) DEFAULT 'new', -- new, messaged, replied, booked, paid
    source VARCHAR(100) DEFAULT 'apollo',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Lead Interactions Table
-- Logs every touchpoint (discovery, outreach, reply, etc.)
CREATE TABLE IF NOT EXISTS lead_interactions (
    id SERIAL PRIMARY KEY,
    lead_id INTEGER REFERENCES leads(id) ON DELETE CASCADE,
    interaction_type VARCHAR(50) NOT NULL, -- discovery, outreach, reply, note
    content TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Daily Sales Velocity View (Scoreboard)
-- A helper view for leGriot to pull stats quickly.
CREATE OR REPLACE VIEW daily_scoreboard AS
SELECT 
    COUNT(*) FILTER (WHERE date(created_at) = CURRENT_DATE) as leads_found,
    COUNT(*) FILTER (WHERE status = 'messaged' AND date(updated_at) = CURRENT_DATE) as messages_sent,
    COUNT(*) FILTER (WHERE status = 'replied' AND date(updated_at) = CURRENT_DATE) as replies_received,
    COUNT(*) FILTER (WHERE status = 'booked' AND date(updated_at) = CURRENT_DATE) as calls_booked,
    0 as revenue -- placeholder for revenue if tracked later
FROM leads;

-- Indexing for performance
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
CREATE INDEX IF NOT EXISTS idx_leads_location ON leads(location);
CREATE INDEX IF NOT EXISTS idx_interactions_lead_id ON lead_interactions(lead_id);

-- Instructions:
-- Run this against your existing agentsHQ PostgreSQL database.
