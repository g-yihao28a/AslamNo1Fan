## Database Microservice

Postgres data layer for the Telco churn platform. Stores customer records and model inference logs, exposed via a REST API.

## Components
- database - Postgres 16, auto-initialized from init_scripts/
- api - Flask REST API on port 5000
- loader - one-off script that loads the Excel dataset into Postgres

## Data Model
- customers - one row per customer (customer_id is the primary key).
- inference_logs - model prediction history: customer_id, churn_probability, predicted_churn, model_version, created_at.

## Main API request paths
- GET /health - service + database status
- GET /customers, GET /customers/<id> - list or fetch customers
- POST /customers - create or insert a customer
- POST /customers/upload - bulk upsert from a CSV file
- POST /logs - insert inference logs
- GET /logs - retrieve inference logs

## Additional API request paths
- PUT /customers/<id> - update a customer
- DELETE /customers/<id> - delete a customer
