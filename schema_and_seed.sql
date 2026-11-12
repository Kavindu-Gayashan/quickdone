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
(5, 'Dilani',  'Jayawardena',  'dilani.j@email.lk',        '070-1122334', 'hash_dj55', '29 Nawala Rd, Rajagiriya',         '2026-05-10 08:50:00'),
(6, 'Kavindi', 'Alwis',        'kavindi.alwis@email.lk',   '077-4455667', 'hash_ka66', '14 Temple Rd, Mount Lavinia',      '2026-05-18 10:30:00'),
(7, 'Dinesh',  'Ratnayake',    'dinesh.r@email.lk',        '071-3322110', 'hash_dr77', '82 Peradeniya Rd, Kandy',          '2026-06-01 14:15:00'),
(8, 'Shenali', 'De Silva',     'shenali.ds@email.lk',      '076-8899001', 'hash_sd88', '55 Negombo Rd, Wattala',           '2026-06-22 16:00:00'),
(9, 'Mohamed', 'Farook',       'farook.m@email.lk',        '077-1239876', 'hash_mf99', '210 Main Street, Battaramulla',     '2026-07-05 11:45:00'),
(10,'Anura',   'Kumara',       'anura.k@email.lk',         '078-5544332', 'hash_ak10', '33 Station Rd, Moratuwa',           '2026-07-19 09:20:00');

INSERT INTO worker (worker_id, first_name, last_name, email, phone, password_hash, city, experience_years, bio, profile_image_url, registered_at) VALUES
(1, 'Kasun',   'Bandara',      'kasun.bandara@quickdone.lk',  '077-5501122', 'hash_kb1', 'Colombo',      8, 'NVQ Level 4 certified master electrician and smart-panel installer.', 'https://images.unsplash.com/photo-1540569014015-19a7be504e3a?w=400&q=80', '2025-11-01 10:00:00'),
(2, 'Chaminda','Rajapaksa',    'chaminda.r@quickdone.lk',     '071-6602233', 'hash_cr2', 'Nugegoda',     6, 'Residential and commercial plumbing specialist for leak & pump systems.', 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&q=80', '2025-11-15 11:30:00'),
(3, 'Suresh',  'Kumar',        'suresh.kumar@quickdone.lk',   '076-7703344', 'hash_sk3', 'Dehiwala',     11,'HVAC and inverter air-conditioner servicing & gas refilling technician.', 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=400&q=80', '2025-12-05 09:45:00'),
(4, 'Malithi', 'Gunawardena',  'malithi.g@quickdone.lk',      '077-8804455', 'hash_mg4', 'Rajagiriya',   4, 'Eco-friendly deep home cleaning and post-renovation sanitation lead.',   'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=400&q=80', '2026-01-20 13:15:00'),
(5, 'Nuwan',   'Dissanayake',  'nuwan.d@quickdone.lk',        '071-9905566', 'hash_nd5', 'Maharagama',   9, 'Custom teak furniture repair, door fitting, and architectural carpentry.', 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=400&q=80', '2026-02-14 15:00:00'),
(6, 'Sachith', 'Pathirana',    'sachith.p@quickdone.lk',      '077-3344112', 'hash_sp6', 'Colombo',      7, 'Commercial wiring expert specializing in lighting automation and generator systems.', 'https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=400&q=80', '2026-02-28 10:00:00'),
(7, 'Priyantha','Mendis',      'priyantha.m@quickdone.lk',    '071-5566778', 'hash_pm7', 'Moratuwa',     12,'Master craftsman in architectural wood carving, staircase restoration, and pantry cupboards.', 'https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?w=400&q=80', '2026-03-15 08:30:00'),
(8, 'Kavitha', 'Selvaraj',     'kavitha.s@quickdone.lk',      '076-2233445', 'hash_ks8', 'Dehiwala',     5, 'Specialized in post-construction cleaning, carpet steam extraction, and window polishing.', 'https://images.unsplash.com/photo-1580489944761-15a19d654956?w=400&q=80', '2026-04-02 11:20:00');

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
(5, 2, 1950.00), -- Nuwan: Plumbing
(6, 1, 2700.00), -- Sachith: Electrical
(6, 3, 3000.00), -- Sachith: AC Servicing
(7, 5, 2900.00), -- Priyantha: Carpentry
(8, 4, 1950.00), -- Kavitha: Deep Cleaning
(8, 2, 1800.00); -- Kavitha: Plumbing

INSERT INTO qualification (worker_id, qualification_no, title, institution, year_obtained) VALUES
(1, 1, 'NVQ Level 4 Certificate in Electrical Technology', 'VTA Sri Lanka',            2019),
(1, 2, 'Domestic Solar & Smart Breaker Safety Diploma',    'Ceylon German Tech (CGTTI)', 2022),
(2, 1, 'National Certificate in Sanitary & Pipe Fitting',  'NAITA',                    2020),
(3, 1, 'Diploma in Refrigeration & Air Conditioning',      'Ceylon German Tech (CGTTI)', 2016),
(3, 2, 'Inverter R32/R410A Refrigerant Handling License',  'Ministry of Environment',  2021),
(4, 1, 'Professional Hospitality Housekeeping Certificate','SLITHM Colombo',           2022),
(5, 1, 'Master Craftsmanship in Timber & Joinery',         'NAITA',                    2018),
(6, 1, 'Higher National Diploma in Electrical Engineering','SLIATE Mattakkuliya',      2018),
(6, 2, 'Certified Industrial Automation & PLC Technician', 'University of Moratuwa NDT', 2021),
(7, 1, 'National Craft Certificate in Fine Woodworking',   'NAITA Galle',               2014),
(7, 2, 'Heritage Architecture Wood Restoration Specialist','Department of Archaeology', 2019),
(8, 1, 'Advanced Certificate in Environmental Sanitation', 'National Institute of Health', 2021);

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
(5, 'Saturday',  '08:00', '16:00'),
(6, 'Monday',    '08:30', '17:30'),
(6, 'Wednesday', '08:30', '17:30'),
(6, 'Friday',    '09:00', '16:00'),
(7, 'Tuesday',   '08:00', '16:30'),
(7, 'Thursday',  '08:00', '16:30'),
(7, 'Saturday',  '08:00', '15:00'),
(8, 'Monday',    '08:00', '16:00'),
(8, 'Wednesday', '08:00', '16:00'),
(8, 'Saturday',  '09:00', '17:00');

INSERT INTO badge (badge_id, name, min_jobs_required) VALUES
(1, 'Rising Pro', 1),
(2, 'Expert',     2),
(3, 'Master',     3);

-- Badges awarded to workers
INSERT INTO worker_badge (worker_id, badge_id, awarded_date) VALUES
(1, 1, '2026-06-15'),
(1, 2, '2026-08-20'),
(1, 3, '2026-09-10'),
(2, 1, '2026-07-10'),
(2, 2, '2026-09-20'),
(3, 1, '2026-07-22'),
(3, 2, '2026-10-05'),
(4, 1, '2026-10-15'),
(5, 1, '2026-11-05'),
(6, 1, '2026-09-02'),
(7, 1, '2026-09-18');

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
(9, 4, 5, 5, 'Refit warped mahogany main entrance door & deadbolt lock',     '105 Havelock Rd, Colombo 05',   '2026-10-25 09:00:00', 'COMPLETED',   2600.00, '2026-10-22 17:15:00', '2026-10-25 12:00:00'),
(10,6, 6, 1, 'Factory sub-distribution panel upgrade and thermal testing',   '14 Temple Rd, Mount Lavinia',   '2026-08-28 09:00:00', 'COMPLETED',   2700.00, '2026-08-25 10:30:00', '2026-08-28 14:00:00'),
(11,7, 7, 5, 'Bespoke solid teak pantry cupboards and quartz counter fitting','82 Peradeniya Rd, Kandy',      '2026-09-12 08:30:00', 'COMPLETED',   2900.00, '2026-09-08 16:45:00', '2026-09-12 15:30:00'),
(12,8, 8, 4, 'Post-renovation multi-story dust extraction and floor buffing', '55 Negombo Rd, Wattala',        '2026-09-28 08:00:00', 'COMPLETED',   1950.00, '2026-09-24 11:20:00', '2026-09-28 14:00:00'),
(13,9, 2, 2, 'Main sewer line clearing and high pressure pipe jetting',      '210 Main Street, Battaramulla', '2026-10-18 10:00:00', 'COMPLETED',   2200.00, '2026-10-15 08:15:00', '2026-10-18 13:00:00'),
(14,10,6, 3, 'Server room dual-split AC maintenance and filter renewal',     '33 Station Rd, Moratuwa',        '2026-10-29 11:00:00', 'COMPLETED',   3000.00, '2026-10-26 14:50:00', '2026-10-29 13:45:00'),
(15,1, 7, 5, 'Restoration of antique colonial dining table and 8 chairs',    '42 Flower Rd, Colombo 07',      '2026-11-02 09:00:00', 'COMPLETED',   2900.00, '2026-10-29 13:00:00', '2026-11-02 14:30:00'),
(16,2, 8, 4, 'Full villa sofa dry cleaning and curtain steam wash',           '18 Galle Rd, Dehiwala',         '2026-11-08 08:30:00', 'COMPLETED',   1950.00, '2026-11-05 10:15:00', '2026-11-08 12:30:00'),
(17,3, 1, 1, 'Solar inverter load balancing and surge arrester installation','7A Wijerama Mawatha, Nugegoda', '2026-11-12 10:00:00', 'IN_PROGRESS', 2500.00, '2026-11-09 15:40:00', NULL),
(18,5, 2, 2, 'Underground sump pump float switch replacement and rewiring',  '29 Nawala Rd, Rajagiriya',      '2026-11-12 13:30:00', 'IN_PROGRESS', 2200.00, '2026-11-10 11:00:00', NULL),
(19,6, 3, 1, 'Three-phase workshop machinery supply line diagnosis',          '14 Temple Rd, Mount Lavinia',   '2026-11-12 14:00:00', 'IN_PROGRESS', 2300.00, '2026-11-10 16:30:00', NULL),
(20,7, 5, 5, 'Custom hardwood louvered window frames for garden pavilion',   '82 Peradeniya Rd, Kandy',       '2026-11-14 09:00:00', 'CONFIRMED',   2600.00, '2026-11-11 11:20:00', NULL),
(21,8, 6, 1, 'EV home wall-charger wiring, dedicated earthing, and testing', '55 Negombo Rd, Wattala',        '2026-11-15 10:00:00', 'CONFIRMED',   2700.00, '2026-11-11 14:10:00', NULL),
(22,9, 8, 2, 'Commercial restaurant grease trap cleaning and drain inspection','210 Main Street, Battaramulla','2026-11-16 08:30:00', 'CONFIRMED',   1800.00, '2026-11-11 17:00:00', NULL),
(23,10,4, 4, 'Full house deep sanitization before tenant move-in',           '33 Station Rd, Moratuwa',        '2026-11-18 09:00:00', 'PENDING',     1800.00, '2026-11-12 08:45:00', NULL),
(24,4, 7, 5, 'Fitting modern magnetic door closers and security deadbolts',   '105 Havelock Rd, Colombo 05',   '2026-11-19 14:00:00', 'PENDING',     2900.00, '2026-11-12 10:15:00', NULL),
(25,2, 3, 3, 'Living room ceiling cassette AC chemical flush',               '18 Galle Rd, Dehiwala',         '2026-10-15 10:00:00', 'CANCELLED',   3200.00, '2026-10-12 09:30:00', NULL),
(26,5, 1, 3, 'Dual split AC emergency capacitor repair',                      '29 Nawala Rd, Rajagiriya',      '2026-10-20 14:00:00', 'CANCELLED',   2800.00, '2026-10-18 16:00:00', NULL);

-- Reviews
INSERT INTO review (review_id, booking_id, rating, comment, review_date) VALUES
(1, 1, 5, 'Kasun diagnosed the breaker fault in 10 minutes and neatened the entire DB box.', '2026-06-10 18:00:00'),
(2, 2, 5, 'Very punctual and clean ceiling light installation. Highly recommended.',         '2026-08-14 19:20:00'),
(3, 3, 4, 'Good AC service, cooling improved immediately.',                                  '2026-09-06 10:00:00'),
(4, 4, 4, 'Pump noise is completely gone and water pressure is steady.',                     '2026-07-08 16:40:00'),
(5, 5, 5, 'Saved us from breaking tiles by locating the exact valve joint leak.',            '2026-09-18 20:15:00'),
(6, 6, 5, 'Suresh brought digital manifold gauges and checked every AC unit thoroughly.',    '2026-07-20 17:10:00'),
(7, 7, 5, 'Fixed the PCB relay instead of charging for a whole new board!',                  '2026-10-02 19:00:00'),
(8, 8, 5, 'Spotless kitchen and living room shampooing. Looks brand new.',                   '2026-10-12 18:30:00'),
(9, 9, 5, 'Nuwan planed the teak door perfectly without damaging the frame finish.',         '2026-10-25 18:00:00'),
(10,10,5, 'Sachith did an exceptional thermal scanning and rewired our factory panel safely.', '2026-08-28 17:30:00'),
(11,11,5, 'Priyantha is a true timber artist. The pantry cupboards look luxurious.',         '2026-09-12 19:00:00'),
(12,12,4, 'Kavitha and team arrived with industrial scrubbers and left the floors spotless.', '2026-09-28 17:15:00'),
(13,13,5, 'Chaminda cleared the deep blockage without any mess. Lifesaver!',                 '2026-10-18 16:30:00'),
(14,14,5, 'Server room AC operates at peak temperature now. Very knowledgeable technician.', '2026-10-29 16:00:00'),
(15,15,5, 'The French polish restoration on our heirloom table is flawless. Outstanding work.', '2026-11-02 17:45:00'),
(16,16,4, 'Great deep steam cleaning on the living room velvet sofa.',                       '2026-11-08 16:15:00');

-- Portfolio images
INSERT INTO worker_portfolio (portfolio_id, worker_id, image_url, title, uploaded_at) VALUES
(1, 1, 'https://images.unsplash.com/photo-1621905251189-08b45d6a269e?w=800&q=80', 'Main Breaker Panel Upgrade & Wiring', '2026-06-15 10:00:00'),
(2, 1, 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=800&q=80', 'Recessed Smart LED Lighting Project',   '2026-08-20 14:30:00'),
(3, 1, 'https://images.unsplash.com/photo-1563770660941-20978e870e26?w=800&q=80', 'Solar Inverter Distribution Setup',    '2026-09-15 11:00:00'),
(4, 2, 'https://images.unsplash.com/photo-1585704032915-c3400ca199e7?w=800&q=80', 'Concealed Bathroom Mixer Valve Fitting', '2026-07-15 11:20:00'),
(5, 2, 'https://images.unsplash.com/photo-1504328345606-18bbc8c9d7d1?w=800&q=80', 'Overhead Water Tank Pump Installation',  '2026-09-20 16:45:00'),
(6, 3, 'https://images.unsplash.com/photo-1569154941061-e231b4725ef1?w=800&q=80', 'Dual Inverter Split AC Chemical Wash',   '2026-07-25 09:15:00'),
(7, 3, 'https://images.unsplash.com/photo-1621905252507-b35492cc74b4?w=800&q=80', 'Outdoor Compressor Unit Gas Recharge',   '2026-10-05 14:20:00'),
(8, 4, 'https://images.unsplash.com/photo-1581578731548-c64695cc6952?w=800&q=80', '3-Bedroom Apartment Deep Sanitization',  '2026-10-15 12:00:00'),
(9, 4, 'https://images.unsplash.com/photo-1527515637462-cff94eecc1ac?w=800&q=80', 'Kitchen Tiles & Range Hood Degreasing',  '2026-10-22 15:30:00'),
(10,5, 'https://images.unsplash.com/photo-1565008447742-97f6f38c985c?w=800&q=80', 'Solid Teak Custom Entrance Door & Lock', '2026-11-05 15:30:00'),
(11,5, 'https://images.unsplash.com/photo-1538688525198-9b88f6f53126?w=800&q=80', 'Hardwood Louvered Window Restoration',    '2026-11-08 13:00:00'),
(12,6, 'https://images.unsplash.com/photo-1581092160607-ee22621dd758?w=800&q=80', 'Factory Control Panel Wiring & Cable Tray','2026-08-30 11:30:00'),
(13,6, 'https://images.unsplash.com/photo-1513694203232-719a280e022f?w=800&q=80', 'Smart Home Multi-circuit Breaker Setup', '2026-09-18 16:15:00'),
(14,7, 'https://images.unsplash.com/photo-1556911220-e15b29be8c8f?w=800&q=80', 'Solid Mahogany Fitted Pantry Cupboards',    '2026-09-14 10:45:00'),
(15,7, 'https://images.unsplash.com/photo-1616486338812-3dadae4b4ace?w=800&q=80', 'Colonial Dining Table French Polish Restor.','2026-11-03 14:00:00'),
(16,8, 'https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=800&q=80', 'Post-Construction Living Room Clean',     '2026-09-30 12:00:00'),
(17,8, 'https://images.unsplash.com/photo-1584622650111-993a426fbf0a?w=800&q=80', 'Upholstery & Carpet Steam Extraction',   '2026-11-09 11:15:00');

