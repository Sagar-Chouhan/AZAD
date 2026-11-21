-- 061_seed_www_areas_missing_centres.sql
-- 2026-09-21
--
-- Fix: the WWW Add-Trainee "Area" dropdown is empty for every PI whose centre
-- has no rows in www_areas.  Reported for Dharini (PI, Chennai); it also hit
-- akash and bhoomi (Chennai) and himanshi_PI and Princhika (Jaipur).
--
-- Why it happens:
--   GET /api/www-master/dropdown/areas serves BROWSERS out of www_areas, with
--   _www_scope.scope_geo() pinning the request to the caller's own
--   state + district + centre (a PI is pinned on all three).  www_areas only
--   ever received rows for the Delhi and Kolkata centres, so a Chennai or
--   Jaipur PI matches nothing and the dropdown renders empty.
--   The legacy www_enrollment UNION further down that endpoint cannot rescue
--   them: it is switched off with a hard FALSE whenever district_code is
--   pinned -- which is always the case for a PI.
--
-- Why central_areas is the right source:
--   central_areas is the FLP master the mobiliser MOBILE app is already served
--   from for these very users (same endpoint, non-browser User-Agent branch),
--   and it uses the same <district><centre>GP<n> area_code convention that
--   www_areas uses.  Seeding from it makes web agree with mobile.
--
-- Safety:
--   * INSERT only -- nothing is updated or deleted.
--   * Only centres that today have NO areas at all are seeded, so the Delhi and
--     Kolkata dropdowns are untouched and no already-saved trainee area_code
--     can change meaning.
--   * The centre_name half of the "no areas yet" test deliberately SKIPS West
--     Kolkata: its www_centres row is keyed 'S19349B5' while its 21 existing
--     www_areas rows are keyed 'West Kolkata', so seeding it would collide on
--     the www_areas primary key.  That key mismatch is a separate, pre-existing
--     problem and is left alone here.
--   * The last NOT EXISTS is a belt-and-braces guard on the primary key, so
--     re-running this script is harmless.

BEGIN;

-- Rollback point.  Drop it once the fix has been signed off.
CREATE TABLE IF NOT EXISTS mis_azad.www_areas_bak_20260921_seed AS
SELECT * FROM mis_azad.www_areas;

INSERT INTO mis_azad.www_areas
    (area_code, area_name, centre_code, district_code, state_code,
     status, created_at, updated_at)
SELECT ca.area_code,
       TRIM(ca.area_name),
       w.centre_code,
       w.district_code,
       w.state_code,
       'Active',
       NOW(),
       NOW()
FROM mis_azad.central_areas   ca
JOIN mis_azad.central_centres cc
     ON cc.centre_code = ca.centre_code
JOIN mis_azad.www_centres     w
     ON LOWER(TRIM(w.centre_name)) = LOWER(TRIM(cc.centre_name))
    AND w.district_code = cc.district_code
    AND w.deleted_at IS NULL
WHERE ca.deleted_at IS NULL
  AND LOWER(COALESCE(ca.status, 'Active')) = 'active'
  AND NULLIF(TRIM(ca.area_name), '') IS NOT NULL
  AND NOT EXISTS (
        SELECT 1
          FROM mis_azad.www_areas a
         WHERE a.deleted_at IS NULL
           AND (a.centre_code = w.centre_code
                OR LOWER(TRIM(a.centre_code)) = LOWER(TRIM(w.centre_name))))
  AND NOT EXISTS (
        SELECT 1
          FROM mis_azad.www_areas x
         WHERE x.area_code = ca.area_code);

COMMIT;
