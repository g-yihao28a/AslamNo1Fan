INSERT INTO customers (
    customer_id, country, state, city, zip_code, lat_long, latitude, longitude,
    gender, age, under_30, senior_citizen, partner, dependents, number_of_dependents,
    tenure_in_months, phone_service, multiple_lines, internet_service, internet_type,
    online_security, online_backup, device_protection, tech_support, streaming_tv,
    streaming_movies, contract, paperless_billing, payment_method, monthly_charge, total_charges,
    satisfaction_score, customer_status, churn_label, churn_value, churn_score, cltv,
    churn_category, churn_reason
)
VALUES (
    '7590-VHVEG', 'United States', 'California', 'Los Angeles', '90001', '33.9736, -118.2488', 33.973600, -118.248800,
    'Female', 41, 'No', 'No', 'Yes', 'No', 0,
    1, 'No', 'No phone service', 'DSL', 'DSL',
    'No', 'Yes', 'No', 'No', 'No',
    'No', 'Month-to-month', 'Yes', 'Electronic check', 29.85, 29.85,
    3, 'Stayed', 'No', 0, 65, 3969,
    NULL, NULL
)
ON CONFLICT DO NOTHING;
