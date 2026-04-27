CREATE TABLE IF NOT EXISTS video_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_type TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    priority INT DEFAULT 5,
    prompt TEXT,
    params_json JSONB DEFAULT '{}'::jsonb,
    result_json JSONB,
    error_msg TEXT,
    attempts INT DEFAULT 0,
    max_attempts INT DEFAULT 3,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    dispatched_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    linked_content_id TEXT,
    requested_by TEXT DEFAULT 'system',
    feature_flag TEXT DEFAULT 'video_crew_v1'
);

CREATE INDEX IF NOT EXISTS idx_video_jobs_status
    ON video_jobs (status, priority, created_at);

CREATE INDEX IF NOT EXISTS idx_video_jobs_job_type
    ON video_jobs (job_type, status);
