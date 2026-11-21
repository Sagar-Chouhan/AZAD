-- Migration 063: Add remarks_date to ak_trainings
ALTER TABLE mis_azad.ak_trainings
ADD COLUMN IF NOT EXISTS remarks TEXT,
ADD COLUMN IF NOT EXISTS remarks_date DATE;
