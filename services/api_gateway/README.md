## API Gateway Microservice
This microservice facilitates communication into the system and between other microservices.

## API Gateway Functions
Displays an HTML home page that allows users to navigate to other pages:

* **Dashboard:** Redirects users to the dashboard microservice
* **Database:** 
  * **View customer record:** Search for specific users by their ID
  * **Single customer entry:** Enter customer information directly into the database
  * **CSV file upload:** Bulk upload customer information via a `.csv` file
* **Machine Learning:** 
  * **Train/Retrain model:** Trigger machine learning model training/retraining
  * **Manually input prediction:** Redirects users to the machine learning prediction service
  * **Model info:** Request and display machine learning model metadata
  * **Reload model:** Force reload the active machine learning model
  * **Predictions from CSV:** Upload a `.csv` file containing customer data to predict churn

## API Routes

| Category | Endpoint | HTTP Method | Description |
| :--- | :--- | :--- | :--- |
| **Dashboard** | `/dashboard` | `GET` | Redirect to dashboard service |
| **Database** | `/database/customers/full/<customer_id>` | `GET` | Retrieve specific customer details |
| | `/database/customers/upload` | `POST` | Upload customer `.csv` file |
| | `/database/customers/<customer_id>` | `GET`, `PUT`, `DELETE` | Specific customer CRUD interactions |
| | `/database/logs` | `GET`, `PUT` | Read or append inference logs |
| **Machine Learning** | `/ml_prediction` | `GET` | Redirect to prediction service |
| | `/ml/train` | `POST` | Trigger model training or retraining |
| | `/ml/model/info` | `GET` | Retrieve model metadata |
| | `/ml/model/reload` | `POST` | Reload the current model instance |
| | `/ml/predict` | `POST` | Forward single prediction request |
| | `/ml/predict_csv_single` | `POST` | Forward batch `.csv` prediction request |
| **Debug** | `/health` | `GET` | Retrieve health status of downstream services |