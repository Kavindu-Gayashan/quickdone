# ============================================================
# QUICKDONE — Skilled-Worker Service Marketplace
# DBMS Foundations Assignment
# ============================================================
#
# Minimal project structure (as required):
#   schema_and_seed.sql  — submitted DB schema  (DO NOT MODIFY)
#   app.py               — this file: Python, SQL, routes, HTML/CSS
#   requirements.txt     — Flask only
#
# Commands:
#   Initialize / reset DB : python app.py --init-db
#   Run the application   : python app.py
#   Application URL       : http://127.0.0.1:5000
#
# Admin login (Python-only, no DB table): username=admin  password=admin
# Seeded password_hash values are placeholders (e.g. hash_ap91).
# Seeded users CANNOT log in. Register new accounts to test login.
#
# ============================================================
# VIVA QUICK-REFERENCE (SQL concepts demonstrated)
# ============================================================
# SELECT / INSERT / UPDATE / DELETE  — throughout DATABASE QUERIES section
# WHERE, ORDER BY                    — every query
# INNER JOIN                         — search_workers, get_worker_reviews, etc.
# LEFT JOIN                          — get_customer_bookings (includes bookings
#                                      without reviews), get_category_worker_counts
# GROUP BY, HAVING                   — get_category_worker_counts, admin popular categories
# Aggregate: COUNT, AVG, MIN, MAX   — admin stats, avg_rating, rate range
# Subquery                           — award_eligible_badges (NOT EXISTS),
#                                      admin top_workers (IN subquery)
# Transaction (BEGIN/COMMIT/ROLLBACK)— create_worker (multi-table insert)
# Triggers (existing, not modified)  — trg_update_worker_jobs_on_complete fires when
#                                      booking status → COMPLETED;
#                                      trg_update_worker_rating_on_review fires when
#                                      a review is inserted
# View (existing, not modified)      — v_worker_derived_stats queried in admin dashboard
# DELETE with business-rule check    — remove_worker_service
# Parameterised placeholders (?)     — all user-supplied values
# ============================================================

import sys
import os
import sqlite3
from functools import wraps
from flask import (Flask, render_template_string, request, redirect,
                   url_for, session, flash, g)
from werkzeug.security import generate_password_hash, check_password_hash

# ============================================================
# CONFIGURATION
# ============================================================

DATABASE   = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'quickdone.db')
SCHEMA     = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schema_and_seed.sql')
SECRET_KEY = 'qd-secret-2026-dbms-foundations'

def get_db_path():
    """
    Return the active SQLite database path.
    - Localhost: returns the local quickdone.db directly.
    - Vercel / serverless: ensures quickdone.db is copied to /tmp/quickdone.db
      with explicit write permissions (0o666), avoiding read-only errors.
    """
    local_db = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'quickdone.db')
    schema   = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schema_and_seed.sql')

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
        import shutil
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

# Admin credentials — Python-only; no admin database table (rule 0.4.4)
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin'

# Presentation-only image URLs.
# No image column exists in the database; these are UI-layer constants only.
HERO_IMAGE = 'https://images.unsplash.com/photo-1621905251189-08b45d6a269e?w=1600&q=80'

CATEGORY_IMAGES = {
    'Electrical':    'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=800&q=80',
    'Plumbing':      'https://images.unsplash.com/photo-1504328345606-18bbc8c9d7d1?w=800&q=80',
    'AC Servicing':  'https://images.unsplash.com/photo-1569154941061-e231b4725ef1?w=800&q=80',
    'Deep Cleaning': 'https://images.unsplash.com/photo-1581578731548-c64695cc6952?w=800&q=80',
    'Carpentry':     'https://images.unsplash.com/photo-1565008447742-97f6f38c985c?w=800&q=80',
}
CATEGORY_ICONS = {
    'Electrical':    '⚡',
    'Plumbing':      '🔧',
    'AC Servicing':  '❄️',
    'Deep Cleaning': '🧹',
    'Carpentry':     '🪵',
}

app = Flask(__name__)
app.secret_key = SECRET_KEY


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_db():
    """
    Return a SQLite connection cached in Flask's application context (g).
    - sqlite3.Row  : allows column access by name (row['col'] or row.col in Jinja2)
    - PRAGMA foreign_keys = ON : enforced on EVERY connection (rule 0.4.2)
    """
    if 'db' not in g:
        g.db = sqlite3.connect(get_db_path())
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys = ON')
    return g.db


@app.teardown_appcontext
def close_db(error):
    """Close the database connection at the end of each request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    """
    Execute schema_and_seed.sql to initialize (or reset) the database.
    Called ONLY via: python app.py --init-db   (never on normal startup)
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
    confirm = input("  Type 'yes' to proceed: ").strip().lower()
    if confirm != 'yes':
        print('  Cancelled — no changes made.')
        sys.exit(0)

    with sqlite3.connect(DATABASE) as conn:
        conn.execute('PRAGMA foreign_keys = ON')
        with open(SCHEMA, 'r', encoding='utf-8') as f:
            script = f.read()
        conn.executescript(script)

    print()
    print('  Database initialized successfully.')

    # Verify created objects
    with sqlite3.connect(DATABASE) as conn:
        tables   = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()]
        triggers = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='trigger' ORDER BY name").fetchall()]
        views    = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='view' ORDER BY name").fetchall()]

    print(f'  Tables   ({len(tables)}): {", ".join(tables)}')
    print(f'  Triggers ({len(triggers)}): {", ".join(triggers)}')
    print(f'  Views    ({len(views)}): {", ".join(views)}')
    print()
    print('  Run the application: python app.py')


# ============================================================
# DATABASE QUERIES
# All SQL used by the application is kept in this section.
# Flask routes call these functions; SQL is NOT written inside routes.
# All user-supplied values use parameterised ? placeholders.
# ============================================================


# ------------------------------------------------------------------
# CATEGORIES & WORKER DISCOVERY
# ------------------------------------------------------------------

def get_all_categories():
    """
    Retrieve all service categories.
    SQL: SELECT with ORDER BY
    """
    db = get_db()
    return db.execute("""
        SELECT  category_id,
                name,
                description
        FROM    category
        ORDER   BY name
    """).fetchall()


def get_category_worker_counts():
    """
    Retrieve categories with a live count of workers offering each service.
    SQL: SELECT, LEFT JOIN, GROUP BY, COUNT aggregate
    """
    db = get_db()
    return db.execute("""
        -- LEFT JOIN keeps categories that have zero workers
        SELECT   c.category_id,
                 c.name,
                 c.description,
                 COUNT(ws.worker_id) AS worker_count
        FROM     category c
        LEFT JOIN worker_service ws ON c.category_id = ws.category_id
        GROUP BY c.category_id, c.name, c.description
        ORDER BY worker_count DESC, c.name
    """).fetchall()


def search_workers(name=None, city=None, category_id=None):
    """
    Search workers with optional filters for name, city and category.
    WHERE clause built dynamically in Python; only values are parameterised.
    SQL: SELECT, INNER JOIN, optional WHERE, GROUP BY, ORDER BY,
         GROUP_CONCAT, MIN/MAX aggregates
    """
    db     = get_db()
    conds  = ['1=1']
    params = []

    if name:
        # LIKE filter on concatenated first+last name
        conds.append("(w.first_name || ' ' || w.last_name) LIKE ?")
        params.append(f'%{name}%')
    if city:
        conds.append('w.city LIKE ?')
        params.append(f'%{city}%')
    if category_id:
        conds.append('ws.category_id = ?')
        params.append(int(category_id))

    sql = """
        SELECT   w.worker_id,
                 w.first_name,
                 w.last_name,
                 w.city,
                 w.experience_years,
                 w.avg_rating,
                 w.completed_jobs,
                 w.bio,
                 w.profile_image_url,
                 GROUP_CONCAT(DISTINCT c.name) AS service_names,
                 MIN(ws.hourly_rate)            AS min_rate,
                 MAX(ws.hourly_rate)            AS max_rate
        FROM     worker w
        INNER JOIN worker_service ws ON w.worker_id    = ws.worker_id
        INNER JOIN category       c  ON ws.category_id = c.category_id
        WHERE    {where}
        GROUP BY w.worker_id
        ORDER BY w.avg_rating DESC, w.completed_jobs DESC
    """.format(where=' AND '.join(conds))

    return db.execute(sql, params).fetchall()


def get_featured_workers(limit=6):
    """
    Retrieve top-rated workers for homepage display.
    SQL: SELECT, INNER JOIN, GROUP BY, ORDER BY, LIMIT
    """
    db = get_db()
    return db.execute("""
        SELECT   w.worker_id,
                 w.first_name,
                 w.last_name,
                 w.city,
                 w.experience_years,
                 w.avg_rating,
                 w.completed_jobs,
                 w.profile_image_url,
                 GROUP_CONCAT(DISTINCT c.name) AS service_names,
                 MIN(ws.hourly_rate)            AS min_rate
        FROM     worker w
        INNER JOIN worker_service ws ON w.worker_id    = ws.worker_id
        INNER JOIN category       c  ON ws.category_id = c.category_id
        GROUP BY w.worker_id
        ORDER BY w.avg_rating DESC, w.completed_jobs DESC
        LIMIT    ?
    """, (limit,)).fetchall()


def get_worker_profile(worker_id):
    """
    Retrieve a single worker's full profile row.
    SQL: SELECT with WHERE on primary key
    """
    db = get_db()
    return db.execute("""
        SELECT  worker_id, first_name, last_name, email, phone,
                city, experience_years, bio, profile_image_url,
                avg_rating, completed_jobs, registered_at
        FROM    worker
        WHERE   worker_id = ?
    """, (worker_id,)).fetchone()


def get_worker_portfolio(worker_id):
    """
    Retrieve all work example images for a worker (up to 5).
    SQL: SELECT with WHERE on foreign key, ORDER BY portfolio_id
    """
    db = get_db()
    return db.execute("""
        SELECT  portfolio_id,
                worker_id,
                image_url,
                title,
                uploaded_at
        FROM    worker_portfolio
        WHERE   worker_id = ?
        ORDER   BY portfolio_id ASC
    """, (worker_id,)).fetchall()


def add_portfolio_image(worker_id, image_url, title=None):
    """
    Add a work example image for a worker. Enforces maximum 5 images.
    SQL: SELECT COUNT(*) pre-check, then INSERT INTO worker_portfolio
    """
    db = get_db()
    count = db.execute("""
        SELECT COUNT(*) FROM worker_portfolio WHERE worker_id = ?
    """, (worker_id,)).fetchone()[0]
    if count >= 5:
        return False, 'Maximum 5 work example images allowed.'
    db.execute("""
        INSERT INTO worker_portfolio (worker_id, image_url, title)
        VALUES (?, ?, ?)
    """, (worker_id, image_url, title or None))
    db.commit()
    return True, 'Work example added successfully.'


def delete_portfolio_image(portfolio_id, worker_id):
    """
    Remove a work example image owned by the worker.
    SQL: DELETE with WHERE on portfolio_id and worker_id (ownership check)
    """
    db = get_db()
    db.execute("""
        DELETE FROM worker_portfolio
        WHERE portfolio_id = ? AND worker_id = ?
    """, (int(portfolio_id), int(worker_id)))
    db.commit()
    return True


def get_worker_services(worker_id):
    """
    Retrieve all services and hourly rates offered by a worker.
    SQL: SELECT, INNER JOIN worker_service and category, WHERE, ORDER BY
    """
    db = get_db()
    return db.execute("""
        SELECT  ws.worker_id,
                ws.category_id,
                ws.hourly_rate,
                c.name        AS category_name,
                c.description AS category_description
        FROM    worker_service ws
        INNER JOIN category c ON ws.category_id = c.category_id
        WHERE   ws.worker_id = ?
        ORDER   BY c.name
    """, (worker_id,)).fetchall()


def get_worker_qualifications(worker_id):
    """
    Retrieve a worker's qualifications.
    SQL: SELECT with WHERE, ORDER BY (composite primary key column)
    """
    db = get_db()
    return db.execute("""
        SELECT  qualification_no,
                title,
                institution,
                year_obtained
        FROM    qualification
        WHERE   worker_id = ?
        ORDER   BY qualification_no
    """, (worker_id,)).fetchall()


def get_worker_availability(worker_id):
    """
    Retrieve a worker's recurring weekly availability windows.
    NOTE: availability stores weekday/time ranges, not date-specific slots.
    SQL: SELECT with WHERE; CASE expression to order days logically.
    """
    db = get_db()
    return db.execute("""
        SELECT  day_of_week,
                start_time,
                end_time
        FROM    availability
        WHERE   worker_id = ?
        ORDER   BY
            CASE day_of_week
                WHEN 'Monday'    THEN 1
                WHEN 'Tuesday'   THEN 2
                WHEN 'Wednesday' THEN 3
                WHEN 'Thursday'  THEN 4
                WHEN 'Friday'    THEN 5
                WHEN 'Saturday'  THEN 6
                WHEN 'Sunday'    THEN 7
            END
    """, (worker_id,)).fetchall()


def get_worker_badges(worker_id):
    """
    Retrieve badges earned by a worker.
    SQL: SELECT, INNER JOIN worker_badge and badge, WHERE, ORDER BY
    """
    db = get_db()
    return db.execute("""
        SELECT  b.badge_id,
                b.name              AS badge_name,
                b.min_jobs_required,
                wb.awarded_date
        FROM    worker_badge wb
        INNER JOIN badge b ON wb.badge_id = b.badge_id
        WHERE   wb.worker_id = ?
        ORDER   BY wb.awarded_date
    """, (worker_id,)).fetchall()


def get_worker_reviews(worker_id):
    """
    Retrieve all reviews for a worker, joined with booking and customer info.
    SQL: SELECT, INNER JOIN across review, booking and customer, WHERE, ORDER BY
    """
    db = get_db()
    return db.execute("""
        SELECT  r.review_id,
                r.rating,
                r.comment,
                r.review_date,
                b.booking_id,
                b.job_description,
                b.scheduled_start,
                c.first_name || ' ' || c.last_name AS customer_name
        FROM    review r
        INNER JOIN booking  b ON r.booking_id  = b.booking_id
        INNER JOIN customer c ON b.customer_id = c.customer_id
        WHERE   b.worker_id = ?
        ORDER   BY r.review_date DESC
    """, (worker_id,)).fetchall()


# ------------------------------------------------------------------
# AUTHENTICATION & REGISTRATION
# ------------------------------------------------------------------

def find_customer_by_email(email):
    """
    Look up a customer by email address.
    SQL: SELECT with WHERE on UNIQUE column (email)
    """
    db = get_db()
    return db.execute("""
        SELECT  customer_id, first_name, last_name, email, password_hash
        FROM    customer
        WHERE   email = ?
    """, (email,)).fetchone()


def find_worker_by_email(email):
    """
    Look up a worker by email address.
    SQL: SELECT with WHERE on UNIQUE column (email)
    """
    db = get_db()
    return db.execute("""
        SELECT  worker_id, first_name, last_name, email, password_hash
        FROM    worker
        WHERE   email = ?
    """, (email,)).fetchone()


def create_customer(first_name, last_name, email, phone, pw_hash, address):
    """
    Register a new customer.
    SQL: INSERT INTO customer (all values parameterised)
    """
    db = get_db()
    cur = db.execute("""
        INSERT INTO customer
            (first_name, last_name, email, phone, password_hash, address)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (first_name, last_name, email, phone, pw_hash, address))
    db.commit()
    return cur.lastrowid


def create_worker(first_name, last_name, email, phone, pw_hash,
                  city, experience_years, bio,
                  services, qualifications, availabilities,
                  profile_image_url=None, portfolio_items=None):
    """
    Register a new worker with their services, qualifications, availability,
    optional profile image and up to 5 portfolio work examples.
    Uses an explicit TRANSACTION for atomicity across multiple inserts.
    SQL: BEGIN / COMMIT / ROLLBACK transaction; INSERT into worker, worker_service,
         qualification, availability, worker_portfolio
    """
    db = get_db()
    try:
        db.execute('BEGIN')  # -- TRANSACTION START --

        # INSERT parent entity first
        cur = db.execute("""
            INSERT INTO worker
                (first_name, last_name, email, phone, password_hash,
                 city, experience_years, bio, profile_image_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (first_name, last_name, email, phone, pw_hash,
              city, int(experience_years), bio or '', profile_image_url or None))
        worker_id = cur.lastrowid

        # INSERT associative entity worker_service (at least one required)
        for category_id, hourly_rate in services:
            db.execute("""
                INSERT INTO worker_service (worker_id, category_id, hourly_rate)
                VALUES (?, ?, ?)
            """, (worker_id, int(category_id), float(hourly_rate)))

        # INSERT weak entity qualification (optional; partial key computed manually)
        for idx, (title, institution, year) in enumerate(qualifications, start=1):
            if title and institution and year:
                db.execute("""
                    INSERT INTO qualification
                        (worker_id, qualification_no, title, institution, year_obtained)
                    VALUES (?, ?, ?, ?, ?)
                """, (worker_id, idx, title, institution, int(year)))

        # INSERT weak entity availability (optional)
        for day, start_time, end_time in availabilities:
            if day and start_time and end_time:
                db.execute("""
                    INSERT INTO availability
                        (worker_id, day_of_week, start_time, end_time)
                    VALUES (?, ?, ?, ?)
                """, (worker_id, day, start_time, end_time))

        # INSERT work example / portfolio images (optional, up to 5)
        if portfolio_items:
            for img_url, img_title in portfolio_items[:5]:
                if img_url:
                    db.execute("""
                        INSERT INTO worker_portfolio
                            (worker_id, image_url, title)
                        VALUES (?, ?, ?)
                    """, (worker_id, img_url, img_title or None))

        db.execute('COMMIT')   # -- TRANSACTION COMMIT --
        return worker_id

    except Exception:
        db.execute('ROLLBACK')  # -- TRANSACTION ROLLBACK on error --
        raise


def add_worker_service(worker_id, category_id, hourly_rate):
    """
    Add a new service offering for an existing worker.
    SQL: INSERT into worker_service (composite primary key)
    """
    db = get_db()
    db.execute("""
        INSERT INTO worker_service (worker_id, category_id, hourly_rate)
        VALUES (?, ?, ?)
    """, (worker_id, int(category_id), float(hourly_rate)))
    db.commit()


def remove_worker_service(worker_id, category_id):
    """
    Remove a service offering (DELETE demonstration).
    Business rule: Cannot delete if active bookings reference this service.
    SQL: DELETE with WHERE; active-booking check prevents FK violation.
    """
    db = get_db()
    # Pre-check: count active bookings for this worker/category pair
    active = db.execute("""
        SELECT  COUNT(*)
        FROM    booking
        WHERE   worker_id   = ?
          AND   category_id = ?
          AND   status IN ('PENDING', 'CONFIRMED', 'IN_PROGRESS')
    """, (worker_id, int(category_id))).fetchone()[0]

    if active > 0:
        return False   # Cannot delete — has active bookings

    # -- DELETE: removes the row from worker_service --
    db.execute("""
        DELETE FROM worker_service
        WHERE  worker_id   = ?
          AND  category_id = ?
    """, (worker_id, int(category_id)))
    db.commit()
    return True


def add_qualification(worker_id, title, institution, year_obtained):
    """
    Add a qualification for an existing worker.
    Computes the next qualification_no using a MAX subquery (partial key).
    SQL: INSERT with partial key derived from MAX aggregate subquery
    """
    db = get_db()
    next_no = db.execute("""
        SELECT  COALESCE(MAX(qualification_no), 0) + 1
        FROM    qualification
        WHERE   worker_id = ?
    """, (worker_id,)).fetchone()[0]

    db.execute("""
        INSERT INTO qualification
            (worker_id, qualification_no, title, institution, year_obtained)
        VALUES (?, ?, ?, ?, ?)
    """, (worker_id, next_no, title, institution, int(year_obtained)))
    db.commit()


def add_availability(worker_id, day_of_week, start_time, end_time):
    """
    Add or replace a weekly availability slot.
    SQL: INSERT OR REPLACE (upsert using composite primary key)
    """
    db = get_db()
    db.execute("""
        INSERT OR REPLACE INTO availability
            (worker_id, day_of_week, start_time, end_time)
        VALUES (?, ?, ?, ?)
    """, (worker_id, day_of_week, start_time, end_time))
    db.commit()


def update_worker_profile(worker_id, bio, phone, city, experience_years, profile_image_url=None):
    """
    Update editable fields of an existing worker profile including profile_image_url.
    SQL: UPDATE with WHERE on primary key
    """
    db = get_db()
    db.execute("""
        UPDATE  worker
        SET     bio               = ?,
                phone             = ?,
                city              = ?,
                experience_years  = ?,
                profile_image_url = ?
        WHERE   worker_id = ?
    """, (bio, phone, city, int(experience_years), profile_image_url or None, worker_id))
    db.commit()


# ------------------------------------------------------------------
# BOOKINGS — CUSTOMER SIDE
# ------------------------------------------------------------------

def get_worker_service_rate(worker_id, category_id):
    """
    Look up the hourly rate for a specific worker/category pair.
    SQL: SELECT with WHERE on composite primary key
    """
    db = get_db()
    row = db.execute("""
        SELECT  hourly_rate
        FROM    worker_service
        WHERE   worker_id   = ?
          AND   category_id = ?
    """, (int(worker_id), int(category_id))).fetchone()
    return row['hourly_rate'] if row else None


def create_booking(customer_id, worker_id, category_id,
                   job_description, job_address, scheduled_start, agreed_rate):
    """
    Create a new booking record.
    The composite FK (worker_id, category_id) → worker_service is enforced by SQLite.
    New bookings start as PENDING; the trigger only fires on status=COMPLETED.
    SQL: INSERT INTO booking with parameterised values and default status 'PENDING'
    """
    db = get_db()
    cur = db.execute("""
        INSERT INTO booking
            (customer_id, worker_id, category_id,
             job_description, job_address, scheduled_start,
             status, agreed_rate)
        VALUES (?, ?, ?, ?, ?, ?, 'PENDING', ?)
    """, (customer_id, int(worker_id), int(category_id),
          job_description, job_address, scheduled_start, float(agreed_rate)))
    db.commit()
    return cur.lastrowid


def get_customer_bookings(customer_id):
    """
    Retrieve all bookings for a customer with worker, category and review status.
    SQL: SELECT, INNER JOIN (booking→worker, booking→category),
         LEFT JOIN (booking→review to include bookings without reviews), WHERE, ORDER BY
    """
    db = get_db()
    return db.execute("""
        -- LEFT JOIN includes bookings whether or not a review exists
        SELECT  b.booking_id,
                b.status,
                b.job_description,
                b.job_address,
                b.scheduled_start,
                b.agreed_rate,
                b.created_at,
                b.completed_at,
                b.worker_id,
                w.first_name || ' ' || w.last_name  AS worker_name,
                w.city                              AS worker_city,
                c.name                              AS category_name,
                r.review_id,
                r.rating
        FROM    booking b
        INNER JOIN worker   w ON b.worker_id   = w.worker_id
        INNER JOIN category c ON b.category_id = c.category_id
        LEFT  JOIN review   r ON b.booking_id  = r.booking_id
        WHERE   b.customer_id = ?
        ORDER   BY b.created_at DESC
    """, (customer_id,)).fetchall()


def get_booking_detail(booking_id):
    """
    Retrieve a single booking with full customer, worker, category and review details.
    SQL: SELECT, multiple INNER JOINs, LEFT JOIN for review, WHERE
    """
    db = get_db()
    return db.execute("""
        SELECT  b.booking_id,
                b.status,
                b.job_description,
                b.job_address,
                b.scheduled_start,
                b.agreed_rate,
                b.created_at,
                b.completed_at,
                b.customer_id,
                b.worker_id,
                b.category_id,
                cu.first_name || ' ' || cu.last_name  AS customer_name,
                cu.phone                               AS customer_phone,
                w.first_name  || ' ' || w.last_name   AS worker_name,
                w.phone                                AS worker_phone,
                w.city                                 AS worker_city,
                c.name                                 AS category_name,
                r.review_id,
                r.rating,
                r.comment
        FROM    booking b
        INNER JOIN customer  cu ON b.customer_id = cu.customer_id
        INNER JOIN worker     w ON b.worker_id   = w.worker_id
        INNER JOIN category   c ON b.category_id = c.category_id
        LEFT  JOIN review     r ON b.booking_id  = r.booking_id
        WHERE   b.booking_id = ?
    """, (booking_id,)).fetchone()


def cancel_booking(booking_id, customer_id):
    """
    Set booking status to CANCELLED (customer side — PENDING or CONFIRMED only).
    SQL: UPDATE with WHERE including customer_id ownership check and status IN constraint
    """
    db = get_db()
    db.execute("""
        UPDATE  booking
        SET     status = 'CANCELLED'
        WHERE   booking_id  = ?
          AND   customer_id = ?
          AND   status IN ('PENDING', 'CONFIRMED')
    """, (booking_id, customer_id))
    db.commit()


# ------------------------------------------------------------------
# BOOKINGS — WORKER SIDE
# ------------------------------------------------------------------

def get_worker_bookings(worker_id):
    """
    Retrieve all bookings assigned to a worker with customer and category details.
    SQL: SELECT, INNER JOIN (booking→customer, booking→category), WHERE, ORDER BY
    """
    db = get_db()
    return db.execute("""
        SELECT  b.booking_id,
                b.status,
                b.job_description,
                b.job_address,
                b.scheduled_start,
                b.agreed_rate,
                b.created_at,
                b.completed_at,
                b.category_id,
                cu.first_name || ' ' || cu.last_name  AS customer_name,
                cu.phone                               AS customer_phone,
                c.name                                AS category_name
        FROM    booking b
        INNER JOIN customer  cu ON b.customer_id = cu.customer_id
        INNER JOIN category   c ON b.category_id = c.category_id
        WHERE   b.worker_id = ?
        ORDER   BY b.created_at DESC
    """, (worker_id,)).fetchall()


def update_booking_status(booking_id, worker_id, new_status):
    """
    Update booking status (worker action) with valid-transition check.
    Valid transitions:
        PENDING     → CONFIRMED | CANCELLED
        CONFIRMED   → IN_PROGRESS | CANCELLED
        IN_PROGRESS → COMPLETED | CANCELLED
    After status = 'COMPLETED', the existing trigger
    trg_update_worker_jobs_on_complete fires automatically and
    recalculates worker.completed_jobs.
    SQL: UPDATE with WHERE; existing trigger executes on COMPLETED
    """
    allowed_from = {
        'CONFIRMED':   ('PENDING',),
        'CANCELLED':   ('PENDING', 'CONFIRMED', 'IN_PROGRESS'),
        'IN_PROGRESS': ('CONFIRMED',),
        'COMPLETED':   ('IN_PROGRESS',),
    }
    if new_status not in allowed_from:
        return False

    db = get_db()
    # Build parameterised IN placeholders for allowed source statuses
    ph = ','.join('?' * len(allowed_from[new_status]))
    db.execute("""
        UPDATE  booking
        SET     status       = ?,
                completed_at = CASE WHEN ? = 'COMPLETED'
                                    THEN CURRENT_TIMESTAMP
                                    ELSE completed_at END
        WHERE   booking_id = ?
          AND   worker_id  = ?
          AND   status IN ({ph})
    """.format(ph=ph),
    (new_status, new_status, booking_id, worker_id) + allowed_from[new_status])
    db.commit()
    return True


# ------------------------------------------------------------------
# REVIEWS & BADGES
# ------------------------------------------------------------------

def check_booking_has_review(booking_id):
    """
    Check whether a booking already has a review (enforces one-review-per-booking).
    SQL: SELECT COUNT(*) with WHERE (the UNIQUE constraint on booking_id also enforces this)
    """
    db = get_db()
    count = db.execute("""
        SELECT  COUNT(*)
        FROM    review
        WHERE   booking_id = ?
    """, (booking_id,)).fetchone()[0]
    return count > 0


def add_review(booking_id, rating, comment):
    """
    Insert a review for a completed booking.
    The existing trigger trg_update_worker_rating_on_review fires automatically,
    recalculating worker.avg_rating = ROUND(AVG(rating), 2).
    The UNIQUE constraint on booking_id prevents duplicate reviews.
    SQL: INSERT INTO review; existing trigger fires to update worker.avg_rating
    """
    db = get_db()
    cur = db.execute("""
        INSERT INTO review (booking_id, rating, comment)
        VALUES (?, ?, ?)
    """, (booking_id, int(rating), comment or None))
    db.commit()
    return cur.lastrowid


def award_eligible_badges(worker_id):
    """
    Award all badges the worker qualifies for but has not yet received.
    Uses INSERT ... SELECT with a NOT EXISTS subquery to prevent duplicates.
    No new trigger is added — this uses only existing badge and worker_badge tables.
    SQL: INSERT ... SELECT, NOT EXISTS subquery, scalar subquery for completed_jobs
    """
    db = get_db()
    db.execute("""
        -- Award eligible badges using INSERT ... SELECT + NOT EXISTS
        INSERT INTO worker_badge (worker_id, badge_id, awarded_date)
        SELECT  ?,
                b.badge_id,
                DATE('now')
        FROM    badge b
        WHERE   b.min_jobs_required <= (
                    -- Scalar subquery: current completed_jobs value
                    SELECT  completed_jobs
                    FROM    worker
                    WHERE   worker_id = ?
                )
          AND   NOT EXISTS (
                    -- NOT EXISTS subquery: skip already-awarded badges
                    SELECT  1
                    FROM    worker_badge wb
                    WHERE   wb.worker_id = ?
                      AND   wb.badge_id  = b.badge_id
                )
    """, (worker_id, worker_id, worker_id))
    db.commit()


# ------------------------------------------------------------------
# ADMIN REPORTING
# ------------------------------------------------------------------

def get_admin_dashboard_stats():
    """
    Retrieve all statistics for the admin dashboard.
    SQL: COUNT, AVG, MIN, MAX aggregate functions; GROUP BY with HAVING;
         subquery; INNER JOIN; LEFT JOIN; ORDER BY
    """
    db    = get_db()
    stats = {}

    # -- COUNT aggregates --
    stats['total_customers'] = db.execute('SELECT COUNT(*) FROM customer').fetchone()[0]
    stats['total_workers']   = db.execute('SELECT COUNT(*) FROM worker').fetchone()[0]
    stats['total_bookings']  = db.execute('SELECT COUNT(*) FROM booking').fetchone()[0]
    stats['total_reviews']   = db.execute('SELECT COUNT(*) FROM review').fetchone()[0]

    # -- AVG aggregate: platform-wide average rating --
    stats['avg_rating'] = db.execute(
        'SELECT COALESCE(ROUND(AVG(rating), 2), 0.00) FROM review'
    ).fetchone()[0]

    # -- MIN and MAX: booking agreed-rate range --
    rate_row = db.execute(
        'SELECT MIN(agreed_rate), MAX(agreed_rate) FROM booking'
    ).fetchone()
    stats['min_rate'] = rate_row[0]
    stats['max_rate'] = rate_row[1]

    # -- GROUP BY status --
    stats['bookings_by_status'] = db.execute("""
        SELECT   status,
                 COUNT(*) AS cnt
        FROM     booking
        GROUP BY status
        ORDER BY cnt DESC
    """).fetchall()

    # -- GROUP BY with HAVING: categories with at least 1 worker offering --
    stats['popular_categories'] = db.execute("""
        SELECT   c.name,
                 COUNT(DISTINCT ws.worker_id) AS worker_count,
                 COUNT(DISTINCT b.booking_id) AS booking_count
        FROM     category c
        LEFT JOIN worker_service ws ON c.category_id = ws.category_id
        LEFT JOIN booking        b  ON c.category_id = b.category_id
        GROUP BY c.category_id, c.name
        HAVING   COUNT(DISTINCT ws.worker_id) >= 1
        ORDER BY booking_count DESC, worker_count DESC
    """).fetchall()

    # -- Subquery: top-rated workers who have at least one review --
    stats['top_workers'] = db.execute("""
        SELECT   w.worker_id,
                 w.first_name || ' ' || w.last_name  AS name,
                 w.city,
                 w.avg_rating,
                 w.completed_jobs
        FROM     worker w
        WHERE    w.worker_id IN (
                     -- Subquery: workers referenced by at least one review
                     SELECT DISTINCT b.worker_id
                     FROM   booking b
                     INNER JOIN review r ON b.booking_id = r.booking_id
                 )
        ORDER BY w.avg_rating DESC, w.completed_jobs DESC
        LIMIT    5
    """).fetchall()

    # -- Most active workers by completed_jobs --
    stats['most_active'] = db.execute("""
        SELECT   w.worker_id,
                 w.first_name || ' ' || w.last_name  AS name,
                 w.city,
                 w.completed_jobs,
                 w.avg_rating
        FROM     worker w
        ORDER BY w.completed_jobs DESC, w.avg_rating DESC
        LIMIT    5
    """).fetchall()

    # -- Recent bookings: INNER JOIN across 4 tables --
    stats['recent_bookings'] = db.execute("""
        SELECT   b.booking_id,
                 b.worker_id,
                 cu.first_name || ' ' || cu.last_name  AS customer_name,
                 w.first_name  || ' ' || w.last_name   AS worker_name,
                 c.name                                AS category_name,
                 b.status,
                 b.agreed_rate,
                 b.scheduled_start,
                 b.created_at
        FROM     booking b
        INNER JOIN customer  cu ON b.customer_id = cu.customer_id
        INNER JOIN worker     w ON b.worker_id   = w.worker_id
        INNER JOIN category   c ON b.category_id = c.category_id
        ORDER BY b.created_at DESC
        LIMIT    10
    """).fetchall()

    return stats


def get_view_worker_stats():
    """
    Query the existing v_worker_derived_stats view.
    The view dynamically recalculates completed_jobs and avg_rating for audit.
    It can be compared with the trigger-maintained stored values in worker table.
    SQL: SELECT from an existing VIEW (defined in schema_and_seed.sql, not modified)
    """
    db = get_db()
    return db.execute("""
        -- Using the existing view v_worker_derived_stats
        SELECT   worker_id,
                 worker_name,
                 city,
                 experience_years,
                 completed_jobs,
                 avg_rating
        FROM     v_worker_derived_stats
        ORDER BY avg_rating DESC, completed_jobs DESC
    """).fetchall()


def get_all_customers_admin():
    """Retrieve all customers for admin view. SQL: SELECT, ORDER BY"""
    db = get_db()
    return db.execute("""
        SELECT  customer_id, first_name, last_name, email,
                phone, address, registered_at
        FROM    customer
        ORDER   BY registered_at DESC
    """).fetchall()


def get_all_workers_admin():
    """
    Retrieve all workers with service counts for admin view.
    SQL: SELECT, LEFT JOIN, GROUP BY, COUNT aggregate
    """
    db = get_db()
    return db.execute("""
        SELECT   w.worker_id,
                 w.first_name || ' ' || w.last_name  AS name,
                 w.city,
                 w.experience_years,
                 w.avg_rating,
                 w.completed_jobs,
                 w.registered_at,
                 COUNT(ws.category_id) AS service_count
        FROM     worker w
        LEFT JOIN worker_service ws ON w.worker_id = ws.worker_id
        GROUP BY w.worker_id
        ORDER BY w.registered_at DESC
    """).fetchall()


def get_all_bookings_admin():
    """
    Retrieve all bookings for admin view.
    SQL: SELECT, INNER JOIN across 4 tables, ORDER BY
    """
    db = get_db()
    return db.execute("""
        SELECT   b.booking_id,
                 b.job_description,
                 cu.first_name || ' ' || cu.last_name  AS customer_name,
                 w.first_name  || ' ' || w.last_name   AS worker_name,
                 c.name                                AS category_name,
                 b.status,
                 b.agreed_rate,
                 b.scheduled_start,
                 b.created_at
        FROM     booking b
        INNER JOIN customer  cu ON b.customer_id = cu.customer_id
        INNER JOIN worker     w ON b.worker_id   = w.worker_id
        INNER JOIN category   c ON b.category_id = c.category_id
        ORDER BY b.created_at DESC
    """).fetchall()


# ============================================================
# TEMPLATE FILTERS & HELPERS
# ============================================================

@app.template_filter('lkr')
def lkr_format(value):
    """Format a number as LKR with comma thousands separator."""
    if value is None:
        return 'N/A'
    return f'{value:,.0f}'


@app.template_filter('stars')
def stars_filter(rating):
    """Return filled/empty star characters for a 1–5 rating."""
    r = int(rating or 0)
    return '★' * r + '☆' * (5 - r)


def get_initials(full_name):
    """Return up to two initials from a full name string."""
    parts = str(full_name).split()
    return ''.join(p[0].upper() for p in parts[:2]) if parts else '?'


app.jinja_env.globals['get_initials'] = get_initials


# ============================================================
# AUTH DECORATORS
# ============================================================

def login_required_customer(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('user_type') != 'customer':
            flash('Please log in as a customer to continue.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def login_required_worker(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('user_type') != 'worker':
            flash('Please log in as a worker to continue.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def login_required_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('user_type') != 'admin':
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated


# ============================================================
# FLASK ROUTES
# ============================================================

# ---- PUBLIC ----

@app.route('/')
def home():
    categories = get_category_worker_counts()
    workers    = get_featured_workers()
    return render_template_string(HOME_TEMPLATE,
        categories=categories, workers=workers,
        category_images=CATEGORY_IMAGES,
        category_icons=CATEGORY_ICONS,
        hero_image=HERO_IMAGE)


@app.route('/workers')
def worker_list():
    name        = request.args.get('name',        '').strip()
    city        = request.args.get('city',        '').strip()
    category_id = request.args.get('category_id', '').strip()
    workers     = search_workers(name or None, city or None, category_id or None)
    categories  = get_all_categories()
    return render_template_string(WORKERS_TEMPLATE,
        workers=workers, categories=categories,
        name=name, city=city, category_id=category_id,
        category_icons=CATEGORY_ICONS)


@app.route('/worker/<int:worker_id>')
def worker_profile(worker_id):
    worker         = get_worker_profile(worker_id)
    if not worker:
        flash('Worker not found.', 'error')
        return redirect(url_for('worker_list'))
    services       = get_worker_services(worker_id)
    qualifications = get_worker_qualifications(worker_id)
    availability   = get_worker_availability(worker_id)
    badges         = get_worker_badges(worker_id)
    reviews        = get_worker_reviews(worker_id)
    portfolio      = get_worker_portfolio(worker_id)
    return render_template_string(WORKER_PROFILE_TEMPLATE,
        worker=worker, services=services,
        qualifications=qualifications, availability=availability,
        badges=badges, reviews=reviews, portfolio=portfolio)


# ---- AUTH ----

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email     = request.form.get('email',     '').strip().lower()
        password  = request.form.get('password',  '')
        user_type = request.form.get('user_type', 'customer')

        if user_type == 'customer':
            user = find_customer_by_email(email)
            if user and check_password_hash(user['password_hash'], password):
                session['user_type'] = 'customer'
                session['user_id']   = user['customer_id']
                session['user_name'] = f"{user['first_name']} {user['last_name']}"
                return redirect(url_for('customer_dashboard'))
            flash('Invalid email or password.', 'error')

        elif user_type == 'worker':
            user = find_worker_by_email(email)
            if user and check_password_hash(user['password_hash'], password):
                session['user_type'] = 'worker'
                session['user_id']   = user['worker_id']
                session['user_name'] = f"{user['first_name']} {user['last_name']}"
                return redirect(url_for('worker_dashboard'))
            flash('Invalid email or password.', 'error')

    return render_template_string(LOGIN_TEMPLATE)


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))


@app.route('/register/customer', methods=['GET', 'POST'])
def register_customer():
    if request.method == 'POST':
        fn   = request.form.get('first_name', '').strip()
        ln   = request.form.get('last_name',  '').strip()
        em   = request.form.get('email',      '').strip().lower()
        ph   = request.form.get('phone',      '').strip()
        pw   = request.form.get('password',   '')
        addr = request.form.get('address',    '').strip()

        if not all([fn, ln, em, ph, pw, addr]):
            flash('All fields are required.', 'error')
        elif find_customer_by_email(em):
            flash('An account with that email already exists.', 'error')
        else:
            try:
                cid = create_customer(fn, ln, em, ph, generate_password_hash(pw), addr)
                session.update({'user_type': 'customer', 'user_id': cid,
                                'user_name': f'{fn} {ln}'})
                flash('Welcome to QuickDone! Your account has been created.', 'success')
                return redirect(url_for('customer_dashboard'))
            except Exception as e:
                flash(f'Registration failed: {e}', 'error')

    return render_template_string(REGISTER_CUSTOMER_TEMPLATE)


@app.route('/register/worker', methods=['GET', 'POST'])
def register_worker():
    categories = get_all_categories()
    if request.method == 'POST':
        fn  = request.form.get('first_name',       '').strip()
        ln  = request.form.get('last_name',        '').strip()
        em  = request.form.get('email',            '').strip().lower()
        ph  = request.form.get('phone',            '').strip()
        pw  = request.form.get('password',         '')
        cy  = request.form.get('city',             '').strip()
        exp = request.form.get('experience_years', '0').strip()
        bio = request.form.get('bio',              '').strip()
        profile_img = request.form.get('profile_image_url', '').strip() or None

        # Collect checked categories and their rates
        services = []
        for cat_id in request.form.getlist('category_ids'):
            rate = request.form.get(f'rate_{cat_id}', '').strip()
            if rate:
                try:
                    services.append((int(cat_id), float(rate)))
                except ValueError:
                    pass

        # Collect optional qualifications (up to 3)
        qualifications = []
        for i in [1, 2, 3]:
            t    = request.form.get(f'qual_title_{i}',       '').strip()
            inst = request.form.get(f'qual_institution_{i}', '').strip()
            yr   = request.form.get(f'qual_year_{i}',        '').strip()
            if t and inst and yr:
                qualifications.append((t, inst, yr))

        # Collect optional availability
        availabilities = []
        for day in ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']:
            if day in request.form.getlist('avail_days'):
                st = request.form.get(f'avail_start_{day}', '').strip()
                et = request.form.get(f'avail_end_{day}',   '').strip()
                if st and et:
                    availabilities.append((day, st, et))

        # Collect optional work example / portfolio images (up to 5)
        portfolio_items = []
        for i in range(1, 6):
            p_url   = request.form.get(f'portfolio_url_{i}', '').strip()
            p_title = request.form.get(f'portfolio_title_{i}', '').strip()
            if p_url:
                portfolio_items.append((p_url, p_title))

        if not all([fn, ln, em, ph, pw, cy]):
            flash('Please fill in all required fields.', 'error')
        elif not services:
            flash('Please select at least one service with a rate.', 'error')
        elif find_worker_by_email(em):
            flash('An account with that email already exists.', 'error')
        else:
            try:
                wid = create_worker(fn, ln, em, ph, generate_password_hash(pw),
                                    cy, exp or '0', bio,
                                    services, qualifications, availabilities,
                                    profile_image_url=profile_img,
                                    portfolio_items=portfolio_items)
                session.update({'user_type': 'worker', 'user_id': wid,
                                'user_name': f'{fn} {ln}'})
                flash('Welcome to QuickDone! Your worker profile is live.', 'success')
                return redirect(url_for('worker_dashboard'))
            except Exception as e:
                flash(f'Registration failed: {e}', 'error')

    return render_template_string(REGISTER_WORKER_TEMPLATE, categories=categories)


# ---- CUSTOMER ----

@app.route('/dashboard/customer')
@login_required_customer
def customer_dashboard():
    bookings = get_customer_bookings(session['user_id'])
    return render_template_string(CUSTOMER_DASHBOARD_TEMPLATE, bookings=bookings)


@app.route('/book/<int:worker_id>', methods=['GET', 'POST'])
@login_required_customer
def book_worker(worker_id):
    worker   = get_worker_profile(worker_id)
    if not worker:
        flash('Worker not found.', 'error')
        return redirect(url_for('worker_list'))
    services = get_worker_services(worker_id)
    if not services:
        flash('This worker has no services listed.', 'error')
        return redirect(url_for('worker_profile', worker_id=worker_id))

    if request.method == 'POST':
        cat_id  = request.form.get('category_id',    '').strip()
        desc    = request.form.get('job_description', '').strip()
        addr    = request.form.get('job_address',     '').strip()
        sched   = request.form.get('scheduled_start', '').strip()

        if not all([cat_id, desc, addr, sched]):
            flash('All fields are required.', 'error')
        else:
            rate = get_worker_service_rate(worker_id, cat_id)
            if rate is None:
                flash('Invalid service selection.', 'error')
            else:
                try:
                    sched = sched.replace('T', ' ')   # datetime-local → SQLite format
                    bid = create_booking(session['user_id'], worker_id, cat_id,
                                        desc, addr, sched, rate)
                    flash('Booking submitted successfully!', 'success')
                    return redirect(url_for('booking_detail', booking_id=bid))
                except Exception as e:
                    flash(f'Booking failed: {e}', 'error')

    return render_template_string(BOOK_TEMPLATE, worker=worker, services=services)


@app.route('/booking/<int:booking_id>')
@login_required_customer
def booking_detail(booking_id):
    booking = get_booking_detail(booking_id)
    if not booking or booking['customer_id'] != session['user_id']:
        flash('Booking not found.', 'error')
        return redirect(url_for('customer_dashboard'))
    return render_template_string(BOOKING_DETAIL_TEMPLATE, booking=booking)


@app.route('/booking/<int:booking_id>/cancel', methods=['POST'])
@login_required_customer
def cancel_booking_route(booking_id):
    booking = get_booking_detail(booking_id)
    if not booking or booking['customer_id'] != session['user_id']:
        flash('Booking not found.', 'error')
    elif booking['status'] not in ('PENDING', 'CONFIRMED'):
        flash('This booking cannot be cancelled.', 'error')
    else:
        cancel_booking(booking_id, session['user_id'])
        flash('Booking cancelled successfully.', 'success')
    return redirect(url_for('customer_dashboard'))


@app.route('/booking/<int:booking_id>/review', methods=['GET', 'POST'])
@login_required_customer
def write_review(booking_id):
    booking = get_booking_detail(booking_id)
    if not booking or booking['customer_id'] != session['user_id']:
        flash('Booking not found.', 'error')
        return redirect(url_for('customer_dashboard'))
    if booking['status'] != 'COMPLETED':
        flash('Only completed bookings can be reviewed.', 'error')
        return redirect(url_for('customer_dashboard'))
    if check_booking_has_review(booking_id):
        flash('You have already reviewed this booking.', 'info')
        return redirect(url_for('customer_dashboard'))

    if request.method == 'POST':
        rating  = request.form.get('rating',  '').strip()
        comment = request.form.get('comment', '').strip()
        if not rating:
            flash('Please select a star rating.', 'error')
        else:
            try:
                add_review(booking_id, int(rating), comment or None)
                flash('Review submitted! Thank you for your feedback.', 'success')
                return redirect(url_for('customer_dashboard'))
            except Exception as e:
                flash(f'Could not submit review: {e}', 'error')

    return render_template_string(REVIEW_TEMPLATE, booking=booking)


# ---- WORKER ----

@app.route('/dashboard/worker')
@login_required_worker
def worker_dashboard():
    worker   = get_worker_profile(session['user_id'])
    bookings = get_worker_bookings(session['user_id'])
    badges   = get_worker_badges(session['user_id'])
    return render_template_string(WORKER_DASHBOARD_TEMPLATE,
        worker=worker, bookings=bookings, badges=badges)


@app.route('/booking/<int:booking_id>/status', methods=['POST'])
@login_required_worker
def update_status(booking_id):
    new_status = request.form.get('status', '').strip()
    ok = update_booking_status(booking_id, session['user_id'], new_status)
    if ok:
        flash(f'Booking updated to {new_status}.', 'success')
        if new_status == 'COMPLETED':
            award_eligible_badges(session['user_id'])
            flash('Badges checked and awarded if eligible.', 'info')
    else:
        flash('Status update not permitted.', 'error')
    return redirect(url_for('worker_dashboard'))


@app.route('/dashboard/worker/profile', methods=['GET', 'POST'])
@login_required_worker
def worker_profile_edit():
    wid            = session['user_id']
    worker         = get_worker_profile(wid)
    services       = get_worker_services(wid)
    qualifications = get_worker_qualifications(wid)
    availability   = get_worker_availability(wid)
    portfolio      = get_worker_portfolio(wid)
    all_categories = get_all_categories()

    if request.method == 'POST':
        action = request.form.get('action', '')

        if action == 'update_profile':
            p_img = request.form.get('profile_image_url', '').strip() or None
            update_worker_profile(wid,
                request.form.get('bio',              '').strip(),
                request.form.get('phone',            '').strip(),
                request.form.get('city',             '').strip(),
                request.form.get('experience_years', '0').strip() or '0',
                profile_image_url=p_img)
            flash('Profile updated.', 'success')

        elif action == 'add_service':
            cat_id = request.form.get('category_id', '').strip()
            rate   = request.form.get('hourly_rate',  '').strip()
            if cat_id and rate:
                try:
                    add_worker_service(wid, cat_id, rate)
                    flash('Service added.', 'success')
                except Exception as e:
                    flash(f'Could not add service: {e}', 'error')
            else:
                flash('Select a category and enter a rate.', 'error')

        elif action == 'remove_service':
            cat_id = request.form.get('category_id', '').strip()
            if cat_id:
                ok = remove_worker_service(wid, cat_id)
                flash('Service removed.' if ok else
                      'Cannot remove — active bookings exist for this service.', 
                      'success' if ok else 'error')

        elif action == 'add_qualification':
            t    = request.form.get('qual_title',       '').strip()
            inst = request.form.get('qual_institution', '').strip()
            yr   = request.form.get('qual_year',        '').strip()
            if t and inst and yr:
                try:
                    add_qualification(wid, t, inst, yr)
                    flash('Qualification added.', 'success')
                except Exception as e:
                    flash(f'Could not add qualification: {e}', 'error')
            else:
                flash('All qualification fields are required.', 'error')

        elif action == 'add_availability':
            day = request.form.get('avail_day',   '').strip()
            st  = request.form.get('avail_start', '').strip()
            et  = request.form.get('avail_end',   '').strip()
            if day and st and et:
                try:
                    add_availability(wid, day, st, et)
                    flash('Availability updated.', 'success')
                except Exception as e:
                    flash(f'Could not update availability: {e}', 'error')
            else:
                flash('Select a day and time range.', 'error')

        elif action == 'add_portfolio':
            img_url = request.form.get('image_url', '').strip()
            title   = request.form.get('title',     '').strip()
            if img_url:
                ok, msg = add_portfolio_image(wid, img_url, title)
                flash(msg, 'success' if ok else 'error')
            else:
                flash('Image URL is required.', 'error')

        elif action == 'remove_portfolio':
            port_id = request.form.get('portfolio_id', '').strip()
            if port_id:
                delete_portfolio_image(port_id, wid)
                flash('Work example removed.', 'success')

        return redirect(url_for('worker_profile_edit'))

    return render_template_string(WORKER_PROFILE_EDIT_TEMPLATE,
        worker=worker, services=services,
        qualifications=qualifications, availability=availability,
        portfolio=portfolio, all_categories=all_categories)


# ---- ADMIN ----

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        uname = request.form.get('username', '').strip()
        pw    = request.form.get('password', '')
        # Admin credentials are Python-only constants; no DB lookup
        if uname == ADMIN_USERNAME and pw == ADMIN_PASSWORD:
            session.update({'user_type': 'admin', 'user_name': 'Admin'})
            return redirect(url_for('admin_dashboard'))
        flash('Invalid admin credentials.', 'error')
    return render_template_string(ADMIN_LOGIN_TEMPLATE)


@app.route('/admin/dashboard')
@login_required_admin
def admin_dashboard():
    stats      = get_admin_dashboard_stats()
    view_stats = get_view_worker_stats()
    return render_template_string(ADMIN_DASHBOARD_TEMPLATE,
        stats=stats, view_stats=view_stats)


@app.route('/admin/customers')
@login_required_admin
def admin_customers():
    customers = get_all_customers_admin()
    return render_template_string(ADMIN_CUSTOMERS_TEMPLATE, customers=customers)


@app.route('/admin/workers')
@login_required_admin
def admin_workers():
    workers = get_all_workers_admin()
    return render_template_string(ADMIN_WORKERS_TEMPLATE, workers=workers)


@app.route('/admin/bookings')
@login_required_admin
def admin_bookings():
    bookings = get_all_bookings_admin()
    return render_template_string(ADMIN_BOOKINGS_TEMPLATE, bookings=bookings)


# ============================================================
# HTML TEMPLATES & CSS
# All embedded templates use render_template_string with Jinja2.
# SHARED_CSS is defined once and embedded in every page via Python
# string concatenation at module load time (no runtime overhead).
# ============================================================

SHARED_CSS = """
/* ---- RESET & BASE ---- */
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}
html{scroll-behavior:smooth;}
:root{
  --g950:#062F25;--g900:#083B2E;--g800:#0B4A39;--g700:#12634A;
  --m100:#E7F2EC;--m200:#D4E8DC;
  --bg:#F7F8F5;--surf:#FFFFFF;
  --tp:#18231E;--ts:#69766F;--bd:#E5EAE6;--star:#E9AD45;
  --r:10px;--rl:16px;--sh:0 2px 12px rgba(0,0,0,.07);
}
body{font-family:'Inter',system-ui,-apple-system,BlinkMacSystemFont,sans-serif;
  background:var(--bg);color:var(--tp);line-height:1.65;font-size:15px;
  -webkit-font-smoothing:antialiased;}
a{color:inherit;text-decoration:none;}
img{max-width:100%;display:block;}
button,input,select,textarea{font-family:inherit;}

/* ---- CONTAINER ---- */
.c{max-width:1240px;margin:0 auto;padding:0 24px;}

/* ---- NAVIGATION ---- */
.nav-h{position:absolute;top:0;left:0;right:0;z-index:100;}
.nav-s{position:sticky;top:0;z-index:100;background:var(--surf);
  border-bottom:1.5px solid var(--bd);}
.nav-i{max-width:1240px;margin:0 auto;padding:0 24px;
  display:flex;align-items:center;height:68px;}
.nav-logo{display:flex;align-items:center;gap:9px;font-size:19px;
  font-weight:800;letter-spacing:-.5px;flex-shrink:0;}
.nav-logo-mark{width:30px;height:30px;background:var(--g700);border-radius:8px;
  display:flex;align-items:center;justify-content:center;
  font-size:14px;font-weight:900;color:#fff;}
.nav-h .nav-logo{color:#fff;}
.nav-s .nav-logo{color:var(--tp);}
.nav-h .nav-logo-mark{background:rgba(255,255,255,.15);border:1.5px solid rgba(255,255,255,.25);}
.nav-links{display:flex;gap:4px;list-style:none;margin:0 auto;}
.nav-links a{font-size:14px;font-weight:500;padding:7px 14px;
  border-radius:7px;transition:background .15s,color .15s;}
.nav-h .nav-links a{color:rgba(255,255,255,.85);}
.nav-h .nav-links a:hover{background:rgba(255,255,255,.1);color:#fff;}
.nav-s .nav-links a{color:var(--ts);}
.nav-s .nav-links a:hover{background:var(--bg);color:var(--tp);}
.nav-actions{display:flex;gap:8px;align-items:center;}

/* ---- BUTTONS ---- */
.btn{display:inline-flex;align-items:center;justify-content:center;gap:6px;
  padding:10px 20px;border-radius:var(--r);font-size:14px;font-weight:600;
  border:none;cursor:pointer;transition:all .15s;text-align:center;
  line-height:1;white-space:nowrap;}
.btn-p{background:var(--g800);color:#fff;}
.btn-p:hover{background:var(--g700);}
.btn-s{background:#fff;color:var(--g800);border:1.5px solid var(--bd);}
.btn-s:hover{border-color:var(--g700);color:var(--g700);}
.btn-d{background:#FEE2E2;color:#991B1B;}
.btn-d:hover{background:#FECACA;}
.btn-sm{padding:7px 15px;font-size:13px;}
.btn-fw{width:100%;display:flex;}
.btn-ghost-w{color:rgba(255,255,255,.9);border:1.5px solid rgba(255,255,255,.3);}
.btn-ghost-w:hover{background:rgba(255,255,255,.1);}
.btn-cta-hero{background:#fff;color:var(--g900);}
.btn-cta-hero:hover{background:var(--m100);}
.btn-s-nav{background:#fff;color:var(--g800);border:1.5px solid var(--bd);}
.btn-s-nav:hover{border-color:var(--g700);}

/* ---- HERO ---- */
.hero{position:relative;min-height:580px;display:flex;align-items:center;
  background:var(--g950);overflow:hidden;}
.hero-bg{position:absolute;inset:0;background-size:cover;
  background-position:center;opacity:.38;}
.hero-ov{position:absolute;inset:0;
  background:linear-gradient(135deg,rgba(6,47,37,.93) 0%,rgba(8,59,46,.78) 55%,rgba(11,74,57,.65) 100%);}
.hero-ct{position:relative;z-index:10;width:100%;max-width:1240px;
  margin:0 auto;padding:112px 24px 64px;text-align:center;}
.hero-title{font-size:clamp(28px,5vw,54px);font-weight:800;color:#fff;
  line-height:1.08;letter-spacing:-.025em;margin-bottom:16px;}
.hero-sub{font-size:17px;color:rgba(255,255,255,.78);max-width:500px;
  margin:0 auto 36px;line-height:1.6;}

/* ---- SEARCH BAR ---- */
.sb-wrap{max-width:700px;margin:0 auto;}
.sb{background:#fff;border-radius:50px;display:flex;align-items:center;
  padding:5px 5px 5px 22px;box-shadow:0 10px 40px rgba(0,0,0,.28);}
.sb input[type=text]{flex:1;border:none;outline:none;font-size:15px;
  color:var(--tp);background:transparent;min-width:0;}
.sb input[type=text]::placeholder{color:var(--ts);}
.sb-div{width:1.5px;height:24px;background:var(--bd);margin:0 12px;flex-shrink:0;}
.sb select{border:none;outline:none;font-size:14px;color:var(--ts);
  background:transparent;cursor:pointer;padding:0 4px;min-width:130px;
  -webkit-appearance:none;}
.sb-btn{background:var(--g800);color:#fff;border:none;border-radius:44px;
  padding:12px 28px;font-size:14px;font-weight:600;cursor:pointer;
  transition:background .15s;flex-shrink:0;}
.sb-btn:hover{background:var(--g700);}

/* ---- CATEGORY SHORTCUTS ---- */
.cat-short{display:flex;flex-wrap:wrap;gap:10px;justify-content:center;
  margin-top:28px;position:relative;z-index:10;}
.cat-pill{display:flex;align-items:center;gap:7px;
  background:rgba(255,255,255,.11);border:1.5px solid rgba(255,255,255,.22);
  border-radius:50px;padding:7px 16px;color:#fff;font-size:13px;
  font-weight:500;transition:all .15s;backdrop-filter:blur(4px);}
.cat-pill:hover{background:rgba(255,255,255,.20);border-color:rgba(255,255,255,.4);}

/* ---- SECTIONS ---- */
.sec{padding:72px 0;}
.sec-sm{padding:48px 0;}
.sec-bg-w{background:#fff;}
.sec-bg-pg{background:var(--bg);}
.sl{font-size:11.5px;font-weight:700;letter-spacing:.09em;
  text-transform:uppercase;color:var(--g700);margin-bottom:10px;}
.st{font-size:30px;font-weight:800;color:var(--tp);letter-spacing:-.02em;
  margin-bottom:10px;line-height:1.1;}
.ss{font-size:15px;color:var(--ts);max-width:480px;line-height:1.65;}
.sh{margin-bottom:44px;}
.sh-row{display:flex;align-items:flex-end;justify-content:space-between;
  margin-bottom:44px;}

/* ---- CATEGORY CARDS (tall, image-based) ---- */
.cc-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:20px;}
.cc{position:relative;border-radius:var(--rl);overflow:hidden;height:310px;
  display:block;transition:transform .2s;}
.cc:hover{transform:translateY(-4px);}
.cc:hover .cc-bg{transform:scale(1.05);}
.cc-bg{position:absolute;inset:0;background-size:cover;background-position:center;
  background-color:var(--g800);transition:transform .3s ease;}
.cc-ov{position:absolute;inset:0;
  background:linear-gradient(to top,rgba(6,47,37,.92) 0%,rgba(6,47,37,.35) 55%,transparent 100%);}
.cc-body{position:absolute;bottom:0;left:0;right:0;padding:20px;}
.cc-name{color:#fff;font-size:18px;font-weight:700;line-height:1.2;}
.cc-count{color:rgba(255,255,255,.70);font-size:13px;margin-top:5px;}

/* ---- WORKER CARDS ---- */
.wc-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:20px;}
.wc{background:#fff;border-radius:var(--rl);border:1.5px solid var(--bd);
  padding:20px;display:flex;flex-direction:column;gap:14px;
  transition:box-shadow .2s,transform .2s;}
.wc:hover{box-shadow:var(--sh);transform:translateY(-2px);}
.wc-top{display:flex;align-items:flex-start;gap:14px;}
.av{width:50px;height:50px;border-radius:50%;background:var(--g800);color:#fff;
  font-size:17px;font-weight:700;display:flex;align-items:center;
  justify-content:center;flex-shrink:0;}
.av-lg{width:76px;height:76px;font-size:26px;}
.av-xl{width:88px;height:88px;font-size:30px;border:3px solid rgba(255,255,255,.2);}
.wn{font-size:16px;font-weight:700;line-height:1.2;}
.wm{font-size:13px;color:var(--ts);display:flex;align-items:center;
  gap:10px;flex-wrap:wrap;margin-top:4px;}
.tags{display:flex;flex-wrap:wrap;gap:6px;}
.tag{display:inline-block;background:var(--m100);color:var(--g800);
  font-size:12px;font-weight:600;padding:3px 10px;border-radius:50px;}
.rate-t{font-size:13px;color:var(--ts);}
.rate-t strong{color:var(--tp);}

/* ---- STEPS ---- */
.steps-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:32px;}
.step-card{background:#fff;border:1.5px solid var(--bd);border-radius:var(--rl);
  padding:32px 24px;text-align:center;}
.step-num{width:46px;height:46px;border-radius:50%;background:var(--g800);
  color:#fff;font-size:20px;font-weight:800;display:flex;align-items:center;
  justify-content:center;margin:0 auto 16px;}
.step-title{font-size:16px;font-weight:700;margin-bottom:8px;}
.step-desc{font-size:14px;color:var(--ts);}

/* ---- FOOTER ---- */
.footer{background:var(--g950);color:rgba(255,255,255,.65);padding:56px 0 28px;}
.ft{display:flex;justify-content:space-between;align-items:flex-start;
  margin-bottom:44px;gap:32px;}
.fl{font-size:20px;font-weight:800;color:#fff;display:flex;
  align-items:center;gap:9px;margin-bottom:10px;}
.fl-mark{width:28px;height:28px;background:var(--g700);border-radius:7px;
  display:flex;align-items:center;justify-content:center;
  font-size:13px;color:#fff;font-weight:900;}
.ft-tag{font-size:13px;max-width:260px;line-height:1.6;}
.ft-cols{display:flex;gap:56px;}
.ft-col h4{color:#fff;font-size:13px;font-weight:700;margin-bottom:14px;}
.ft-col a{display:block;font-size:13px;color:rgba(255,255,255,.60);
  line-height:2.2;transition:color .15s;}
.ft-col a:hover{color:#fff;}
.ft-bot{border-top:1px solid rgba(255,255,255,.10);padding-top:24px;font-size:12.5px;}

/* ---- FLASH ---- */
.fl-wrap{padding:12px 0;}
.fl-ct{max-width:1240px;margin:0 auto;padding:0 24px;}
.fl-msg{padding:12px 18px;border-radius:8px;font-size:14px;margin-bottom:8px;}
.fl-success{background:#D1FAE5;color:#065F46;border:1px solid #A7F3D0;}
.fl-error{background:#FEE2E2;color:#991B1B;border:1px solid #FECACA;}
.fl-info{background:var(--m100);color:var(--g900);border:1px solid var(--m200);}
.fl-warning{background:#FEF3C7;color:#92400E;border:1px solid #FDE68A;}

/* ---- FORMS ---- */
.fg{margin-bottom:20px;}
.fl-label{display:block;font-size:12.5px;font-weight:700;color:var(--ts);
  letter-spacing:.05em;text-transform:uppercase;margin-bottom:7px;}
.fi,.fsel,.fta{width:100%;padding:11px 14px;border:1.5px solid var(--bd);
  border-radius:var(--r);font-size:15px;color:var(--tp);background:#fff;
  transition:border-color .15s;outline:none;-webkit-appearance:none;}
.fi:focus,.fsel:focus,.fta:focus{border-color:var(--g700);
  box-shadow:0 0 0 3px rgba(18,99,74,.10);}
.fta{min-height:100px;resize:vertical;}
.fsel{appearance:none;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8'%3E%3Cpath fill='%2369766F' d='M6 8L0 0h12z'/%3E%3C/svg%3E");
  background-repeat:no-repeat;background-position:right 14px center;padding-right:36px;}
.fr{display:grid;grid-template-columns:1fr 1fr;gap:16px;}
.f-hint{font-size:12px;color:var(--ts);margin-top:5px;}

/* ---- PAGE HEADER ---- */
.ph{background:var(--g900);padding:44px 0;color:#fff;}
.ph h1{font-size:26px;font-weight:800;margin-bottom:6px;}
.ph p{color:rgba(255,255,255,.70);font-size:15px;}

/* ---- PROFILE PAGE ---- */
.prof-h{background:var(--g900);padding:48px 0;}
.prof-hi{max-width:1240px;margin:0 auto;padding:0 24px;
  display:flex;align-items:flex-start;gap:24px;}
.prof-info h1{font-size:26px;font-weight:800;color:#fff;margin-bottom:8px;}
.prof-meta{display:flex;flex-wrap:wrap;gap:16px;color:rgba(255,255,255,.75);
  font-size:14px;}
.prof-meta span{display:flex;align-items:center;gap:5px;}
.prof-rating{margin-top:12px;display:flex;align-items:center;gap:10px;}
.r-big{font-size:22px;font-weight:800;color:#fff;}
.prof-body{max-width:1240px;margin:0 auto;padding:32px 24px 56px;
  display:grid;grid-template-columns:1fr 320px;gap:24px;}
.panel{background:#fff;border:1.5px solid var(--bd);border-radius:var(--rl);
  overflow:hidden;margin-bottom:20px;}
.pan-h{padding:15px 20px;font-size:14px;font-weight:700;
  border-bottom:1.5px solid var(--bd);color:var(--tp);}
.pan-b{padding:20px;}
.pan-b p{font-size:14px;color:var(--ts);line-height:1.65;}
.avail-row{display:flex;gap:10px;align-items:center;
  padding:7px 0;border-bottom:1px solid var(--bd);font-size:14px;}
.avail-row:last-child{border-bottom:none;}
.avail-day{width:100px;font-weight:600;color:var(--tp);}
.avail-time{color:var(--ts);}
.rev-item{padding:16px 0;border-bottom:1px solid var(--bd);}
.rev-item:last-child{border-bottom:none;}
.rev-hd{display:flex;align-items:center;gap:10px;margin-bottom:6px;}
.rev-nm{font-weight:700;font-size:14px;}
.rev-dt{font-size:12px;color:var(--ts);margin-left:auto;}
.rev-txt{font-size:14px;color:var(--ts);line-height:1.65;}

/* ---- DASHBOARD ---- */
.dash-wrap{display:flex;min-height:calc(100vh - 68px);}
.sidebar{width:220px;background:#fff;border-right:1.5px solid var(--bd);
  padding:20px 0;flex-shrink:0;}
.sb-logo{padding:0 16px 16px;border-bottom:1.5px solid var(--bd);margin-bottom:8px;}
.sb-logo-txt{font-size:17px;font-weight:800;color:var(--tp);
  display:flex;align-items:center;gap:7px;}
.sb-logo-mark{width:24px;height:24px;background:var(--g800);color:#fff;
  border-radius:6px;display:flex;align-items:center;justify-content:center;
  font-size:12px;font-weight:900;}
.sb-user{font-size:12px;color:var(--ts);margin-top:5px;}
.sb-nav{padding:8px 0;}
.sb-nav a{display:flex;align-items:center;gap:8px;padding:9px 16px;
  font-size:14px;font-weight:500;color:var(--ts);
  border-left:3px solid transparent;transition:all .15s;}
.sb-nav a:hover,.sb-nav a.active{background:var(--m100);color:var(--g800);
  border-left-color:var(--g800);}
.sb-sec{font-size:11px;font-weight:700;text-transform:uppercase;
  letter-spacing:.07em;color:var(--ts);padding:12px 16px 4px;opacity:.7;}
.dash-main{flex:1;padding:32px;overflow-y:auto;background:var(--bg);}
.dash-title{font-size:22px;font-weight:800;margin-bottom:24px;}

/* ---- KPI ---- */
.kpi-row{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));
  gap:16px;margin-bottom:28px;}
.kpi{background:#fff;border:1.5px solid var(--bd);border-radius:var(--rl);
  padding:20px;}
.kpi-gl{border-left:3px solid var(--g700);}
.kpi-l{font-size:11.5px;font-weight:700;text-transform:uppercase;
  letter-spacing:.06em;color:var(--ts);margin-bottom:10px;}
.kpi-v{font-size:32px;font-weight:800;color:var(--tp);line-height:1;}
.kpi-s{font-size:12px;color:var(--ts);margin-top:5px;}

/* ---- TABLES ---- */
.tw{background:#fff;border:1.5px solid var(--bd);border-radius:var(--rl);
  overflow:hidden;margin-bottom:24px;}
.tw-hd{display:flex;align-items:center;justify-content:space-between;
  padding:14px 20px;border-bottom:1.5px solid var(--bd);}
.tw-t{font-size:15px;font-weight:700;}
table{width:100%;border-collapse:collapse;}
thead th{text-align:left;padding:10px 16px;font-size:11px;font-weight:700;
  text-transform:uppercase;letter-spacing:.06em;color:var(--ts);
  background:var(--bg);border-bottom:1.5px solid var(--bd);}
tbody td{padding:12px 16px;font-size:14px;border-bottom:1px solid var(--bd);
  vertical-align:middle;}
tbody tr:last-child td{border-bottom:none;}
tbody tr:hover td{background:#FAFBFA;}

/* ---- STATUS ---- */
.st-b{display:inline-block;padding:3px 10px;border-radius:50px;
  font-size:11.5px;font-weight:700;letter-spacing:.03em;}
.s-PENDING{background:#FEF3C7;color:#92400E;}
.s-CONFIRMED{background:#DBEAFE;color:#1E40AF;}
.s-IN_PROGRESS{background:var(--m100);color:var(--g800);}
.s-COMPLETED{background:#D1FAE5;color:#065F46;}
.s-CANCELLED{background:#FEE2E2;color:#991B1B;}

/* ---- BADGE PILL ---- */
.badge-pill{display:inline-flex;align-items:center;gap:5px;background:var(--m100);
  color:var(--g800);font-size:12px;font-weight:700;padding:4px 11px;
  border-radius:50px;border:1.5px solid var(--m200);}

/* ---- AUTH PAGES ---- */
.auth-pg{min-height:100vh;display:flex;align-items:center;justify-content:center;
  background:var(--g950);padding:24px;}
.auth-card{background:#fff;border-radius:var(--rl);padding:40px;
  width:100%;max-width:460px;box-shadow:0 20px 60px rgba(0,0,0,.35);}
.auth-logo{text-align:center;margin-bottom:28px;}
.auth-logo-mark{width:48px;height:48px;background:var(--g800);border-radius:13px;
  color:#fff;font-size:22px;font-weight:900;display:inline-flex;
  align-items:center;justify-content:center;margin-bottom:10px;}
.auth-logo-name{font-size:22px;font-weight:800;color:var(--tp);}
.auth-t{font-size:20px;font-weight:800;margin-bottom:5px;}
.auth-s{font-size:14px;color:var(--ts);margin-bottom:28px;}
.auth-sw{text-align:center;font-size:13px;color:var(--ts);margin-top:20px;}
.auth-sw a{color:var(--g800);font-weight:600;}
.ut-tabs{display:flex;border:1.5px solid var(--bd);border-radius:var(--r);
  overflow:hidden;margin-bottom:24px;}
.ut-tab{flex:1;padding:10px;text-align:center;font-size:14px;font-weight:600;
  cursor:pointer;color:var(--ts);border:none;background:#fff;
  transition:all .15s;}
.ut-tab.act{background:var(--g800);color:#fff;}

/* ---- FILTER BAR ---- */
.fbar{background:#fff;border:1.5px solid var(--bd);border-radius:var(--rl);
  padding:20px;display:flex;gap:16px;align-items:flex-end;
  flex-wrap:wrap;margin-bottom:28px;}
.fg-f{display:flex;flex-direction:column;gap:6px;min-width:150px;flex:1;}
.fg-fl{font-size:11.5px;font-weight:700;text-transform:uppercase;
  letter-spacing:.05em;color:var(--ts);}
.f-in,.f-sel{padding:9px 13px;border:1.5px solid var(--bd);
  border-radius:var(--r);font-size:14px;color:var(--tp);
  background:#fff;outline:none;-webkit-appearance:none;
  transition:border-color .15s;width:100%;}
.f-in:focus,.f-sel:focus{border-color:var(--g700);}

/* ---- EMPTY STATE ---- */
.empty{text-align:center;padding:56px 24px;}
.empty-icon{font-size:48px;margin-bottom:16px;}
.empty-t{font-size:18px;font-weight:700;margin-bottom:8px;}
.empty-s{font-size:14px;color:var(--ts);max-width:320px;margin:0 auto 20px;}

/* ---- MISC ---- */
.div{height:1.5px;background:var(--bd);margin:20px 0;}
.tc{text-align:center;}.ts-m{color:var(--ts);}.ts-sm{font-size:13px;}
.fw7{font-weight:700;}.mt-a{margin-top:auto;}
.mt16{margin-top:16px;}.mb16{margin-bottom:16px;}.mb24{margin-bottom:24px;}
.star-y{color:var(--star);}
.flex-row{display:flex;align-items:center;gap:12px;}
.ml-a{margin-left:auto;}
.p0{padding:0;}

/* ---- BOOKING ACTION FORM ---- */
.ba-form{display:inline;}

/* ---- RESPONSIVE ---- */
@media(max-width:768px){
  .nav-links{display:none;}
  .hero{min-height:480px;}
  .hero-ct{padding:90px 20px 50px;}
  .sb{flex-wrap:wrap;border-radius:16px;padding:12px;border-radius:14px;}
  .sb-div{display:none;}
  .sb-btn{width:100%;border-radius:var(--r);margin-top:8px;padding:12px;}
  .cc-grid{grid-template-columns:repeat(2,1fr);}
  .steps-grid{grid-template-columns:1fr;}
  .prof-body{grid-template-columns:1fr;}
  .dash-wrap{flex-direction:column;}
  .sidebar{width:100%;border-right:none;border-bottom:1.5px solid var(--bd);}
  .ft{flex-direction:column;}
  .ft-cols{flex-wrap:wrap;gap:24px;}
  .fr{grid-template-columns:1fr;}
  .kpi-row{grid-template-columns:repeat(2,1fr);}
  .sh-row{flex-direction:column;gap:16px;align-items:flex-start;}
  .wc-grid{grid-template-columns:1fr;}
}
"""

# -- Shared nav + footer Jinja2 template fragments --

_NAV_H = """
<nav class="nav-h">
  <div class="nav-i">
    <a class="nav-logo" href="/"><span class="nav-logo-mark">Q</span>QuickDone</a>
    <ul class="nav-links">
      <li><a href="/">Home</a></li>
      <li><a href="/workers">Find Workers</a></li>
    </ul>
    <div class="nav-actions">
      {% if session.get('user_type') == 'customer' %}
        <a href="/dashboard/customer" class="btn btn-sm btn-ghost-w">My Bookings</a>
        <a href="/logout" class="btn btn-sm btn-cta-hero">Log Out</a>
      {% elif session.get('user_type') == 'worker' %}
        <a href="/dashboard/worker" class="btn btn-sm btn-ghost-w">Dashboard</a>
        <a href="/logout" class="btn btn-sm btn-cta-hero">Log Out</a>
      {% elif session.get('user_type') == 'admin' %}
        <a href="/admin/dashboard" class="btn btn-sm btn-ghost-w">Admin</a>
        <a href="/logout" class="btn btn-sm btn-cta-hero">Log Out</a>
      {% else %}
        <a href="/login" class="btn btn-sm btn-ghost-w">Log In</a>
        <a href="/register/customer" class="btn btn-sm btn-cta-hero">Get Started</a>
      {% endif %}
    </div>
  </div>
</nav>
"""

_NAV_S = """
<nav class="nav-s">
  <div class="nav-i">
    <a class="nav-logo" href="/"><span class="nav-logo-mark" style="background:var(--g700);border:none;">Q</span>QuickDone</a>
    <ul class="nav-links">
      <li><a href="/">Home</a></li>
      <li><a href="/workers">Find Workers</a></li>
    </ul>
    <div class="nav-actions">
      {% if session.get('user_type') == 'customer' %}
        <a href="/dashboard/customer" class="btn btn-sm btn-s-nav">My Bookings</a>
        <a href="/logout" class="btn btn-sm btn-p">Log Out</a>
      {% elif session.get('user_type') == 'worker' %}
        <a href="/dashboard/worker" class="btn btn-sm btn-s-nav">Dashboard</a>
        <a href="/logout" class="btn btn-sm btn-p">Log Out</a>
      {% elif session.get('user_type') == 'admin' %}
        <a href="/admin/dashboard" class="btn btn-sm btn-s-nav">Admin Panel</a>
        <a href="/logout" class="btn btn-sm btn-p">Log Out</a>
      {% else %}
        <a href="/login" class="btn btn-sm btn-s">Log In</a>
        <a href="/register/customer" class="btn btn-sm btn-p">Get Started</a>
      {% endif %}
    </div>
  </div>
</nav>
"""

_FLASHES = """
{% with messages = get_flashed_messages(with_categories=True) %}
{% if messages %}
<div class="fl-wrap"><div class="fl-ct">
{% for cat, msg in messages %}
<div class="fl-msg fl-{{ cat }}">{{ msg }}</div>
{% endfor %}
</div></div>
{% endif %}
{% endwith %}
"""

_FOOTER = """
<footer class="footer">
  <div class="c">
    <div class="ft">
      <div>
        <div class="fl"><span class="fl-mark">Q</span>QuickDone</div>
        <p class="ft-tag">Connecting trusted local service professionals with people who need them across Sri Lanka.</p>
      </div>
      <div class="ft-cols">
        <div class="ft-col">
          <h4>Find Services</h4>
          <a href="/workers">All Workers</a>
          <a href="/workers?category_id=1">Electrical</a>
          <a href="/workers?category_id=2">Plumbing</a>
          <a href="/workers?category_id=3">AC Servicing</a>
          <a href="/workers?category_id=4">Deep Cleaning</a>
          <a href="/workers?category_id=5">Carpentry</a>
        </div>
        <div class="ft-col">
          <h4>Account</h4>
          <a href="/login">Log In</a>
          <a href="/register/customer">Register as Customer</a>
          <a href="/register/worker">Join as Worker</a>
          <a href="/admin/login">Admin Login</a>
        </div>
      </div>
    </div>
    <div class="ft-bot">© 2026 QuickDone — DBMS Foundations Assignment</div>
  </div>
</footer>
"""


def _page(title, body, nav='solid'):
    """Wrap body Jinja2 string in a complete HTML page with shared CSS."""
    nav_html = _NAV_H if nav == 'hero' else _NAV_S
    return (
        '<!DOCTYPE html><html lang="en"><head>'
        '<meta charset="UTF-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1.0">'
        '<title>' + title + ' | QuickDone</title>'
        '<link rel="preconnect" href="https://fonts.googleapis.com">'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
        '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">'
        '<style>' + SHARED_CSS + '</style>'
        '</head><body>'
        + nav_html + _FLASHES + body + _FOOTER +
        '</body></html>'
    )


# ============================================================
# PAGE: HOMEPAGE
# ============================================================

HOME_TEMPLATE = _page('Find Skilled Workers', """
<section class="hero">
  <div class="hero-bg" style="background-image:url('{{ hero_image }}')"></div>
  <div class="hero-ov"></div>
  <div class="hero-ct">
    <h1 class="hero-title">Find the right professional<br>for every job.</h1>
    <p class="hero-sub">Discover and book trusted local service workers in Sri Lanka. Electrical, plumbing, AC, cleaning, carpentry — done right, done quickly.</p>
    <div class="sb-wrap">
      <form class="sb" action="/workers" method="GET">
        <input type="text" name="name" placeholder="Search by worker name…" value="{{ request.args.get('name','') }}">
        <span class="sb-div"></span>
        <select name="category_id" class="sb" style="border:none;outline:none;font-size:14px;color:var(--ts);background:transparent;cursor:pointer;padding:0 4px;min-width:130px;-webkit-appearance:none;">
          <option value="">All Categories</option>
          {% for cat in categories %}
          <option value="{{ cat['category_id'] }}">{{ cat['name'] }}</option>
          {% endfor %}
        </select>
        <button type="submit" class="sb-btn">Search</button>
      </form>
    </div>
    <div class="cat-short">
      {% for cat in categories %}
      <a href="/workers?category_id={{ cat['category_id'] }}" class="cat-pill">
        <span>{{ category_icons.get(cat['name'],'🔧') }}</span>{{ cat['name'] }}
      </a>
      {% endfor %}
    </div>
  </div>
</section>

<section class="sec sec-bg-pg">
  <div class="c">
    <div class="sh-row">
      <div>
        <div class="sl">Browse by Category</div>
        <h2 class="st">Popular Services</h2>
        <p class="ss">From licensed electricians to master carpenters — find the specialist your home needs.</p>
      </div>
      <a href="/workers" class="btn btn-s" style="flex-shrink:0;">View All Workers</a>
    </div>
    <div class="cc-grid">
      {% for cat in categories %}
      <a href="/workers?category_id={{ cat['category_id'] }}" class="cc">
        <div class="cc-bg" style="background-image:url('{{ category_images.get(cat['name'],'') }}')"></div>
        <div class="cc-ov"></div>
        <div class="cc-body">
          <div class="cc-name">{{ cat['name'] }}</div>
          <div class="cc-count">{{ cat['worker_count'] }} worker{{ 's' if cat['worker_count'] != 1 else '' }} available</div>
        </div>
      </a>
      {% endfor %}
    </div>
  </div>
</section>

<section class="sec sec-bg-w">
  <div class="c">
    <div class="sh-row">
      <div>
        <div class="sl">Top Rated</div>
        <h2 class="st">Featured Professionals</h2>
        <p class="ss">Skilled, vetted and highly rated workers ready for your next project.</p>
      </div>
      <a href="/workers" class="btn btn-s" style="flex-shrink:0;">See All Workers</a>
    </div>
    <div class="wc-grid">
      {% for w in workers %}
      <div class="wc">
        <div class="wc-top">
          {% if w['profile_image_url'] %}
          <img src="{{ w['profile_image_url'] }}" alt="{{ w['first_name'] }}" class="av" style="object-fit:cover;">
          {% else %}
          <div class="av">{{ get_initials(w['first_name'] + ' ' + w['last_name']) }}</div>
          {% endif %}
          <div>
            <div class="wn">{{ w['first_name'] }} {{ w['last_name'] }}</div>
            <div class="wm">
              <span>📍 {{ w['city'] }}</span>
              <span>🛠 {{ w['experience_years'] }}yr</span>
            </div>
          </div>
        </div>
        <div style="display:flex;align-items:center;gap:8px;">
          <span class="star-y" style="font-size:14px;">★ {{ "%.1f"|format(w['avg_rating']) }}</span>
          <span class="ts-m ts-sm">· {{ w['completed_jobs'] }} jobs done</span>
        </div>
        <div class="tags">
          {% if w['service_names'] %}{% for svc in w['service_names'].split(',') %}
          <span class="tag">{{ svc.strip() }}</span>
          {% endfor %}{% endif %}
        </div>
        {% if w['min_rate'] %}<p class="rate-t">From <strong>LKR {{ w['min_rate']|lkr }}/hr</strong></p>{% endif %}
        <a href="/worker/{{ w['worker_id'] }}" class="btn btn-p btn-sm" style="margin-top:auto;">View Profile</a>
      </div>
      {% endfor %}
    </div>
  </div>
</section>

<section class="sec sec-bg-pg">
  <div class="c">
    <div class="sh tc">
      <div class="sl">Simple Process</div>
      <h2 class="st">How QuickDone Works</h2>
    </div>
    <div class="steps-grid">
      <div class="step-card">
        <div class="step-num">1</div>
        <div class="step-title">Find</div>
        <p class="step-desc">Search workers by name, city or service category. View profiles, qualifications, weekly availability and real customer reviews.</p>
      </div>
      <div class="step-card">
        <div class="step-num">2</div>
        <div class="step-title">Book</div>
        <p class="step-desc">Select a service and confirm your booking. The worker's agreed hourly rate is shown upfront — no hidden charges.</p>
      </div>
      <div class="step-card">
        <div class="step-num">3</div>
        <div class="step-title">Review</div>
        <p class="step-desc">After the job is done, leave an honest rating. Your review updates the worker's profile instantly via the database trigger.</p>
      </div>
    </div>
  </div>
</section>
""", nav='hero')


# ============================================================
# PAGE: WORKER LISTING
# ============================================================

WORKERS_TEMPLATE = _page('Find Workers', """
<div class="ph">
  <div class="c">
    <h1>Find a Worker</h1>
    <p>Search from our network of verified service professionals.</p>
  </div>
</div>
""" + _FLASHES + """
<div class="sec sec-sm">
  <div class="c">
    <form class="fbar" method="GET" action="/workers">
      <div class="fg-f">
        <label class="fg-fl">Worker Name</label>
        <input class="f-in" type="text" name="name" value="{{ name }}" placeholder="e.g. Kasun">
      </div>
      <div class="fg-f">
        <label class="fg-fl">City</label>
        <input class="f-in" type="text" name="city" value="{{ city }}" placeholder="e.g. Colombo">
      </div>
      <div class="fg-f">
        <label class="fg-fl">Category</label>
        <select class="f-sel" name="category_id">
          <option value="">All Categories</option>
          {% for cat in categories %}
          <option value="{{ cat['category_id'] }}" {% if category_id == cat['category_id']|string %}selected{% endif %}>
            {{ category_icons.get(cat['name'],'') }} {{ cat['name'] }}
          </option>
          {% endfor %}
        </select>
      </div>
      <button type="submit" class="btn btn-p" style="flex-shrink:0;align-self:flex-end;">Search</button>
      <a href="/workers" class="btn btn-s" style="flex-shrink:0;align-self:flex-end;">Clear</a>
    </form>

    {% if workers %}
    <p style="font-size:14px;color:var(--ts);margin-bottom:20px;">{{ workers|length }} worker{{ 's' if workers|length != 1 else '' }} found</p>
    <div class="wc-grid">
      {% for w in workers %}
      <div class="wc">
        <div class="wc-top">
          {% if w['profile_image_url'] %}
          <img src="{{ w['profile_image_url'] }}" alt="{{ w['first_name'] }}" class="av" style="object-fit:cover;">
          {% else %}
          <div class="av">{{ get_initials(w['first_name'] + ' ' + w['last_name']) }}</div>
          {% endif %}
          <div>
            <div class="wn">{{ w['first_name'] }} {{ w['last_name'] }}</div>
            <div class="wm">
              <span>📍 {{ w['city'] }}</span>
              <span>🛠 {{ w['experience_years'] }}yr exp</span>
            </div>
          </div>
        </div>
        <div style="display:flex;align-items:center;gap:8px;">
          <span class="star-y" style="font-size:14px;">★ {{ "%.1f"|format(w['avg_rating']) }}</span>
          <span class="ts-m ts-sm">· {{ w['completed_jobs'] }} jobs</span>
        </div>
        <div class="tags">
          {% if w['service_names'] %}{% for svc in w['service_names'].split(',') %}
          <span class="tag">{{ svc.strip() }}</span>
          {% endfor %}{% endif %}
        </div>
        <div class="rate-t">
          {% if w['min_rate'] == w['max_rate'] %}
            Rate: <strong>LKR {{ w['min_rate']|lkr }}/hr</strong>
          {% elif w['min_rate'] %}
            From <strong>LKR {{ w['min_rate']|lkr }}</strong> to <strong>LKR {{ w['max_rate']|lkr }}/hr</strong>
          {% endif %}
        </div>
        <a href="/worker/{{ w['worker_id'] }}" class="btn btn-p btn-sm" style="margin-top:auto;">View Profile</a>
      </div>
      {% endfor %}
    </div>
    {% else %}
    <div class="empty">
      <div class="empty-icon">🔍</div>
      <div class="empty-t">No workers found</div>
      <p class="empty-s">Try a different name, city or category filter.</p>
      <a href="/workers" class="btn btn-p">Clear filters</a>
    </div>
    {% endif %}
  </div>
</div>
""")


# ============================================================
# PAGE: WORKER PROFILE
# ============================================================

WORKER_PROFILE_TEMPLATE = _page('{{ worker["first_name"] }} {{ worker["last_name"] }}', """
<div class="prof-h">
  <div class="prof-hi">
    {% if worker['profile_image_url'] %}
    <img src="{{ worker['profile_image_url'] }}" alt="{{ worker['first_name'] }}" class="av av-xl" style="object-fit:cover;border:3px solid rgba(255,255,255,.25);">
    {% else %}
    <div class="av av-xl">{{ get_initials(worker['first_name'] + ' ' + worker['last_name']) }}</div>
    {% endif %}
    <div class="prof-info">
      <h1>{{ worker['first_name'] }} {{ worker['last_name'] }}</h1>
      <div class="prof-meta">
        <span>📍 {{ worker['city'] }}</span>
        <span>🛠 {{ worker['experience_years'] }} years experience</span>
        <span>✅ {{ worker['completed_jobs'] }} jobs completed</span>
      </div>
      <div class="prof-rating">
        <span class="r-big star-y">★ {{ "%.1f"|format(worker['avg_rating']) }}</span>
        <span style="color:rgba(255,255,255,.65);font-size:14px;">average rating</span>
        {% for b in badges %}
        <span class="badge-pill" style="background:rgba(255,255,255,.12);border-color:rgba(255,255,255,.25);color:#fff;">
          🏅 {{ b['badge_name'] }}
        </span>
        {% endfor %}
      </div>
    </div>
    <div style="margin-left:auto;">
      {% if session.get('user_type') == 'customer' %}
      <a href="/book/{{ worker['worker_id'] }}" class="btn btn-cta-hero" style="font-size:15px;padding:12px 28px;">Book Now</a>
      {% elif not session.get('user_type') %}
      <a href="/login" class="btn btn-ghost-w">Log in to Book</a>
      {% endif %}
    </div>
  </div>
</div>

<div class="prof-body">
  <div>
    <div class="panel">
      <div class="pan-h">About</div>
      <div class="pan-b">
        <p>{% if worker['bio'] %}{{ worker['bio'] }}{% else %}No bio provided.{% endif %}</p>
      </div>
    </div>

    {% if portfolio %}
    <div class="panel">
      <div class="pan-h" style="display:flex;align-items:center;justify-content:space-between;">
        <span>Work Examples &amp; Previous Projects</span>
        <span class="ts-sm ts-m">{{ portfolio|length }} photo{{ 's' if portfolio|length != 1 else '' }}</span>
      </div>
      <div class="pan-b">
        <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:16px;">
          {% for item in portfolio %}
          <div style="border:1.5px solid var(--bd);border-radius:var(--r);overflow:hidden;background:#fff;transition:transform .2s;" onmouseover="this.style.transform='translateY(-2px)'" onmouseout="this.style.transform='none'">
            <a href="{{ item['image_url'] }}" target="_blank" rel="noopener" title="Click to view full image">
              <img src="{{ item['image_url'] }}" alt="{{ item['title'] or 'Work Example' }}" style="width:100%;height:150px;object-fit:cover;">
            </a>
            {% if item['title'] %}
            <div style="padding:10px 12px;font-size:13px;font-weight:600;color:var(--tp);line-height:1.35;">
              {{ item['title'] }}
            </div>
            {% endif %}
          </div>
          {% endfor %}
        </div>
      </div>
    </div>
    {% endif %}

    <div class="panel">
      <div class="pan-h">Services &amp; Rates</div>
      <div class="pan-b p0">
        <table>
          <thead><tr><th>Service</th><th>Description</th><th>Hourly Rate</th></tr></thead>
          <tbody>
          {% for s in services %}
          <tr>
            <td><strong>{{ s['category_name'] }}</strong></td>
            <td class="ts-m ts-sm">{{ s['category_description'][:60] }}…</td>
            <td><strong>LKR {{ s['hourly_rate']|lkr }}/hr</strong></td>
          </tr>
          {% endfor %}
          </tbody>
        </table>
      </div>
    </div>

    {% if qualifications %}
    <div class="panel">
      <div class="pan-h">Qualifications</div>
      <div class="pan-b p0">
        <table>
          <thead><tr><th>#</th><th>Title</th><th>Institution</th><th>Year</th></tr></thead>
          <tbody>
          {% for q in qualifications %}
          <tr>
            <td class="ts-m">{{ q['qualification_no'] }}</td>
            <td><strong>{{ q['title'] }}</strong></td>
            <td class="ts-m">{{ q['institution'] }}</td>
            <td class="ts-m">{{ q['year_obtained'] }}</td>
          </tr>
          {% endfor %}
          </tbody>
        </table>
      </div>
    </div>
    {% endif %}

    <div class="panel">
      <div class="pan-h">Customer Reviews{% if reviews %} ({{ reviews|length }}){% endif %}</div>
      <div class="pan-b">
        {% if reviews %}
        {% for r in reviews %}
        <div class="rev-item">
          <div class="rev-hd">
            <div class="av" style="width:34px;height:34px;font-size:12px;">{{ get_initials(r['customer_name']) }}</div>
            <div class="rev-nm">{{ r['customer_name'] }}</div>
            <div class="star-y" style="font-size:13px;">{{ r['rating']|stars }}</div>
            <div class="rev-dt">{{ r['review_date'][:10] }}</div>
          </div>
          {% if r['comment'] %}<p class="rev-txt">{{ r['comment'] }}</p>{% endif %}
        </div>
        {% endfor %}
        {% else %}
        <p class="ts-m ts-sm">No reviews yet.</p>
        {% endif %}
      </div>
    </div>
  </div>

  <div>
    <div class="panel">
      <div class="pan-h">Weekly Availability</div>
      <div class="pan-b p0">
        <div style="padding:12px 20px;">
          <p class="ts-sm ts-m" style="margin-bottom:12px;">Recurring weekly schedule (not date-specific calendar slots)</p>
          {% if availability %}
          {% for a in availability %}
          <div class="avail-row">
            <div class="avail-day">{{ a['day_of_week'] }}</div>
            <div class="avail-time">{{ a['start_time'] }} – {{ a['end_time'] }}</div>
          </div>
          {% endfor %}
          {% else %}
          <p class="ts-m ts-sm">No availability listed.</p>
          {% endif %}
        </div>
      </div>
    </div>

    {% if badges %}
    <div class="panel">
      <div class="pan-h">Badges Earned</div>
      <div class="pan-b">
        {% for b in badges %}
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
          <span class="badge-pill">🏅 {{ b['badge_name'] }}</span>
          <span class="ts-sm ts-m">{{ b['awarded_date'] }}</span>
        </div>
        {% endfor %}
      </div>
    </div>
    {% endif %}

    {% if session.get('user_type') == 'customer' %}
    <div class="panel" style="border-color:var(--g800);">
      <div class="pan-h" style="background:var(--g900);color:#fff;">Ready to book?</div>
      <div class="pan-b">
        <p class="ts-m ts-sm" style="margin-bottom:16px;">Select a service and schedule your appointment.</p>
        <a href="/book/{{ worker['worker_id'] }}" class="btn btn-p btn-fw">Book {{ worker['first_name'] }}</a>
      </div>
    </div>
    {% elif not session.get('user_type') %}
    <div class="panel">
      <div class="pan-b tc">
        <p class="ts-m ts-sm" style="margin-bottom:16px;">Log in to book this worker.</p>
        <a href="/login" class="btn btn-p btn-fw">Log In</a>
        <a href="/register/customer" class="btn btn-s btn-fw mt16">Register as Customer</a>
      </div>
    </div>
    {% endif %}
  </div>
</div>
""")


# ============================================================
# PAGE: LOGIN
# ============================================================

LOGIN_TEMPLATE = (
    '<!DOCTYPE html><html lang="en"><head>'
    '<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">'
    '<title>Log In | QuickDone</title>'
    '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">'
    '<style>' + SHARED_CSS + '</style>'
    '</head><body>'
    + _FLASHES + """
<div class="auth-pg">
  <div class="auth-card">
    <div class="auth-logo">
      <div class="auth-logo-mark">Q</div>
      <div class="auth-logo-name">QuickDone</div>
    </div>
    <h2 class="auth-t">Welcome back</h2>
    <p class="auth-s">Log in to your account</p>
    <form method="POST">
      <div class="ut-tabs" id="ut-tabs">
        <button type="button" class="ut-tab act" onclick="setType('customer',this)">I'm a Customer</button>
        <button type="button" class="ut-tab" onclick="setType('worker',this)">I'm a Worker</button>
      </div>
      <input type="hidden" name="user_type" id="user_type_field" value="customer">
      <div class="fg">
        <label class="fl-label">Email Address</label>
        <input class="fi" type="email" name="email" required placeholder="your@email.com">
      </div>
      <div class="fg">
        <label class="fl-label">Password</label>
        <input class="fi" type="password" name="password" required placeholder="••••••••">
      </div>
      <button class="btn btn-p btn-fw" type="submit">Log In</button>
    </form>
    <div class="auth-sw">
      No account? <a href="/register/customer">Register as Customer</a> or <a href="/register/worker">Join as Worker</a>
    </div>
    <div class="auth-sw" style="margin-top:8px;">
      <a href="/admin/login" style="color:var(--ts);">Admin login →</a>
    </div>
  </div>
</div>
<script>
function setType(type, btn) {
  document.getElementById('user_type_field').value = type;
  document.querySelectorAll('.ut-tab').forEach(b => b.classList.remove('act'));
  btn.classList.add('act');
}
</script>
</body></html>"""
)


# ============================================================
# PAGE: CUSTOMER REGISTRATION
# ============================================================

REGISTER_CUSTOMER_TEMPLATE = (
    '<!DOCTYPE html><html lang="en"><head>'
    '<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">'
    '<title>Register | QuickDone</title>'
    '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">'
    '<style>' + SHARED_CSS + '</style>'
    '</head><body>'
    + _FLASHES + """
<div class="auth-pg">
  <div class="auth-card" style="max-width:500px;">
    <div class="auth-logo">
      <div class="auth-logo-mark">Q</div>
      <div class="auth-logo-name">QuickDone</div>
    </div>
    <h2 class="auth-t">Create your account</h2>
    <p class="auth-s">Join thousands of customers finding great workers</p>
    <form method="POST">
      <div class="fr">
        <div class="fg"><label class="fl-label">First Name</label>
          <input class="fi" type="text" name="first_name" required placeholder="Amaya"></div>
        <div class="fg"><label class="fl-label">Last Name</label>
          <input class="fi" type="text" name="last_name" required placeholder="Perera"></div>
      </div>
      <div class="fg"><label class="fl-label">Email Address</label>
        <input class="fi" type="email" name="email" required placeholder="amaya@email.lk"></div>
      <div class="fg"><label class="fl-label">Phone Number</label>
        <input class="fi" type="text" name="phone" required placeholder="077-1234567"></div>
      <div class="fg"><label class="fl-label">Password</label>
        <input class="fi" type="password" name="password" required placeholder="••••••••" minlength="6"></div>
      <div class="fg"><label class="fl-label">Address</label>
        <input class="fi" type="text" name="address" required placeholder="42 Flower Rd, Colombo 07"></div>
      <button class="btn btn-p btn-fw" type="submit">Create Account</button>
    </form>
    <div class="auth-sw">Already have an account? <a href="/login">Log In</a></div>
    <div class="auth-sw" style="margin-top:6px;">Want to offer services? <a href="/register/worker">Join as Worker</a></div>
  </div>
</div>
</body></html>"""
)


# ============================================================
# PAGE: WORKER REGISTRATION
# ============================================================

REGISTER_WORKER_TEMPLATE = (
    '<!DOCTYPE html><html lang="en"><head>'
    '<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">'
    '<title>Join as Worker | QuickDone</title>'
    '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">'
    '<style>' + SHARED_CSS + '</style>'
    '</head><body>'
    + _FLASHES + """
<div style="background:var(--bg);padding:40px 24px;min-height:100vh;">
  <div style="max-width:720px;margin:0 auto;">
    <div style="text-align:center;margin-bottom:32px;">
      <a href="/" style="display:inline-flex;align-items:center;gap:9px;font-size:19px;font-weight:800;color:var(--tp);">
        <span style="width:32px;height:32px;background:var(--g800);border-radius:9px;color:#fff;font-size:15px;font-weight:900;display:inline-flex;align-items:center;justify-content:center;">Q</span>QuickDone
      </a>
      <h1 style="font-size:26px;font-weight:800;margin-top:20px;">Join as a Service Worker</h1>
      <p style="color:var(--ts);font-size:15px;margin-top:8px;">Create your profile and start receiving booking requests today.</p>
    </div>

    <form method="POST" style="background:#fff;border:1.5px solid var(--bd);border-radius:var(--rl);padding:32px;">

      <h3 style="font-size:16px;font-weight:700;margin-bottom:20px;padding-bottom:12px;border-bottom:1.5px solid var(--bd);">Personal Details</h3>
      <div class="fr">
        <div class="fg"><label class="fl-label">First Name *</label>
          <input class="fi" type="text" name="first_name" required placeholder="Kasun"></div>
        <div class="fg"><label class="fl-label">Last Name *</label>
          <input class="fi" type="text" name="last_name" required placeholder="Bandara"></div>
      </div>
      <div class="fr">
        <div class="fg"><label class="fl-label">Email Address *</label>
          <input class="fi" type="email" name="email" required placeholder="kasun@email.lk"></div>
        <div class="fg"><label class="fl-label">Phone Number *</label>
          <input class="fi" type="text" name="phone" required placeholder="077-5501122"></div>
      </div>
      <div class="fg"><label class="fl-label">Password *</label>
        <input class="fi" type="password" name="password" required placeholder="••••••••" minlength="6"></div>
      <div class="fr">
        <div class="fg"><label class="fl-label">City *</label>
          <input class="fi" type="text" name="city" required placeholder="Colombo"></div>
        <div class="fg"><label class="fl-label">Years of Experience *</label>
          <input class="fi" type="number" name="experience_years" min="0" max="60" value="0" required></div>
      </div>
      <div class="fg"><label class="fl-label">Bio (optional)</label>
        <textarea class="fta" name="bio" placeholder="Briefly describe your expertise and specialisations…" style="min-height:80px;"></textarea></div>
      <div class="fg"><label class="fl-label">Profile Picture URL (optional)</label>
        <input class="fi" type="url" name="profile_image_url" placeholder="https://images.unsplash.com/... or any image link">
        <p class="f-hint">Provide an image link, or leave blank to display your name initials avatar.</p></div>

      <h3 style="font-size:16px;font-weight:700;margin:28px 0 16px;padding-bottom:12px;border-bottom:1.5px solid var(--bd);">Services &amp; Rates *</h3>
      <p class="f-hint" style="margin-bottom:14px;">Select the services you offer and enter your hourly rate in LKR for each.</p>
      {% for cat in categories %}
      <div style="display:flex;align-items:center;gap:14px;margin-bottom:12px;padding:12px;border:1.5px solid var(--bd);border-radius:var(--r);">
        <input type="checkbox" name="category_ids" value="{{ cat['category_id'] }}" id="cat_{{ cat['category_id'] }}" style="width:18px;height:18px;accent-color:var(--g800);">
        <label for="cat_{{ cat['category_id'] }}" style="min-width:140px;font-weight:600;cursor:pointer;">{{ cat['name'] }}</label>
        <input class="fi" type="number" name="rate_{{ cat['category_id'] }}" placeholder="Hourly rate (LKR)" min="1" step="0.01" style="max-width:200px;margin-bottom:0;">
      </div>
      {% endfor %}

      <h3 style="font-size:16px;font-weight:700;margin:28px 0 16px;padding-bottom:12px;border-bottom:1.5px solid var(--bd);">Qualifications (optional, up to 3)</h3>
      {% for i in [1,2,3] %}
      <div style="border:1.5px solid var(--bd);border-radius:var(--r);padding:16px;margin-bottom:12px;">
        <p style="font-size:12px;font-weight:700;color:var(--ts);text-transform:uppercase;letter-spacing:.05em;margin-bottom:12px;">Qualification {{ i }}</p>
        <div class="fr">
          <div class="fg" style="margin-bottom:0;"><label class="fl-label">Title</label>
            <input class="fi" type="text" name="qual_title_{{ i }}" placeholder="e.g. NVQ Level 4 Electrical"></div>
          <div class="fg" style="margin-bottom:0;"><label class="fl-label">Year Obtained</label>
            <input class="fi" type="number" name="qual_year_{{ i }}" placeholder="2020" min="1950" max="2026"></div>
        </div>
        <div class="fg" style="margin-top:12px;margin-bottom:0;"><label class="fl-label">Institution</label>
          <input class="fi" type="text" name="qual_institution_{{ i }}" placeholder="e.g. VTA Sri Lanka"></div>
      </div>
      {% endfor %}

      <h3 style="font-size:16px;font-weight:700;margin:28px 0 16px;padding-bottom:12px;border-bottom:1.5px solid var(--bd);">Weekly Availability (optional)</h3>
      <p class="f-hint" style="margin-bottom:14px;">Select the days you are available and your working hours for each.</p>
      {% for day in ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'] %}
      <div style="display:flex;align-items:center;gap:14px;margin-bottom:10px;">
        <input type="checkbox" name="avail_days" value="{{ day }}" id="day_{{ day }}" style="width:18px;height:18px;accent-color:var(--g800);">
        <label for="day_{{ day }}" style="min-width:100px;font-weight:600;cursor:pointer;">{{ day }}</label>
        <input type="time" name="avail_start_{{ day }}" value="08:00" class="fi" style="max-width:120px;margin-bottom:0;">
        <span style="color:var(--ts);font-size:13px;">to</span>
        <input type="time" name="avail_end_{{ day }}" value="17:00" class="fi" style="max-width:120px;margin-bottom:0;">
      </div>
      {% endfor %}

      <h3 style="font-size:16px;font-weight:700;margin:28px 0 16px;padding-bottom:12px;border-bottom:1.5px solid var(--bd);">Work Examples / Previous Jobs (optional, up to 5)</h3>
      <p class="f-hint" style="margin-bottom:14px;">Add image links of previous jobs or completed projects to showcase on your profile.</p>
      {% for i in [1,2,3,4,5] %}
      <div style="border:1.5px solid var(--bd);border-radius:var(--r);padding:14px;margin-bottom:10px;">
        <div class="fr">
          <div class="fg" style="margin-bottom:0;">
            <label class="fl-label">Work Photo {{ i }} URL</label>
            <input class="fi" type="url" name="portfolio_url_{{ i }}" placeholder="https://...">
          </div>
          <div class="fg" style="margin-bottom:0;">
            <label class="fl-label">Project Title / Caption</label>
            <input class="fi" type="text" name="portfolio_title_{{ i }}" placeholder="e.g. Master Breaker Panel Upgrade">
          </div>
        </div>
      </div>
      {% endfor %}

      <div style="margin-top:28px;">
        <button class="btn btn-p btn-fw" type="submit" style="padding:14px;">Create Worker Profile</button>
      </div>
    </form>
    <div class="auth-sw" style="text-align:center;margin-top:16px;">Already have an account? <a href="/login">Log In</a></div>
  </div>
</div>
</body></html>"""
)


# ============================================================
# PAGE: CUSTOMER DASHBOARD
# ============================================================

CUSTOMER_DASHBOARD_TEMPLATE = _page('My Bookings', """
<div class="dash-wrap">
  <div class="sidebar">
    <div class="sb-logo">
      <div class="sb-logo-txt"><span class="sb-logo-mark">Q</span>QuickDone</div>
      <div class="sb-user">{{ session.get('user_name','Customer') }}</div>
    </div>
    <nav class="sb-nav">
      <a href="/dashboard/customer" class="active">📋 My Bookings</a>
      <a href="/workers">🔍 Find Workers</a>
      <a href="/logout">↩ Log Out</a>
    </nav>
  </div>
  <div class="dash-main">
    <div class="dash-title">My Bookings</div>
    {% if bookings %}
    <div class="tw">
      <div class="tw-hd"><span class="tw-t">All Bookings</span>
        <a href="/workers" class="btn btn-p btn-sm">+ New Booking</a></div>
      <table>
        <thead><tr>
          <th>Booking</th><th>Worker</th><th>Service</th>
          <th>Scheduled</th><th>Rate/hr</th><th>Status</th><th>Actions</th>
        </tr></thead>
        <tbody>
        {% for b in bookings %}
        <tr>
          <td class="ts-sm ts-m">#{{ b['booking_id'] }}</td>
          <td><strong>{{ b['worker_name'] }}</strong><br>
            <span class="ts-sm ts-m">📍 {{ b['worker_city'] }}</span></td>
          <td><span class="tag">{{ b['category_name'] }}</span></td>
          <td class="ts-sm ts-m">{{ b['scheduled_start'][:16].replace('T',' ') }}</td>
          <td><strong>LKR {{ b['agreed_rate']|lkr }}</strong></td>
          <td><span class="st-b s-{{ b['status'] }}">{{ b['status'].replace('_',' ') }}</span></td>
          <td>
            <div style="display:flex;gap:6px;flex-wrap:wrap;">
              <a href="/booking/{{ b['booking_id'] }}" class="btn btn-s btn-sm">Details</a>
              {% if b['status'] == 'COMPLETED' and not b['review_id'] %}
              <a href="/booking/{{ b['booking_id'] }}/review" class="btn btn-p btn-sm">★ Review</a>
              {% elif b['review_id'] %}
              <span class="st-b s-COMPLETED">Reviewed ★{{ b['rating'] }}</span>
              {% endif %}
              {% if b['status'] in ('PENDING','CONFIRMED') %}
              <form class="ba-form" method="POST" action="/booking/{{ b['booking_id'] }}/cancel"
                    onsubmit="return confirm('Cancel this booking?')">
                <button class="btn btn-d btn-sm" type="submit">Cancel</button>
              </form>
              {% endif %}
            </div>
          </td>
        </tr>
        {% endfor %}
        </tbody>
      </table>
    </div>
    {% else %}
    <div class="empty">
      <div class="empty-icon">📋</div>
      <div class="empty-t">No bookings yet</div>
      <p class="empty-s">Find a skilled worker and make your first booking today.</p>
      <a href="/workers" class="btn btn-p">Find Workers</a>
    </div>
    {% endif %}
  </div>
</div>
""")


# ============================================================
# PAGE: BOOKING FORM (Customer books a worker)
# ============================================================

BOOK_TEMPLATE = _page('Book {{ worker["first_name"] }}', """
<div class="ph">
  <div class="c">
    <h1>Book {{ worker['first_name'] }} {{ worker['last_name'] }}</h1>
    <p>Fill in the job details below. The agreed rate is taken from the worker's listed service rate.</p>
  </div>
</div>
<div class="sec sec-sm">
  <div class="c" style="max-width:640px;">
    <div style="background:#fff;border:1.5px solid var(--bd);border-radius:var(--rl);padding:28px;">
      <form method="POST">
        <div class="fg">
          <label class="fl-label">Service *</label>
          <select class="fsel" name="category_id" required id="svc-sel" onchange="updateRate(this)">
            {% for s in services %}
            <option value="{{ s['category_id'] }}" data-rate="{{ s['hourly_rate'] }}">
              {{ s['category_name'] }} — LKR {{ s['hourly_rate']|lkr }}/hr
            </option>
            {% endfor %}
          </select>
        </div>
        <div class="fg">
          <label class="fl-label">Agreed Rate (LKR/hr)</label>
          <input class="fi" type="text" id="rate-display" readonly
            value="LKR {{ services[0]['hourly_rate']|lkr }}/hr — set automatically from selected service"
            style="background:var(--bg);color:var(--ts);">
          <p class="f-hint">This rate is automatically set from the worker's listed price for the selected service.</p>
        </div>
        <div class="fg">
          <label class="fl-label">Job Description *</label>
          <textarea class="fta" name="job_description" required
            placeholder="Describe what needs to be done, e.g. Replace main RCB breaker and fix kitchen socket trip"></textarea>
        </div>
        <div class="fg">
          <label class="fl-label">Job Address *</label>
          <input class="fi" type="text" name="job_address" required placeholder="e.g. 42 Flower Rd, Colombo 07">
        </div>
        <div class="fg">
          <label class="fl-label">Scheduled Start *</label>
          <input class="fi" type="datetime-local" name="scheduled_start" required>
          <p class="f-hint">Note: availability is based on weekly recurring slots, not a fully locked calendar.</p>
        </div>
        <div style="display:flex;gap:12px;margin-top:4px;">
          <button class="btn btn-p" type="submit" style="flex:1;">Confirm Booking</button>
          <a href="/worker/{{ worker['worker_id'] }}" class="btn btn-s" style="flex:1;">Cancel</a>
        </div>
      </form>
    </div>
  </div>
</div>
<script>
function updateRate(sel) {
  var rate = sel.options[sel.selectedIndex].getAttribute('data-rate');
  var n = parseFloat(rate).toLocaleString('en-LK', {maximumFractionDigits:0});
  document.getElementById('rate-display').value = 'LKR ' + n + '/hr — set automatically from selected service';
}
</script>
""")


# ============================================================
# PAGE: BOOKING DETAIL
# ============================================================

BOOKING_DETAIL_TEMPLATE = _page('Booking #{{ booking["booking_id"] }}', """
<div class="ph">
  <div class="c">
    <h1>Booking #{{ booking['booking_id'] }}</h1>
    <p>Details for your service booking.</p>
  </div>
</div>
<div class="sec sec-sm">
  <div class="c" style="max-width:720px;">
    <div class="panel">
      <div class="pan-h" style="display:flex;align-items:center;justify-content:space-between;">
        <span>Booking Summary</span>
        <span class="st-b s-{{ booking['status'] }}">{{ booking['status'].replace('_',' ') }}</span>
      </div>
      <div class="pan-b">
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:20px;">
          <div>
            <div class="ts-sm ts-m" style="margin-bottom:4px;">WORKER</div>
            <div class="fw7">{{ booking['worker_name'] }}</div>
            <div class="ts-sm ts-m">{{ booking['worker_city'] }} · {{ booking['worker_phone'] }}</div>
          </div>
          <div>
            <div class="ts-sm ts-m" style="margin-bottom:4px;">SERVICE</div>
            <div class="fw7">{{ booking['category_name'] }}</div>
            <div class="ts-sm ts-m">LKR {{ booking['agreed_rate']|lkr }}/hr</div>
          </div>
          <div>
            <div class="ts-sm ts-m" style="margin-bottom:4px;">SCHEDULED START</div>
            <div class="fw7">{{ booking['scheduled_start'][:16].replace('T',' ') }}</div>
          </div>
          <div>
            <div class="ts-sm ts-m" style="margin-bottom:4px;">BOOKED ON</div>
            <div class="fw7">{{ booking['created_at'][:10] }}</div>
          </div>
        </div>
        <div class="div"></div>
        <div style="margin-bottom:16px;">
          <div class="ts-sm ts-m" style="margin-bottom:4px;">JOB DESCRIPTION</div>
          <div>{{ booking['job_description'] }}</div>
        </div>
        <div>
          <div class="ts-sm ts-m" style="margin-bottom:4px;">JOB ADDRESS</div>
          <div>{{ booking['job_address'] }}</div>
        </div>
        {% if booking['review_id'] %}
        <div class="div"></div>
        <div style="background:var(--m100);border-radius:var(--r);padding:14px;">
          <div class="ts-sm ts-m" style="margin-bottom:4px;">YOUR REVIEW</div>
          <div class="star-y">{{ booking['rating']|stars }}</div>
          {% if booking['comment'] %}<p style="margin-top:8px;font-size:14px;">{{ booking['comment'] }}</p>{% endif %}
        </div>
        {% endif %}
        <div style="display:flex;gap:10px;margin-top:20px;">
          <a href="/dashboard/customer" class="btn btn-s btn-sm">← Back to Bookings</a>
          {% if booking['status'] == 'COMPLETED' and not booking['review_id'] %}
          <a href="/booking/{{ booking['booking_id'] }}/review" class="btn btn-p btn-sm">★ Write Review</a>
          {% endif %}
          {% if booking['status'] in ('PENDING','CONFIRMED') %}
          <form method="POST" action="/booking/{{ booking['booking_id'] }}/cancel"
                onsubmit="return confirm('Cancel this booking?')">
            <button class="btn btn-d btn-sm" type="submit">Cancel Booking</button>
          </form>
          {% endif %}
        </div>
      </div>
    </div>
  </div>
</div>
""")


# ============================================================
# PAGE: WRITE REVIEW
# ============================================================

REVIEW_TEMPLATE = _page('Write a Review', """
<div class="ph">
  <div class="c">
    <h1>Write a Review</h1>
    <p>Share your experience for booking #{{ booking['booking_id'] }} with {{ booking['worker_name'] }}.</p>
  </div>
</div>
<div class="sec sec-sm">
  <div class="c" style="max-width:560px;">
    <div style="background:#fff;border:1.5px solid var(--bd);border-radius:var(--rl);padding:28px;">
      <div style="display:flex;align-items:center;gap:14px;margin-bottom:24px;padding-bottom:20px;border-bottom:1.5px solid var(--bd);">
        <div class="av">{{ get_initials(booking['worker_name']) }}</div>
        <div>
          <div class="fw7">{{ booking['worker_name'] }}</div>
          <div class="ts-sm ts-m">{{ booking['category_name'] }}</div>
        </div>
      </div>
      <form method="POST">
        <div class="fg">
          <label class="fl-label">Star Rating *</label>
          <div style="display:flex;gap:8px;margin-top:4px;" id="star-row">
            {% for i in [1,2,3,4,5] %}
            <button type="button" class="star-btn" data-val="{{ i }}"
              onclick="setStar({{ i }})"
              style="background:none;border:none;font-size:36px;cursor:pointer;color:var(--bd);transition:color .1s;padding:0;">★</button>
            {% endfor %}
          </div>
          <input type="hidden" name="rating" id="rating-val" value="">
        </div>
        <div class="fg">
          <label class="fl-label">Comment (optional)</label>
          <textarea class="fta" name="comment"
            placeholder="Describe the quality of work, punctuality, professionalism…"></textarea>
        </div>
        <div style="display:flex;gap:12px;">
          <button class="btn btn-p" type="submit" style="flex:1;">Submit Review</button>
          <a href="/dashboard/customer" class="btn btn-s" style="flex:1;">Cancel</a>
        </div>
      </form>
    </div>
  </div>
</div>
<script>
var selected = 0;
function setStar(n) {
  selected = n;
  document.getElementById('rating-val').value = n;
  var btns = document.querySelectorAll('.star-btn');
  btns.forEach(function(b, i) {
    b.style.color = i < n ? 'var(--star)' : 'var(--bd)';
  });
}
</script>
""")


# ============================================================
# PAGE: WORKER DASHBOARD
# ============================================================

WORKER_DASHBOARD_TEMPLATE = _page('Worker Dashboard', """
<div class="dash-wrap">
  <div class="sidebar">
    <div class="sb-logo">
      <div class="sb-logo-txt"><span class="sb-logo-mark">Q</span>QuickDone</div>
      <div class="sb-user">{{ session.get('user_name','Worker') }}</div>
    </div>
    <nav class="sb-nav">
      <a href="/dashboard/worker" class="active">📋 Bookings</a>
      <a href="/dashboard/worker/profile">👤 My Profile</a>
      <a href="/logout">↩ Log Out</a>
    </nav>
  </div>
  <div class="dash-main">
    {% if worker %}
    <div class="kpi-row">
      <div class="kpi kpi-gl"><div class="kpi-l">Avg Rating</div>
        <div class="kpi-v star-y">{{ "%.2f"|format(worker['avg_rating']) }}</div>
        <div class="kpi-s">★ out of 5.00</div></div>
      <div class="kpi kpi-gl"><div class="kpi-l">Completed Jobs</div>
        <div class="kpi-v">{{ worker['completed_jobs'] }}</div>
        <div class="kpi-s">trigger-maintained count</div></div>
      <div class="kpi"><div class="kpi-l">Experience</div>
        <div class="kpi-v">{{ worker['experience_years'] }}yr</div></div>
      <div class="kpi"><div class="kpi-l">Badges</div>
        <div class="kpi-v">{{ badges|length }}</div>
        <div class="kpi-s">{% for b in badges %}<span class="badge-pill">{{ b['badge_name'] }}</span> {% endfor %}</div></div>
    </div>
    {% endif %}

    <div class="tw">
      <div class="tw-hd"><span class="tw-t">Booking Requests</span></div>
      {% if bookings %}
      <table>
        <thead><tr>
          <th>#</th><th>Customer</th><th>Service</th>
          <th>Scheduled</th><th>Rate/hr</th><th>Status</th><th>Actions</th>
        </tr></thead>
        <tbody>
        {% for b in bookings %}
        <tr>
          <td class="ts-sm ts-m">#{{ b['booking_id'] }}</td>
          <td>
            <strong>{{ b['customer_name'] }}</strong><br>
            <span class="ts-sm ts-m">{{ b['customer_phone'] }}</span>
          </td>
          <td>
            <span class="tag">{{ b['category_name'] }}</span><br>
            <span class="ts-sm" style="color:var(--tp);font-weight:500;">{{ b['job_description'] }}</span><br>
            <span class="ts-sm ts-m">📍 {{ b['job_address'] }}</span>
          </td>
          <td class="ts-sm ts-m">{{ b['scheduled_start'][:16].replace('T',' ') }}</td>
          <td><strong>LKR {{ b['agreed_rate']|lkr }}</strong></td>
          <td><span class="st-b s-{{ b['status'] }}">{{ b['status'].replace('_',' ') }}</span></td>
          <td>
            <div style="display:flex;gap:6px;flex-wrap:wrap;">
              {% if b['status'] == 'PENDING' %}
              <form class="ba-form" method="POST" action="/booking/{{ b['booking_id'] }}/status">
                <input type="hidden" name="status" value="CONFIRMED">
                <button class="btn btn-p btn-sm" type="submit">Accept</button>
              </form>
              <form class="ba-form" method="POST" action="/booking/{{ b['booking_id'] }}/status">
                <input type="hidden" name="status" value="CANCELLED">
                <button class="btn btn-d btn-sm" type="submit">Reject</button>
              </form>
              {% elif b['status'] == 'CONFIRMED' %}
              <form class="ba-form" method="POST" action="/booking/{{ b['booking_id'] }}/status">
                <input type="hidden" name="status" value="IN_PROGRESS">
                <button class="btn btn-p btn-sm" type="submit">Start</button>
              </form>
              <form class="ba-form" method="POST" action="/booking/{{ b['booking_id'] }}/status">
                <input type="hidden" name="status" value="CANCELLED">
                <button class="btn btn-d btn-sm" type="submit">Cancel</button>
              </form>
              {% elif b['status'] == 'IN_PROGRESS' %}
              <form class="ba-form" method="POST" action="/booking/{{ b['booking_id'] }}/status"
                    onsubmit="return confirm('Mark as COMPLETED? This will trigger the completed_jobs counter and award eligible badges.')">
                <input type="hidden" name="status" value="COMPLETED">
                <button class="btn btn-p btn-sm" type="submit">Complete</button>
              </form>
              {% endif %}
            </div>
          </td>
        </tr>
        {% endfor %}
        </tbody>
      </table>
      {% else %}
      <div class="empty"><div class="empty-icon">📋</div>
        <div class="empty-t">No bookings yet</div>
        <p class="empty-s">Your booking requests will appear here.</p></div>
      {% endif %}
    </div>
    <div style="margin-top:12px;">
      <p class="ts-sm ts-m">Status transitions: PENDING → CONFIRMED → IN_PROGRESS → COMPLETED. Trigger <code>trg_update_worker_jobs_on_complete</code> fires on COMPLETED, updating your completed jobs counter and checking badge eligibility.</p>
    </div>
  </div>
</div>
""")


# ============================================================
# PAGE: WORKER PROFILE EDIT
# ============================================================

WORKER_PROFILE_EDIT_TEMPLATE = _page('Edit My Profile', """
<div class="dash-wrap">
  <div class="sidebar">
    <div class="sb-logo">
      <div class="sb-logo-txt"><span class="sb-logo-mark">Q</span>QuickDone</div>
      <div class="sb-user">{{ session.get('user_name','Worker') }}</div>
    </div>
    <nav class="sb-nav">
      <a href="/dashboard/worker">📋 Bookings</a>
      <a href="/dashboard/worker/profile" class="active">👤 My Profile</a>
      <a href="/logout">↩ Log Out</a>
    </nav>
  </div>
  <div class="dash-main">
    <div class="dash-title">My Profile</div>

    <!-- PROFILE UPDATE -->
    <div class="tw mb24">
      <div class="tw-hd"><span class="tw-t">Basic Information</span></div>
      <div style="padding:20px;">
        <form method="POST">
          <input type="hidden" name="action" value="update_profile">
          <div class="fr">
            <div class="fg"><label class="fl-label">Bio</label>
              <textarea class="fta" name="bio" style="min-height:80px;">{{ worker['bio'] or '' }}</textarea></div>
            <div>
              <div class="fg"><label class="fl-label">Profile Picture URL (optional)</label>
                <input class="fi" type="url" name="profile_image_url" value="{{ worker['profile_image_url'] or '' }}" placeholder="https://images.unsplash.com/..."></div>
              <div class="fg"><label class="fl-label">Phone</label>
                <input class="fi" type="text" name="phone" value="{{ worker['phone'] }}"></div>
              <div class="fg"><label class="fl-label">City</label>
                <input class="fi" type="text" name="city" value="{{ worker['city'] }}"></div>
              <div class="fg"><label class="fl-label">Experience (years)</label>
                <input class="fi" type="number" name="experience_years" value="{{ worker['experience_years'] }}" min="0"></div>
            </div>
          </div>
          <button class="btn btn-p btn-sm" type="submit">Save Profile</button>
        </form>
      </div>
    </div>

    <!-- WORK EXAMPLES / PORTFOLIO -->
    <div class="tw mb24">
      <div class="tw-hd" style="display:flex;align-items:center;justify-content:space-between;">
        <span class="tw-t">Work Examples / Portfolio (Max 5)</span>
        <span class="ts-sm ts-m">{{ portfolio|length }} of 5 uploaded</span>
      </div>
      <div style="padding:20px;">
        {% if portfolio %}
        <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:16px;margin-bottom:20px;">
          {% for item in portfolio %}
          <div style="border:1.5px solid var(--bd);border-radius:var(--r);overflow:hidden;background:#fff;display:flex;flex-direction:column;">
            <a href="{{ item['image_url'] }}" target="_blank" rel="noopener">
              <img src="{{ item['image_url'] }}" alt="{{ item['title'] or 'Work Example' }}" style="width:100%;height:120px;object-fit:cover;">
            </a>
            <div style="padding:10px;display:flex;flex-direction:column;flex:1;">
              <div style="font-weight:600;font-size:13px;color:var(--tp);margin-bottom:8px;line-height:1.3;">{{ item['title'] or 'Work Sample' }}</div>
              <form method="POST" style="margin-top:auto;" onsubmit="return confirm('Remove this work sample photo?')">
                <input type="hidden" name="action" value="remove_portfolio">
                <input type="hidden" name="portfolio_id" value="{{ item['portfolio_id'] }}">
                <button class="btn btn-d btn-sm" type="submit" style="width:100%;padding:4px 8px;font-size:12px;">Remove</button>
              </form>
            </div>
          </div>
          {% endfor %}
        </div>
        {% else %}
        <p class="ts-sm ts-m" style="margin-bottom:16px;">You haven't added any work example photos yet.</p>
        {% endif %}

        {% if portfolio|length < 5 %}
        <form method="POST" style="background:var(--bg);border:1.5px dashed var(--bd);border-radius:var(--r);padding:16px;">
          <input type="hidden" name="action" value="add_portfolio">
          <p style="font-size:13px;font-weight:700;color:var(--tp);margin-bottom:12px;">Add Work Example Photo ({{ 5 - portfolio|length }} slot{{ 's' if (5 - portfolio|length) != 1 else '' }} remaining)</p>
          <div class="fr">
            <div class="fg" style="margin-bottom:0;">
              <label class="fl-label">Image URL *</label>
              <input class="fi" type="url" name="image_url" required placeholder="https://images.unsplash.com/... or image link">
            </div>
            <div class="fg" style="margin-bottom:0;">
              <label class="fl-label">Project Title / Caption (optional)</label>
              <input class="fi" type="text" name="title" placeholder="e.g. Master Breaker Panel Upgrade">
            </div>
          </div>
          <button class="btn btn-p btn-sm" type="submit" style="margin-top:12px;">+ Add Work Example</button>
        </form>
        {% else %}
        <div style="padding:12px 16px;background:var(--m100);border-radius:var(--r);color:var(--g900);font-size:13px;font-weight:600;">
          ✓ You have reached the maximum of 5 work example photos. Remove an existing image above to add a new one.
        </div>
        {% endif %}
      </div>
    </div>

    <!-- SERVICES -->
    <div class="tw mb24">
      <div class="tw-hd"><span class="tw-t">My Services</span>
        <span class="ts-sm ts-m">Rate in LKR per hour</span></div>
      <div style="padding:20px;">
        {% if services %}
        <table style="margin-bottom:20px;">
          <thead><tr><th>Category</th><th>Rate / hr</th><th>Action</th></tr></thead>
          <tbody>
          {% for s in services %}
          <tr>
            <td><strong>{{ s['category_name'] }}</strong></td>
            <td>LKR {{ s['hourly_rate']|lkr }}</td>
            <td>
              <form class="ba-form" method="POST"
                    onsubmit="return confirm('Remove {{ s[\"category_name\"] }} from your services?')">
                <input type="hidden" name="action" value="remove_service">
                <input type="hidden" name="category_id" value="{{ s['category_id'] }}">
                <button class="btn btn-d btn-sm" type="submit">Remove</button>
              </form>
            </td>
          </tr>
          {% endfor %}
          </tbody>
        </table>
        {% endif %}
        <form method="POST" style="display:flex;gap:12px;align-items:flex-end;flex-wrap:wrap;">
          <input type="hidden" name="action" value="add_service">
          <div class="fg-f" style="min-width:160px;flex:1;">
            <label class="fg-fl">Add Category</label>
            <select class="f-sel" name="category_id">
              {% for cat in all_categories %}
              <option value="{{ cat['category_id'] }}">{{ cat['name'] }}</option>
              {% endfor %}
            </select>
          </div>
          <div class="fg-f" style="min-width:140px;">
            <label class="fg-fl">Hourly Rate (LKR)</label>
            <input class="f-in" type="number" name="hourly_rate" placeholder="e.g. 2500" min="1" step="0.01">
          </div>
          <button class="btn btn-p btn-sm" type="submit" style="align-self:flex-end;">Add Service</button>
        </form>
      </div>
    </div>

    <!-- QUALIFICATIONS -->
    <div class="tw mb24">
      <div class="tw-hd"><span class="tw-t">Qualifications</span></div>
      <div style="padding:20px;">
        {% if qualifications %}
        <table style="margin-bottom:20px;">
          <thead><tr><th>#</th><th>Title</th><th>Institution</th><th>Year</th></tr></thead>
          <tbody>
          {% for q in qualifications %}
          <tr>
            <td class="ts-m">{{ q['qualification_no'] }}</td>
            <td><strong>{{ q['title'] }}</strong></td>
            <td class="ts-m">{{ q['institution'] }}</td>
            <td class="ts-m">{{ q['year_obtained'] }}</td>
          </tr>
          {% endfor %}
          </tbody>
        </table>
        {% endif %}
        <form method="POST" style="display:grid;grid-template-columns:2fr 2fr 1fr auto;gap:12px;align-items:flex-end;">
          <input type="hidden" name="action" value="add_qualification">
          <div class="fg-f"><label class="fg-fl">Title</label>
            <input class="f-in" type="text" name="qual_title" placeholder="NVQ Level 4 Electrical"></div>
          <div class="fg-f"><label class="fg-fl">Institution</label>
            <input class="f-in" type="text" name="qual_institution" placeholder="VTA Sri Lanka"></div>
          <div class="fg-f"><label class="fg-fl">Year</label>
            <input class="f-in" type="number" name="qual_year" placeholder="2020" min="1950" max="2026"></div>
          <button class="btn btn-p btn-sm" type="submit" style="align-self:flex-end;">Add</button>
        </form>
      </div>
    </div>

    <!-- AVAILABILITY -->
    <div class="tw mb24">
      <div class="tw-hd"><span class="tw-t">Weekly Availability</span>
        <span class="ts-sm ts-m">Recurring weekday slots (not calendar-specific)</span></div>
      <div style="padding:20px;">
        {% if availability %}
        <div style="margin-bottom:20px;">
          {% for a in availability %}
          <div class="avail-row"><div class="avail-day">{{ a['day_of_week'] }}</div>
            <div class="avail-time">{{ a['start_time'] }} – {{ a['end_time'] }}</div></div>
          {% endfor %}
        </div>
        {% endif %}
        <form method="POST" style="display:flex;gap:12px;align-items:flex-end;flex-wrap:wrap;">
          <input type="hidden" name="action" value="add_availability">
          <div class="fg-f" style="min-width:140px;">
            <label class="fg-fl">Day</label>
            <select class="f-sel" name="avail_day">
              {% for day in ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'] %}
              <option value="{{ day }}">{{ day }}</option>
              {% endfor %}
            </select>
          </div>
          <div class="fg-f"><label class="fg-fl">Start</label>
            <input class="f-in" type="time" name="avail_start" value="08:00"></div>
          <div class="fg-f"><label class="fg-fl">End</label>
            <input class="f-in" type="time" name="avail_end" value="17:00"></div>
          <button class="btn btn-p btn-sm" type="submit" style="align-self:flex-end;">Add / Update</button>
        </form>
      </div>
    </div>

    <!-- BADGES -->
    {% if worker %}
    <div class="tw">
      <div class="tw-hd"><span class="tw-t">Badges</span></div>
      <div style="padding:20px;">
        {% for b in services %}{% endfor %}
        <p class="ts-sm ts-m" style="margin-bottom:12px;">
          Badges are awarded automatically after a booking is marked COMPLETED.
          Current completed jobs: <strong>{{ worker['completed_jobs'] }}</strong>
        </p>
        <a href="/worker/{{ session.get('user_id') }}" class="btn btn-s btn-sm">View Public Profile</a>
      </div>
    </div>
    {% endif %}
  </div>
</div>
""")


# ============================================================
# PAGE: ADMIN LOGIN
# ============================================================

ADMIN_LOGIN_TEMPLATE = (
    '<!DOCTYPE html><html lang="en"><head>'
    '<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">'
    '<title>Admin Login | QuickDone</title>'
    '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">'
    '<style>' + SHARED_CSS + '</style>'
    '</head><body>'
    + _FLASHES + """
<div class="auth-pg">
  <div class="auth-card">
    <div class="auth-logo">
      <div class="auth-logo-mark">Q</div>
      <div class="auth-logo-name">QuickDone Admin</div>
    </div>
    <h2 class="auth-t">Admin Login</h2>
    <p class="auth-s">Credentials are defined in Python only — no database table.</p>
    <form method="POST">
      <div class="fg"><label class="fl-label">Username</label>
        <input class="fi" type="text" name="username" required placeholder="admin"></div>
      <div class="fg"><label class="fl-label">Password</label>
        <input class="fi" type="password" name="password" required placeholder="••••••••"></div>
      <button class="btn btn-p btn-fw" type="submit">Log In as Admin</button>
    </form>
    <div class="auth-sw"><a href="/">← Back to QuickDone</a></div>
  </div>
</div>
</body></html>"""
)


# ============================================================
# PAGE: ADMIN DASHBOARD
# ============================================================

ADMIN_DASHBOARD_TEMPLATE = _page('Admin Dashboard', """
<div class="dash-wrap">
  <div class="sidebar">
    <div class="sb-logo">
      <div class="sb-logo-txt"><span class="sb-logo-mark">Q</span>Admin</div>
      <div class="sb-user">QuickDone Admin</div>
    </div>
    <nav class="sb-nav">
      <a href="/admin/dashboard" class="active">📊 Dashboard</a>
      <a href="/admin/customers">👥 Customers</a>
      <a href="/admin/workers">🔧 Workers</a>
      <a href="/admin/bookings">📋 Bookings</a>
      <a href="/logout">↩ Log Out</a>
    </nav>
  </div>
  <div class="dash-main">
    <div class="dash-title">Admin Dashboard</div>

    <!-- KPI ROW -->
    <div class="kpi-row">
      <div class="kpi kpi-gl"><div class="kpi-l">Total Customers</div>
        <div class="kpi-v">{{ stats.total_customers }}</div></div>
      <div class="kpi kpi-gl"><div class="kpi-l">Total Workers</div>
        <div class="kpi-v">{{ stats.total_workers }}</div></div>
      <div class="kpi kpi-gl"><div class="kpi-l">Total Bookings</div>
        <div class="kpi-v">{{ stats.total_bookings }}</div></div>
      <div class="kpi kpi-gl"><div class="kpi-l">Total Reviews</div>
        <div class="kpi-v">{{ stats.total_reviews }}</div></div>
      <div class="kpi"><div class="kpi-l">Avg Platform Rating</div>
        <div class="kpi-v star-y">{{ "%.2f"|format(stats.avg_rating) }}</div>
        <div class="kpi-s">★ out of 5.00 (AVG aggregate)</div></div>
      <div class="kpi"><div class="kpi-l">Rate Range (LKR)</div>
        <div class="kpi-v" style="font-size:18px;">{{ stats.min_rate|lkr }}–{{ stats.max_rate|lkr }}</div>
        <div class="kpi-s">MIN and MAX aggregates</div></div>
    </div>

    <!-- BOOKING STATUS BREAKDOWN -->
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:24px;">
      <div class="tw">
        <div class="tw-hd"><span class="tw-t">Bookings by Status</span>
          <span class="ts-sm ts-m">GROUP BY</span></div>
        <table>
          <thead><tr><th>Status</th><th>Count</th></tr></thead>
          <tbody>
          {% for row in stats.bookings_by_status %}
          <tr><td><span class="st-b s-{{ row['status'] }}">{{ row['status'].replace('_',' ') }}</span></td>
              <td><strong>{{ row['cnt'] }}</strong></td></tr>
          {% endfor %}
          </tbody>
        </table>
      </div>

      <div class="tw">
        <div class="tw-hd"><span class="tw-t">Popular Categories</span>
          <span class="ts-sm ts-m">GROUP BY + HAVING</span></div>
        <table>
          <thead><tr><th>Category</th><th>Workers</th><th>Bookings</th></tr></thead>
          <tbody>
          {% for row in stats.popular_categories %}
          <tr><td><strong>{{ row['name'] }}</strong></td>
              <td>{{ row['worker_count'] }}</td>
              <td>{{ row['booking_count'] }}</td></tr>
          {% endfor %}
          </tbody>
        </table>
      </div>
    </div>

    <!-- TOP WORKERS (uses subquery) -->
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:24px;">
      <div class="tw">
        <div class="tw-hd"><span class="tw-t">Top-Rated Workers</span>
          <span class="ts-sm ts-m">Subquery (workers with reviews only)</span></div>
        <table>
          <thead><tr><th>Worker</th><th>Rating</th><th>Jobs</th></tr></thead>
          <tbody>
          {% for w in stats.top_workers %}
          <tr><td><a href="/worker/{{ w['worker_id'] }}" class="fw7" style="color:var(--g800);">{{ w['name'] }}</a><br>
              <span class="ts-sm ts-m">{{ w['city'] }}</span></td>
              <td class="star-y">★ {{ "%.2f"|format(w['avg_rating']) }}</td>
              <td>{{ w['completed_jobs'] }}</td></tr>
          {% endfor %}
          </tbody>
        </table>
      </div>

      <div class="tw">
        <div class="tw-hd"><span class="tw-t">Most Active Workers</span>
          <span class="ts-sm ts-m">ORDER BY completed_jobs DESC</span></div>
        <table>
          <thead><tr><th>Worker</th><th>Completed</th><th>Rating</th></tr></thead>
          <tbody>
          {% for w in stats.most_active %}
          <tr><td><a href="/worker/{{ w['worker_id'] }}" class="fw7" style="color:var(--g800);">{{ w['name'] }}</a><br>
              <span class="ts-sm ts-m">{{ w['city'] }}</span></td>
              <td><strong>{{ w['completed_jobs'] }}</strong></td>
              <td class="star-y">★ {{ "%.1f"|format(w['avg_rating']) }}</td></tr>
          {% endfor %}
          </tbody>
        </table>
      </div>
    </div>

    <!-- RECENT BOOKINGS -->
    <div class="tw mb24">
      <div class="tw-hd"><span class="tw-t">Recent Bookings</span>
        <span class="ts-sm ts-m">INNER JOIN across booking, customer, worker, category</span></div>
      <table>
        <thead><tr><th>#</th><th>Customer</th><th>Worker</th><th>Category</th>
          <th>Status</th><th>Rate</th><th>Scheduled</th></tr></thead>
        <tbody>
        {% for b in stats.recent_bookings %}
        <tr>
          <td class="ts-sm ts-m">#{{ b['booking_id'] }}</td>
          <td>{{ b['customer_name'] }}</td>
          <td><a href="/worker/{{ b['worker_id'] }}" style="color:var(--g800);">{{ b['worker_name'] }}</a></td>
          <td><span class="tag">{{ b['category_name'] }}</span></td>
          <td><span class="st-b s-{{ b['status'] }}">{{ b['status'].replace('_',' ') }}</span></td>
          <td>LKR {{ b['agreed_rate']|lkr }}</td>
          <td class="ts-sm ts-m">{{ b['scheduled_start'][:10] }}</td>
        </tr>
        {% endfor %}
        </tbody>
      </table>
    </div>

    <!-- VIEW: v_worker_derived_stats -->
    <div class="tw">
      <div class="tw-hd">
        <span class="tw-t">Worker Statistics — View <code style="font-size:11px;background:var(--m100);padding:2px 6px;border-radius:4px;">v_worker_derived_stats</code></span>
        <span class="ts-sm ts-m">Dynamically derived values vs trigger-maintained stored values</span>
      </div>
      <table>
        <thead><tr>
          <th>Worker</th><th>City</th><th>Exp</th>
          <th>Completed Jobs (view)</th><th>Avg Rating (view)</th>
        </tr></thead>
        <tbody>
        {% for v in view_stats %}
        <tr>
          <td><strong>{{ v['worker_name'] }}</strong></td>
          <td class="ts-m">{{ v['city'] }}</td>
          <td class="ts-m">{{ v['experience_years'] }}yr</td>
          <td><strong>{{ v['completed_jobs'] }}</strong></td>
          <td class="star-y">{% if v['avg_rating'] %}★ {{ "%.2f"|format(v['avg_rating']) }}{% else %}—{% endif %}</td>
        </tr>
        {% endfor %}
        </tbody>
      </table>
    </div>
  </div>
</div>
""")


# ============================================================
# PAGE: ADMIN — CUSTOMERS
# ============================================================

ADMIN_CUSTOMERS_TEMPLATE = _page('Customers — Admin', """
<div class="dash-wrap">
  <div class="sidebar">
    <div class="sb-logo">
      <div class="sb-logo-txt"><span class="sb-logo-mark">Q</span>Admin</div>
      <div class="sb-user">QuickDone Admin</div>
    </div>
    <nav class="sb-nav">
      <a href="/admin/dashboard">📊 Dashboard</a>
      <a href="/admin/customers" class="active">👥 Customers</a>
      <a href="/admin/workers">🔧 Workers</a>
      <a href="/admin/bookings">📋 Bookings</a>
      <a href="/logout">↩ Log Out</a>
    </nav>
  </div>
  <div class="dash-main">
    <div class="dash-title">Customers ({{ customers|length }})</div>
    <div class="tw">
      <table>
        <thead><tr><th>ID</th><th>Name</th><th>Email</th><th>Phone</th><th>Address</th><th>Registered</th></tr></thead>
        <tbody>
        {% for c in customers %}
        <tr>
          <td class="ts-m">{{ c['customer_id'] }}</td>
          <td><strong>{{ c['first_name'] }} {{ c['last_name'] }}</strong></td>
          <td class="ts-m">{{ c['email'] }}</td>
          <td class="ts-m">{{ c['phone'] }}</td>
          <td class="ts-sm ts-m">{{ c['address'] }}</td>
          <td class="ts-sm ts-m">{{ c['registered_at'][:10] }}</td>
        </tr>
        {% endfor %}
        </tbody>
      </table>
    </div>
  </div>
</div>
""")


# ============================================================
# PAGE: ADMIN — WORKERS
# ============================================================

ADMIN_WORKERS_TEMPLATE = _page('Workers — Admin', """
<div class="dash-wrap">
  <div class="sidebar">
    <div class="sb-logo">
      <div class="sb-logo-txt"><span class="sb-logo-mark">Q</span>Admin</div>
      <div class="sb-user">QuickDone Admin</div>
    </div>
    <nav class="sb-nav">
      <a href="/admin/dashboard">📊 Dashboard</a>
      <a href="/admin/customers">👥 Customers</a>
      <a href="/admin/workers" class="active">🔧 Workers</a>
      <a href="/admin/bookings">📋 Bookings</a>
      <a href="/logout">↩ Log Out</a>
    </nav>
  </div>
  <div class="dash-main">
    <div class="dash-title">Workers ({{ workers|length }})</div>
    <div class="tw">
      <table>
        <thead><tr>
          <th>ID</th><th>Name</th><th>City</th><th>Exp</th>
          <th>Avg Rating</th><th>Completed</th><th>Services</th><th>Registered</th>
        </tr></thead>
        <tbody>
        {% for w in workers %}
        <tr>
          <td class="ts-m">{{ w['worker_id'] }}</td>
          <td><a href="/worker/{{ w['worker_id'] }}" class="fw7" style="color:var(--g800);">{{ w['name'] }}</a></td>
          <td class="ts-m">{{ w['city'] }}</td>
          <td class="ts-m">{{ w['experience_years'] }}yr</td>
          <td class="star-y">{% if w['avg_rating'] > 0 %}★ {{ "%.2f"|format(w['avg_rating']) }}{% else %}—{% endif %}</td>
          <td><strong>{{ w['completed_jobs'] }}</strong></td>
          <td class="ts-m">{{ w['service_count'] }}</td>
          <td class="ts-sm ts-m">{{ w['registered_at'][:10] }}</td>
        </tr>
        {% endfor %}
        </tbody>
      </table>
    </div>
  </div>
</div>
""")


# ============================================================
# PAGE: ADMIN — BOOKINGS
# ============================================================

ADMIN_BOOKINGS_TEMPLATE = _page('Bookings — Admin', """
<div class="dash-wrap">
  <div class="sidebar">
    <div class="sb-logo">
      <div class="sb-logo-txt"><span class="sb-logo-mark">Q</span>Admin</div>
      <div class="sb-user">QuickDone Admin</div>
    </div>
    <nav class="sb-nav">
      <a href="/admin/dashboard">📊 Dashboard</a>
      <a href="/admin/customers">👥 Customers</a>
      <a href="/admin/workers">🔧 Workers</a>
      <a href="/admin/bookings" class="active">📋 Bookings</a>
      <a href="/logout">↩ Log Out</a>
    </nav>
  </div>
  <div class="dash-main">
    <div class="dash-title">All Bookings ({{ bookings|length }})</div>
    <div class="tw">
      <table>
        <thead><tr>
          <th>#</th><th>Customer</th><th>Worker</th><th>Category &amp; Details</th>
          <th>Status</th><th>Rate</th><th>Scheduled</th><th>Created</th>
        </tr></thead>
        <tbody>
        {% for b in bookings %}
        <tr>
          <td class="ts-m">#{{ b['booking_id'] }}</td>
          <td>{{ b['customer_name'] }}</td>
          <td>{{ b['worker_name'] }}</td>
          <td><span class="tag">{{ b['category_name'] }}</span><br><span class="ts-sm ts-m">{{ b['job_description'] }}</span></td>
          <td><span class="st-b s-{{ b['status'] }}">{{ b['status'].replace('_',' ') }}</span></td>
          <td>LKR {{ b['agreed_rate']|lkr }}</td>
          <td class="ts-sm ts-m">{{ b['scheduled_start'][:16].replace('T',' ') }}</td>
          <td class="ts-sm ts-m">{{ b['created_at'][:10] }}</td>
        </tr>
        {% endfor %}
        </tbody>
      </table>
    </div>
  </div>
</div>
""")


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--init-db':
        init_db()
    else:
        if not os.path.exists(DATABASE):
            print('QuickDone: database not found.')
            print('Run: python app.py --init-db')
            sys.exit(1)
        print('QuickDone running at http://127.0.0.1:5000')
        app.run(debug=True, host='127.0.0.1', port=5000)
