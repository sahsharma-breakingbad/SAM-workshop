#!/usr/bin/env python3
"""
Generate comprehensive world travel data SQL from OpenFlights open data.
Produces postgres/03_world_data.sql with ~300 airports, ~200 airlines,
~8000-12000 routes, flight schedules, and hotels for every airport city.

Usage: python3 generate_world_data.py
Output: postgres/03_world_data.sql
"""
import csv
import math
import random
import hashlib
import os
import re
from collections import defaultdict, Counter

DATA_DIR = os.path.join(os.path.dirname(__file__), "openflights")
OUT_FILE = os.path.join(os.path.dirname(__file__), "03_world_data.sql")

# Deterministic seed for reproducible data
random.seed(42)

TOP_N_AIRPORTS = 300

# ── helpers ──────────────────────────────────────────────────────────────────

def sq(s):
    return str(s).replace("'", "''")

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
    return 2 * R * math.asin(math.sqrt(a))

def flight_hash(s, n=4):
    """Deterministic n-digit number from string."""
    h = int(hashlib.md5(s.encode()).hexdigest(), 16)
    return str(h % (10**n)).zfill(n)

def duration_from_km(km):
    """Estimated flight duration in minutes."""
    return max(60, round(km / 850 * 60))

def aircraft_for_duration(minutes):
    if minutes < 180:
        return random.choice(["320", "321", "738"])
    elif minutes < 480:
        return random.choice(["789", "359", "321"])
    else:
        return random.choice(["77W", "388", "789"])

def price_from_km(km):
    """Base economy price USD from great-circle distance."""
    return max(50, round(km * 0.12))

# Airports that get multi-terminal assignments
MULTI_TERMINAL = {
    "LHR": ["1","2","3","4","5"],
    "LGW": ["N","S"],
    "CDG": ["1","2","3"],
    "JFK": ["1","2","4","5","7","8"],
    "LAX": ["1","2","3","4","5","6","7","8","B","D"],
    "ORD": ["1","2","3","5"],
    "ATL": ["D","E","F","T"],
    "DXB": ["1","2","3"],
    "SIN": ["1","2","3"],
    "HKG": ["1"],
    "PEK": ["1","2","3"],
    "PVG": ["1","2"],
    "NRT": ["1","2","3"],
    "HND": ["1","2","3","SAT"],
    "FRA": ["1","2"],
    "MUC": ["1","2","M"],
    "AMS": ["1","2","3"],
    "MAD": ["1","2","3","4"],
    "BCN": ["1","2"],
    "FCO": ["1","2","3"],
    "IST": ["I"],
    "BOM": ["1","2"],
    "DEL": ["1","2","3"],
    "SYD": ["1"],
    "MEL": ["1","2","3","4"],
    "DFW": ["A","B","C","D","E"],
    "MIA": ["D","E","F","G","H","J"],
    "BOS": ["A","B","C","E"],
    "SEA": ["A","B","C","D","N","S"],
    "SFO": ["A","B","C","D","E","F","G","I"],
    "IAH": ["A","B","C","D","E"],
    "GRU": ["1","2","3"],
    "EZE": ["A","B"],
    "YYZ": ["1","3"],
    "YVR": ["D","I"],
    "CPT": ["A","B"],
    "JNB": ["A","B"],
    "CAI": ["1","2","3"],
    "DUB": ["1","2"],
    "MAN": ["1","2","3"],
    "ZRH": ["A","B","E"],
    "VIE": ["A","B","C","D"],
    "BRU": ["A","B","T"],
    "HEL": ["1","2"],
    "ARN": ["2","5"],
    "OSL": ["D","E","F","G"],
    "CPH": ["1","2","3"],
    "WAW": ["A","B"],
    "PRG": ["1","2"],
    "BUD": ["2A","2B"],
    "ATH": ["A"],
    "LIS": ["1","2"],
    "OPO": ["1","2"],
    "KUL": ["M","S"],
    "BKK": ["S1","S2"],
    "CGK": ["1","2","3"],
    "MNL": ["1","2","3"],
    "ICN": ["1","2"],
    "GMP": ["D","I"],
    "TPE": ["1","2"],
    "KHH": ["1"],
    "SGN": ["T1","T2"],
    "HAN": ["T1","T2"],
    "CCU": ["2"],
    "MAA": ["D","I"],
    "HYD": ["D","I"],
    "BLR": ["D","I"],
    "CMB": ["D","I"],
    "DAC": ["D","I"],
    "KTM": ["D","I"],
    "AUH": ["A","B","C"],
    "DOH": ["D","E"],
    "KWI": ["1","2","3","4","5"],
    "MCT": ["1"],
    "AMM": ["1","2","3"],
    "BEY": ["1"],
    "TLV": ["1","3"],
    "ADD": ["T1","T2"],
    "NBO": ["1A","1B"],
    "LOS": ["D","I"],
    "ACC": ["1"],
    "ABV": ["D","I"],
    "TUN": ["D"],
    "CMN": ["1","2"],
    "ALG": ["1"],
    "HRE": ["I"],
    "DAR": ["D","I"],
    "LAD": ["4"],
    "MPM": ["D","I"],
    "AKL": ["D","I"],
    "CHC": ["D","I"],
    "MEX": ["1","2"],
    "CUN": ["2","3","4"],
    "BOG": ["E","P"],
    "LIM": ["T1","T2"],
    "SCL": ["D","I"],
    "GIG": ["A","B"],
    "SSA": ["D","I"],
    "FOR": ["D","I"],
}

# Price region multipliers for hotels
PRICE_REGIONS = {
    "US": 1.5, "GB": 1.4, "JP": 1.3, "AU": 1.3, "CH": 1.6, "NO": 1.5,
    "SE": 1.2, "DK": 1.3, "FR": 1.3, "DE": 1.2, "NL": 1.2, "BE": 1.1,
    "AT": 1.2, "IE": 1.2, "IT": 1.1, "ES": 1.0, "PT": 0.9,
    "SG": 1.2, "HK": 1.3, "AE": 1.2, "QA": 1.2, "KW": 1.1,
    "CN": 0.9, "KR": 1.0, "TW": 0.9, "NZ": 1.1,
    "IN": 0.6, "PK": 0.5, "BD": 0.4, "LK": 0.5, "NP": 0.4,
    "TH": 0.6, "MY": 0.6, "ID": 0.5, "PH": 0.5, "VN": 0.4,
    "BR": 0.7, "AR": 0.6, "CL": 0.7, "CO": 0.6, "PE": 0.6, "MX": 0.7,
    "EG": 0.5, "ZA": 0.6, "KE": 0.5, "NG": 0.5, "ET": 0.4,
    "MA": 0.5, "TN": 0.4, "DZ": 0.4,
    "TR": 0.7, "GR": 0.8, "PL": 0.7, "CZ": 0.7, "HU": 0.6,
}

HOTEL_AMENITY_SETS = [
    ["SWIMMING_POOL","SPA","FITNESS_CENTER","WIFI","RESTAURANT","CONCIERGE"],
    ["SWIMMING_POOL","FITNESS_CENTER","WIFI","RESTAURANT","BAR"],
    ["SPA","FITNESS_CENTER","WIFI","RESTAURANT"],
    ["FITNESS_CENTER","WIFI","RESTAURANT"],
    ["WIFI","RESTAURANT","BAR"],
    ["SWIMMING_POOL","SPA","FITNESS_CENTER","WIFI","RESTAURANT"],
]

ROOM_TEMPLATES = [
    ("STANDARD_ROOM","QUEEN",0.6,"Standard Room"),
    ("STANDARD_ROOM","KING",0.8,"Standard Room with city view"),
    ("DELUXE_ROOM","KING",1.0,"Deluxe Room"),
    ("DELUXE_ROOM","KING",1.2,"Deluxe Room with panoramic view"),
    ("SUITE","KING",2.2,"Executive Suite"),
    ("SUITE","KING",3.0,"Presidential Suite"),
    ("PREMIER_ROOM","KING",1.5,"Premier Room with lounge access"),
    ("SUPERIOR_ROOM","QUEEN",0.7,"Superior Room"),
    ("EXECUTIVE_ROOM","KING",1.4,"Executive Room"),
    ("TWIN_ROOM","DOUBLE",0.75,"Twin Room"),
    ("FAMILY_ROOM","DOUBLE",1.1,"Family Room"),
    ("JUNIOR_SUITE","KING",1.8,"Junior Suite with sitting area"),
]

HOTEL_PREFIXES = [
    "MARRIOTT","HILTON","SHERATON","WESTIN","HYATT REGENCY","PARK HYATT",
    "INTERCONTINENTAL","HOLIDAY INN","CROWNE PLAZA","RADISSON","SOFITEL",
    "NOVOTEL","IBIS","BEST WESTERN","MERCURE","PULLMAN","GRAND HYATT",
    "FOUR SEASONS","RITZ-CARLTON","ST. REGIS","W HOTEL","AUTOGRAPH",
    "RENAISSANCE","COURTYARD","FAIRFIELD","SPRINGHILL","RESIDENCE INN",
    "DOUBLETREE","EMBASSY SUITES","HAMPTON","COMFORT INN",
]

# ── load raw OpenFlights data ─────────────────────────────────────────────────

# airports.dat columns: ID, Name, City, Country(full name), IATA, ICAO, Lat, Lon, ...
# There is no ISO country code column — map from full country name.
COUNTRY_NAME_TO_ISO = {
    "Afghanistan":"AF","Albania":"AL","Algeria":"DZ","Angola":"AO","Argentina":"AR",
    "Armenia":"AM","Australia":"AU","Austria":"AT","Azerbaijan":"AZ","Bahrain":"BH",
    "Bangladesh":"BD","Belarus":"BY","Belgium":"BE","Bolivia":"BO","Bosnia and Herzegovina":"BA",
    "Botswana":"BW","Brazil":"BR","Bulgaria":"BG","Cambodia":"KH","Cameroon":"CM",
    "Canada":"CA","Chile":"CL","China":"CN","Colombia":"CO","Congo (Brazzaville)":"CG",
    "Congo (Kinshasa)":"CD","Costa Rica":"CR","Croatia":"HR","Cuba":"CU","Cyprus":"CY",
    "Czech Republic":"CZ","Czechia":"CZ","Denmark":"DK","Dominican Republic":"DO",
    "Ecuador":"EC","Egypt":"EG","El Salvador":"SV","Estonia":"EE","Ethiopia":"ET",
    "Finland":"FI","France":"FR","Georgia":"GE","Germany":"DE","Ghana":"GH","Greece":"GR",
    "Guatemala":"GT","Honduras":"HN","Hong Kong":"HK","Hungary":"HU","Iceland":"IS",
    "India":"IN","Indonesia":"ID","Iran":"IR","Iraq":"IQ","Ireland":"IE","Israel":"IL",
    "Italy":"IT","Ivory Coast":"CI","Jamaica":"JM","Japan":"JP","Jordan":"JO",
    "Kazakhstan":"KZ","Kenya":"KE","Kosovo":"XK","Kuwait":"KW","Kyrgyzstan":"KG",
    "Laos":"LA","Latvia":"LV","Lebanon":"LB","Libya":"LY","Lithuania":"LT",
    "Luxembourg":"LU","Macau":"MO","Madagascar":"MG","Malawi":"MW","Malaysia":"MY",
    "Maldives":"MV","Mali":"ML","Malta":"MT","Mauritius":"MU","Mexico":"MX",
    "Moldova":"MD","Mongolia":"MN","Montenegro":"ME","Morocco":"MA","Mozambique":"MZ",
    "Myanmar":"MM","Namibia":"NA","Nepal":"NP","Netherlands":"NL","New Zealand":"NZ",
    "Nicaragua":"NI","Nigeria":"NG","North Korea":"KP","North Macedonia":"MK",
    "Norway":"NO","Oman":"OM","Pakistan":"PK","Panama":"PA","Papua New Guinea":"PG",
    "Paraguay":"PY","Peru":"PE","Philippines":"PH","Poland":"PL","Portugal":"PT",
    "Puerto Rico":"PR","Qatar":"QA","Romania":"RO","Russia":"RU","Rwanda":"RW",
    "Saudi Arabia":"SA","Senegal":"SN","Serbia":"RS","Singapore":"SG","Slovakia":"SK",
    "Slovenia":"SI","Somalia":"SO","South Africa":"ZA","South Korea":"KR","South Sudan":"SS",
    "Spain":"ES","Sri Lanka":"LK","Sudan":"SD","Sweden":"SE","Switzerland":"CH",
    "Syria":"SY","Taiwan":"TW","Tajikistan":"TJ","Tanzania":"TZ","Thailand":"TH",
    "Tunisia":"TN","Turkey":"TR","Turkmenistan":"TM","Uganda":"UG","Ukraine":"UA",
    "United Arab Emirates":"AE","United Kingdom":"GB","United States":"US","Uruguay":"UY",
    "Uzbekistan":"UZ","Venezuela":"VE","Vietnam":"VN","Yemen":"YE","Zambia":"ZM",
    "Zimbabwe":"ZW","Bahamas":"BS","Barbados":"BB","Belize":"BZ","Benin":"BJ",
    "Bhutan":"BT","Burkina Faso":"BF","Burundi":"BI","Cape Verde":"CV",
    "Central African Republic":"CF","Chad":"TD","Comoros":"KM","Djibouti":"DJ",
    "Equatorial Guinea":"GQ","Eritrea":"ER","Eswatini":"SZ","Fiji":"FJ","Gabon":"GA",
    "Gambia":"GM","Guinea":"GN","Guinea-Bissau":"GW","Guyana":"GY","Haiti":"HT",
    "Kosovo":"XK","Lesotho":"LS","Liberia":"LR","Liechtenstein":"LI","Macedonia":"MK",
    "Malawi":"MW","Maldives":"MV","Marshall Islands":"MH","Mauritania":"MR",
    "Micronesia":"FM","Monaco":"MC","Myanmar":"MM","Niger":"NE","Palau":"PW",
    "Palestine":"PS","Papua New Guinea":"PG","Samoa":"WS","San Marino":"SM",
    "Sao Tome and Principe":"ST","Sierra Leone":"SL","Solomon Islands":"SB",
    "Suriname":"SR","Timor-Leste":"TL","Togo":"TG","Tonga":"TO","Trinidad and Tobago":"TT",
    "Turkmenistan":"TM","Tuvalu":"TV","Vanuatu":"VU","Vatican City":"VA",
    "Western Sahara":"EH","Antigua and Barbuda":"AG","Saint Kitts and Nevis":"KN",
    "Saint Lucia":"LC","Saint Vincent and the Grenadines":"VC","Grenada":"GD",
    "Dominica":"DM","Seychelles":"SC","Kiribati":"KI","Nauru":"NR","Niue":"NU",
    "Cook Islands":"CK","French Polynesia":"PF","New Caledonia":"NC","Guam":"GU",
    "Northern Mariana Islands":"MP","American Samoa":"AS","US Virgin Islands":"VI",
    "British Virgin Islands":"VG","Cayman Islands":"KY","Bermuda":"BM",
    "Turks and Caicos Islands":"TC","Aruba":"AW","Curacao":"CW","Sint Maarten":"SX",
    "French Guiana":"GF","Guadeloupe":"GP","Martinique":"MQ","Reunion":"RE",
    "Mayotte":"YT","Gibraltar":"GI","Faroe Islands":"FO","Greenland":"GL",
    "Azores":"PT","Canary Islands":"ES","Madeira":"PT",
}

def load_airports():
    """Returns dict iata -> {name, city, city_code, country, country_code, lat, lon}"""
    airports = {}
    with open(os.path.join(DATA_DIR, "airports.dat"), encoding="utf-8") as f:
        for row in csv.reader(f):
            if len(row) < 8:
                continue
            # columns: 0=ID, 1=Name, 2=City, 3=Country(full), 4=IATA, 5=ICAO, 6=Lat, 7=Lon
            iata = row[4].strip('"')
            if not iata or iata == r'\N' or len(iata) != 3:
                continue
            try:
                lat = float(row[6])
                lon = float(row[7])
            except (ValueError, IndexError):
                continue
            name = row[1].strip('"')
            city = row[2].strip('"').upper()
            country_full = row[3].strip('"')
            country_code = COUNTRY_NAME_TO_ISO.get(country_full, "")
            if not country_code:
                continue
            city_code = re.sub(r'[^A-Z]', '', city.upper())[:3].ljust(3, 'X')
            airports[iata] = {
                "name": name, "city": city, "city_code": city_code,
                "country": country_full, "country_code": country_code,
                "lat": lat, "lon": lon
            }
    return airports

def load_airlines():
    """Returns dict iata_2char -> name"""
    airlines = {}
    with open(os.path.join(DATA_DIR, "airlines.dat"), encoding="utf-8") as f:
        for row in csv.reader(f):
            if len(row) < 8:
                continue
            iata = row[3].strip('"')
            active = row[7].strip('"')
            if not iata or iata == r'\N' or len(iata) != 2:
                continue
            if active != 'Y':
                continue
            name = row[1].strip('"').upper()
            if name and name != r'\N':
                airlines[iata] = name
    return airlines

def load_routes():
    """Returns list of (airline_iata, origin_iata, dest_iata)"""
    routes = []
    with open(os.path.join(DATA_DIR, "routes.dat"), encoding="utf-8") as f:
        for row in csv.reader(f):
            if len(row) < 5:
                continue
            airline = row[0].strip('"')
            origin = row[2].strip('"')
            dest = row[4].strip('"')
            if (len(airline) == 2 and len(origin) == 3 and len(dest) == 3
                    and airline != r'\N' and origin != r'\N' and dest != r'\N'):
                routes.append((airline, origin, dest))
    return routes

# ── select top airports ───────────────────────────────────────────────────────

# Tourist/holiday destinations — always included regardless of route frequency
TOURIST_AIRPORTS = {
    # Southeast Asia islands & resorts
    "HKT",  # Phuket, Thailand
    "CNX",  # Chiang Mai, Thailand
    "DPS",  # Bali (Denpasar), Indonesia
    "LGK",  # Langkawi, Malaysia
    "PEN",  # Penang, Malaysia
    "CEB",  # Cebu, Philippines
    "MPH",  # Malay / Caticlan (Boracay), Philippines
    "TAG",  # Tagbilaran (Bohol), Philippines
    "REP",  # Siem Reap (Angkor Wat), Cambodia
    "PNH",  # Phnom Penh, Cambodia
    "VTE",  # Vientiane, Laos
    "RGN",  # Yangon (Rangoon), Myanmar
    # Indian Ocean
    "MLE",  # Male, Maldives
    "GAN",  # Addu Atoll, Maldives
    "SEZ",  # Mahé, Seychelles
    "MRU",  # Mauritius
    "RUN",  # Réunion
    "ZNZ",  # Zanzibar, Tanzania
    "HAH",  # Moroni, Comoros
    # South Pacific
    "PPT",  # Papeete (Tahiti), French Polynesia
    "BOB",  # Bora Bora, French Polynesia
    "NAN",  # Nadi, Fiji
    # Middle East / Egypt
    "LXR",  # Luxor, Egypt
    "SSH",  # Sharm El Sheikh, Egypt
    "HRG",  # Hurghada, Egypt
    # Mediterranean — Greek Islands
    "CFU",  # Corfu, Greece
    "JTR",  # Santorini, Greece
    "KGS",  # Kos, Greece
    "MJT",  # Mytilene (Lesbos), Greece
    "JMK",  # Mykonos, Greece
    "SKU",  # Skiathos, Greece
    "SMI",  # Samos, Greece
    # Mediterranean — Turkey resorts
    "AYT",  # Antalya, Turkey
    "DLM",  # Dalaman, Turkey
    "BJV",  # Bodrum, Turkey
    # Mediterranean — Croatia / Balkans
    "DBV",  # Dubrovnik, Croatia
    "SPU",  # Split, Croatia
    "TIV",  # Tivat, Montenegro
    "OHD",  # Ohrid, North Macedonia
    "VAR",  # Varna, Bulgaria
    # North Africa
    "RAK",  # Marrakech, Morocco
    "AGA",  # Agadir, Morocco
    "TNG",  # Tangier, Morocco
    "DJE",  # Djerba, Tunisia
    # Alps ski resorts
    "CMF",  # Chambéry (Alps), France
    "INN",  # Innsbruck, Austria
    "SZG",  # Salzburg, Austria
    # South Asia
    "KTM",  # Kathmandu, Nepal
    "CMB",  # Colombo, Sri Lanka
    # Australia leisure
    "OOL",  # Gold Coast, Australia
    "CNS",  # Cairns (Great Barrier Reef), Australia
    "DRW",  # Darwin, Australia
    # South America
    "CUZ",  # Cusco (Machu Picchu), Peru
    "IGR",  # Iguazú, Argentina
    "USH",  # Ushuaia (Patagonia), Argentina
    "PMC",  # Puerto Montt, Chile
    "GYE",  # Guayaquil, Ecuador
    "GPS",  # Galápagos, Ecuador
    "UIO",  # Quito, Ecuador
    "CTG",  # Cartagena, Colombia
    "SMR",  # Santa Marta, Colombia
    "NAT",  # Natal, Brazil
    "FOR",  # Fortaleza, Brazil
    "SSA",  # Salvador (Bahia), Brazil
    "GIG",  # Rio de Janeiro, Brazil
    # Caribbean
    "CUN",  # Cancún, Mexico
    "NAS",  # Nassau, Bahamas
    # Japan leisure
    "OKA",  # Okinawa, Japan
    "KIX",  # Osaka (Kyoto gateway), Japan
    "CTS",  # Sapporo, Japan
    "FUK",  # Fukuoka, Japan
    # Europe city-breaks & coastal
    "NCE",  # Nice, France
    "VCE",  # Venice, Italy
    "IBZ",  # Ibiza, Spain
    "PMI",  # Palma de Mallorca, Spain
    "TFS",  # Tenerife South, Spain
    "LPA",  # Gran Canaria, Spain
    "FUE",  # Fuerteventura, Spain
    "ACE",  # Lanzarote, Spain
    "FAO",  # Faro (Algarve), Portugal
    "OPO",  # Porto, Portugal
    "HER",  # Heraklion (Crete), Greece
    "RHO",  # Rhodes, Greece
    "SKG",  # Thessaloniki, Greece
}

# Resort/tourist hotel name prefixes
RESORT_PREFIXES = [
    "PARADISE BEACH RESORT","ANANTARA","BANYAN TREE","SIX SENSES","SONEVA",
    "COMO","AMAN","OBEROI","TAJ EXOTICA","CLUB MED","SANDALS","CONSTANCE",
    "FOUR SEASONS RESORT","SHANGRI-LA","CENTARA GRAND","CENTARA","AMARI",
    "SUNWAY","MÖVENPICK RESORT","IBEROTEL","ROBINSON CLUB","TUI BLUE",
    "CORAL BEACH RESORT","PALM BEACH RESORT","AZURE RESORT","LAGOON RESORT",
    "OCEAN VISTA","REEF RESORT","ISLAND HIDEAWAY","BALINESE RESORT",
    "SERENITY RESORT","SUNRISE RESORT","SUNSET VILLAS",
]

# Resort room templates
RESORT_ROOM_TEMPLATES = [
    ("GARDEN_VILLA",   "KING",   1.0, "Garden Villa with private pool"),
    ("BEACH_VILLA",    "KING",   1.8, "Beach Villa with direct ocean access"),
    ("WATER_BUNGALOW", "KING",   2.5, "Overwater Bungalow with glass floor panel"),
    ("OCEAN_SUITE",    "KING",   3.2, "Ocean Suite with infinity pool"),
    ("DELUXE_ROOM",    "KING",   0.7, "Deluxe Room with sea view"),
    ("SUPERIOR_ROOM",  "QUEEN",  0.5, "Superior Room with garden view"),
    ("POOL_SUITE",     "KING",   2.0, "Pool Suite with private plunge pool"),
    ("FAMILY_SUITE",   "DOUBLE", 1.4, "Family Suite sleeping up to 4 guests"),
    ("DIVE_LODGE",     "TWIN",   0.6, "Dive Lodge room with equipment storage"),
    ("RICE_TERRACE_VILLA","KING",1.2, "Villa overlooking rice terraces"),
    ("CLIFFTOP_SUITE", "KING",   2.8, "Clifftop Suite with panoramic ocean views"),
    ("JUNGLE_VILLA",   "KING",   1.5, "Jungle Villa with open-air bathroom"),
]

def select_top_airports(all_airports, all_routes, n=TOP_N_AIRPORTS):
    """Pick top n airports by route frequency, always including tourist destinations."""
    freq = Counter()
    for _, o, d in all_routes:
        if o in all_airports:
            freq[o] += 1
        if d in all_airports:
            freq[d] += 1
    selected = {iata for iata, _ in freq.most_common(n)}
    # Always include original mock airports and all tourist destinations
    selected |= {"SIN","LHR","JFK","LAX","SYD","DXB","CDG","HND","NRT",
                 "BKK","HKG","DEL","BOM","BLR"}
    selected |= TOURIST_AIRPORTS
    return {iata: all_airports[iata] for iata in selected if iata in all_airports}

# ── build deduplicated routes ─────────────────────────────────────────────────

def build_routes(selected_airports, all_airlines, all_routes):
    """
    For each (origin, dest) pair in selected airports, collect all operating airlines.
    Returns: dict (origin, dest) -> [airline_iata, ...]
    """
    route_carriers = defaultdict(list)
    for airline, origin, dest in all_routes:
        if origin in selected_airports and dest in selected_airports and airline in all_airlines:
            if airline not in route_carriers[(origin, dest)]:
                route_carriers[(origin, dest)].append(airline)
    return route_carriers

# ── generate SQL ──────────────────────────────────────────────────────────────

def generate_sql(selected_airports, selected_airlines, route_carriers):
    lines = []
    lines.append("-- =============================================================")
    lines.append("-- Amadeus World Travel Data — PostgreSQL Seed Data (v3)")
    lines.append("-- Generated from OpenFlights open data (CC BY licence)")
    lines.append("-- {} airports, {} airlines, {} routes".format(
        len(selected_airports), len(selected_airlines), len(route_carriers)))
    lines.append("-- =============================================================")
    lines.append("")

    # ── Airlines ──────────────────────────────────────────────────────────────
    lines.append("-- Airlines ({})".format(len(selected_airlines)))
    lines.append("INSERT INTO airlines (carrier_code, name) VALUES")
    rows = []
    for code, name in sorted(selected_airlines.items()):
        rows.append("    ('{}', '{}')".format(code, sq(name[:100])))
    lines.append(",\n".join(rows) + "\nON CONFLICT DO NOTHING;")
    lines.append("")

    # ── Aircraft types (reuse from mock) ─────────────────────────────────────
    AIRCRAFT = {
        "359": "AIRBUS A350-900",
        "77W": "BOEING 777-300ER",
        "789": "BOEING 787-9",
        "388": "AIRBUS A380-800",
        "321": "AIRBUS A321",
        "738": "BOEING 737-800",
        "320": "AIRBUS A320",
        "744": "BOEING 747-400",
    }
    lines.append("-- Aircraft types")
    lines.append("INSERT INTO aircraft_types (aircraft_code, name) VALUES")
    rows = ["    ('{}', '{}')".format(k, v) for k, v in AIRCRAFT.items()]
    lines.append(",\n".join(rows) + "\nON CONFLICT DO NOTHING;")
    lines.append("")

    # ── Airports ──────────────────────────────────────────────────────────────
    # Deduplicate city_code: if two airports share same city_code, use iata as city_code
    city_code_count = Counter(d["city_code"] for d in selected_airports.values())
    lines.append("-- Airports ({})".format(len(selected_airports)))
    lines.append("INSERT INTO airports (iata_code, name, city_code, city_name, country_code, latitude, longitude) VALUES")
    rows = []
    for iata in sorted(selected_airports.keys()):
        d = selected_airports[iata]
        cc = d["city_code"] if city_code_count[d["city_code"]] == 1 else iata
        rows.append("    ('{}', '{}', '{}', '{}', '{}', {}, {})".format(
            iata, sq(d["name"][:100]), cc, sq(d["city"][:100]),
            d["country_code"], d["lat"], d["lon"]))
    lines.append(",\n".join(rows) + "\nON CONFLICT DO NOTHING;")
    lines.append("")

    # ── Cabin fares (same as before) ──────────────────────────────────────────
    lines.append("-- Cabin fares")
    lines.append("INSERT INTO cabin_fares (cabin, price_multiplier, fare_code, branded_fare, booking_class, checked_bags) VALUES")
    lines.append("    ('ECONOMY', 1.000, 'YOWSGB', 'LITE', 'Y', 1),")
    lines.append("    ('PREMIUM_ECONOMY', 1.900, 'WOWSGB', 'FLEX', 'W', 2),")
    lines.append("    ('BUSINESS', 4.400, 'COWSGB', 'BUSINESS', 'C', 2),")
    lines.append("    ('FIRST', 9.000, 'FOWSGB', 'SUITES', 'F', 3)")
    lines.append("ON CONFLICT DO NOTHING;")
    lines.append("")

    # ── Routes + schedules ────────────────────────────────────────────────────
    lines.append("-- Routes and flight schedules")
    lines.append("")

    # Batch routes INSERT
    route_rows = []
    schedule_inserts = []

    # Track flight numbers to avoid duplicates
    used_flight_nos = set()

    for (origin, dest), carriers in sorted(route_carriers.items()):
        if origin not in selected_airports or dest not in selected_airports:
            continue
        o = selected_airports[origin]
        d = selected_airports[dest]
        dist_km = haversine_km(o["lat"], o["lon"], d["lat"], d["lon"])
        if dist_km < 50:
            continue  # skip trivially short routes

        eco = price_from_km(dist_km)
        pre = round(eco * 1.9)
        biz = round(eco * 4.4)
        fst = round(eco * 9.0)
        route_rows.append("    ('{}', '{}', {}, {}, {}, {})".format(
            origin, dest, eco, pre, biz, fst))

        # Generate 1–3 schedules per route
        dur = duration_from_km(dist_km)
        n_schedules = min(len(carriers), 1 + (1 if dist_km > 500 else 0) + (1 if dist_km > 2000 else 0))
        dep_times = ["06:00:00", "12:30:00", "20:00:00"]

        for i, carrier in enumerate(carriers[:n_schedules]):
            dep = dep_times[i % 3]

            # Generate unique flight number
            base_no = carrier + flight_hash(origin + dest + carrier + str(i), 4)
            flight_no = base_no
            attempt = 0
            while flight_no in used_flight_nos:
                attempt += 1
                flight_no = carrier + flight_hash(origin + dest + carrier + str(i) + str(attempt), 4)
            used_flight_nos.add(flight_no)

            aircraft = aircraft_for_duration(dur)
            seats = random.randint(4, 30)

            # Terminal assignment
            t_dep_list = MULTI_TERMINAL.get(origin, ["1"])
            t_arr_list = MULTI_TERMINAL.get(dest, ["1"])
            t_dep = random.choice(t_dep_list)
            t_arr = random.choice(t_arr_list)

            schedule_inserts.append(
                "INSERT INTO flight_schedules "
                "(route_id, flight_no, carrier_code, aircraft_code, departure_time, duration_minutes, terminal_dep, terminal_arr, available_seats)\n"
                "SELECT id, '{}', '{}', '{}', '{}', {}, '{}', '{}', {}\n"
                "FROM routes WHERE origin_iata = '{}' AND destination_iata = '{}';".format(
                    sq(flight_no), carrier, aircraft, dep, dur, sq(t_dep), sq(t_arr), seats, origin, dest))

    lines.append("INSERT INTO routes (origin_iata, destination_iata, economy_base_price, premium_economy_base_price, business_base_price, first_base_price) VALUES")
    lines.append(",\n".join(route_rows) + "\nON CONFLICT DO NOTHING;")
    lines.append("")

    lines.append("-- Flight schedules ({} routes)".format(len(schedule_inserts)))
    for ins in schedule_inserts:
        lines.append(ins)
        lines.append("")

    # ── Hotels ────────────────────────────────────────────────────────────────
    # Use the airport IATA code as city_code — guaranteed unique, no collisions.
    # Deduplicate so multiple airports in the same city (e.g. LHR/LGW/STN for
    # London) produce only one hotel city entry, keyed by the alphabetically
    # first IATA code for that city.
    seen_cities = {}  # (city_upper, country_code) -> iata
    for iata in sorted(selected_airports.keys()):
        d = selected_airports[iata]
        ck = (d["city"].upper(), d["country_code"])
        if ck not in seen_cities:
            seen_cities[ck] = iata

    city_map = {}  # iata -> {final_city_code, city, country_code, lat, lon}
    for (city_upper, country_code), iata in seen_cities.items():
        d = selected_airports[iata]
        city_map[iata] = {
            "final_city_code": iata,
            "city": d["city"],
            "country_code": d["country_code"],
            "lat": d["lat"],
            "lon": d["lon"]
        }

    lines.append("-- Hotel cities ({})".format(len(city_map)))
    lines.append("INSERT INTO hotel_cities (city_code, city_name, country_code) VALUES")
    rows = []
    for iata in sorted(city_map.keys()):
        info = city_map[iata]
        rows.append("    ('{}', '{}', '{}')".format(
            iata, sq(info["city"][:100]), info["country_code"]))
    lines.append(",\n".join(rows) + "\nON CONFLICT DO NOTHING;")
    lines.append("")

    lines.append("-- Hotels and rooms")
    for iata in sorted(city_map.keys()):
        info = city_map[iata]
        city_code = iata
        country_code = info["country_code"]
        region_mul = PRICE_REGIONS.get(country_code, 0.7)
        city_name = info["city"]
        base_lat = info["lat"]
        base_lon = info["lon"]

        is_tourist = iata in TOURIST_AIRPORTS
        name_pool = RESORT_PREFIXES if is_tourist else HOTEL_PREFIXES
        room_pool_src = RESORT_ROOM_TEMPLATES if is_tourist else ROOM_TEMPLATES

        # Tourist destinations always get 3 resort properties; regular cities 1–3 by region
        if is_tourist:
            n_hotels = 3
        elif region_mul >= 1.3:
            n_hotels = 3
        elif region_mul >= 1.0:
            n_hotels = 2
        else:
            n_hotels = 1

        for hi in range(n_hotels):
            hotel_id = "AD{}{}{:02d}".format(city_code[:3], country_code, hi + 1)
            prefix = name_pool[hash(hotel_id) % len(name_pool)]
            if is_tourist:
                hotel_name = "{} {}".format(prefix, city_name.title())
                star = 5
                address = "BEACHFRONT ROAD, {}".format(city_name.title())
                distance = round(0.2 + hi * 1.2 + random.uniform(0, 0.5), 1)
                amenity_set = ["POOL", "SPA", "BEACH_ACCESS", "RESTAURANT", "BAR",
                               "WATER_SPORTS", "WIFI", "AIRPORT_TRANSFER"]
            else:
                hotel_name = "{} {}".format(prefix, city_name.title())
                star = 5 if hi == 0 else (4 if hi == 1 else 3)
                addr_no = random.randint(1, 200)
                address = "{} CITY CENTRE".format(addr_no)
                distance = round(0.5 + hi * 1.5 + random.uniform(0, 1.0), 1)
                amenity_set = AMENITY_SETS_FOR[hi % len(HOTEL_AMENITY_SETS)]

            lat_offset = random.uniform(-0.02, 0.02)
            lon_offset = random.uniform(-0.02, 0.02)
            lat = round(base_lat + lat_offset, 6)
            lon = round(base_lon + lon_offset, 6)
            amenities_pg = "{" + ",".join(amenity_set) + "}"

            lines.append(
                "INSERT INTO hotels (hotel_id, name, city_code, star_rating, address, country_code, latitude, longitude, distance_km, amenities) VALUES\n"
                "    ('{}', '{}', '{}', {}, '{}', '{}', {}, {}, {}, '{}');".format(
                    hotel_id, sq(hotel_name[:150]), city_code, star,
                    sq(address), country_code, lat, lon, distance, amenities_pg))

            # Tourist resorts get 3 room types; regular hotels get 2
            n_rooms = 3 if is_tourist else 2
            available = list(room_pool_src)
            random.shuffle(available)
            room_pool = available[:n_rooms]
            for room_type, bed_type, price_mul, desc_tmpl in room_pool:
                if is_tourist:
                    base_price = 200 * region_mul * price_mul
                else:
                    base_price = 100 * region_mul * (star / 5.0) * price_mul
                price = round(base_price, 2)
                desc = "{} in {}".format(desc_tmpl, city_name.title())
                lines.append(
                    "INSERT INTO hotel_rooms (hotel_id, room_type, beds, bed_type, price_per_night, currency, description) VALUES\n"
                    "    ('{}', '{}', 1, '{}', {}, 'USD', '{}');".format(
                        hotel_id, room_type, bed_type, price, sq(desc)))

        lines.append("")

    return "\n".join(lines)

# Alias so the variable is resolved at generation time
AMENITY_SETS_FOR = HOTEL_AMENITY_SETS

# ── main ──────────────────────────────────────────────────────────────────────

def main():
    print("Loading OpenFlights data...")
    all_airports = load_airports()
    all_airlines = load_airlines()
    all_routes = load_routes()
    print("  Raw: {} airports, {} airlines, {} routes".format(
        len(all_airports), len(all_airlines), len(all_routes)))

    print("Selecting top {} airports...".format(TOP_N_AIRPORTS))
    selected_airports = select_top_airports(all_airports, all_routes, TOP_N_AIRPORTS)
    print("  Selected: {} airports".format(len(selected_airports)))

    print("Building route map...")
    route_carriers = build_routes(selected_airports, all_airlines, all_routes)
    print("  Routes: {}".format(len(route_carriers)))

    # Select only airlines that operate at least one route in selected airports
    active_carrier_codes = set()
    for carriers in route_carriers.values():
        active_carrier_codes.update(carriers)
    selected_airlines = {k: v for k, v in all_airlines.items() if k in active_carrier_codes}
    print("  Airlines: {}".format(len(selected_airlines)))

    print("Generating SQL...")
    sql = generate_sql(selected_airports, selected_airlines, route_carriers)

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write(sql)
    print("Written to: {}".format(OUT_FILE))
    print("Lines: {:,}".format(sql.count('\n')))

if __name__ == "__main__":
    main()
