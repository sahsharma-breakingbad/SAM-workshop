-- =============================================================
-- Amadeus Travel Data — PostgreSQL Seed Data (v2)
-- Full data including flight schedules, stops, hotel rooms
-- =============================================================

-- Airlines
INSERT INTO airlines (carrier_code, name) VALUES
    ('SQ', 'SINGAPORE AIRLINES'),
    ('QF', 'QANTAS'),
    ('BA', 'BRITISH AIRWAYS'),
    ('EK', 'EMIRATES'),
    ('AA', 'AMERICAN AIRLINES'),
    ('UA', 'UNITED AIRLINES'),
    ('LH', 'LUFTHANSA'),
    ('AF', 'AIR FRANCE'),
    ('CX', 'CATHAY PACIFIC'),
    ('JL', 'JAPAN AIRLINES'),
    ('TK', 'TURKISH AIRLINES'),
    ('NH', 'ANA - ALL NIPPON AIRWAYS'),
    ('AI', 'AIR INDIA'),
    ('6E', 'INDIGO');

-- Aircraft types
INSERT INTO aircraft_types (aircraft_code, name) VALUES
    ('359', 'AIRBUS A350-900'),
    ('77W', 'BOEING 777-300ER'),
    ('789', 'BOEING 787-9'),
    ('388', 'AIRBUS A380-800'),
    ('321', 'AIRBUS A321'),
    ('738', 'BOEING 737-800'),
    ('320', 'AIRBUS A320'),
    ('744', 'BOEING 747-400');

-- Airports
INSERT INTO airports (iata_code, name, city_code, city_name, country_code) VALUES
    ('SIN', 'CHANGI AIRPORT', 'SIN', 'SINGAPORE', 'SG'),
    ('LHR', 'HEATHROW AIRPORT', 'LON', 'LONDON', 'GB'),
    ('JFK', 'JOHN F KENNEDY INTL', 'NYC', 'NEW YORK', 'US'),
    ('LAX', 'LOS ANGELES INTL', 'LAX', 'LOS ANGELES', 'US'),
    ('SYD', 'SYDNEY KINGSFORD SMITH', 'SYD', 'SYDNEY', 'AU'),
    ('DXB', 'DUBAI INTL', 'DXB', 'DUBAI', 'AE'),
    ('CDG', 'CHARLES DE GAULLE', 'PAR', 'PARIS', 'FR'),
    ('HND', 'TOKYO HANEDA', 'TYO', 'TOKYO', 'JP'),
    ('NRT', 'NARITA INTL', 'TYO', 'TOKYO', 'JP'),
    ('BKK', 'SUVARNABHUMI AIRPORT', 'BKK', 'BANGKOK', 'TH'),
    ('HKG', 'HONG KONG INTL', 'HKG', 'HONG KONG', 'HK'),
    ('FRA', 'FRANKFURT MAIN', 'FRA', 'FRA', 'DE'),
    ('DEL', 'INDIRA GANDHI INTL', 'DEL', 'NEW DELHI', 'IN'),
    ('BOM', 'CHHATRAPATI SHIVAJI MAHARAJ INTL', 'BOM', 'MUMBAI', 'IN'),
    ('BLR', 'KEMPEGOWDA INTL', 'BLR', 'BANGALORE', 'IN');

-- Cabin fares
INSERT INTO cabin_fares (cabin, price_multiplier, fare_code, branded_fare, booking_class, checked_bags) VALUES
    ('ECONOMY', 1.0, 'YOWSGB', 'LITE', 'Y', 1),
    ('PREMIUM_ECONOMY', 1.9, 'WOWSGB', 'FLEX', 'W', 2),
    ('BUSINESS', 4.4, 'COWSGB', 'BUSINESS', 'C', 2),
    ('FIRST', 9.0, 'FOWSGB', 'SUITES', 'F', 3);

-- Routes
INSERT INTO routes (origin_iata, destination_iata, economy_base_price, premium_economy_base_price, business_base_price, first_base_price) VALUES
    ('SIN', 'LHR', 950, 1800, 4200, 8500),
    ('SIN', 'SYD', 620, 1200, 3100, 6500),
    ('JFK', 'LAX', 280, 520, 1100, 2200),
    ('LHR', 'CDG', 120, 230, 550, 1100),
    ('DXB', 'SIN', 480, 920, 2400, 5200),
    ('SIN', 'HND', 550, 1050, 2800, 6000),
    ('SIN', 'BKK', 180, 340, 820, 1800),
    ('HKG', 'LHR', 780, 1500, 3800, 7800),
    ('DEL', 'LHR', 650, 1250, 3200, 7000),
    ('BOM', 'LHR', 620, 1200, 3000, 6800),
    ('DEL', 'DXB', 180, 350, 900, 2000),
    ('BOM', 'SIN', 320, 620, 1600, 3500),
    ('DEL', 'SIN', 380, 720, 1800, 3800),
    ('BLR', 'SIN', 280, 540, 1400, 3200);

-- Flight schedules

INSERT INTO flight_schedules (route_id, flight_no, carrier_code, aircraft_code, departure_time, duration_minutes, terminal_dep, terminal_arr, available_seats)
SELECT id, 'SQ317', 'SQ', '359', '01:30:00', 810, '3', '2', 9
FROM routes WHERE origin_iata = 'SIN' AND destination_iata = 'LHR';

INSERT INTO flight_schedules (route_id, flight_no, carrier_code, aircraft_code, departure_time, duration_minutes, terminal_dep, terminal_arr, available_seats)
SELECT id, 'BA12', 'BA', '77W', '23:55:00', 780, '1', '5', 4
FROM routes WHERE origin_iata = 'SIN' AND destination_iata = 'LHR';

INSERT INTO flight_schedules (route_id, flight_no, carrier_code, aircraft_code, departure_time, duration_minutes, terminal_dep, terminal_arr, available_seats)
SELECT id, 'EK431', 'EK', '388', '03:45:00', 1110, '2', '3', 15
FROM routes WHERE origin_iata = 'SIN' AND destination_iata = 'LHR';

INSERT INTO flight_schedules (route_id, flight_no, carrier_code, aircraft_code, departure_time, duration_minutes, terminal_dep, terminal_arr, available_seats)
SELECT id, 'SQ221', 'SQ', '359', '08:20:00', 465, '3', '1', 9
FROM routes WHERE origin_iata = 'SIN' AND destination_iata = 'SYD';

INSERT INTO flight_schedules (route_id, flight_no, carrier_code, aircraft_code, departure_time, duration_minutes, terminal_dep, terminal_arr, available_seats)
SELECT id, 'QF82', 'QF', '789', '16:00:00', 480, '1', '1', 6
FROM routes WHERE origin_iata = 'SIN' AND destination_iata = 'SYD';

INSERT INTO flight_schedules (route_id, flight_no, carrier_code, aircraft_code, departure_time, duration_minutes, terminal_dep, terminal_arr, available_seats)
SELECT id, 'AA1', 'AA', '321', '07:00:00', 360, '8', '4', 20
FROM routes WHERE origin_iata = 'JFK' AND destination_iata = 'LAX';

INSERT INTO flight_schedules (route_id, flight_no, carrier_code, aircraft_code, departure_time, duration_minutes, terminal_dep, terminal_arr, available_seats)
SELECT id, 'UA177', 'UA', '738', '10:30:00', 355, '7', '7', 12
FROM routes WHERE origin_iata = 'JFK' AND destination_iata = 'LAX';

INSERT INTO flight_schedules (route_id, flight_no, carrier_code, aircraft_code, departure_time, duration_minutes, terminal_dep, terminal_arr, available_seats)
SELECT id, 'AA3', 'AA', '738', '18:00:00', 375, '8', '4', 8
FROM routes WHERE origin_iata = 'JFK' AND destination_iata = 'LAX';

INSERT INTO flight_schedules (route_id, flight_no, carrier_code, aircraft_code, departure_time, duration_minutes, terminal_dep, terminal_arr, available_seats)
SELECT id, 'BA306', 'BA', '320', '06:55:00', 75, '5', '2', 30
FROM routes WHERE origin_iata = 'LHR' AND destination_iata = 'CDG';

INSERT INTO flight_schedules (route_id, flight_no, carrier_code, aircraft_code, departure_time, duration_minutes, terminal_dep, terminal_arr, available_seats)
SELECT id, 'AF1681', 'AF', '320', '09:30:00', 80, '2', '2F', 22
FROM routes WHERE origin_iata = 'LHR' AND destination_iata = 'CDG';

INSERT INTO flight_schedules (route_id, flight_no, carrier_code, aircraft_code, departure_time, duration_minutes, terminal_dep, terminal_arr, available_seats)
SELECT id, 'EK432', 'EK', '388', '09:30:00', 420, '3', '1', 11
FROM routes WHERE origin_iata = 'DXB' AND destination_iata = 'SIN';

INSERT INTO flight_schedules (route_id, flight_no, carrier_code, aircraft_code, departure_time, duration_minutes, terminal_dep, terminal_arr, available_seats)
SELECT id, 'SQ496', 'SQ', '77W', '14:00:00', 435, '2', '3', 7
FROM routes WHERE origin_iata = 'DXB' AND destination_iata = 'SIN';

INSERT INTO flight_schedules (route_id, flight_no, carrier_code, aircraft_code, departure_time, duration_minutes, terminal_dep, terminal_arr, available_seats)
SELECT id, 'SQ637', 'SQ', '789', '00:05:00', 420, '3', '3', 9
FROM routes WHERE origin_iata = 'SIN' AND destination_iata = 'HND';

INSERT INTO flight_schedules (route_id, flight_no, carrier_code, aircraft_code, departure_time, duration_minutes, terminal_dep, terminal_arr, available_seats)
SELECT id, 'JL37', 'JL', '789', '11:20:00', 415, '1', '3', 14
FROM routes WHERE origin_iata = 'SIN' AND destination_iata = 'HND';

INSERT INTO flight_schedules (route_id, flight_no, carrier_code, aircraft_code, departure_time, duration_minutes, terminal_dep, terminal_arr, available_seats)
SELECT id, 'SQ705', 'SQ', '320', '07:30:00', 150, '3', '2', 25
FROM routes WHERE origin_iata = 'SIN' AND destination_iata = 'BKK';

INSERT INTO flight_schedules (route_id, flight_no, carrier_code, aircraft_code, departure_time, duration_minutes, terminal_dep, terminal_arr, available_seats)
SELECT id, 'TK67', 'TK', '321', '14:15:00', 165, '1', '2', 18
FROM routes WHERE origin_iata = 'SIN' AND destination_iata = 'BKK';

INSERT INTO flight_schedules (route_id, flight_no, carrier_code, aircraft_code, departure_time, duration_minutes, terminal_dep, terminal_arr, available_seats)
SELECT id, 'CX251', 'CX', '77W', '23:50:00', 735, '1', '3', 8
FROM routes WHERE origin_iata = 'HKG' AND destination_iata = 'LHR';

INSERT INTO flight_schedules (route_id, flight_no, carrier_code, aircraft_code, departure_time, duration_minutes, terminal_dep, terminal_arr, available_seats)
SELECT id, 'BA31', 'BA', '77W', '12:10:00', 750, '1', '5', 5
FROM routes WHERE origin_iata = 'HKG' AND destination_iata = 'LHR';

INSERT INTO flight_schedules (route_id, flight_no, carrier_code, aircraft_code, departure_time, duration_minutes, terminal_dep, terminal_arr, available_seats)
SELECT id, 'AI161', 'AI', '789', '01:30:00', 560, '3', '2', 12
FROM routes WHERE origin_iata = 'DEL' AND destination_iata = 'LHR';

INSERT INTO flight_schedules (route_id, flight_no, carrier_code, aircraft_code, departure_time, duration_minutes, terminal_dep, terminal_arr, available_seats)
SELECT id, 'EK511', 'EK', '388', '04:15:00', 650, '3', '3', 18
FROM routes WHERE origin_iata = 'DEL' AND destination_iata = 'LHR';

INSERT INTO flight_schedules (route_id, flight_no, carrier_code, aircraft_code, departure_time, duration_minutes, terminal_dep, terminal_arr, available_seats)
SELECT id, 'BA256', 'BA', '77W', '13:30:00', 585, '3', '5', 6
FROM routes WHERE origin_iata = 'DEL' AND destination_iata = 'LHR';

INSERT INTO flight_schedules (route_id, flight_no, carrier_code, aircraft_code, departure_time, duration_minutes, terminal_dep, terminal_arr, available_seats)
SELECT id, 'AI111', 'AI', '789', '02:35:00', 575, '2', '2', 10
FROM routes WHERE origin_iata = 'BOM' AND destination_iata = 'LHR';

INSERT INTO flight_schedules (route_id, flight_no, carrier_code, aircraft_code, departure_time, duration_minutes, terminal_dep, terminal_arr, available_seats)
SELECT id, 'BA138', 'BA', '77W', '13:00:00', 560, '2', '5', 7
FROM routes WHERE origin_iata = 'BOM' AND destination_iata = 'LHR';

INSERT INTO flight_schedules (route_id, flight_no, carrier_code, aircraft_code, departure_time, duration_minutes, terminal_dep, terminal_arr, available_seats)
SELECT id, 'AI995', 'AI', '321', '07:30:00', 200, '3', '1', 22
FROM routes WHERE origin_iata = 'DEL' AND destination_iata = 'DXB';

INSERT INTO flight_schedules (route_id, flight_no, carrier_code, aircraft_code, departure_time, duration_minutes, terminal_dep, terminal_arr, available_seats)
SELECT id, 'EK510', 'EK', '77W', '13:30:00', 195, '3', '3', 15
FROM routes WHERE origin_iata = 'DEL' AND destination_iata = 'DXB';

INSERT INTO flight_schedules (route_id, flight_no, carrier_code, aircraft_code, departure_time, duration_minutes, terminal_dep, terminal_arr, available_seats)
SELECT id, '6E1413', '6E', '321', '22:00:00', 205, '2', '2', 30
FROM routes WHERE origin_iata = 'DEL' AND destination_iata = 'DXB';

INSERT INTO flight_schedules (route_id, flight_no, carrier_code, aircraft_code, departure_time, duration_minutes, terminal_dep, terminal_arr, available_seats)
SELECT id, 'SQ424', 'SQ', '789', '09:10:00', 340, '2', '3', 11
FROM routes WHERE origin_iata = 'BOM' AND destination_iata = 'SIN';

INSERT INTO flight_schedules (route_id, flight_no, carrier_code, aircraft_code, departure_time, duration_minutes, terminal_dep, terminal_arr, available_seats)
SELECT id, 'AI357', 'AI', '789', '14:00:00', 330, '2', '1', 16
FROM routes WHERE origin_iata = 'BOM' AND destination_iata = 'SIN';

INSERT INTO flight_schedules (route_id, flight_no, carrier_code, aircraft_code, departure_time, duration_minutes, terminal_dep, terminal_arr, available_seats)
SELECT id, 'SQ406', 'SQ', '359', '10:15:00', 340, '3', '3', 9
FROM routes WHERE origin_iata = 'DEL' AND destination_iata = 'SIN';

INSERT INTO flight_schedules (route_id, flight_no, carrier_code, aircraft_code, departure_time, duration_minutes, terminal_dep, terminal_arr, available_seats)
SELECT id, 'AI382', 'AI', '789', '08:00:00', 350, '3', '1', 14
FROM routes WHERE origin_iata = 'DEL' AND destination_iata = 'SIN';

INSERT INTO flight_schedules (route_id, flight_no, carrier_code, aircraft_code, departure_time, duration_minutes, terminal_dep, terminal_arr, available_seats)
SELECT id, 'SQ517', 'SQ', '789', '09:55:00', 265, '2', '3', 13
FROM routes WHERE origin_iata = 'BLR' AND destination_iata = 'SIN';

INSERT INTO flight_schedules (route_id, flight_no, carrier_code, aircraft_code, departure_time, duration_minutes, terminal_dep, terminal_arr, available_seats)
SELECT id, 'AI549', 'AI', '320', '13:00:00', 260, '2', '1', 20
FROM routes WHERE origin_iata = 'BLR' AND destination_iata = 'SIN';

-- Flight stops (connecting flights only)

INSERT INTO flight_stops (schedule_id, stop_order, iata_code, arrival_time, departure_time, layover_duration)
SELECT id, 1, 'DXB', '06:30', '08:45', 'PT2H15M'
FROM flight_schedules WHERE flight_no = 'EK431';

INSERT INTO flight_stops (schedule_id, stop_order, iata_code, arrival_time, departure_time, layover_duration)
SELECT id, 1, 'DXB', '06:00', '08:00', 'PT2H00M'
FROM flight_schedules WHERE flight_no = 'EK511';

-- Hotel cities
INSERT INTO hotel_cities (city_code, city_name, country_code) VALUES
    ('SIN', 'SINGAPORE', 'SG'),
    ('LON', 'LONDON', 'GB'),
    ('NYC', 'NEW YORK', 'US'),
    ('SYD', 'SYDNEY', 'AU'),
    ('DXB', 'DUBAI', 'AE'),
    ('PAR', 'PARIS', 'FR'),
    ('DEL', 'NEW DELHI', 'IN'),
    ('BOM', 'MUMBAI', 'IN'),
    ('BLR', 'BANGALORE', 'IN'),
    ('TYO', 'TOKYO', 'JP');

-- Hotels
INSERT INTO hotels (hotel_id, name, city_code, star_rating, address, postal_code, country_code, latitude, longitude, distance_km, amenities) VALUES
    ('ADSINFL1', 'THE FULLERTON HOTEL SINGAPORE', 'SIN', 5, '1 FULLERTON SQUARE', '049178', 'SG', 1.2864, 103.8534, 0.9, '{SWIMMING_POOL,SPA,FITNESS_CENTER,WIFI,RESTAURANT,CONCIERGE}');
INSERT INTO hotels (hotel_id, name, city_code, star_rating, address, postal_code, country_code, latitude, longitude, distance_km, amenities) VALUES
    ('ADSINMA1', 'MARINA BAY SANDS HOTEL', 'SIN', 5, '10 BAYFRONT AVENUE', '018956', 'SG', 1.2839, 103.8607, 1.2, '{SWIMMING_POOL,SPA,FITNESS_CENTER,WIFI,RESTAURANT,CASINO}');
INSERT INTO hotels (hotel_id, name, city_code, star_rating, address, postal_code, country_code, latitude, longitude, distance_km, amenities) VALUES
    ('ADSINRA1', 'RAFFLES HOTEL SINGAPORE', 'SIN', 5, '1 BEACH ROAD', '189673', 'SG', 1.2952, 103.8527, 0.5, '{SPA,FITNESS_CENTER,WIFI,RESTAURANT,BAR}');
INSERT INTO hotels (hotel_id, name, city_code, star_rating, address, postal_code, country_code, latitude, longitude, distance_km, amenities) VALUES
    ('ADSINCO1', 'COMO METROPOLITAN SINGAPORE', 'SIN', 5, '1 UNITY STREET', '237983', 'SG', 1.3025, 103.8379, 2.1, '{SPA,FITNESS_CENTER,WIFI,RESTAURANT}');
INSERT INTO hotels (hotel_id, name, city_code, star_rating, address, postal_code, country_code, latitude, longitude, distance_km, amenities) VALUES
    ('ADSINHI1', 'HILTON SINGAPORE ORCHARD', 'SIN', 5, '333 ORCHARD ROAD', '238867', 'SG', 1.3041, 103.8321, 2.5, '{SWIMMING_POOL,FITNESS_CENTER,WIFI,RESTAURANT}');

INSERT INTO hotels (hotel_id, name, city_code, star_rating, address, postal_code, country_code, latitude, longitude, distance_km, amenities) VALUES
    ('ADLONSA1', 'THE SAVOY HOTEL', 'LON', 5, 'STRAND', 'WC2R 0EU', 'GB', 51.5107, -0.1204, 1.1, '{SPA,FITNESS_CENTER,WIFI,RESTAURANT,POOL}');
INSERT INTO hotels (hotel_id, name, city_code, star_rating, address, postal_code, country_code, latitude, longitude, distance_km, amenities) VALUES
    ('ADLONCL1', 'THE CLARIDGE''S', 'LON', 5, 'BROOK STREET, MAYFAIR', 'W1K 4HR', 'GB', 51.5122, -0.148, 0.8, '{SPA,FITNESS_CENTER,WIFI,RESTAURANT,BAR}');
INSERT INTO hotels (hotel_id, name, city_code, star_rating, address, postal_code, country_code, latitude, longitude, distance_km, amenities) VALUES
    ('ADLONHI1', 'HILTON LONDON METROPOLE', 'LON', 4, '225 EDGWARE ROAD', 'W2 1JU', 'GB', 51.5171, -0.1676, 3.2, '{FITNESS_CENTER,WIFI,RESTAURANT}');

INSERT INTO hotels (hotel_id, name, city_code, star_rating, address, postal_code, country_code, latitude, longitude, distance_km, amenities) VALUES
    ('ADNYCPL1', 'THE PLAZA NEW YORK', 'NYC', 5, '768 5TH AVENUE', '10019', 'US', 40.7644, -73.9747, 0.5, '{SPA,FITNESS_CENTER,WIFI,RESTAURANT,BAR}');
INSERT INTO hotels (hotel_id, name, city_code, star_rating, address, postal_code, country_code, latitude, longitude, distance_km, amenities) VALUES
    ('ADNYCMA1', 'NEW YORK MARRIOTT MARQUIS', 'NYC', 4, '1535 BROADWAY', '10036', 'US', 40.758, -73.9855, 1.2, '{SWIMMING_POOL,FITNESS_CENTER,WIFI,RESTAURANT}');
INSERT INTO hotels (hotel_id, name, city_code, star_rating, address, postal_code, country_code, latitude, longitude, distance_km, amenities) VALUES
    ('ADNYCST1', 'ST. REGIS NEW YORK', 'NYC', 5, '2 EAST 55TH STREET', '10022', 'US', 40.7613, -73.973, 0.3, '{SPA,FITNESS_CENTER,WIFI,RESTAURANT,BUTLER_SERVICE}');

INSERT INTO hotels (hotel_id, name, city_code, star_rating, address, postal_code, country_code, latitude, longitude, distance_km, amenities) VALUES
    ('ADSYDOP1', 'PARK HYATT SYDNEY', 'SYD', 5, '7 HICKSON ROAD, THE ROCKS', '2000', 'AU', -33.8567, 151.2099, 0.4, '{SWIMMING_POOL,SPA,FITNESS_CENTER,WIFI,RESTAURANT}');
INSERT INTO hotels (hotel_id, name, city_code, star_rating, address, postal_code, country_code, latitude, longitude, distance_km, amenities) VALUES
    ('ADSYDSH1', 'SHERATON GRAND SYDNEY HYDE PARK', 'SYD', 5, '161 ELIZABETH STREET', '2000', 'AU', -33.8723, 151.2099, 1.8, '{SWIMMING_POOL,SPA,FITNESS_CENTER,WIFI,RESTAURANT}');

INSERT INTO hotels (hotel_id, name, city_code, star_rating, address, postal_code, country_code, latitude, longitude, distance_km, amenities) VALUES
    ('ADDXBBR1', 'BURJ AL ARAB JUMEIRAH', 'DXB', 5, 'JUMEIRAH BEACH ROAD', '74925', 'AE', 25.1413, 55.1853, 15.0, '{PRIVATE_BEACH,SWIMMING_POOL,SPA,FITNESS_CENTER,WIFI,RESTAURANT,HELIPAD}');
INSERT INTO hotels (hotel_id, name, city_code, star_rating, address, postal_code, country_code, latitude, longitude, distance_km, amenities) VALUES
    ('ADDXBAT1', 'ATLANTIS THE PALM', 'DXB', 5, 'CRESCENT ROAD, THE PALM', '74915', 'AE', 25.1303, 55.1171, 24.0, '{WATERPARK,PRIVATE_BEACH,SWIMMING_POOL,SPA,FITNESS_CENTER,WIFI,RESTAURANT,CASINO}');
INSERT INTO hotels (hotel_id, name, city_code, star_rating, address, postal_code, country_code, latitude, longitude, distance_km, amenities) VALUES
    ('ADDXBAD1', 'ADDRESS DOWNTOWN DUBAI', 'DXB', 5, 'DOWNTOWN DUBAI', '75888', 'AE', 25.1972, 55.2744, 1.2, '{SWIMMING_POOL,SPA,FITNESS_CENTER,WIFI,RESTAURANT}');

INSERT INTO hotels (hotel_id, name, city_code, star_rating, address, postal_code, country_code, latitude, longitude, distance_km, amenities) VALUES
    ('ADPARRI1', 'THE RITZ PARIS', 'PAR', 5, '15 PLACE VENDÔME', '75001', 'FR', 48.8687, 2.3303, 0.6, '{SPA,SWIMMING_POOL,FITNESS_CENTER,WIFI,RESTAURANT,BAR}');
INSERT INTO hotels (hotel_id, name, city_code, star_rating, address, postal_code, country_code, latitude, longitude, distance_km, amenities) VALUES
    ('ADPARLE1', 'LE MEURICE', 'PAR', 5, '228 RUE DE RIVOLI', '75001', 'FR', 48.8645, 2.33, 0.4, '{SPA,FITNESS_CENTER,WIFI,RESTAURANT}');

INSERT INTO hotels (hotel_id, name, city_code, star_rating, address, postal_code, country_code, latitude, longitude, distance_km, amenities) VALUES
    ('ADDELOB1', 'THE OBEROI NEW DELHI', 'DEL', 5, 'DR ZAKIR HUSSAIN MARG', '110003', 'IN', 28.5981, 77.2389, 0.8, '{SWIMMING_POOL,SPA,FITNESS_CENTER,WIFI,RESTAURANT,CONCIERGE}');
INSERT INTO hotels (hotel_id, name, city_code, star_rating, address, postal_code, country_code, latitude, longitude, distance_km, amenities) VALUES
    ('ADDELTJ1', 'TAJ MAHAL HOTEL NEW DELHI', 'DEL', 5, '1 MANSINGH ROAD', '110011', 'IN', 28.6015, 77.222, 2.1, '{SWIMMING_POOL,SPA,FITNESS_CENTER,WIFI,RESTAURANT,BAR}');
INSERT INTO hotels (hotel_id, name, city_code, star_rating, address, postal_code, country_code, latitude, longitude, distance_km, amenities) VALUES
    ('ADDELLI1', 'THE LEELA PALACE NEW DELHI', 'DEL', 5, 'DIPLOMATIC ENCLAVE, CHANAKYAPURI', '110023', 'IN', 28.5973, 77.1839, 6.5, '{SWIMMING_POOL,SPA,FITNESS_CENTER,WIFI,RESTAURANT,BUTLER_SERVICE}');
INSERT INTO hotels (hotel_id, name, city_code, star_rating, address, postal_code, country_code, latitude, longitude, distance_km, amenities) VALUES
    ('ADDELITC1', 'ITC MAURYA NEW DELHI', 'DEL', 5, 'SARDAR PATEL MARG, DIPLOMATIC ENCLAVE', '110021', 'IN', 28.5994, 77.1735, 7.2, '{SWIMMING_POOL,SPA,FITNESS_CENTER,WIFI,RESTAURANT}');

INSERT INTO hotels (hotel_id, name, city_code, star_rating, address, postal_code, country_code, latitude, longitude, distance_km, amenities) VALUES
    ('ADBOMTJ1', 'TAJ MAHAL PALACE MUMBAI', 'BOM', 5, 'APOLLO BUNDER', '400001', 'IN', 18.922, 72.8332, 0.3, '{SWIMMING_POOL,SPA,FITNESS_CENTER,WIFI,RESTAURANT,BAR,CONCIERGE}');
INSERT INTO hotels (hotel_id, name, city_code, star_rating, address, postal_code, country_code, latitude, longitude, distance_km, amenities) VALUES
    ('ADBOMOB1', 'THE OBEROI MUMBAI', 'BOM', 5, 'NARIMAN POINT', '400021', 'IN', 18.9245, 72.823, 1.5, '{SWIMMING_POOL,SPA,FITNESS_CENTER,WIFI,RESTAURANT}');
INSERT INTO hotels (hotel_id, name, city_code, star_rating, address, postal_code, country_code, latitude, longitude, distance_km, amenities) VALUES
    ('ADBOMFS1', 'FOUR SEASONS HOTEL MUMBAI', 'BOM', 5, '1/136 DR E MOSES ROAD, WORLI', '400018', 'IN', 19.0176, 72.8178, 4.2, '{SWIMMING_POOL,SPA,FITNESS_CENTER,WIFI,RESTAURANT,BAR}');

INSERT INTO hotels (hotel_id, name, city_code, star_rating, address, postal_code, country_code, latitude, longitude, distance_km, amenities) VALUES
    ('ADBLRLL1', 'THE LEELA PALACE BANGALORE', 'BLR', 5, '23 KODIHALLI, HAL AIRPORT ROAD', '560008', 'IN', 12.96, 77.648, 9.5, '{SWIMMING_POOL,SPA,FITNESS_CENTER,WIFI,RESTAURANT,BUTLER_SERVICE}');
INSERT INTO hotels (hotel_id, name, city_code, star_rating, address, postal_code, country_code, latitude, longitude, distance_km, amenities) VALUES
    ('ADBLRITC1', 'ITC GARDENIA BANGALORE', 'BLR', 5, '1 RESIDENCY ROAD', '560025', 'IN', 12.9716, 77.6006, 2.3, '{SWIMMING_POOL,SPA,FITNESS_CENTER,WIFI,RESTAURANT}');
INSERT INTO hotels (hotel_id, name, city_code, star_rating, address, postal_code, country_code, latitude, longitude, distance_km, amenities) VALUES
    ('ADBLROB1', 'THE OBEROI BANGALORE', 'BLR', 5, '37-39 MAHATMA GANDHI ROAD', '560001', 'IN', 12.9759, 77.6074, 1.1, '{SWIMMING_POOL,SPA,FITNESS_CENTER,WIFI,RESTAURANT}');

INSERT INTO hotels (hotel_id, name, city_code, star_rating, address, postal_code, country_code, latitude, longitude, distance_km, amenities) VALUES
    ('ADTYOPA1', 'PARK HYATT TOKYO', 'TYO', 5, '3-7-1-2 NISHI-SHINJUKU', '163-1055', 'JP', 35.6877, 139.6902, 8.0, '{SWIMMING_POOL,SPA,FITNESS_CENTER,WIFI,RESTAURANT,BAR}');
INSERT INTO hotels (hotel_id, name, city_code, star_rating, address, postal_code, country_code, latitude, longitude, distance_km, amenities) VALUES
    ('ADTYOMA1', 'THE PALACE HOTEL TOKYO', 'TYO', 5, '1-1-1 MARUNOUCHI', '100-0005', 'JP', 35.6855, 139.7594, 1.5, '{SWIMMING_POOL,SPA,FITNESS_CENTER,WIFI,RESTAURANT}');

-- Hotel rooms
INSERT INTO hotel_rooms (hotel_id, room_type, beds, bed_type, price_per_night, currency, description) VALUES
    ('ADSINFL1', 'DELUXE_ROOM', 1, 'KING', 420, 'USD', 'Deluxe Room with heritage courtyard view');
INSERT INTO hotel_rooms (hotel_id, room_type, beds, bed_type, price_per_night, currency, description) VALUES
    ('ADSINFL1', 'SUITE', 1, 'KING', 850, 'USD', 'Grand Suite with city and bay views');
INSERT INTO hotel_rooms (hotel_id, room_type, beds, bed_type, price_per_night, currency, description) VALUES
    ('ADSINMA1', 'DELUXE_ROOM', 1, 'KING', 480, 'USD', 'Deluxe Room with Marina Bay view');
INSERT INTO hotel_rooms (hotel_id, room_type, beds, bed_type, price_per_night, currency, description) VALUES
    ('ADSINMA1', 'PREMIER_ROOM', 1, 'KING', 650, 'USD', 'Premier Room with Sands SkyPark access');
INSERT INTO hotel_rooms (hotel_id, room_type, beds, bed_type, price_per_night, currency, description) VALUES
    ('ADSINMA1', 'SUITE', 1, 'KING', 1200, 'USD', 'Chairman Suite with panoramic city views');
INSERT INTO hotel_rooms (hotel_id, room_type, beds, bed_type, price_per_night, currency, description) VALUES
    ('ADSINRA1', 'SUITE', 1, 'KING', 900, 'USD', 'Courtyard Suite with colonial garden view');
INSERT INTO hotel_rooms (hotel_id, room_type, beds, bed_type, price_per_night, currency, description) VALUES
    ('ADSINRA1', 'SUITE', 2, 'DOUBLE', 750, 'USD', 'Palm Court Suite with tropical garden views');
INSERT INTO hotel_rooms (hotel_id, room_type, beds, bed_type, price_per_night, currency, description) VALUES
    ('ADSINCO1', 'STANDARD_ROOM', 1, 'QUEEN', 280, 'USD', 'Superior Room with city views');
INSERT INTO hotel_rooms (hotel_id, room_type, beds, bed_type, price_per_night, currency, description) VALUES
    ('ADSINCO1', 'DELUXE_ROOM', 1, 'KING', 380, 'USD', 'Deluxe Room with balcony');
INSERT INTO hotel_rooms (hotel_id, room_type, beds, bed_type, price_per_night, currency, description) VALUES
    ('ADSINHI1', 'STANDARD_ROOM', 1, 'KING', 220, 'USD', 'Deluxe Room');
INSERT INTO hotel_rooms (hotel_id, room_type, beds, bed_type, price_per_night, currency, description) VALUES
    ('ADSINHI1', 'DELUXE_ROOM', 2, 'DOUBLE', 260, 'USD', 'Twin Room');

INSERT INTO hotel_rooms (hotel_id, room_type, beds, bed_type, price_per_night, currency, description) VALUES
    ('ADLONSA1', 'STANDARD_ROOM', 1, 'KING', 520, 'USD', 'Classic Room with river view');
INSERT INTO hotel_rooms (hotel_id, room_type, beds, bed_type, price_per_night, currency, description) VALUES
    ('ADLONSA1', 'SUITE', 1, 'KING', 1400, 'USD', 'River Suite');
INSERT INTO hotel_rooms (hotel_id, room_type, beds, bed_type, price_per_night, currency, description) VALUES
    ('ADLONCL1', 'CLASSIC_ROOM', 1, 'KING', 680, 'USD', 'Classic Room with Art Deco design');
INSERT INTO hotel_rooms (hotel_id, room_type, beds, bed_type, price_per_night, currency, description) VALUES
    ('ADLONCL1', 'SUITE', 1, 'KING', 2200, 'USD', 'Royal Suite');
INSERT INTO hotel_rooms (hotel_id, room_type, beds, bed_type, price_per_night, currency, description) VALUES
    ('ADLONHI1', 'STANDARD_ROOM', 1, 'DOUBLE', 180, 'USD', 'Standard Room');
INSERT INTO hotel_rooms (hotel_id, room_type, beds, bed_type, price_per_night, currency, description) VALUES
    ('ADLONHI1', 'EXECUTIVE_ROOM', 1, 'KING', 260, 'USD', 'Executive Room with lounge access');

INSERT INTO hotel_rooms (hotel_id, room_type, beds, bed_type, price_per_night, currency, description) VALUES
    ('ADNYCPL1', 'STANDARD_ROOM', 1, 'KING', 750, 'USD', 'Classic Room with Central Park view');
INSERT INTO hotel_rooms (hotel_id, room_type, beds, bed_type, price_per_night, currency, description) VALUES
    ('ADNYCPL1', 'SUITE', 1, 'KING', 2500, 'USD', 'Eloise Suite');
INSERT INTO hotel_rooms (hotel_id, room_type, beds, bed_type, price_per_night, currency, description) VALUES
    ('ADNYCMA1', 'STANDARD_ROOM', 1, 'KING', 380, 'USD', 'Times Square View Room');
INSERT INTO hotel_rooms (hotel_id, room_type, beds, bed_type, price_per_night, currency, description) VALUES
    ('ADNYCMA1', 'DELUXE_ROOM', 2, 'DOUBLE', 420, 'USD', 'Double Room City View');
INSERT INTO hotel_rooms (hotel_id, room_type, beds, bed_type, price_per_night, currency, description) VALUES
    ('ADNYCST1', 'DELUXE_ROOM', 1, 'KING', 920, 'USD', 'Deluxe Room');
INSERT INTO hotel_rooms (hotel_id, room_type, beds, bed_type, price_per_night, currency, description) VALUES
    ('ADNYCST1', 'SUITE', 1, 'KING', 3200, 'USD', 'Presidential Suite');

INSERT INTO hotel_rooms (hotel_id, room_type, beds, bed_type, price_per_night, currency, description) VALUES
    ('ADSYDOP1', 'PARK_ROOM', 1, 'KING', 680, 'USD', 'Park Room with Opera House view');
INSERT INTO hotel_rooms (hotel_id, room_type, beds, bed_type, price_per_night, currency, description) VALUES
    ('ADSYDOP1', 'SUITE', 1, 'KING', 1800, 'USD', 'Opera Suite');
INSERT INTO hotel_rooms (hotel_id, room_type, beds, bed_type, price_per_night, currency, description) VALUES
    ('ADSYDSH1', 'STANDARD_ROOM', 1, 'KING', 290, 'USD', 'Superior Room');
INSERT INTO hotel_rooms (hotel_id, room_type, beds, bed_type, price_per_night, currency, description) VALUES
    ('ADSYDSH1', 'DELUXE_ROOM', 1, 'KING', 380, 'USD', 'Deluxe Room with park view');

INSERT INTO hotel_rooms (hotel_id, room_type, beds, bed_type, price_per_night, currency, description) VALUES
    ('ADDXBBR1', 'SUITE', 1, 'KING', 2800, 'USD', 'Deluxe Suite with Arabian Gulf view');
INSERT INTO hotel_rooms (hotel_id, room_type, beds, bed_type, price_per_night, currency, description) VALUES
    ('ADDXBBR1', 'ROYAL_SUITE', 1, 'KING', 8500, 'USD', 'Royal Suite with private butler');
INSERT INTO hotel_rooms (hotel_id, room_type, beds, bed_type, price_per_night, currency, description) VALUES
    ('ADDXBAT1', 'CORAL_ROOM', 1, 'KING', 480, 'USD', 'Coral Room with lagoon view');
INSERT INTO hotel_rooms (hotel_id, room_type, beds, bed_type, price_per_night, currency, description) VALUES
    ('ADDXBAT1', 'TERRACE_SUITE', 1, 'KING', 1100, 'USD', 'Terrace Suite with Palm view');
INSERT INTO hotel_rooms (hotel_id, room_type, beds, bed_type, price_per_night, currency, description) VALUES
    ('ADDXBAD1', 'PREMIER_ROOM', 1, 'KING', 380, 'USD', 'Premier Room with Burj Khalifa view');
INSERT INTO hotel_rooms (hotel_id, room_type, beds, bed_type, price_per_night, currency, description) VALUES
    ('ADDXBAD1', 'SUITE', 1, 'KING', 950, 'USD', 'Suite with panoramic views');

INSERT INTO hotel_rooms (hotel_id, room_type, beds, bed_type, price_per_night, currency, description) VALUES
    ('ADPARRI1', 'CLASSIC_ROOM', 1, 'KING', 1100, 'USD', 'Classic Room');
INSERT INTO hotel_rooms (hotel_id, room_type, beds, bed_type, price_per_night, currency, description) VALUES
    ('ADPARRI1', 'SUITE', 1, 'KING', 4500, 'USD', 'Imperial Suite');
INSERT INTO hotel_rooms (hotel_id, room_type, beds, bed_type, price_per_night, currency, description) VALUES
    ('ADPARLE1', 'DELUXE_ROOM', 1, 'KING', 950, 'USD', 'Deluxe Room with garden view');
INSERT INTO hotel_rooms (hotel_id, room_type, beds, bed_type, price_per_night, currency, description) VALUES
    ('ADPARLE1', 'SUITE', 1, 'KING', 3800, 'USD', 'Belle Etoile Suite');

INSERT INTO hotel_rooms (hotel_id, room_type, beds, bed_type, price_per_night, currency, description) VALUES
    ('ADDELOB1', 'LUXURY_ROOM', 1, 'KING', 480, 'USD', 'Luxury Room with city views');
INSERT INTO hotel_rooms (hotel_id, room_type, beds, bed_type, price_per_night, currency, description) VALUES
    ('ADDELOB1', 'SUITE', 1, 'KING', 1200, 'USD', 'Oberoi Suite with Humayun''s Tomb view');
INSERT INTO hotel_rooms (hotel_id, room_type, beds, bed_type, price_per_night, currency, description) VALUES
    ('ADDELTJ1', 'SUPERIOR_ROOM', 1, 'KING', 350, 'USD', 'Superior Room');
INSERT INTO hotel_rooms (hotel_id, room_type, beds, bed_type, price_per_night, currency, description) VALUES
    ('ADDELTJ1', 'LUXURY_ROOM', 1, 'KING', 450, 'USD', 'Luxury Room with garden view');
INSERT INTO hotel_rooms (hotel_id, room_type, beds, bed_type, price_per_night, currency, description) VALUES
    ('ADDELTJ1', 'SUITE', 1, 'KING', 980, 'USD', 'Luxury Suite');
INSERT INTO hotel_rooms (hotel_id, room_type, beds, bed_type, price_per_night, currency, description) VALUES
    ('ADDELLI1', 'DELUXE_ROOM', 1, 'KING', 520, 'USD', 'Deluxe Room');
INSERT INTO hotel_rooms (hotel_id, room_type, beds, bed_type, price_per_night, currency, description) VALUES
    ('ADDELLI1', 'SUITE', 1, 'KING', 1400, 'USD', 'Royal Suite');
INSERT INTO hotel_rooms (hotel_id, room_type, beds, bed_type, price_per_night, currency, description) VALUES
    ('ADDELITC1', 'CLASSIC_ROOM', 1, 'KING', 280, 'USD', 'Classic Room');
INSERT INTO hotel_rooms (hotel_id, room_type, beds, bed_type, price_per_night, currency, description) VALUES
    ('ADDELITC1', 'EXECUTIVE_ROOM', 1, 'KING', 380, 'USD', 'Executive Club Room');

INSERT INTO hotel_rooms (hotel_id, room_type, beds, bed_type, price_per_night, currency, description) VALUES
    ('ADBOMTJ1', 'SUPERIOR_ROOM', 1, 'KING', 380, 'USD', 'Superior Room with harbour view');
INSERT INTO hotel_rooms (hotel_id, room_type, beds, bed_type, price_per_night, currency, description) VALUES
    ('ADBOMTJ1', 'GRAND_LUXURY_ROOM', 1, 'KING', 580, 'USD', 'Grand Luxury Room in the Palace wing');
INSERT INTO hotel_rooms (hotel_id, room_type, beds, bed_type, price_per_night, currency, description) VALUES
    ('ADBOMTJ1', 'SUITE', 1, 'KING', 1500, 'USD', 'Sea Lounge Suite');
INSERT INTO hotel_rooms (hotel_id, room_type, beds, bed_type, price_per_night, currency, description) VALUES
    ('ADBOMOB1', 'DELUXE_ROOM', 1, 'KING', 420, 'USD', 'Deluxe Room with Arabian Sea view');
INSERT INTO hotel_rooms (hotel_id, room_type, beds, bed_type, price_per_night, currency, description) VALUES
    ('ADBOMOB1', 'SUITE', 1, 'KING', 1100, 'USD', 'Luxury Suite');
INSERT INTO hotel_rooms (hotel_id, room_type, beds, bed_type, price_per_night, currency, description) VALUES
    ('ADBOMFS1', 'SUPERIOR_ROOM', 1, 'KING', 320, 'USD', 'Superior Room');
INSERT INTO hotel_rooms (hotel_id, room_type, beds, bed_type, price_per_night, currency, description) VALUES
    ('ADBOMFS1', 'DELUXE_ROOM', 1, 'KING', 420, 'USD', 'Deluxe Room with Bandra-Worli Sea Link view');

INSERT INTO hotel_rooms (hotel_id, room_type, beds, bed_type, price_per_night, currency, description) VALUES
    ('ADBLRLL1', 'DELUXE_ROOM', 1, 'KING', 320, 'USD', 'Deluxe Room with garden view');
INSERT INTO hotel_rooms (hotel_id, room_type, beds, bed_type, price_per_night, currency, description) VALUES
    ('ADBLRLL1', 'SUITE', 1, 'KING', 950, 'USD', 'Royal Suite');
INSERT INTO hotel_rooms (hotel_id, room_type, beds, bed_type, price_per_night, currency, description) VALUES
    ('ADBLRITC1', 'LUXURY_ROOM', 1, 'KING', 280, 'USD', 'Luxury Room');
INSERT INTO hotel_rooms (hotel_id, room_type, beds, bed_type, price_per_night, currency, description) VALUES
    ('ADBLRITC1', 'EXECUTIVE_ROOM', 1, 'KING', 360, 'USD', 'Executive Club Room');
INSERT INTO hotel_rooms (hotel_id, room_type, beds, bed_type, price_per_night, currency, description) VALUES
    ('ADBLROB1', 'LUXURY_ROOM', 1, 'KING', 350, 'USD', 'Luxury Room');
INSERT INTO hotel_rooms (hotel_id, room_type, beds, bed_type, price_per_night, currency, description) VALUES
    ('ADBLROB1', 'SUITE', 1, 'KING', 1000, 'USD', 'Kohinoor Suite');

INSERT INTO hotel_rooms (hotel_id, room_type, beds, bed_type, price_per_night, currency, description) VALUES
    ('ADTYOPA1', 'PARK_ROOM', 1, 'KING', 620, 'USD', 'Park Room with Mount Fuji view');
INSERT INTO hotel_rooms (hotel_id, room_type, beds, bed_type, price_per_night, currency, description) VALUES
    ('ADTYOPA1', 'SUITE', 1, 'KING', 2100, 'USD', 'Presidential Suite');
INSERT INTO hotel_rooms (hotel_id, room_type, beds, bed_type, price_per_night, currency, description) VALUES
    ('ADTYOMA1', 'DELUXE_ROOM', 1, 'KING', 540, 'USD', 'Deluxe Room with Imperial Palace view');
INSERT INTO hotel_rooms (hotel_id, room_type, beds, bed_type, price_per_night, currency, description) VALUES
    ('ADTYOMA1', 'SUITE', 1, 'KING', 1600, 'USD', 'Palace Suite');

