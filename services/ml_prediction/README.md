# ML Prediction Microservice (Telco Churn)
Streamlit UI for scoring a customer against the churn model. Collects feature
inputs and posts them through the API gateway to `ml_engine`.

## Tabs
- **Predict Churn**  – form that builds a customer payload and calls the ML engine live
- **Recent Predictions** – last inference logs (customer_id, probability, predicted_churn, model_version)

### API Integration & Data Access
The service communicates exclusively through the API Gateway (`GATEWAY_URL` configured in `config.py`), isolating it from direct database or ML engine access:

- `POST /ml/predict` – Receives customer feature payloads and returns calculated churn probabilities and binary risk predictions (`likely to churn` / `likely to stay`).
- `GET /database/logs` – Retrieves recent inference logs
- `GET /database/customers/full` – Pulls full customer datasets for analysis 

### Feature Options
Form controls are configured in `config.py` to match the expected schema:
- **Demographics**: Gender, Senior Citizen, Partner, Dependents
- **Services**: Phone Service, Internet Service
- **Billing & Contract**: Contract length, Paperless Billing, Payment Method, Tenure (months), Monthly Charges, Total Charges


The microservice runs as a Streamlit application on port `8011`. Submitting a prediction automatically generates a unique `Customer ID` (or accepts a manual ID), posts the payload to the API gateway, displays live probability metrics, and instantly updates the history log tab.

The UI does not train or load the model itself. `POST /train` on `ml_engine`
must succeed first (see `services/ml_engine/README.md`), otherwise Predict
Churn will surface an error from the gateway. A customer ID is required so
the engine can write the result into `inference_logs`; the form pre-fills
an auto-generated `MANUAL-…` ID if you do not enter a real one.
