CREATE TABLE user(
    user_id INT PRIMARY KEY,
    user_name VARCHAR(50),
    user_email VARCHAR(50),
    user_phone_number VARCHAR (11),
    appointment_day DATE,
    property_id INT FOREIGN KEY fk
);
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

