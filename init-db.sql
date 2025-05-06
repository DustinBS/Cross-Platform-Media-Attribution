-- Create tables

-- Table for sim_id_mapping.csv
CREATE TABLE sim_id_mapping (
    simulated_household_id_linear VARCHAR,
    simulated_device_id_A VARCHAR,
    simulated_user_id_A VARCHAR,
    simulated_visitor_cookie_id VARCHAR
);

-- Table for sim_linear_ad_log.csv
CREATE TABLE sim_linear_ad_log (
    linear_airing_id VARCHAR,
    timestamp_utc TIMESTAMP WITH TIME ZONE, -- Use TIMESTAMP WITH TIME ZONE for UTC
    linear_channel VARCHAR,
    creative_name VARCHAR,
    simulated_household_id_linear VARCHAR,
    simulated_impressions INTEGER
);

-- Table for sim_streaming_ad_log_A.csv
CREATE TABLE sim_streaming_ad_log_A (
    streaming_ad_id_A VARCHAR,
    timestamp_app_A TIMESTAMP WITH TIME ZONE,
    streaming_platform VARCHAR,
    creative_id_A VARCHAR,
    simulated_device_id_A VARCHAR,
    simulated_user_id_A VARCHAR,
    simulated_impressions_count INTEGER
);

-- Table for sim_website_visits.csv
CREATE TABLE sim_website_visits (
    visit_id VARCHAR,
    visit_timestamp TIMESTAMP WITH TIME ZONE,
    entry_url VARCHAR,
    simulated_visitor_cookie_id VARCHAR
);

-- Table for sim_purchases.csv
CREATE TABLE sim_purchases (
    purchase_id VARCHAR,
    purchase_timestamp TIMESTAMP WITH TIME ZONE, 
    purchase_value NUMERIC,
    simulated_visitor_cookie_id VARCHAR
);

-- Load data from CSV files
-- The paths below assume the 'data' directory is mounted to /docker-entrypoint-initdb.d/ (look at your docker-compose.yml if path error)

COPY sim_id_mapping FROM '/docker-entrypoint-initdb.d/data/sim_id_mapping.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');
COPY sim_linear_ad_log FROM '/docker-entrypoint-initdb.d/data/sim_linear_ad_log.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');
COPY sim_streaming_ad_log_A FROM '/docker-entrypoint-initdb.d/data/sim_streaming_ad_log_A.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');
COPY sim_website_visits FROM '/docker-entrypoint-initdb.d/data/sim_website_visits.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');
COPY sim_purchases FROM '/docker-entrypoint-initdb.d/data/sim_purchases.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');