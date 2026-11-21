-- 073_mgj_pakhwada_conducted_date.sql
-- Add conducted_date column to mgj_pakhwada_sessions
ALTER TABLE mgj_pakhwada_sessions ADD COLUMN IF NOT EXISTS conducted_date date;
