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

Form fields include customer ID, tenure, monthly/total charges, and the
categorical features in `config.FEATURE_OPTIONS` (gender, contract, internet
service, payment method, etc.). Fields not shown in the form are sent as
defaults (`"No"` for add-on services such as Online Security).


The UI does not train or load the model itself. `POST /train` on `ml_engine`
must succeed first (see `services/ml_engine/README.md`), otherwise Predict
Churn will surface an error from the gateway. A customer ID is required so
the engine can write the result into `inference_logs`; the form pre-fills
an auto-generated `MANUAL-…` ID if you do not enter a real one.
