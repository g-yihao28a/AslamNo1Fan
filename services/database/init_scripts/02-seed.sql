INSERT INTO customer_location (customer_id, country, state, city, zip_code, lat_long, latitude, longitude)
VALUES ('7590-VHVEG', 'United States', 'California', 'Los Angeles', '90001', '33.9736, -118.2488', 33.973600, -118.248800)
ON CONFLICT DO NOTHING;

INSERT INTO customer_demographics (customer_id, gender, age, under_18, senior_citizen, partner, dependents, number_of_dependents)
VALUES ('7590-VHVEG', 'Female', 41, 'No', 'No', 'Yes', 'No', 0)
ON CONFLICT DO NOTHING;

INSERT INTO customer_services (customer_id, tenure_in_months, phone_service, multiple_lines, internet_service, internet_type, online_security, online_backup, device_protection, tech_support, streaming_tv, streaming_movies, contract, paperless_billing, payment_method, monthly_charge, total_charges)
VALUES ('7590-VHVEG', 1, 'No', 'No phone service', 'DSL', 'DSL', 'No', 'Yes', 'No', 'No', 'No', 'No', 'Month-to-month', 'Yes', 'Electronic check', 29.85, 29.85)
ON CONFLICT DO NOTHING;

INSERT INTO customer_status (customer_id, satisfaction_score, customer_status, churn_label, churn_value, churn_score, cltv, churn_category, churn_reason)
VALUES ('7590-VHVEG', 3, 'Stayed', 'No', 0, 65, 3969, NULL, NULL)
ON CONFLICT DO NOTHING;