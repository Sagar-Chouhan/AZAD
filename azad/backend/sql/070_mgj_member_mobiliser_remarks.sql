-- MGJ list parity: mobiliser name and member remarks.
ALTER TABLE mgj_members
  ADD COLUMN IF NOT EXISTS mobiliser_name VARCHAR(200),
  ADD COLUMN IF NOT EXISTS remarks TEXT,
  ADD COLUMN IF NOT EXISTS remarks_date DATE;
