-- AK training remarks parity with MGJ
ALTER TABLE mis_azad.ak_trainings
ADD COLUMN IF NOT EXISTS remarks TEXT,
ADD COLUMN IF NOT EXISTS remarks_date DATE;
