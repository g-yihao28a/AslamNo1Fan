# Telco Customer Churn Platform
List of services:
db_loader
database
database_service
ml_engine
ml_prediction
dashboard
api_gateway

## First-time setup
Windows:
  In po: `Add-Content -Path C:\Windows\System32\drivers\etc\hosts -Value "127.0.0.1 telco-churn.local"`
  Run setup.ps1

## Everyday use
Run start.ps1 to start (Windows)
Run stop.ps1 to stop (Windows)

## Notes

- The trained model is stored in a Docker volume (`ml_model_data`), so it survives
  container restarts. Retrain any time from "http://localhost:8008/ml/train".
- `db_loader` is a one-off job (`profiles: [tools]`), so it won't start with
  `docker compose up` — run it explicitly when you need to (re)seed the database.
- Raw Excel source files live in `data/telco_data/`.
