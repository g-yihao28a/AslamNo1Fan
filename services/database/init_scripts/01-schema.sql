CREATE TABLE IF NOT EXISTS customer_location (
    customer_id VARCHAR(50) PRIMARY KEY,
    country VARCHAR(50),
    state VARCHAR(50),
    city VARCHAR(100),
    zip_code VARCHAR(10),
    lat_long VARCHAR(100),
    latitude NUMERIC(10, 6),
    longitude NUMERIC(10, 6)
);

CREATE TABLE IF NOT EXISTS customer_demographics (
    customer_id VARCHAR(50) PRIMARY KEY,
    gender VARCHAR(10),
    age INT,
    under_18 VARCHAR(5),
    senior_citizen VARCHAR(5),
    partner VARCHAR(5),
    dependents VARCHAR(5),
    number_of_dependents INT,
    FOREIGN KEY (customer_id) REFERENCES customer_location(customer_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS customer_services (
    customer_id VARCHAR(50) PRIMARY KEY,
    tenure_in_months INT,
    phone_service VARCHAR(5),
    multiple_lines VARCHAR(20),
    internet_service VARCHAR(20),
    internet_type VARCHAR(20),
    online_security VARCHAR(20),
    online_backup VARCHAR(20),
    device_protection VARCHAR(20),
    tech_support VARCHAR(20),
    streaming_tv VARCHAR(20),
    streaming_movies VARCHAR(20),
    contract VARCHAR(20),
    paperless_billing VARCHAR(5),
    payment_method VARCHAR(30),
    monthly_charge NUMERIC(10, 2),
    total_charges NUMERIC(10, 2),
    FOREIGN KEY (customer_id) REFERENCES customer_location(customer_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS customer_status (
    customer_id VARCHAR(50) PRIMARY KEY,
    satisfaction_score INT,
    customer_status VARCHAR(20),
    churn_label VARCHAR(5),
    churn_value INT,
    churn_score INT,
    cltv INT,
    churn_category VARCHAR(50),
    churn_reason TEXT,
    FOREIGN KEY (customer_id) REFERENCES customer_location(customer_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS inference_logs (
    inference_id SERIAL PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    churn_probability NUMERIC(5, 4),
    predicted_churn BOOLEAN NOT NULL,
    model_version VARCHAR(20) DEFAULT 'v1.0',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);