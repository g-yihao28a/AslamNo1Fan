# Database Microservice (Telco Churn)

Provides the PostgreSQL database server for storing normalized customer churn data and inference logs.

## Run locally with Docker
```bash
docker build -t telco-db-service .
docker run -d -p 5432:5432 --name test-db telco-db-service