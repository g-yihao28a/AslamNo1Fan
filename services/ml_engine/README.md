# ML Engine Microservice (Telco Churn)

Trains and serves a churn-prediction model (scikit-learn `RandomForestClassifier`)
over the Telco customer churn dataset.

## Endpoints
- `GET  /health`       – liveness check, reports whether a trained model is loaded
- `POST /train`        – (re)trains the model from `data/telco_data/Telco_customer_churn.xlsx`
- `GET  /model/info`   – metadata for the currently loaded model (metrics, version, trained_at)
- `POST /predict`      – returns churn probability for a customer

### Example: train the model
```bash
curl -X POST http://localhost:8010/train
```

### Example: predict
```bash
curl -X POST http://localhost:8010/predict \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "7590-VHVEG",
    "Gender": "Female",
    "Senior Citizen": "No",
    "Partner": "Yes",
    "Dependents": "No",
    "Tenure Months": 1,
    "Phone Service": "No",
    "Multiple Lines": "No phone service",
    "Internet Service": "DSL",
    "Online Security": "No",
    "Online Backup": "Yes",
    "Device Protection": "No",
    "Tech Support": "No",
    "Streaming TV": "No",
    "Streaming Movies": "No",
    "Contract": "Month-to-month",
    "Paperless Billing": "Yes",
    "Payment Method": "Electronic check",
    "Monthly Charges": 29.85,
    "Total Charges": 29.85
  }'
```

The model isn't baked into the Docker image (the training data is mounted in
via `compose.yaml`, not copied at build time), so you need to call `POST /train`
once after `docker compose up` before `/predict` will work. The trained model
is written to `services/ml_engine/model/` and reused on the next container
restart.
