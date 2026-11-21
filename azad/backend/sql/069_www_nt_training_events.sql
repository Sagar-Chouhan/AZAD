-- WWW-only event dates attached to Non-Technical Training records.
-- This migration is intentionally not executed by the UI sync task.
SET search_path TO mis_azad, public;

CREATE TABLE IF NOT EXISTS www_nt_training_events (
  id                     SERIAL PRIMARY KEY,
  training_id            INT NOT NULL REFERENCES www_nt_trainings(id) ON DELETE CASCADE,
  assembly_date          DATE,
  family_faculty_date    DATE,
  individual_start_date  DATE,
  individual_end_date    DATE,
  created_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT chk_www_nt_event_has_date CHECK (
    assembly_date IS NOT NULL OR family_faculty_date IS NOT NULL OR
    individual_start_date IS NOT NULL OR individual_end_date IS NOT NULL
  ),
  CONSTRAINT chk_www_nt_individual_dates CHECK (
    individual_start_date IS NULL OR individual_end_date IS NULL OR
    individual_end_date >= individual_start_date
  )
);

CREATE INDEX IF NOT EXISTS idx_www_nt_events_training
  ON www_nt_training_events(training_id, created_at DESC);
