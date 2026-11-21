"""
Azad Foundation MIS - Database Connection Pool
"""
import psycopg2
import psycopg2.pool
import psycopg2.extras
from contextlib import contextmanager
from config import DATABASE_URL, DB_NAME, DB_SCHEMA

# Parse the DATABASE_URL
# Format: postgresql://user:password@host:port/dbname
_pool = None


def init_pool(minconn=2, maxconn=10):
    """Initialize the connection pool."""
    global _pool
    if _pool is None:
        _pool = psycopg2.pool.ThreadedConnectionPool(
            minconn, maxconn, DATABASE_URL
        )
    return _pool


def get_pool():
    """Get the connection pool, initializing if needed."""
    global _pool
    if _pool is None:
        init_pool()
    return _pool


@contextmanager
def get_connection():
    """Get a connection from the pool as a context manager."""
    pool = get_pool()
    conn = pool.getconn()
    try:
        if DB_SCHEMA:
            try:
                with conn.cursor() as cur:
                    cur.execute(f"SET search_path TO {DB_SCHEMA}, public")
            except Exception:
                pass
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)


@contextmanager
def get_cursor(cursor_factory=None):
    """Get a cursor with automatic connection management.

    2026-08-26: If a WWW-module HTTP request has stashed a user id in
    the contextvar (see routes/_www_meta.py + main.py middleware), we
    push it into a Postgres transaction-local setting so the WWW
    stamping trigger (www_stamp_user_cols) can auto-fill
    created_by/updated_by. No-op for background jobs / calls made from
    outside an HTTP request context.
    """
    with get_connection() as conn:
        factory = cursor_factory or psycopg2.extras.RealDictCursor
        cursor = conn.cursor(cursor_factory=factory)
        try:
            if DB_SCHEMA:
                cursor.execute(f"SET search_path TO {DB_SCHEMA}, public")
            from routes._www_meta import get_current_user_id as _www_uid
            _uid = _www_uid()
            if _uid:
                cursor.execute(
                    "SELECT set_config('app.current_user_id', %s, true)",
                    (str(_uid),),
                )
        except Exception:
            pass  # never fail a DB call because the stamp failed
        try:
            yield cursor
        finally:
            cursor.close()


def close_pool():
    """Close the connection pool."""
    global _pool
    if _pool is not None:
        _pool.closeall()
        _pool = None
