-- Migration 062: AK Mentoring & Remarks fields
-- 1. Sangini Entries: Mentoring (mentees count and topic)
ALTER TABLE mis_azad.sangini_entries
ADD COLUMN IF NOT EXISTS mentoring_mentees INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS mentoring_topic TEXT;

-- 2. AK Trainings: Remarks
ALTER TABLE mis_azad.ak_trainings
ADD COLUMN IF NOT EXISTS remarks TEXT;
