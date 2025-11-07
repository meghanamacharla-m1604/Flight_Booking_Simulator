--  MILESTONE 1: DATABASE SCHEMA DESIGN AND IMPLEMENTATION (80 Flights Version)

-- 1. DROP EXISTING TABLES (for a clean start)
DROP TABLE IF EXISTS booking;
DROP TABLE IF EXISTS cancelled_booking;
DROP TABLE IF EXISTS flight;
DROP TABLE IF EXISTS airport_lookup;
DROP TABLE IF EXISTS user;

-- =======================================================
-- 2. SCHEMA DEFINITION
-- =======================================================

CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(20) NOT NULL UNIQUE,
    password_hash VARCHAR(128) NOT NULL,
    full_name VARCHAR(100),
    phone VARCHAR(20),
    country VARCHAR(50)
);

CREATE TABLE airport_lookup (
    code VARCHAR(10) PRIMARY KEY,
    city_country VARCHAR(100) NOT NULL
);

CREATE TABLE flight (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    flight_number VARCHAR(50) NOT NULL UNIQUE,
    airline VARCHAR(50) NOT NULL,
    from_city_country VARCHAR(100) NOT NULL,
    to_city_country VARCHAR(100) NOT NULL,
    base_price REAL NOT NULL,
    total_seats INTEGER NOT NULL,
    seats_remaining INTEGER NOT NULL,
    demand_factor REAL DEFAULT 1.0,
    CHECK(seats_remaining >= 0 AND seats_remaining <= total_seats)
);

CREATE TABLE booking (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    flight_id INTEGER NOT NULL,
    pnr VARCHAR(10) NOT NULL UNIQUE,
    price_paid REAL NOT NULL,
    booking_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING_PAYMENT',
    passenger_full_name VARCHAR(100),
    FOREIGN KEY (user_id) REFERENCES user(id),
    FOREIGN KEY (flight_id) REFERENCES flight(id)
);

CREATE TABLE cancelled_booking (
    archive_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pnr VARCHAR(10),
    user_id INTEGER,
    flight_id INTEGER,
    price_paid REAL,
    refund_amount REAL,
    cancellation_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    passenger_full_name VARCHAR(100)
);

-- =======================================================
-- 3. POPULATE SAMPLE DATA
-- =======================================================

-- Users
INSERT INTO user (username, password_hash, full_name, phone, country) VALUES
('admin_user', '44798dd7d0f2c058bff13fdbac8c49b3a2ee56823eddcc2d26054a15ef41c842', 'Admin Manager', '9991110000', 'USA'),
('traveler', '44798dd7d0f2c058bff13fdbac8c49b3a2ee56823eddcc2d26054a15ef41c842', 'Travel User', '8882223333', 'UK'),
('rahul', '44798dd7d0f2c058bff13fdbac8c49b3a2ee56823eddcc2d26054a15ef41c842', 'Rahul Mehta', '7774445555', 'India'),
('sarah', '44798dd7d0f2c058bff13fdbac8c49b3a2ee56823eddcc2d26054a15ef41c842', 'Sarah Jones', '6669991111', 'Canada');

-- Airports
INSERT INTO airport_lookup (code, city_country) VALUES
('JFK', 'New York, USA'), ('LHR', 'London, UK'), ('DXB', 'Dubai, UAE'), ('DEL', 'New Delhi, India'),
('CDG', 'Paris, France'), ('HND', 'Tokyo, Japan'), ('SYD', 'Sydney, Australia'), ('SIN', 'Singapore, Singapore'),
('FRA', 'Frankfurt, Germany'), ('BOM', 'Mumbai, India'), ('YYZ', 'Toronto, Canada'), ('ATH', 'Athens, Greece'),
('ICN', 'Seoul, South Korea'), ('IST', 'Istanbul, Turkey'), ('JNB', 'Johannesburg, South Africa'),
('LAX', 'Los Angeles, USA'), ('BKK', 'Bangkok, Thailand'), ('KUL', 'Kuala Lumpur, Malaysia'),
('PER', 'Perth, Australia'), ('DUB', 'Dublin, Ireland');

-- =======================================================
-- 4. FLIGHT DATA (80 RECORDS)
-- =======================================================

INSERT INTO flight (flight_number, airline, from_city_country, to_city_country, base_price, total_seats, seats_remaining) VALUES
('FL001', 'Emirates', 'Dubai, UAE', 'London, UK', 620.00, 280, 250),
('FL002', 'Air India', 'New Delhi, India', 'Dubai, UAE', 340.00, 200, 180),
('FL003', 'British Airways', 'London, UK', 'New York, USA', 690.00, 320, 300),
('FL004', 'United Airlines', 'New York, USA', 'London, UK', 700.00, 320, 290),
('FL005', 'Qantas', 'Sydney, Australia', 'Singapore, Singapore', 500.00, 260, 240),
('FL006', 'Singapore Airlines', 'Singapore, Singapore', 'Sydney, Australia', 510.00, 260, 250),
('FL007', 'Air France', 'Paris, France', 'Tokyo, Japan', 950.00, 280, 270),
('FL008', 'Japan Airlines', 'Tokyo, Japan', 'Paris, France', 960.00, 280, 260),
('FL009', 'Lufthansa', 'Frankfurt, Germany', 'Toronto, Canada', 720.00, 230, 200),
('FL010', 'Air Canada', 'Toronto, Canada', 'Frankfurt, Germany', 730.00, 230, 210),
('FL011', 'IndiGo', 'Mumbai, India', 'New Delhi, India', 130.00, 180, 160),
('FL012', 'Vistara', 'New Delhi, India', 'Mumbai, India', 140.00, 180, 150),
('FL013', 'SpiceJet', 'Bengaluru, India', 'Hyderabad, India', 75.00, 150, 130),
('FL014', 'IndiGo', 'Hyderabad, India', 'Bengaluru, India', 80.00, 150, 140),
('FL015', 'Thai Airways', 'Bangkok, Thailand', 'Singapore, Singapore', 230.00, 200, 180),
('FL016', 'Singapore Airlines', 'Singapore, Singapore', 'Bangkok, Thailand', 240.00, 200, 190),
('FL017', 'Emirates', 'Dubai, UAE', 'Frankfurt, Germany', 540.00, 300, 280),
('FL018', 'Lufthansa', 'Frankfurt, Germany', 'Dubai, UAE', 550.00, 300, 290),
('FL019', 'Air France', 'Paris, France', 'Rome, Italy', 170.00, 140, 120),
('FL020', 'Alitalia', 'Rome, Italy', 'Paris, France', 180.00, 140, 130),
('FL021', 'Air India', 'Mumbai, India', 'Singapore, Singapore', 400.00, 240, 210),
('FL022', 'Singapore Airlines', 'Singapore, Singapore', 'Mumbai, India', 410.00, 240, 220),
('FL023', 'Qatar Airways', 'Doha, Qatar', 'Dubai, UAE', 160.00, 220, 200),
('FL024', 'Emirates', 'Dubai, UAE', 'Doha, Qatar', 170.00, 220, 210),
('FL025', 'Turkish Airlines', 'Istanbul, Turkey', 'Athens, Greece', 190.00, 180, 150),
('FL026', 'Aegean Airlines', 'Athens, Greece', 'Istanbul, Turkey', 200.00, 180, 160),
('FL027', 'Qantas', 'Sydney, Australia', 'Perth, Australia', 220.00, 190, 170),
('FL028', 'Virgin Australia', 'Perth, Australia', 'Sydney, Australia', 230.00, 190, 160),
('FL029', 'United Airlines', 'Los Angeles, USA', 'New York, USA', 320.00, 300, 270),
('FL030', 'American Airlines', 'New York, USA', 'Los Angeles, USA', 330.00, 300, 280),
('FL031', 'Lufthansa', 'Frankfurt, Germany', 'London, UK', 250.00, 200, 170),
('FL032', 'British Airways', 'London, UK', 'Frankfurt, Germany', 260.00, 200, 160),
('FL033', 'IndiGo', 'Kolkata, India', 'Bengaluru, India', 110.00, 160, 140),
('FL034', 'Vistara', 'Bengaluru, India', 'Kolkata, India', 120.00, 160, 150),
('FL035', 'Air India', 'Hyderabad, India', 'Chennai, India', 85.00, 170, 160),
('FL036', 'SpiceJet', 'Chennai, India', 'Hyderabad, India', 90.00, 170, 150),
('FL037', 'Emirates', 'Dubai, UAE', 'Mumbai, India', 320.00, 220, 200),
('FL038', 'Air India', 'Mumbai, India', 'Dubai, UAE', 330.00, 220, 210),
('FL039', 'KLM', 'Amsterdam, Netherlands', 'Paris, France', 180.00, 150, 130),
('FL040', 'Air France', 'Paris, France', 'Amsterdam, Netherlands', 190.00, 150, 120),
('FL041', 'Delta Airlines', 'Chicago, USA', 'Miami, USA', 280.00, 260, 230),
('FL042', 'American Airlines', 'Miami, USA', 'Chicago, USA', 290.00, 260, 240),
('FL043', 'Qantas', 'Sydney, Australia', 'Melbourne, Australia', 180.00, 200, 190),
('FL044', 'Virgin Australia', 'Melbourne, Australia', 'Sydney, Australia', 190.00, 200, 170),
('FL045', 'Emirates', 'Dubai, UAE', 'Johannesburg, South Africa', 980.00, 320, 300),
('FL046', 'South African Airways', 'Johannesburg, South Africa', 'Dubai, UAE', 990.00, 320, 310),
('FL047', 'Lufthansa', 'Munich, Germany', 'New York, USA', 880.00, 330, 300),
('FL048', 'United Airlines', 'New York, USA', 'Munich, Germany', 890.00, 330, 310),
('FL049', 'Qatar Airways', 'Doha, Qatar', 'London, UK', 720.00, 290, 270),
('FL050', 'British Airways', 'London, UK', 'Doha, Qatar', 730.00, 290, 260),
('FL051', 'Air India', 'Bengaluru, India', 'Pune, India', 75.00, 150, 130),
('FL052', 'IndiGo', 'Pune, India', 'Bengaluru, India', 80.00, 150, 140),
('FL053', 'Vistara', 'New Delhi, India', 'Chennai, India', 145.00, 180, 170),
('FL054', 'SpiceJet', 'Chennai, India', 'New Delhi, India', 150.00, 180, 160),
('FL055', 'Air France', 'Paris, France', 'Montreal, Canada', 610.00, 250, 230),
('FL056', 'Air Canada', 'Montreal, Canada', 'Paris, France', 620.00, 250, 220),
('FL057', 'Emirates', 'Dubai, UAE', 'Singapore, Singapore', 450.00, 280, 250),
('FL058', 'Singapore Airlines', 'Singapore, Singapore', 'Dubai, UAE', 460.00, 280, 260),
('FL059', 'Turkish Airlines', 'Istanbul, Turkey', 'New Delhi, India', 470.00, 240, 200),
('FL060', 'Air India', 'New Delhi, India', 'Istanbul, Turkey', 480.00, 240, 210),
('FL061', 'Lufthansa', 'Frankfurt, Germany', 'Rome, Italy', 220.00, 160, 150),
('FL062', 'Alitalia', 'Rome, Italy', 'Frankfurt, Germany', 230.00, 160, 140),
('FL063', 'KLM', 'Amsterdam, Netherlands', 'New York, USA', 680.00, 300, 270),
('FL064', 'United Airlines', 'New York, USA', 'Amsterdam, Netherlands', 690.00, 300, 280),
('FL065', 'Qantas', 'Sydney, Australia', 'Tokyo, Japan', 900.00, 310, 280),
('FL066', 'Japan Airlines', 'Tokyo, Japan', 'Sydney, Australia', 910.00, 310, 290),
('FL067', 'Singapore Airlines', 'Singapore, Singapore', 'Kuala Lumpur, Malaysia', 180.00, 200, 180),
('FL068', 'Malaysia Airlines', 'Kuala Lumpur, Malaysia', 'Singapore, Singapore', 190.00, 200, 170),
('FL069', 'Delta Airlines', 'Los Angeles, USA', 'Mexico City, Mexico', 400.00, 270, 250),
('FL070', 'Aeromexico', 'Mexico City, Mexico', 'Los Angeles, USA', 410.00, 270, 240),
('FL071', 'Air India', 'Goa, India', 'New Delhi, India', 120.00, 160, 140),
('FL072', 'IndiGo', 'New Delhi, India', 'Goa, India', 125.00, 160, 150),
('FL073', 'SpiceJet', 'Chennai, India', 'Pune, India', 70.00, 170, 150),
('FL074', 'Vistara', 'Pune, India', 'Chennai, India', 75.00, 170, 160),
('FL075', 'Qatar Airways', 'Doha, Qatar', 'New York, USA', 1100.00, 340, 310),
('FL076', 'United Airlines', 'New York, USA', 'Doha, Qatar', 1120.00, 340, 320),
('FL077', 'British Airways', 'London, UK', 'Toronto, Canada', 580.00, 280, 250),
('FL078', 'Air Canada', 'Toronto, Canada', 'London, UK', 590.00, 280, 260),
('FL079', 'Emirates', 'Dubai, UAE', 'Kuwait City, Kuwait', 150.00, 200, 180),
('FL080', 'Kuwait Airways', 'Kuwait City, Kuwait', 'Dubai, UAE', 160.00, 200, 170);

-- =======================================================
-- 5. SAMPLE BOOKINGS
-- =======================================================

INSERT INTO booking (user_id, flight_id, pnr, price_paid, passenger_full_name, status) VALUES
(3, 1, 'PNRCONFIRM', 620.00, 'Rahul Mehta', 'CONFIRMED');

INSERT INTO cancelled_booking (pnr, user_id, flight_id, price_paid, refund_amount, passenger_full_name) VALUES
('PNRCXL', 4, 2, 340.00, 272.00, 'Sarah Jones');
