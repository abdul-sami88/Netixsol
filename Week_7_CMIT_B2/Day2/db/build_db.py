"""
build_db.py — loads the knowledge base CSVs into SQLite, using the exact
`properties` schema supplied by the user (translated to SQLite types).
This DB backs the *structured* half of the retrieval system (Task 3).
"""
import sqlite3
import csv
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
DB_PATH = os.path.join(HERE, "real_estate.db")

SCHEMA = """
CREATE TABLE properties (
    property_id INTEGER PRIMARY KEY,
    location_id INTEGER,
    page_url TEXT,
    property_type TEXT,
    price REAL,
    price_bin TEXT,
    location TEXT,
    city TEXT,
    province_name TEXT,
    locality TEXT,
    latitude REAL,
    longitude REAL,
    baths INTEGER,
    area TEXT,
    area_marla REAL,
    area_sqft REAL,
    purpose TEXT,
    bedrooms INTEGER,
    date_added TEXT,
    year INTEGER,
    month INTEGER,
    day INTEGER,
    agency TEXT,
    agent TEXT
);

CREATE TABLE locations (
    location_id INTEGER PRIMARY KEY,
    city TEXT, locality TEXT, province_name TEXT,
    latitude REAL, longitude REAL,
    popularity_score REAL, avg_price_per_marla REAL
);

CREATE TABLE amenities (
    amenity_id INTEGER PRIMARY KEY,
    property_id INTEGER REFERENCES properties(property_id),
    amenity_name TEXT
);

CREATE TABLE schools (
    school_id INTEGER PRIMARY KEY,
    location_id INTEGER REFERENCES locations(location_id),
    school_name TEXT, distance_km REAL, school_type TEXT
);

CREATE TABLE hospitals (
    hospital_id INTEGER PRIMARY KEY,
    location_id INTEGER REFERENCES locations(location_id),
    hospital_name TEXT, distance_km REAL, emergency_services INTEGER
);

CREATE TABLE payment_plans (
    plan_id INTEGER PRIMARY KEY,
    property_id INTEGER REFERENCES properties(property_id),
    down_payment_pct REAL, down_payment_amount REAL,
    num_installments INTEGER, installment_amount REAL,
    tenure_years INTEGER, developer TEXT
);

CREATE TABLE developers (
    developer_id INTEGER PRIMARY KEY,
    developer_name TEXT, founded_year INTEGER,
    active_projects INTEGER, reputation_score REAL, hq_city TEXT
);

CREATE TABLE faqs (
    faq_id TEXT PRIMARY KEY,
    category TEXT, question TEXT, answer TEXT, language TEXT
);

CREATE TABLE descriptions (
    id TEXT PRIMARY KEY,
    property_id INTEGER REFERENCES properties(property_id),
    text TEXT
);
"""

TABLE_FILES = {
    "properties": "properties.csv",
    "locations": "locations.csv",
    "amenities": "amenities.csv",
    "schools": "schools.csv",
    "hospitals": "hospitals.csv",
    "payment_plans": "payment_plans.csv",
    "developers": "developers.csv",
    "faqs": "faqs.csv",
    "descriptions": "descriptions.csv",
}


def load_csv(cur, table, path):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        cols = reader.fieldnames
        placeholders = ",".join(["?"] * len(cols))
        sql = f"INSERT INTO {table} ({','.join(cols)}) VALUES ({placeholders})"
        rows = [tuple(r[c] for c in cols) for r in reader]
        cur.executemany(sql, rows)
    return len(rows)


def main():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.executescript(SCHEMA)
    for table, fname in TABLE_FILES.items():
        n = load_csv(cur, table, os.path.join(DATA, fname))
        print(f"loaded {n} rows into {table}")
    conn.commit()
    conn.close()
    print(f"DB built at {DB_PATH}")


if __name__ == "__main__":
    main()
