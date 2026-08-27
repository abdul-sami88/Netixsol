-- =========================================================
-- Zameen/RealEstate Hub knowledge base — PostgreSQL schema
-- Converts the SQLite dev schema (db/build_db.py) to Postgres,
-- keeping your original `properties` DDL untouched, and adds
-- the supporting knowledge-base tables + indexes for the
-- agent's structured (SQL) lookups.
-- =========================================================

-- ---------------------------------------------------------
-- Core table (unchanged from your original definition)
-- ---------------------------------------------------------
CREATE TABLE properties (
    property_id BIGINT PRIMARY KEY,
    location_id BIGINT,
    page_url TEXT,
    property_type VARCHAR(100),
    price NUMERIC(15, 2),
    price_bin VARCHAR(50),
    location TEXT,
    city VARCHAR(100),
    province_name VARCHAR(100),
    locality VARCHAR(150),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    baths INTEGER,
    area TEXT,
    area_marla NUMERIC(12, 2),
    area_sqft NUMERIC(12, 2),
    purpose VARCHAR(50),
    bedrooms INTEGER,
    date_added DATE,
    year INTEGER,
    month INTEGER,
    day INTEGER,
    agency TEXT,
    agent TEXT
);

-- ---------------------------------------------------------
-- Supporting knowledge-base tables
-- ---------------------------------------------------------
CREATE TABLE locations (
    location_id BIGINT PRIMARY KEY,
    city VARCHAR(100),
    locality VARCHAR(150),
    province_name VARCHAR(100),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    popularity_score NUMERIC(3, 1),
    avg_price_per_marla NUMERIC(15, 2)
);

CREATE TABLE amenities (
    amenity_id BIGINT PRIMARY KEY,
    property_id BIGINT REFERENCES properties(property_id),
    amenity_name VARCHAR(150)
);

CREATE TABLE schools (
    school_id BIGINT PRIMARY KEY,
    location_id BIGINT REFERENCES locations(location_id),
    school_name VARCHAR(200),
    distance_km NUMERIC(5, 1),
    school_type VARCHAR(50)
);

CREATE TABLE hospitals (
    hospital_id BIGINT PRIMARY KEY,
    location_id BIGINT REFERENCES locations(location_id),
    hospital_name VARCHAR(200),
    distance_km NUMERIC(5, 1),
    emergency_services BOOLEAN
);

CREATE TABLE payment_plans (
    plan_id BIGINT PRIMARY KEY,
    property_id BIGINT REFERENCES properties(property_id),
    down_payment_pct NUMERIC(5, 2),
    down_payment_amount NUMERIC(15, 2),
    num_installments INTEGER,
    installment_amount NUMERIC(15, 2),
    tenure_years INTEGER,
    developer VARCHAR(150)
);

CREATE TABLE developers (
    developer_id BIGINT PRIMARY KEY,
    developer_name VARCHAR(150),
    founded_year INTEGER,
    active_projects INTEGER,
    reputation_score NUMERIC(3, 1),
    hq_city VARCHAR(100)
);

-- FAQs — includes category + language so the agent can filter by locale
-- (e.g. serve only 'urdulish' FAQs to the voice agent) and topic.
CREATE TABLE faqs (
    faq_id VARCHAR(20) PRIMARY KEY,      -- e.g. 'faq_001'
    category VARCHAR(50),                -- payment | legal | amenities | location | investment | builder | maintenance | booking | company | pricing
    question TEXT,
    answer TEXT,
    language VARCHAR(20) DEFAULT 'urdulish'
);

-- Property description / brochure chunks — the unstructured corpus used
-- for semantic (vector) retrieval. One or more chunks per property.
CREATE TABLE property_description_chunks (
    id VARCHAR(30) PRIMARY KEY,          -- e.g. 'desc_prop_001'
    property_id BIGINT REFERENCES properties(property_id),
    text TEXT
);

-- =========================================================
-- Helpful indexes for the agent's structured lookups
-- =========================================================
-- Note: your example used `listing_status`; this schema's equivalent
-- column is `purpose` (For Sale / For Rent). Indexed under that name so
-- it actually matches a real column — add a `listing_status` column
-- instead/alongside if you introduce finer-grained states later
-- (e.g. Available / Under Offer / Sold / Rented).
CREATE INDEX idx_properties_purpose    ON properties(purpose);
CREATE INDEX idx_properties_type       ON properties(property_type);
CREATE INDEX idx_properties_price      ON properties(price);
CREATE INDEX idx_properties_location   ON properties(location_id);
CREATE INDEX idx_properties_bedrooms   ON properties(bedrooms);

-- Additional indexes worth having given the agent's actual query patterns
-- (city/locality filters and agent-name lookups are asked constantly):
CREATE INDEX idx_properties_city       ON properties(city);
CREATE INDEX idx_properties_locality   ON properties(locality);
CREATE INDEX idx_properties_agent      ON properties(agent);
CREATE INDEX idx_properties_city_price ON properties(city, price);   -- composite: "houses in Lahore under X"

CREATE INDEX idx_amenities_property    ON amenities(property_id);
CREATE INDEX idx_amenities_name        ON amenities(amenity_name);
CREATE INDEX idx_schools_location      ON schools(location_id);
CREATE INDEX idx_hospitals_location    ON hospitals(location_id);
CREATE INDEX idx_payment_plans_property ON payment_plans(property_id);
CREATE INDEX idx_faqs_category         ON faqs(category);
CREATE INDEX idx_desc_chunks_property  ON property_description_chunks(property_id);

-- Optional: trigram index for fuzzy locality/agent name search
-- (requires: CREATE EXTENSION IF NOT EXISTS pg_trgm;)
-- CREATE INDEX idx_properties_locality_trgm ON properties USING gin (locality gin_trgm_ops);
