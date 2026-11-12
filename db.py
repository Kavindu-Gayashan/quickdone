# ============================================================
# QUICKDONE — DATABASE ENGINE & CONNECTION MANAGEMENT
# File: db.py
# ============================================================
# Responsibilities:
# 1. Connection lifecycle (get_db, close_db) with sqlite3.Row and PRAGMA foreign_keys = ON
# 2. Dual-environment SQLite path resolution (Localhost vs. Vercel serverless /tmp)
# 3. Explicit database initialization from schema_and_seed.sql
# ============================================================

import os
import sys
import shutil
import sqlite3
from flask import g

DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'quickdone.db')
SCHEMA   = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schema_and_seed.sql')


def get_db_path():
    """
    Return the active SQLite database path.
    - Localhost: returns the local quickdone.db directly.
    - Vercel / serverless: ensures quickdone.db is copied to /tmp/quickdone.db
      with explicit write permissions (0o666), avoiding read-only errors.
    """
    local_db = DATABASE
    schema   = SCHEMA

    is_serverless = bool(
        os.environ.get('VERCEL') or
        os.environ.get('VERCEL_ENV') or
        os.environ.get('AWS_LAMBDA_FUNCTION_NAME') or
        not os.access(os.path.dirname(local_db), os.W_OK)
    )

    if not is_serverless:
        return local_db

    tmp_db = '/tmp/quickdone.db'
    if not os.path.exists(tmp_db):
        if os.path.exists(local_db):
            shutil.copyfile(local_db, tmp_db)
        elif os.path.exists(schema):
            with sqlite3.connect(tmp_db) as conn:
                conn.execute('PRAGMA foreign_keys = ON')
                with open(schema, 'r', encoding='utf-8') as f:
                    conn.executescript(f.read())
        try:
            os.chmod(tmp_db, 0o666)
        except Exception:
            pass

    return tmp_db


def get_db():
    """
    Return a SQLite connection cached in Flask's application context (g).
    - sqlite3.Row : allows column access by name (row['column'] or row.column in Jinja2)
    - PRAGMA foreign_keys = ON : enforced on EVERY connection (DBMS constraint rule)
    """
    if 'db' not in g:
        g.db = sqlite3.connect(get_db_path())
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys = ON')
    return g.db


def close_db(error=None):
    """Close the database connection at the end of each request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    """
    Execute schema_and_seed.sql to initialize (or reset) the database.
    WARNING: Drops and recreates all tables — all existing data is lost.
    """
    print('=' * 60)
    print('QuickDone — Database Initialization')
    print('=' * 60)
    print(f'  Schema  : {SCHEMA}')
    print(f'  DB file : {DATABASE}')
    print()
    print('  WARNING: ALL existing tables and data will be DROPPED')
    print('  and recreated from schema_and_seed.sql.')
    print()

    # Prompt only in interactive terminal sessions
    if sys.stdin.isatty():
        confirm = input("  Type 'yes' to proceed: ").strip().lower()
        if confirm != 'yes':
            print('  Cancelled — no changes made.')
            sys.exit(0)
    else:
        # Non-interactive / piped input
        line = sys.stdin.readline().strip().lower()
        if line != 'yes':
            print('  Cancelled — non-interactive confirmation failed.')
            sys.exit(0)

    # Read and execute full schema + seed script
    with open(SCHEMA, 'r', encoding='utf-8') as f:
        script = f.read()

    with sqlite3.connect(DATABASE) as conn:
        conn.execute('PRAGMA foreign_keys = ON')
        conn.executescript(script)

    # Verify created objects
    with sqlite3.connect(DATABASE) as conn:
        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()]
        triggers = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='trigger' ORDER BY name"
        ).fetchall()]
        views = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='view' ORDER BY name"
        ).fetchall()]

    print('  Database initialized successfully.')
    print(f'  Tables   ({len(tables)}): {", ".join(tables)}')
    print(f'  Triggers ({len(triggers)}): {", ".join(triggers)}')
    print(f'  Views    ({len(views)}): {", ".join(views)}')
    print()
    print('  Run the application: python app.py')


if __name__ == '__main__':
    init_db()
