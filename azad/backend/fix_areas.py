"""fix_areas.py -- WWW Add-Trainee "Area" dropdown fix: check, apply, verify.

Uses the app's own database.py, so it needs NO database username or password.
Run it from the backend folder (the one holding main.py and database.py).

    python3 fix_areas.py check     <- read-only. Shows what is wrong.
    python3 fix_areas.py apply     <- takes a backup, then applies the fix.
    python3 fix_areas.py check     <- run again to confirm.

'check' never writes anything.  'apply' only INSERTs; it never updates or
deletes, it backs www_areas up first, and re-running it is harmless.
"""
import sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND = HERE if os.path.exists(os.path.join(HERE, "database.py")) else os.getcwd()
sys.path.insert(0, BACKEND)
os.chdir(BACKEND)

try:
    from database import get_pool
except ImportError:
    sys.exit("ERROR: run this from the backend folder (the one with database.py).\n"
             "       cd ~/azad-mis-backend  then  python3 fix_areas.py check")

MODE = (sys.argv[1] if len(sys.argv) > 1 else "check").lower()
if MODE not in ("check", "apply"):
    sys.exit("usage: python3 fix_areas.py [check|apply]")

BACKUP = "mis_azad.www_areas_bak_20260921_seed"

# Rows the fix would add: areas that exist in central_areas (what the mobile app
# already shows) but not in www_areas (what the web dropdown reads), for centres
# that currently have NO areas at all under either key spelling.
SEED_FROM = """
FROM mis_azad.central_areas   ca
JOIN mis_azad.central_centres cc ON cc.centre_code = ca.centre_code
JOIN mis_azad.central_centres     w
     ON LOWER(TRIM(w.centre_name)) = LOWER(TRIM(cc.centre_name))
    AND w.district_code = cc.district_code
    AND w.deleted_at IS NULL
WHERE ca.deleted_at IS NULL
  AND LOWER(COALESCE(ca.status, 'Active')) = 'active'
  AND NULLIF(TRIM(ca.area_name), '') IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM mis_azad.www_areas a
                   WHERE a.deleted_at IS NULL
                     AND (a.centre_code = w.centre_code
                          OR LOWER(TRIM(a.centre_code)) = LOWER(TRIM(w.centre_name))))
  AND NOT EXISTS (SELECT 1 FROM mis_azad.www_areas x
                   WHERE x.area_code = ca.area_code)
"""

PI_SCOPE = """
WITH pi AS (
    SELECT u.username, u.state_code, u.district_code, u.centre_code
    FROM mis_azad.mis_user u
    JOIN mis_azad.roles r ON r.id = u.role_id
    WHERE u.deleted_at IS NULL
      AND LOWER(r.name) IN ('project incharge (pi)', 'pi')
), eff AS (
    SELECT p.*,
           COALESCE((SELECT w.centre_code
                       FROM mis_azad.central_centres cc
                       JOIN mis_azad.central_centres w
                         ON LOWER(TRIM(w.centre_name)) = LOWER(TRIM(cc.centre_name))
                        AND w.district_code = cc.district_code
                        AND w.deleted_at IS NULL
                      WHERE cc.centre_code = p.centre_code
                      LIMIT 1), p.centre_code) AS eff_centre
    FROM pi p
)
SELECT e.username, e.state_code, e.district_code, e.centre_code, e.eff_centre,
       (SELECT COUNT(*) FROM mis_azad.www_areas a
         WHERE a.deleted_at IS NULL
           AND a.centre_code   = e.eff_centre
           AND a.district_code = e.district_code
           AND a.state_code    = e.state_code
           AND LOWER(a.status) = 'active') AS areas_now
FROM eff e
ORDER BY areas_now, e.state_code, e.username
"""


def banner(t):
    print("\n" + "=" * 72)
    print(t)
    print("=" * 72)


pool = get_pool()
conn = pool.getconn()
try:
    conn.autocommit = True
    cur = conn.cursor()

    banner("[1] Has the fix already been applied here?")
    cur.execute("SELECT to_regclass(%s)", (BACKUP,))
    applied = cur.fetchone()[0] is not None
    print("  backup table %s : %s" % (BACKUP, "FOUND" if applied else "NOT FOUND"))
    print("  -> the fix has %s been run on this database."
          % ("ALREADY" if applied else "NEVER"))

    banner("[2] www_areas rows per centre right now")
    cur.execute("""SELECT state_code, centre_code, COUNT(*)
                   FROM mis_azad.www_areas WHERE deleted_at IS NULL
                   GROUP BY 1,2 ORDER BY 1,2""")
    for s, c, n in cur.fetchall():
        print("  %-5s %-16s %d" % (s or "(blank)", c or "(blank)", n))

    banner("[3] Every PI and how many areas their dropdown returns")
    cur.execute(PI_SCOPE)
    rows = cur.fetchall()
    broken = []        # empty dropdown, and seeding areas can fix it
    no_geo = []        # user record has no state/district/centre -- different problem
    for un, sc, dc, cc, eff, n in rows:
        if not (sc and dc and cc):
            tag = "GEO-INCOMPLETE"
            no_geo.append(un)
        elif n == 0:
            tag = "EMPTY"
            broken.append(un)
        else:
            tag = "ok"
        print("  %-14s %-18s state=%-5s district=%-8s centre=%-12s -> %3d areas"
              % (tag, un, sc or "-", dc or "-", eff or "-", n))

    banner("[4] Rows the fix would add")
    cur.execute("SELECT COUNT(*) " + SEED_FROM)
    pending = cur.fetchone()[0]
    print("  %d row(s) available to insert" % pending)
    if pending:
        cur.execute("SELECT w.state_code, w.centre_code, ca.area_code, TRIM(ca.area_name) "
                    + SEED_FROM + " ORDER BY w.state_code, w.centre_code, 4")
        for s, c, code, nm in cur.fetchall():
            print("    %-5s %-14s %-14s %s" % (s, c, code, nm))

    if MODE == "check":
        banner("VERDICT")
        if broken and pending:
            print("  Empty dropdown for: %s" % ", ".join(broken))
            print("  %d row(s) ready to insert -> run:  python3 fix_areas.py apply" % pending)
        elif broken and not pending:
            print("  Empty dropdown for: %s" % ", ".join(broken))
            print("  BUT there is nothing to insert. central_areas has no areas for")
            print("  those centres, or that centre is keyed differently here.")
            print("  Seeding alone will NOT fix it -- send this whole output back.")
        else:
            print("  Every PI with a complete geo gets areas. Area data is fine.")
        if no_geo:
            print("")
            print("  SEPARATE ISSUE -- these users have no state/district/centre on")
            print("  their own record, so the backend denies them every row no matter")
            print("  what the area master holds: %s" % ", ".join(no_geo))
            print("  Fix them in Master > User Management, not with this script.")
        print("\n  (nothing was written)")
    else:
        banner("[5] APPLYING")
        if not pending:
            print("  Nothing to insert. No changes made.")
        else:
            cur.execute("SELECT COUNT(*) FROM mis_azad.www_areas WHERE deleted_at IS NULL")
            before = cur.fetchone()[0]
            cur.execute("CREATE TABLE IF NOT EXISTS %s AS SELECT * FROM mis_azad.www_areas" % BACKUP)
            print("  backup written to %s" % BACKUP)
            cur.execute("""INSERT INTO mis_azad.www_areas
                             (area_code, area_name, centre_code, district_code,
                              state_code, status, created_at, updated_at)
                           SELECT ca.area_code, TRIM(ca.area_name), w.centre_code,
                                  w.district_code, w.state_code, 'Active', NOW(), NOW()
                        """ + SEED_FROM)
            cur.execute("SELECT COUNT(*) FROM mis_azad.www_areas WHERE deleted_at IS NULL")
            after = cur.fetchone()[0]
            print("  www_areas: %d -> %d   (inserted %d)" % (before, after, after - before))
            print("\n  Now run:  python3 fix_areas.py check")
            print("  No service restart is needed -- this is data only.")
    cur.close()
finally:
    pool.putconn(conn)
