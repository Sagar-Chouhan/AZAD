-- Reconcile the shared FLP/MGJ/AK Area Master hierarchy.
--
-- central_areas is shared by the FLP, MGJ and AK master routes. Legacy/imported
-- rows contained district codes that were absent from central_districts and
-- did not match their centre's canonical hierarchy. Strict joins consequently
-- hid those areas in the management screens.
--
-- The selected centre is the canonical parent for an area, so derive both the
-- district and state from central_centres. IS DISTINCT FROM also handles NULL
-- safely, and makes this migration idempotent.
UPDATE central_areas AS area
SET district_code = centre.district_code,
    state_code = centre.state_code,
    updated_at = CURRENT_TIMESTAMP
FROM central_centres AS centre
WHERE area.centre_code = centre.centre_code
  AND (
    area.district_code IS DISTINCT FROM centre.district_code
    OR area.state_code IS DISTINCT FROM centre.state_code
  );
