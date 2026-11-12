# ============================================================
# QUICKDONE — Skilled-Worker Service Marketplace
# DBMS Foundations Coursework
# File: app.py (Flask Route Controller & Application Entry Point)
# ============================================================
#
# Modular Architecture:
#   db.py               — Connection management, SQLite pathing, init_db
#   queries.py          — ALL pure SQL query functions with viva documentation
#   templates.py        — All HTML templates, layouts and CSS styling
#   app.py              — Flask routes, auth decorators, and HTTP controllers
#   schema_and_seed.sql — Database schema, triggers, view & sample seed data
#
# Commands:
#   Initialize / reset DB : python app.py --init-db
#   Run application       : python app.py
#   Application URL       : http://127.0.0.1:5000
#
# Admin Credentials: username=admin  password=admin (Python-only, no DB table)
# ============================================================

import sys
import os
from functools import wraps
from flask import (Flask, render_template_string, request, redirect,
                   url_for, session, flash)
from werkzeug.security import generate_password_hash, check_password_hash

# Core modular components
from db import get_db, close_db, init_db, DATABASE
import queries as q
import templates as t

# ============================================================
# CONFIGURATION
# ============================================================

SECRET_KEY = 'qd-secret-2026-dbms-foundations'

# Admin credentials — Python-only constant; no admin database table
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin'

# Presentation-only image URLs for categories and hero artwork
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
app.teardown_appcontext(close_db)


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
# PUBLIC ROUTES
# ============================================================

@app.route('/')
def home():
    categories = q.get_category_worker_counts()
    workers    = q.get_featured_workers()
    return render_template_string(t.HOME_TEMPLATE,
        categories=categories, workers=workers,
        category_images=CATEGORY_IMAGES,
        category_icons=CATEGORY_ICONS,
        hero_image=HERO_IMAGE)


@app.route('/workers')
def worker_list():
    name        = request.args.get('name',        '').strip()
    city        = request.args.get('city',        '').strip()
    category_id = request.args.get('category_id', '').strip()
    workers     = q.search_workers(name or None, city or None, category_id or None)
    categories  = q.get_all_categories()
    return render_template_string(t.WORKERS_TEMPLATE,
        workers=workers, categories=categories,
        name=name, city=city, category_id=category_id,
        category_icons=CATEGORY_ICONS)


@app.route('/worker/<int:worker_id>')
def worker_profile(worker_id):
    worker         = q.get_worker_profile(worker_id)
    if not worker:
        flash('Worker not found.', 'error')
        return redirect(url_for('worker_list'))
    services       = q.get_worker_services(worker_id)
    qualifications = q.get_worker_qualifications(worker_id)
    availability   = q.get_worker_availability(worker_id)
    badges         = q.get_worker_badges(worker_id)
    reviews        = q.get_worker_reviews(worker_id)
    portfolio      = q.get_worker_portfolio(worker_id)
    return render_template_string(t.WORKER_PROFILE_TEMPLATE,
        worker=worker, services=services,
        qualifications=qualifications, availability=availability,
        badges=badges, reviews=reviews, portfolio=portfolio)


# ============================================================
# AUTHENTICATION ROUTES
# ============================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email     = request.form.get('email',     '').strip().lower()
        password  = request.form.get('password',  '')
        user_type = request.form.get('user_type', 'customer')

        if user_type == 'customer':
            user = q.find_customer_by_email(email)
            if user and check_password_hash(user['password_hash'], password):
                session['user_type'] = 'customer'
                session['user_id']   = user['customer_id']
                session['user_name'] = f"{user['first_name']} {user['last_name']}"
                return redirect(url_for('customer_dashboard'))
            flash('Invalid email or password.', 'error')

        elif user_type == 'worker':
            user = q.find_worker_by_email(email)
            if user and check_password_hash(user['password_hash'], password):
                session['user_type'] = 'worker'
                session['user_id']   = user['worker_id']
                session['user_name'] = f"{user['first_name']} {user['last_name']}"
                return redirect(url_for('worker_dashboard'))
            flash('Invalid email or password.', 'error')

    return render_template_string(t.LOGIN_TEMPLATE)


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
        elif q.find_customer_by_email(em):
            flash('An account with that email already exists.', 'error')
        else:
            try:
                cid = q.create_customer(fn, ln, em, ph, generate_password_hash(pw), addr)
                session.update({'user_type': 'customer', 'user_id': cid,
                                'user_name': f'{fn} {ln}'})
                flash('Welcome to QuickDone! Your account has been created.', 'success')
                return redirect(url_for('customer_dashboard'))
            except Exception as e:
                flash(f'Registration failed: {e}', 'error')

    return render_template_string(t.REGISTER_CUSTOMER_TEMPLATE)


@app.route('/register/worker', methods=['GET', 'POST'])
def register_worker():
    categories = q.get_all_categories()
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
            title_q = request.form.get(f'qual_title_{i}',       '').strip()
            inst_q  = request.form.get(f'qual_institution_{i}', '').strip()
            yr_q    = request.form.get(f'qual_year_{i}',        '').strip()
            if title_q and inst_q and yr_q:
                qualifications.append((title_q, inst_q, yr_q))

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
        elif q.find_worker_by_email(em):
            flash('An account with that email already exists.', 'error')
        else:
            try:
                wid = q.create_worker(fn, ln, em, ph, generate_password_hash(pw),
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

    return render_template_string(t.REGISTER_WORKER_TEMPLATE, categories=categories)


# ============================================================
# CUSTOMER DASHBOARD & BOOKINGS
# ============================================================

@app.route('/dashboard/customer')
@login_required_customer
def customer_dashboard():
    bookings = q.get_customer_bookings(session['user_id'])
    return render_template_string(t.CUSTOMER_DASHBOARD_TEMPLATE, bookings=bookings)


@app.route('/book/<int:worker_id>', methods=['GET', 'POST'])
@login_required_customer
def book_worker(worker_id):
    worker   = q.get_worker_profile(worker_id)
    if not worker:
        flash('Worker not found.', 'error')
        return redirect(url_for('worker_list'))
    services = q.get_worker_services(worker_id)
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
            rate = q.get_worker_service_rate(worker_id, cat_id)
            if rate is None:
                flash('Invalid service selection.', 'error')
            else:
                try:
                    sched = sched.replace('T', ' ')   # datetime-local → SQLite format
                    bid = q.create_booking(session['user_id'], worker_id, cat_id,
                                          desc, addr, sched, rate)
                    flash('Booking submitted successfully!', 'success')
                    return redirect(url_for('booking_detail', booking_id=bid))
                except Exception as e:
                    flash(f'Booking failed: {e}', 'error')

    return render_template_string(t.BOOK_TEMPLATE, worker=worker, services=services)


@app.route('/booking/<int:booking_id>')
@login_required_customer
def booking_detail(booking_id):
    booking = q.get_booking_detail(booking_id)
    if not booking or booking['customer_id'] != session['user_id']:
        flash('Booking not found.', 'error')
        return redirect(url_for('customer_dashboard'))
    return render_template_string(t.BOOKING_DETAIL_TEMPLATE, booking=booking)


@app.route('/booking/<int:booking_id>/cancel', methods=['POST'])
@login_required_customer
def cancel_booking_route(booking_id):
    booking = q.get_booking_detail(booking_id)
    if not booking or booking['customer_id'] != session['user_id']:
        flash('Booking not found.', 'error')
    elif booking['status'] not in ('PENDING', 'CONFIRMED'):
        flash('This booking cannot be cancelled.', 'error')
    else:
        q.cancel_booking(booking_id, session['user_id'])
        flash('Booking cancelled successfully.', 'success')
    return redirect(url_for('customer_dashboard'))


@app.route('/booking/<int:booking_id>/review', methods=['GET', 'POST'])
@login_required_customer
def write_review(booking_id):
    booking = q.get_booking_detail(booking_id)
    if not booking or booking['customer_id'] != session['user_id']:
        flash('Booking not found.', 'error')
        return redirect(url_for('customer_dashboard'))
    if booking['status'] != 'COMPLETED':
        flash('Only completed bookings can be reviewed.', 'error')
        return redirect(url_for('customer_dashboard'))
    if q.check_booking_has_review(booking_id):
        flash('You have already reviewed this booking.', 'info')
        return redirect(url_for('customer_dashboard'))

    if request.method == 'POST':
        rating  = request.form.get('rating',  '').strip()
        comment = request.form.get('comment', '').strip()
        if not rating:
            flash('Please select a star rating.', 'error')
        else:
            try:
                q.add_review(booking_id, int(rating), comment or None)
                flash('Review submitted! Thank you for your feedback.', 'success')
                return redirect(url_for('customer_dashboard'))
            except Exception as e:
                flash(f'Could not submit review: {e}', 'error')

    return render_template_string(t.REVIEW_TEMPLATE, booking=booking)


# ============================================================
# WORKER DASHBOARD & PROFILE MANAGEMENT
# ============================================================

@app.route('/dashboard/worker')
@login_required_worker
def worker_dashboard():
    worker   = q.get_worker_profile(session['user_id'])
    bookings = q.get_worker_bookings(session['user_id'])
    badges   = q.get_worker_badges(session['user_id'])
    return render_template_string(t.WORKER_DASHBOARD_TEMPLATE,
        worker=worker, bookings=bookings, badges=badges)


@app.route('/booking/<int:booking_id>/status', methods=['POST'])
@login_required_worker
def update_status(booking_id):
    new_status = request.form.get('status', '').strip()
    ok = q.update_booking_status(booking_id, session['user_id'], new_status)
    if ok:
        flash(f'Booking updated to {new_status}.', 'success')
        if new_status == 'COMPLETED':
            q.award_eligible_badges(session['user_id'])
            flash('Badges checked and awarded if eligible.', 'info')
    else:
        flash('Status update not permitted.', 'error')
    return redirect(url_for('worker_dashboard'))


@app.route('/dashboard/worker/profile', methods=['GET', 'POST'])
@login_required_worker
def worker_profile_edit():
    wid            = session['user_id']
    worker         = q.get_worker_profile(wid)
    services       = q.get_worker_services(wid)
    qualifications = q.get_worker_qualifications(wid)
    availability   = q.get_worker_availability(wid)
    portfolio      = q.get_worker_portfolio(wid)
    all_categories = q.get_all_categories()

    if request.method == 'POST':
        action = request.form.get('action', '')

        if action == 'update_profile':
            p_img = request.form.get('profile_image_url', '').strip() or None
            q.update_worker_profile(wid,
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
                    q.add_worker_service(wid, cat_id, rate)
                    flash('Service added.', 'success')
                except Exception as e:
                    flash(f'Could not add service: {e}', 'error')
            else:
                flash('Select a category and enter a rate.', 'error')

        elif action == 'remove_service':
            cat_id = request.form.get('category_id', '').strip()
            if cat_id:
                ok = q.remove_worker_service(wid, cat_id)
                flash('Service removed.' if ok else
                      'Cannot remove — active bookings exist for this service.', 
                      'success' if ok else 'error')

        elif action == 'add_qualification':
            t_qual    = request.form.get('qual_title',       '').strip()
            inst_qual = request.form.get('qual_institution', '').strip()
            yr_qual   = request.form.get('qual_year',        '').strip()
            if t_qual and inst_qual and yr_qual:
                try:
                    q.add_qualification(wid, t_qual, inst_qual, yr_qual)
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
                    q.add_availability(wid, day, st, et)
                    flash('Availability updated.', 'success')
                except Exception as e:
                    flash(f'Could not update availability: {e}', 'error')
            else:
                flash('Select a day and time range.', 'error')

        elif action == 'add_portfolio':
            img_url = request.form.get('image_url', '').strip()
            title   = request.form.get('title',     '').strip()
            if img_url:
                ok, msg = q.add_portfolio_image(wid, img_url, title)
                flash(msg, 'success' if ok else 'error')
            else:
                flash('Image URL is required.', 'error')

        elif action == 'remove_portfolio':
            port_id = request.form.get('portfolio_id', '').strip()
            if port_id:
                q.delete_portfolio_image(port_id, wid)
                flash('Work example removed.', 'success')

        return redirect(url_for('worker_profile_edit'))

    return render_template_string(t.WORKER_PROFILE_EDIT_TEMPLATE,
        worker=worker, services=services,
        qualifications=qualifications, availability=availability,
        portfolio=portfolio, all_categories=all_categories)


# ============================================================
# ADMIN ROUTES
# ============================================================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        uname = request.form.get('username', '').strip()
        pw    = request.form.get('password', '')
        # Admin credentials are Python-only constants; no DB table lookup
        if uname == ADMIN_USERNAME and pw == ADMIN_PASSWORD:
            session.update({'user_type': 'admin', 'user_name': 'Admin'})
            return redirect(url_for('admin_dashboard'))
        flash('Invalid admin credentials.', 'error')
    return render_template_string(t.ADMIN_LOGIN_TEMPLATE)


@app.route('/admin/dashboard')
@login_required_admin
def admin_dashboard():
    stats      = q.get_admin_dashboard_stats()
    view_stats = q.get_view_worker_stats()
    return render_template_string(t.ADMIN_DASHBOARD_TEMPLATE,
        stats=stats, view_stats=view_stats)


@app.route('/admin/customers')
@login_required_admin
def admin_customers():
    customers = q.get_all_customers_admin()
    return render_template_string(t.ADMIN_CUSTOMERS_TEMPLATE, customers=customers)


@app.route('/admin/workers')
@login_required_admin
def admin_workers():
    workers = q.get_all_workers_admin()
    return render_template_string(t.ADMIN_WORKERS_TEMPLATE, workers=workers)


@app.route('/admin/bookings')
@login_required_admin
def admin_bookings():
    bookings = q.get_all_bookings_admin()
    return render_template_string(t.ADMIN_BOOKINGS_TEMPLATE, bookings=bookings)


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
