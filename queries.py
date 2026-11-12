# ============================================================
# QUICKDONE — DATABASE QUERIES & SQL DEMONSTRATION LAYER
# File: queries.py
# ============================================================
#
# VIVA QUICK-REFERENCE OF SQL CONCEPTS DEMONSTRATED IN THIS FILE:
# ----------------------------------------------------------------------------
# 1. SELECT, INSERT, UPDATE, DELETE:
#    - SELECT: Used in all retrieval functions with explicit column projections
#    - INSERT: Customer & worker account creation, bookings, reviews, portfolio
#    - UPDATE: Worker profile updates, booking status workflow
#    - DELETE: remove_worker_service (with pre-check), delete_portfolio_image
#
# 2. JOINS:
#    - INNER JOIN: search_workers, get_featured_workers, get_worker_reviews,
#                  get_booking_detail, get_all_bookings_admin (4-table join)
#    - LEFT JOIN:  get_category_worker_counts (keeps categories with 0 workers),
#                  get_customer_bookings (keeps bookings with or without reviews),
#                  get_all_workers_admin
#
# 3. GROUP BY & HAVING:
#    - GROUP BY:   get_category_worker_counts, search_workers, get_all_workers_admin
#    - HAVING:     get_admin_dashboard_stats (popular_categories with >= 1 worker)
#
# 4. AGGREGATE FUNCTIONS:
#    - COUNT, AVG, MIN, MAX, GROUP_CONCAT, COALESCE, ROUND
#
# 5. SUBQUERIES:
#    - NOT EXISTS subquery: award_eligible_badges (prevents duplicate awards)
#    - Scalar subquery:     add_qualification (computes next qualification_no)
#    - IN subquery:         top_workers in get_admin_dashboard_stats
#
# 6. TRANSACTIONS (ACID):
#    - create_worker: BEGIN / COMMIT / ROLLBACK across 4 related tables
#
# 7. TRIGGERS & VIEWS:
#    - Triggers trg_update_worker_jobs_on_complete & trg_update_worker_rating_on_review
#      execute automatically inside SQLite on status update and review insert.
#    - View v_worker_derived_stats is queried in get_view_worker_stats() for auditing.
# ============================================================

from db import get_db


# ============================================================
# 1. CATEGORIES & WORKER DISCOVERY
# ============================================================

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


# ============================================================
# 2. WORKER PROFILE, SERVICES, QUALIFICATIONS & PORTFOLIO
# ============================================================

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
        ORDER   BY qualification_no ASC
    """, (worker_id,)).fetchall()


def get_worker_availability(worker_id):
    """
    Retrieve a worker's weekly recurring availability slots.
    Orders logically Monday through Sunday using a SQL CASE expression.
    SQL: SELECT with WHERE, ORDER BY CASE expression
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
                ELSE 8
            END,
            start_time ASC
    """, (worker_id,)).fetchall()


def get_worker_badges(worker_id):
    """
    Retrieve all badges awarded to a worker.
    SQL: SELECT, INNER JOIN worker_badge and badge, WHERE, ORDER BY
    """
    db = get_db()
    return db.execute("""
        SELECT  b.badge_id,
                b.name AS badge_name,
                b.min_jobs_required,
                wb.awarded_date
        FROM    worker_badge wb
        INNER JOIN badge b ON wb.badge_id = b.badge_id
        WHERE   wb.worker_id = ?
        ORDER   BY b.min_jobs_required ASC
    """, (worker_id,)).fetchall()


def get_worker_reviews(worker_id):
    """
    Retrieve all customer reviews for a worker, traversing through bookings.
    SQL: SELECT, INNER JOIN across review, booking, customer and category;
         WHERE on worker_id, ORDER BY review_date DESC
    """
    db = get_db()
    return db.execute("""
        -- 4-table INNER JOIN connecting review to its customer & category
        SELECT   r.review_id,
                 r.rating,
                 r.comment,
                 r.review_date,
                 cu.first_name || ' ' || cu.last_name AS customer_name,
                 c.name                                AS category_name,
                 b.booking_id
        FROM     review r
        INNER JOIN booking  b  ON r.booking_id  = b.booking_id
        INNER JOIN customer cu ON b.customer_id = cu.customer_id
        INNER JOIN category c  ON b.category_id = c.category_id
        WHERE    b.worker_id = ?
        ORDER BY r.review_date DESC
    """, (worker_id,)).fetchall()


def get_worker_portfolio(worker_id):
    """
    Retrieve all work example / portfolio images for a worker (up to 5).
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


# ============================================================
# 3. AUTHENTICATION & REGISTRATION
# ============================================================

def find_customer_by_email(email):
    """Look up a customer account by email. SQL: SELECT with WHERE on UNIQUE column"""
    db = get_db()
    return db.execute("""
        SELECT customer_id, first_name, last_name, email, phone, password_hash, address
        FROM   customer
        WHERE  LOWER(email) = LOWER(?)
    """, (email.strip(),)).fetchone()


def find_worker_by_email(email):
    """Look up a worker account by email. SQL: SELECT with WHERE on UNIQUE column"""
    db = get_db()
    return db.execute("""
        SELECT worker_id, first_name, last_name, email, phone, password_hash,
               city, experience_years, bio, profile_image_url
        FROM   worker
        WHERE  LOWER(email) = LOWER(?)
    """, (email.strip(),)).fetchone()


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


# ============================================================
# 4. BOOKINGS (CUSTOMER & WORKER)
# ============================================================

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
    Create a new service booking in PENDING status.
    Enforces composite foreign key (worker_id, category_id) -> worker_service.
    SQL: INSERT INTO booking (status defaults to PENDING per schema CHECK)
    """
    db = get_db()
    cur = db.execute("""
        INSERT INTO booking
            (customer_id, worker_id, category_id,
             job_description, job_address, scheduled_start,
             status, agreed_rate)
        VALUES (?, ?, ?, ?, ?, ?, 'PENDING', ?)
    """, (customer_id, worker_id, category_id,
          job_description, job_address, scheduled_start, float(agreed_rate)))
    db.commit()
    return cur.lastrowid


def get_customer_bookings(customer_id):
    """
    Retrieve all bookings made by a specific customer, including review status.
    SQL: SELECT, INNER JOIN on worker & category, LEFT JOIN on review,
         WHERE on customer_id, ORDER BY created_at DESC
    """
    db = get_db()
    return db.execute("""
        -- LEFT JOIN review to determine whether customer already reviewed this booking
        SELECT   b.booking_id,
                 b.worker_id,
                 b.category_id,
                 b.job_description,
                 b.job_address,
                 b.scheduled_start,
                 b.status,
                 b.agreed_rate,
                 b.created_at,
                 b.completed_at,
                 w.first_name || ' ' || w.last_name AS worker_name,
                 w.phone                            AS worker_phone,
                 c.name                             AS category_name,
                 r.review_id                        AS existing_review_id,
                 r.rating                           AS reviewed_rating
        FROM     booking b
        INNER JOIN worker   w ON b.worker_id   = w.worker_id
        INNER JOIN category c ON b.category_id = c.category_id
        LEFT JOIN  review   r ON b.booking_id  = r.booking_id
        WHERE    b.customer_id = ?
        ORDER BY b.created_at DESC
    """, (customer_id,)).fetchall()


def get_booking_detail(booking_id):
    """
    Retrieve a single booking with customer, worker, category and review info.
    SQL: SELECT, 3x INNER JOIN, 1x LEFT JOIN, WHERE on primary key
    """
    db = get_db()
    return db.execute("""
        SELECT   b.booking_id,
                 b.customer_id,
                 b.worker_id,
                 b.category_id,
                 b.job_description,
                 b.job_address,
                 b.scheduled_start,
                 b.status,
                 b.agreed_rate,
                 b.created_at,
                 b.completed_at,
                 cu.first_name || ' ' || cu.last_name AS customer_name,
                 cu.phone                             AS customer_phone,
                 cu.email                             AS customer_email,
                 w.first_name  || ' ' || w.last_name  AS worker_name,
                 w.phone                              AS worker_phone,
                 w.email                              AS worker_email,
                 c.name                               AS category_name,
                 r.review_id,
                 r.rating,
                 r.comment
        FROM     booking b
        INNER JOIN customer cu ON b.customer_id = cu.customer_id
        INNER JOIN worker   w  ON b.worker_id   = w.worker_id
        INNER JOIN category c  ON b.category_id = c.category_id
        LEFT JOIN  review   r  ON b.booking_id  = r.booking_id
        WHERE    b.booking_id = ?
    """, (booking_id,)).fetchone()


def cancel_booking(booking_id, customer_id):
    """
    Cancel a booking (customer action). Allowed only if PENDING or CONFIRMED.
    SQL: UPDATE with WHERE on booking_id, customer_id, and allowed status values
    """
    db = get_db()
    db.execute("""
        UPDATE booking
        SET    status = 'CANCELLED'
        WHERE  booking_id  = ?
          AND  customer_id = ?
          AND  status IN ('PENDING', 'CONFIRMED')
    """, (booking_id, customer_id))
    db.commit()


def get_worker_bookings(worker_id):
    """
    Retrieve all bookings assigned to a specific worker.
    SQL: SELECT, INNER JOIN on customer and category, WHERE, ORDER BY
    """
    db = get_db()
    return db.execute("""
        SELECT   b.booking_id,
                 b.customer_id,
                 b.category_id,
                 b.job_description,
                 b.job_address,
                 b.scheduled_start,
                 b.status,
                 b.agreed_rate,
                 b.created_at,
                 b.completed_at,
                 cu.first_name || ' ' || cu.last_name AS customer_name,
                 cu.phone                             AS customer_phone,
                 c.name                               AS category_name
        FROM     booking b
        INNER JOIN customer cu ON b.customer_id = cu.customer_id
        INNER JOIN category c  ON b.category_id = c.category_id
        WHERE    b.worker_id = ?
        ORDER BY b.created_at DESC
    """, (worker_id,)).fetchall()


def update_booking_status(booking_id, worker_id, new_status):
    """
    Update a booking's status following valid lifecycle transitions:
      PENDING    -> CONFIRMED or CANCELLED
      CONFIRMED  -> IN_PROGRESS or CANCELLED
      IN_PROGRESS-> COMPLETED
    When COMPLETED: sets completed_at = CURRENT_TIMESTAMP and fires trigger
    trg_update_worker_jobs_on_complete (defined in schema_and_seed.sql).
    SQL: UPDATE with dynamic completed_at and valid-transition WHERE clause
    """
    ALLOWED_TRANSITIONS = {
        'CONFIRMED':   ['PENDING'],
        'CANCELLED':   ['PENDING', 'CONFIRMED'],
        'IN_PROGRESS': ['CONFIRMED'],
        'COMPLETED':   ['IN_PROGRESS'],
    }
    allowed_prev = ALLOWED_TRANSITIONS.get(new_status)
    if not allowed_prev:
        return False

    db = get_db()
    placeholders = ','.join('?' * len(allowed_prev))

    if new_status == 'COMPLETED':
        sql = """
            UPDATE booking
            SET    status       = ?,
                   completed_at = CURRENT_TIMESTAMP
            WHERE  booking_id = ?
              AND  worker_id  = ?
              AND  status IN ({})
        """.format(placeholders)
    else:
        sql = """
            UPDATE booking
            SET    status = ?
            WHERE  booking_id = ?
              AND  worker_id  = ?
              AND  status IN ({})
        """.format(placeholders)

    params = [new_status, booking_id, worker_id] + allowed_prev
    cur = db.execute(sql, params)
    db.commit()
    return cur.rowcount > 0


# ============================================================
# 5. REVIEWS & BADGES
# ============================================================

def check_booking_has_review(booking_id):
    """Check whether a booking already has a review. SQL: SELECT COUNT(*)"""
    db = get_db()
    count = db.execute("""
        SELECT COUNT(*) FROM review WHERE booking_id = ?
    """, (booking_id,)).fetchone()[0]
    return count > 0


def add_review(booking_id, rating, comment=None):
    """
    Insert a customer review for an eligible completed booking.
    Database trigger trg_update_worker_rating_on_review fires AFTER INSERT,
    automatically updating worker.avg_rating.
    Enforces UNIQUE(booking_id) constraint.
    SQL: INSERT INTO review
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
    Award any badges a worker has newly qualified for based on completed_jobs.
    Subquery with NOT EXISTS prevents duplicate badges.
    SQL: INSERT INTO worker_badge ... SELECT with subqueries and NOT EXISTS
    """
    db = get_db()
    db.execute("""
        -- Multi-row INSERT...SELECT with scalar subquery and NOT EXISTS subquery
        INSERT INTO worker_badge (worker_id, badge_id, awarded_date)
        SELECT ?,
               b.badge_id,
               CURRENT_DATE
        FROM   badge b
        WHERE  b.min_jobs_required <= (
                   -- Scalar subquery: current completed_jobs for this worker
                   SELECT completed_jobs FROM worker WHERE worker_id = ?
               )
          AND  NOT EXISTS (
                   -- Correlated NOT EXISTS subquery: badge not already awarded
                   SELECT 1 FROM worker_badge wb
                   WHERE  wb.worker_id = ?
                     AND  wb.badge_id  = b.badge_id
               )
    """, (worker_id, worker_id, worker_id))
    db.commit()


# ============================================================
# 6. ADMIN REPORTING & AUDIT VIEWS
# ============================================================

def get_admin_dashboard_stats():
    """
    Aggregate statistics for the admin dashboard.
    Demonstrates: COUNT, AVG, MIN, MAX, GROUP BY, HAVING, subqueries,
    and a 4-table INNER JOIN.
    """
    db = get_db()
    stats = {}

    # -- Basic counts --
    stats['total_customers'] = db.execute("SELECT COUNT(*) FROM customer").fetchone()[0]
    stats['total_workers']   = db.execute("SELECT COUNT(*) FROM worker").fetchone()[0]
    stats['total_bookings']  = db.execute("SELECT COUNT(*) FROM booking").fetchone()[0]
    stats['total_reviews']   = db.execute("SELECT COUNT(*) FROM review").fetchone()[0]

    # -- Average platform rating (AVG aggregate) --
    row = db.execute("SELECT ROUND(AVG(rating), 2) FROM review").fetchone()
    stats['avg_rating'] = row[0] if row[0] is not None else 0.0
    stats['platform_avg_rating'] = stats['avg_rating']

    # -- Hourly rate range (MIN & MAX aggregates) --
    rate_row = db.execute("SELECT MIN(hourly_rate), MAX(hourly_rate) FROM worker_service").fetchone()
    stats['min_rate'] = rate_row[0] if rate_row and rate_row[0] is not None else 0.0
    stats['max_rate'] = rate_row[1] if rate_row and rate_row[1] is not None else 0.0

    # -- Bookings by status: GROUP BY --
    stats['bookings_by_status'] = db.execute("""
        SELECT   status, COUNT(*) AS cnt, COUNT(*) AS count
        FROM     booking
        GROUP BY status
        ORDER BY cnt DESC
    """).fetchall()

    # -- Popular categories: JOIN, GROUP BY, HAVING, ORDER BY --
    stats['popular_categories'] = db.execute("""
        -- Demonstrates HAVING clause on aggregated category metrics
        SELECT   c.category_id,
                 c.name,
                 COUNT(DISTINCT ws.worker_id) AS worker_count,
                 COUNT(b.booking_id)          AS booking_count,
                 ROUND(AVG(ws.hourly_rate), 2) AS avg_rate
        FROM     category c
        LEFT JOIN worker_service ws ON c.category_id = ws.category_id
        LEFT JOIN booking        b  ON c.category_id = b.category_id
        GROUP BY c.category_id, c.name
        HAVING   COUNT(DISTINCT ws.worker_id) >= 1
        ORDER BY booking_count DESC, worker_count DESC
    """).fetchall()

    # -- Top workers: Subquery filter (only workers with reviews) --
    stats['top_workers'] = db.execute("""
        -- Subquery: only workers who have at least one customer review
        SELECT   w.worker_id,
                 w.first_name || ' ' || w.last_name  AS name,
                 w.city,
                 w.avg_rating,
                 w.completed_jobs
        FROM     worker w
        WHERE    w.worker_id IN (
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
    SQL: SELECT from an existing VIEW (defined in schema_and_seed.sql)
    """
    db = get_db()
    return db.execute("""
        -- Using the database view v_worker_derived_stats
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
