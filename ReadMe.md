# Telco Customer Churn Platform

Four microservices working together over the real Telco customer churn dataset:

| Service       | What it does                                                             | Port |
|---------------|---------------------------------------------------------------------------|------|
| `database`    | Postgres, schema auto-created from `init_scripts/` on first boot          | 5432 |
| `ml_engine`   | Trains + serves a scikit-learn churn classifier (Flask API)               | 8010 |
| `dashboard`   | Streamlit app: interactive charts + a live "predict churn" panel          | 8501 |
| `api_gateway` | Single entrypoint that proxies to `ml_engine` and `dashboard`             | 8008 |

## First-time setup

```bash
powershell commands
cp .env.example .env
docker compose up -d database
docker compose run --rm db_loader      # for loading the real Excel data into Postgres
docker compose up -d                   # to start ml_engine, dashboard, api_gateway
curl.exe -X POST http://localhost:8010/train
```

Then open:
- Dashboard: http://localhost:8501
- API gateway health (all services): http://localhost:8008/health/all

## Everyday use

```bash
docker compose up            # start everything
docker compose up [service]  # start just one service
docker compose down          # stop everything
```

## API gateway routes

- `GET  /health` — gateway liveness
- `GET  /health/all` — aggregated health across all services
- `POST /api/ml/predict` — proxies to the ML engine's `/predict`
- `POST /api/ml/train` — proxies to the ML engine's `/train`
- `GET  /api/ml/model/info` — proxies to the ML engine's `/model/info`

## Notes

- The trained model is stored in a Docker volume (`ml_model_data`), so it survives
  container restarts. Retrain any time with `POST /api/ml/train`.
- `db_loader` is a one-off job (`profiles: [tools]`), so it won't start with
  `docker compose up` — run it explicitly when you need to (re)seed the database.
- Raw Excel source files live in `data/telco_data/`.
