# ML Prediction Microservice (Telco Churn)

Streamlit UI for scoring a customer against the churn model. Collects feature
inputs, posts them through the API gateway to `ml_engine`, and shows recent
inference logs from the database service.

Runs on port `8011`. Predictions go to `{API_GATEWAY_URL}/ml/predict`; history
is loaded from `{API_GATEWAY_URL}/database/logs`.

## Tabs
- **Predict Churn**  – form that builds a customer payload and calls the ML engine live
- **Recent Predictions** – last inference logs (customer_id, probability, predicted_churn, model_version)

Form fields include customer ID, tenure, monthly/total charges, and the
categorical features in `config.FEATURE_OPTIONS` (gender, contract, internet
service, payment method, etc.). Fields not shown in the form are sent as
defaults (`"No"` for add-on services such as Online Security).

### Example: open the UI (Docker Compose)
```bash
# after docker compose up, with the gateway and ML engine healthy
open http://localhost:8011
```

Via the API gateway:
```bash
open http://localhost:8008/ml_prediction
```

### Example: Streamlit health check
```bash
curl http://localhost:8011/_stcore/health
```

The UI does not train or load the model itself. `POST /train` on `ml_engine`
must succeed first (see `services/ml_engine/README.md`), otherwise Predict
Churn will surface an error from the gateway. A customer ID is required so
the engine can write the result into `inference_logs`; the form pre-fills
an auto-generated `MANUAL-…` ID if you do not enter a real one.
