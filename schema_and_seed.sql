-- QuickDone database schema and sample data


PRAGMA foreign_keys = ON;

-- Drop existing objects in reverse dependency order for clean re-initialization
DROP VIEW IF EXISTS v_worker_derived_stats;
DROP TRIGGER IF EXISTS trg_update_worker_jobs_on_complete;
DROP TRIGGER IF EXISTS trg_update_worker_jobs_on_insert;
DROP TRIGGER IF EXISTS trg_update_worker_rating_on_review;
DROP TABLE IF EXISTS review;
DROP TABLE IF EXISTS booking;
DROP TABLE IF EXISTS worker_badge;
DROP TABLE IF EXISTS badge;
DROP TABLE IF EXISTS availability;
DROP TABLE IF EXISTS qualification;
DROP TABLE IF EXISTS worker_portfolio;
DROP TABLE IF EXISTS worker_service;
DROP TABLE IF EXISTS category;
DROP TABLE IF EXISTS worker;
DROP TABLE IF EXISTS customer;

-- Tables

-- Customer
CREATE TABLE customer (
    customer_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name       VARCHAR(100) NOT NULL,
    last_name        VARCHAR(100) NOT NULL,
    email            VARCHAR(255) NOT NULL UNIQUE,
    phone            VARCHAR(30)  NOT NULL,
    password_hash    VARCHAR(255) NOT NULL,
    address          VARCHAR(255) NOT NULL,
    registered_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Worker
CREATE TABLE worker (
    worker_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name       VARCHAR(100) NOT NULL,
    last_name        VARCHAR(100) NOT NULL,
    email            VARCHAR(255) NOT NULL UNIQUE,
    phone            VARCHAR(30)  NOT NULL,
    password_hash    VARCHAR(255) NOT NULL,
    city             VARCHAR(100) NOT NULL,
    experience_years INTEGER      NOT NULL DEFAULT 0 CHECK (experience_years >= 0),
    bio              TEXT,
    profile_image_url VARCHAR(500) NULL,
    registered_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    avg_rating       DECIMAL(3,2) NOT NULL DEFAULT 0.00 CHECK (avg_rating BETWEEN 0.00 AND 5.00),
    completed_jobs   INTEGER      NOT NULL DEFAULT 0 CHECK (completed_jobs >= 0)
);

-- Service category
CREATE TABLE category (
    category_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    name             VARCHAR(100) NOT NULL UNIQUE,
    description      VARCHAR(500) NOT NULL
);

-- Worker services and hourly rates
CREATE TABLE worker_service (
    worker_id        INTEGER        NOT NULL,
    category_id      INTEGER        NOT NULL,
    hourly_rate      DECIMAL(10, 2) NOT NULL CHECK (hourly_rate > 0),
    PRIMARY KEY (worker_id, category_id),
    FOREIGN KEY (worker_id) REFERENCES worker (worker_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (category_id) REFERENCES category (category_id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- Worker qualifications
CREATE TABLE qualification (
    worker_id        INTEGER      NOT NULL,
    qualification_no INTEGER      NOT NULL CHECK (qualification_no > 0),
    title            VARCHAR(200) NOT NULL,
    institution      VARCHAR(200) NOT NULL,
    year_obtained    INTEGER      NOT NULL CHECK (year_obtained >= 1950),
    PRIMARY KEY (worker_id, qualification_no),
    FOREIGN KEY (worker_id) REFERENCES worker (worker_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- Worker weekly availability
CREATE TABLE availability (
    worker_id        INTEGER     NOT NULL,
    day_of_week      VARCHAR(15) NOT NULL CHECK (day_of_week IN (
                         'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'
                     )),
    start_time       TIME        NOT NULL,
    end_time         TIME        NOT NULL,
    PRIMARY KEY (worker_id, day_of_week, start_time),
    CHECK (end_time > start_time),
    FOREIGN KEY (worker_id) REFERENCES worker (worker_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- Badges
CREATE TABLE badge (
    badge_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name              VARCHAR(100) NOT NULL UNIQUE,
    min_jobs_required INTEGER      NOT NULL CHECK (min_jobs_required >= 0)
);

-- Worker badges
CREATE TABLE worker_badge (
    worker_id        INTEGER NOT NULL,
    badge_id         INTEGER NOT NULL,
    awarded_date     DATE    NOT NULL DEFAULT (DATE('now')),
    PRIMARY KEY (worker_id, badge_id),
    FOREIGN KEY (worker_id) REFERENCES worker (worker_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (badge_id) REFERENCES badge (badge_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- Bookings
CREATE TABLE booking (
    booking_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id      INTEGER        NOT NULL,
    worker_id        INTEGER        NOT NULL,
    category_id      INTEGER        NOT NULL,
    job_description  TEXT           NOT NULL,
    job_address      VARCHAR(255)   NOT NULL,
    scheduled_start  DATETIME       NOT NULL,
    status           VARCHAR(30)    NOT NULL DEFAULT 'PENDING' CHECK (status IN (
                         'PENDING', 'CONFIRMED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED'
                     )),
    agreed_rate      DECIMAL(10, 2) NOT NULL CHECK (agreed_rate > 0),
    created_at       DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at     DATETIME       NULL,
    FOREIGN KEY (customer_id) REFERENCES customer (customer_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (worker_id, category_id) REFERENCES worker_service (worker_id, category_id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- Booking reviews
CREATE TABLE review (
    review_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id       INTEGER  NOT NULL UNIQUE,
    rating           INTEGER  NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment          TEXT,
    review_date      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (booking_id) REFERENCES booking (booking_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- Worker portfolio images
CREATE TABLE worker_portfolio (
    portfolio_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    worker_id        INTEGER      NOT NULL,
    image_url        VARCHAR(500) NOT NULL,
    title            VARCHAR(150),
    uploaded_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (worker_id) REFERENCES worker (worker_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- Triggers and views

-- Update completed_jobs when booking status changes to COMPLETED
CREATE TRIGGER trg_update_worker_jobs_on_complete
AFTER UPDATE OF status ON booking
BEGIN
    UPDATE worker
    SET completed_jobs = (
        SELECT COUNT(*)
        FROM booking
        WHERE booking.worker_id = NEW.worker_id
          AND booking.status = 'COMPLETED'
    )
    WHERE worker_id = NEW.worker_id;
END;

-- Update completed_jobs on direct insert of a completed booking
CREATE TRIGGER trg_update_worker_jobs_on_insert
AFTER INSERT ON booking
WHEN NEW.status = 'COMPLETED'
BEGIN
    UPDATE worker
    SET completed_jobs = (
        SELECT COUNT(*)
        FROM booking
        WHERE booking.worker_id = NEW.worker_id
          AND booking.status = 'COMPLETED'
    )
    WHERE worker_id = NEW.worker_id;
END;

-- Recalculate avg_rating when a review is added
CREATE TRIGGER trg_update_worker_rating_on_review
AFTER INSERT ON review
BEGIN
    UPDATE worker
    SET avg_rating = COALESCE((
        SELECT ROUND(AVG(r.rating), 2)
        FROM review r
        INNER JOIN booking b ON r.booking_id = b.booking_id
        WHERE b.worker_id = (SELECT worker_id FROM booking WHERE booking_id = NEW.booking_id)
    ), 0.00)
    WHERE worker_id = (SELECT worker_id FROM booking WHERE booking_id = NEW.booking_id);
END;

-- View for dynamically calculated worker stats
CREATE VIEW v_worker_derived_stats AS
SELECT
    w.worker_id,
    w.first_name || ' ' || w.last_name AS worker_name,
    w.city,
    w.experience_years,
    COUNT(DISTINCT CASE WHEN b.status = 'COMPLETED' THEN b.booking_id END) AS completed_jobs,
    COALESCE(ROUND(AVG(r.rating), 2), 0.00) AS avg_rating
FROM worker w
LEFT JOIN booking b ON b.worker_id = w.worker_id
LEFT JOIN review  r ON r.booking_id = b.booking_id
GROUP BY w.worker_id;

-- Seed data

INSERT INTO customer (customer_id, first_name, last_name, email, phone, password_hash, address, registered_at) VALUES
(1, 'Amaya',   'Perera',       'amaya.perera@email.lk',    '077-2345678', 'hash_ap91', '42 Flower Rd, Colombo 07',         '2026-01-12 09:15:00'),
(2, 'Rohan',   'Silva',        'rohan.silva@email.lk',     '071-8765432', 'hash_rs82', '18 Galle Rd, Dehiwala',            '2026-02-03 14:20:00'),
(3, 'Nadeesha','Fernando',     'nadeesha.f@email.lk',      '076-3456789', 'hash_nf73', '7A Wijerama Mawatha, Nugegoda',    '2026-03-19 11:05:00'),
(4, 'Tariq',   'Ismail',       'tariq.ismail@email.lk',    '077-9988776', 'hash_ti64', '105 Havelock Rd, Colombo 05',      '2026-04-25 16:40:00'),
(5, 'Dilani',  'Jayawardena',  'dilani.j@email.lk',        '070-1122334', 'hash_dj55', '29 Nawala Rd, Rajagiriya',         '2026-05-10 08:50:00');

INSERT INTO worker (worker_id, first_name, last_name, email, phone, password_hash, city, experience_years, bio, profile_image_url, registered_at) VALUES
(1, 'Kasun',   'Bandara',      'kasun.bandara@quickdone.lk',  '077-5501122', 'hash_kb1', 'Colombo',      8, 'NVQ Level 4 certified master electrician and smart-panel installer.', 'https://images.unsplash.com/photo-1540569014015-19a7be504e3a?w=400&q=80', '2025-11-01 10:00:00'),
(2, 'Chaminda','Rajapaksa',    'chaminda.r@quickdone.lk',     '071-6602233', 'hash_cr2', 'Nugegoda',     6, 'Residential and commercial plumbing specialist for leak & pump systems.', 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&q=80', '2025-11-15 11:30:00'),
(3, 'Suresh',  'Kumar',        'suresh.kumar@quickdone.lk',   '076-7703344', 'hash_sk3', 'Dehiwala',     11,'HVAC and inverter air-conditioner servicing & gas refilling technician.', 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=400&q=80', '2025-12-05 09:45:00'),
(4, 'Malithi', 'Gunawardena',  'malithi.g@quickdone.lk',      '077-8804455', 'hash_mg4', 'Rajagiriya',   4, 'Eco-friendly deep home cleaning and post-renovation sanitation lead.',   'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=400&q=80', '2026-01-20 13:15:00'),
(5, 'Nuwan',   'Dissanayake',  'nuwan.d@quickdone.lk',        '071-9905566', 'hash_nd5', 'Maharagama',   9, 'Custom teak furniture repair, door fitting, and architectural carpentry.', 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=400&q=80', '2026-02-14 15:00:00');

INSERT INTO category (category_id, name, description) VALUES
(1, 'Electrical',     'Wiring, breaker panel upgrades, fault finding, and lighting installation'),
(2, 'Plumbing',       'Pipe leak repairs, pressure pump installation, and bathroom fittings'),
(3, 'AC Servicing',   'Split & inverter AC chemical wash, gas top-up, and PCB repair'),
(4, 'Deep Cleaning',  'Full-house sanitization, sofa shampooing, and kitchen degreasing'),
(5, 'Carpentry',      'Door lock fitting, timber furniture restoration, and cabinetry');

INSERT INTO worker_service (worker_id, category_id, hourly_rate) VALUES
(1, 1, 2500.00), -- Kasun: Electrical
(1, 3, 2800.00), -- Kasun: AC Servicing
(2, 2, 2200.00), -- Chaminda: Plumbing
(3, 3, 3200.00), -- Suresh: AC Servicing
(3, 1, 2300.00), -- Suresh: Electrical
(4, 4, 1800.00), -- Malithi: Deep Cleaning
(5, 5, 2600.00), -- Nuwan: Carpentry
(5, 2, 1950.00); -- Nuwan: Plumbing

INSERT INTO qualification (worker_id, qualification_no, title, institution, year_obtained) VALUES
(1, 1, 'NVQ Level 4 Certificate in Electrical Technology', 'VTA Sri Lanka',            2019),
(1, 2, 'Domestic Solar & Smart Breaker Safety Diploma',    'Ceylon German Tech (CGTTI)', 2022),
(2, 1, 'National Certificate in Sanitary & Pipe Fitting',  'NAITA',                    2020),
(3, 1, 'Diploma in Refrigeration & Air Conditioning',      'Ceylon German Tech (CGTTI)', 2016),
(3, 2, 'Inverter R32/R410A Refrigerant Handling License',  'Ministry of Environment',  2021),
(4, 1, 'Professional Hospitality Housekeeping Certificate','SLITHM Colombo',           2022),
(5, 1, 'Master Craftsmanship in Timber & Joinery',         'NAITA',                    2018);

INSERT INTO availability (worker_id, day_of_week, start_time, end_time) VALUES
(1, 'Monday',    '08:00', '17:00'),
(1, 'Wednesday', '08:00', '17:00'),
(1, 'Friday',    '08:00', '16:00'),
(2, 'Tuesday',   '09:00', '18:00'),
(2, 'Thursday',  '09:00', '18:00'),
(2, 'Saturday',  '08:30', '14:30'),
(3, 'Monday',    '08:30', '17:30'),
(3, 'Saturday',  '09:00', '16:00'),
(4, 'Wednesday', '08:00', '15:00'),
(4, 'Sunday',    '09:00', '15:00'),
(5, 'Thursday',  '08:00', '17:00'),
(5, 'Saturday',  '08:00', '16:00');

INSERT INTO badge (badge_id, name, min_jobs_required) VALUES
(1, 'Rising Pro', 1),
(2, 'Expert',     2),
(3, 'Master',     3);

-- Badges awarded to workers
INSERT INTO worker_badge (worker_id, badge_id, awarded_date) VALUES
(1, 1, '2026-06-15'),
(1, 2, '2026-08-20'),
(2, 1, '2026-07-10'),
(3, 1, '2026-07-22');

-- Bookings
INSERT INTO booking (booking_id, customer_id, worker_id, category_id, job_description, job_address, scheduled_start, status, agreed_rate, created_at, completed_at) VALUES
(1, 1, 1, 1, 'Replace 3-phase main RCB breaker and fix kitchen socket trip', '42 Flower Rd, Colombo 07',      '2026-06-10 09:30:00', 'COMPLETED',   2500.00, '2026-06-08 14:00:00', '2026-06-10 12:00:00'),
(2, 2, 1, 1, 'Install surge protector and 6 LED recessed ceiling lights',    '18 Galle Rd, Dehiwala',         '2026-08-14 10:00:00', 'COMPLETED',   2500.00, '2026-08-12 11:20:00', '2026-08-14 13:30:00'),
(3, 3, 1, 3, 'Bedroom inverter AC annual chemical wash and filter check',    '7A Wijerama Mawatha, Nugegoda', '2026-09-05 14:00:00', 'COMPLETED',   2800.00, '2026-09-01 09:10:00', '2026-09-05 16:00:00'),
(4, 1, 2, 2, 'Overhead water tank pressure pump seal replacement',           '42 Flower Rd, Colombo 07',      '2026-07-08 09:00:00', 'COMPLETED',   2200.00, '2026-07-06 18:00:00', '2026-07-08 11:15:00'),
(5, 4, 2, 2, 'Fix concealed hot-water mixer leak in upstairs bathroom',      '105 Havelock Rd, Colombo 05',   '2026-09-18 11:00:00', 'COMPLETED',   2200.00, '2026-09-15 10:05:00', '2026-09-18 13:45:00'),
(6, 5, 3, 3, 'Dual split AC R32 gas top-up and condenser coil service',      '29 Nawala Rd, Rajagiriya',      '2026-07-20 09:00:00', 'COMPLETED',   3200.00, '2026-07-18 08:30:00', '2026-07-20 12:30:00'),
(7, 2, 3, 3, 'Office AC PCB board diagnostic and drainage unblocking',       '18 Galle Rd, Dehiwala',         '2026-10-02 13:30:00', 'COMPLETED',   3200.00, '2026-09-29 15:45:00', '2026-10-02 15:30:00'),
(8, 3, 4, 4, 'Full 3-bedroom apartment deep steam cleaning & sanitization',  '7A Wijerama Mawatha, Nugegoda', '2026-10-12 08:30:00', 'COMPLETED',   1800.00, '2026-10-09 12:00:00', '2026-10-12 14:30:00'),
(9, 4, 5, 5, 'Refit warped mahogany main entrance door & deadbolt lock',     '105 Havelock Rd, Colombo 05',   '2026-11-11 09:00:00', 'CONFIRMED',   2600.00, '2026-11-08 17:15:00', NULL),
(10,5, 1, 1, 'Inspect EV home wall-charger wiring and load balance',         '29 Nawala Rd, Rajagiriya',      '2026-11-12 10:00:00', 'PENDING',     2500.00, '2026-11-09 09:00:00', NULL);

-- Reviews
INSERT INTO review (review_id, booking_id, rating, comment, review_date) VALUES
(1, 1, 5, 'Kasun diagnosed the breaker fault in 10 minutes and neatened the entire DB box.', '2026-06-10 18:00:00'),
(2, 2, 5, 'Very punctual and clean ceiling light installation. Highly recommended.',         '2026-08-14 19:20:00'),
(3, 3, 4, 'Good AC service, cooling improved immediately.',                                  '2026-09-06 10:00:00'),
(4, 4, 4, 'Pump noise is completely gone and water pressure is steady.',                     '2026-07-08 16:40:00'),
(5, 5, 5, 'Saved us from breaking tiles by locating the exact valve joint leak.',            '2026-09-18 20:15:00'),
(6, 6, 5, 'Suresh brought digital manifold gauges and checked every AC unit thoroughly.',    '2026-07-20 17:10:00'),
(7, 7, 5, 'Fixed the PCB relay instead of charging for a whole new board!',                  '2026-10-02 19:00:00'),
(8, 8, 5, 'Spotless kitchen and living room shampooing. Looks brand new.',                   '2026-10-12 18:30:00');

-- Portfolio images
INSERT INTO worker_portfolio (portfolio_id, worker_id, image_url, title, uploaded_at) VALUES
(1, 1, 'https://images.unsplash.com/photo-1621905251189-08b45d6a269e?w=800&q=80', 'Main Breaker Panel Upgrade & Wiring', '2026-06-15 10:00:00'),
(2, 1, 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=800&q=80', 'Recessed Smart LED Lighting Project',   '2026-08-20 14:30:00'),
(3, 2, 'https://images.unsplash.com/photo-1585704032915-c3400ca199e7?w=800&q=80', 'Concealed Bathroom Mixer Valve Fitting', '2026-07-15 11:20:00'),
(4, 2, 'https://images.unsplash.com/photo-1504328345606-18bbc8c9d7d1?w=800&q=80', 'Overhead Water Tank Pump Installation',  '2026-09-20 16:45:00'),
(5, 3, 'https://images.unsplash.com/photo-1569154941061-e231b4725ef1?w=800&q=80', 'Dual Inverter Split AC Chemical Wash',   '2026-07-25 09:15:00'),
(6, 4, 'https://images.unsplash.com/photo-1581578731548-c64695cc6952?w=800&q=80', '3-Bedroom Apartment Deep Sanitization',  '2026-10-15 12:00:00'),
(7, 5, 'https://images.unsplash.com/photo-1565008447742-97f6f38c985c?w=800&q=80', 'Solid Teak Custom Entrance Door & Lock', '2026-11-05 15:30:00');
