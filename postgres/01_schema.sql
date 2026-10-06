-- =============================================================
-- Amadeus Travel Data — PostgreSQL Schema (v2)
-- Full schema including flight schedules, stops, room descriptions
-- =============================================================

-- -------------------------
-- REFERENCE TABLES (shared)
-- -------------------------

CREATE TABLE airlines (
    carrier_code  VARCHAR(3)   PRIMARY KEY,
    name          VARCHAR(100) NOT NULL
);

CREATE TABLE aircraft_types (
    aircraft_code VARCHAR(5)   PRIMARY KEY,
    name          VARCHAR(100) NOT NULL
);

CREATE TABLE airports (
    iata_code    CHAR(3)      PRIMARY KEY,
    name         VARCHAR(100) NOT NULL,
    city_code    CHAR(3)      NOT NULL,
    city_name    VARCHAR(100) NOT NULL,
    country_code CHAR(2)      NOT NULL,
    latitude     NUMERIC(9,6),
    longitude    NUMERIC(9,6)
);

-- =========================================================
-- FLIGHTS DATABASE TABLES
-- =========================================================

CREATE TABLE cabin_fares (
    cabin               VARCHAR(20)  PRIMARY KEY,
    price_multiplier    NUMERIC(5,3) NOT NULL,
    fare_code           VARCHAR(10)  NOT NULL,
    branded_fare        VARCHAR(20)  NOT NULL,
    booking_class       CHAR(1)      NOT NULL,
    checked_bags        SMALLINT     NOT NULL
);

-- Routes: origin/destination pairs with base prices per cabin
CREATE TABLE routes (
    id                         SERIAL        PRIMARY KEY,
    origin_iata                CHAR(3)       NOT NULL REFERENCES airports(iata_code),
    destination_iata           CHAR(3)       NOT NULL REFERENCES airports(iata_code),
    economy_base_price         NUMERIC(10,2) NOT NULL,
    premium_economy_base_price NUMERIC(10,2) NOT NULL,
    business_base_price        NUMERIC(10,2) NOT NULL,
    first_base_price           NUMERIC(10,2) NOT NULL,
    UNIQUE (origin_iata, destination_iata)
);

-- Individual scheduled flights on a route
CREATE TABLE flight_schedules (
    id               SERIAL       PRIMARY KEY,
    route_id         INTEGER      NOT NULL REFERENCES routes(id),
    flight_no        VARCHAR(10)  NOT NULL,
    carrier_code     VARCHAR(3)   NOT NULL REFERENCES airlines(carrier_code),
    aircraft_code    VARCHAR(5)   NOT NULL REFERENCES aircraft_types(aircraft_code),
    departure_time   TIME         NOT NULL,         -- local departure time HH:MM
    duration_minutes INTEGER      NOT NULL,
    terminal_dep     VARCHAR(5),
    terminal_arr     VARCHAR(5),
    available_seats  SMALLINT     NOT NULL DEFAULT 9,
    UNIQUE (flight_no)
);

-- Stops for connecting flights (0 rows = direct flight)
CREATE TABLE flight_stops (
    id              SERIAL      PRIMARY KEY,
    schedule_id     INTEGER     NOT NULL REFERENCES flight_schedules(id),
    stop_order      SMALLINT    NOT NULL DEFAULT 1,
    iata_code       CHAR(3)     NOT NULL REFERENCES airports(iata_code),
    arrival_time    VARCHAR(10),       -- local time at stop HH:MM
    departure_time  VARCHAR(10),       -- local time at stop HH:MM
    layover_duration VARCHAR(10)       -- ISO 8601 e.g. PT2H15M
);

-- Convenience view: complete flight details in one query
CREATE VIEW flight_offers AS
SELECT
    fs.flight_no,
    al.name                                            AS airline,
    fs.carrier_code,
    r.origin_iata,
    ao.city_name                                       AS origin_city,
    r.destination_iata,
    ad.city_name                                       AS destination_city,
    fs.departure_time,
    fs.duration_minutes,
    CONCAT(fs.duration_minutes/60, 'h ', fs.duration_minutes%60, 'm') AS duration,
    fs.terminal_dep,
    fs.terminal_arr,
    at2.name                                           AS aircraft,
    fs.available_seats,
    (SELECT COUNT(*) FROM flight_stops WHERE schedule_id = fs.id) AS num_stops,
    cf.cabin,
    cf.booking_class,
    cf.branded_fare,
    cf.fare_code,
    cf.checked_bags,
    ROUND(r.economy_base_price * cf.price_multiplier, 2) AS base_price_usd,
    ROUND(r.economy_base_price * cf.price_multiplier * 1.12, 2) AS total_price_usd
FROM flight_schedules fs
JOIN routes r           ON r.id          = fs.route_id
JOIN airlines al        ON al.carrier_code = fs.carrier_code
JOIN airports ao        ON ao.iata_code  = r.origin_iata
JOIN airports ad        ON ad.iata_code  = r.destination_iata
JOIN aircraft_types at2 ON at2.aircraft_code = fs.aircraft_code
CROSS JOIN cabin_fares cf
ORDER BY r.origin_iata, r.destination_iata, fs.departure_time, cf.price_multiplier;

-- =========================================================
-- HOTELS DATABASE TABLES
-- =========================================================

CREATE TABLE hotel_cities (
    city_code    CHAR(3)      PRIMARY KEY,
    city_name    VARCHAR(100) NOT NULL,
    country_code CHAR(2)      NOT NULL
);

CREATE TABLE hotels (
    hotel_id        VARCHAR(20)  PRIMARY KEY,
    name            VARCHAR(150) NOT NULL,
    city_code       CHAR(3)      NOT NULL REFERENCES hotel_cities(city_code),
    star_rating     SMALLINT     NOT NULL CHECK (star_rating BETWEEN 1 AND 5),
    address         VARCHAR(200) NOT NULL,
    postal_code     VARCHAR(20),
    country_code    CHAR(2)      NOT NULL,
    latitude        NUMERIC(9,6) NOT NULL,
    longitude       NUMERIC(9,6) NOT NULL,
    distance_km     NUMERIC(5,1) NOT NULL,
    amenities       TEXT[]       NOT NULL DEFAULT '{}'
);

CREATE TABLE hotel_rooms (
    id              SERIAL        PRIMARY KEY,
    hotel_id        VARCHAR(20)   NOT NULL REFERENCES hotels(hotel_id),
    room_type       VARCHAR(50)   NOT NULL,
    beds            SMALLINT      NOT NULL DEFAULT 1,
    bed_type        VARCHAR(20)   NOT NULL DEFAULT 'KING',
    price_per_night NUMERIC(10,2) NOT NULL,
    currency        CHAR(3)       NOT NULL DEFAULT 'USD',
    description     TEXT
);

-- Convenience view: full hotel + room details
CREATE VIEW hotel_offers AS
SELECT
    h.hotel_id,
    h.name                         AS hotel_name,
    h.city_code,
    hc.city_name,
    hc.country_code,
    h.star_rating,
    h.address,
    h.distance_km,
    h.amenities,
    hr.id                          AS room_id,
    hr.room_type,
    hr.beds,
    hr.bed_type,
    hr.price_per_night,
    hr.currency,
    hr.description                 AS room_description
FROM hotels h
JOIN hotel_cities hc ON hc.city_code = h.city_code
JOIN hotel_rooms hr   ON hr.hotel_id  = h.hotel_id
ORDER BY h.city_code, h.distance_km, hr.price_per_night;

-- -------------------------
-- INDEXES
-- -------------------------
CREATE INDEX idx_routes_origin       ON routes(origin_iata);
CREATE INDEX idx_routes_destination  ON routes(destination_iata);
CREATE INDEX idx_schedules_route     ON flight_schedules(route_id);
CREATE INDEX idx_schedules_carrier   ON flight_schedules(carrier_code);
CREATE INDEX idx_stops_schedule      ON flight_stops(schedule_id);
CREATE INDEX idx_hotels_city         ON hotels(city_code);
CREATE INDEX idx_hotel_rooms_hotel   ON hotel_rooms(hotel_id);
