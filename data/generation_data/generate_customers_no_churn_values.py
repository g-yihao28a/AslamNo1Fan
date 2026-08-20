import numpy as np
import pandas as pd

NUM_RECORDS = 250
OUTPUT_FILE = "Company_Data(For ML Prediction).csv"

np.random.seed(42)

# Generate IDs
id_nums = np.arange(1, NUM_RECORDS + 1)
char_strings = ["".join(np.random.choice(list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"), size=5)) for _ in range(NUM_RECORDS)]
customer_ids = [f"{n:05d}-{c}" for n, c in zip(id_nums, char_strings)]

# Demographic features
gender = np.random.choice(["Male", "Female"], size=NUM_RECORDS)
senior_citizen = np.random.choice(["No", "Yes"], size=NUM_RECORDS, p=[0.84, 0.16])
partner = np.random.choice(["Yes", "No"], size=NUM_RECORDS, p=[0.48, 0.52])
dependents = np.where(partner == "Yes", np.random.choice(["Yes", "No"], size=NUM_RECORDS, p=[0.4, 0.6]), "No")

# Service features
phone_service = np.random.choice(["Yes", "No"], size=NUM_RECORDS, p=[0.9, 0.1])
multiple_lines = np.where(phone_service == "Yes", np.random.choice(["Yes", "No"], size=NUM_RECORDS, p=[0.45, 0.55]), "No")
internet_service = np.random.choice(["Yes", "No"], size=NUM_RECORDS, p=[0.8, 0.2])

has_net = internet_service == "Yes"
online_security = np.where(has_net, np.random.choice(["Yes", "No"], size=NUM_RECORDS, p=[0.35, 0.65]), "No")
online_backup = np.where(has_net, np.random.choice(["Yes", "No"], size=NUM_RECORDS, p=[0.4, 0.6]), "No")
device_protection = np.where(has_net, np.random.choice(["Yes", "No"], size=NUM_RECORDS, p=[0.4, 0.6]), "No")
tech_support = np.where(has_net, np.random.choice(["Yes", "No"], size=NUM_RECORDS, p=[0.35, 0.65]), "No")
streaming_tv = np.where(has_net, np.random.choice(["Yes", "No"], size=NUM_RECORDS, p=[0.45, 0.55]), "No")
streaming_movies = np.where(has_net, np.random.choice(["Yes", "No"], size=NUM_RECORDS, p=[0.45, 0.55]), "No")

# Contract & billing
contract = np.random.choice(["Month-to-Month", "One Year", "Two Year"], size=NUM_RECORDS, p=[0.55, 0.25, 0.2])
paperless_billing = np.random.choice(["Yes", "No"], size=NUM_RECORDS, p=[0.6, 0.4])
payment_method = np.random.choice(["Bank Withdrawal", "Credit Card", "Mailed Check"], size=NUM_RECORDS, p=[0.4, 0.35, 0.25])

# Financials
tenure_months = np.random.randint(1, 73, size=NUM_RECORDS)
base_charge = 20.0 + np.where(has_net, 35.0, 0.0) + np.where(phone_service == "Yes", 15.0, 0.0)
monthly_charges = np.round(base_charge + np.random.uniform(5.0, 40.0, size=NUM_RECORDS), 2)
total_charges = np.round(monthly_charges * tenure_months + np.random.uniform(10.0, 50.0, size=NUM_RECORDS), 2)

# Build DataFrame using the exact Title Case names required by ML Engine
df = pd.DataFrame({
    "customer_id": customer_ids,
    "Tenure Months": tenure_months,
    "Monthly Charges": monthly_charges,
    "Total Charges": total_charges,
    "Gender": gender,
    "Senior Citizen": senior_citizen,
    "Partner": partner,
    "Dependents": dependents,
    "Phone Service": phone_service,
    "Multiple Lines": multiple_lines,
    "Internet Service": internet_service,
    "Online Security": online_security,
    "Online Backup": online_backup,
    "Device Protection": device_protection,
    "Tech Support": tech_support,
    "Streaming TV": streaming_tv,
    "Streaming Movies": streaming_movies,
    "Contract": contract,
    "Paperless Billing": paperless_billing,
    "Payment Method": payment_method,
})

df.to_csv(OUTPUT_FILE, index=False)
print(f"Generated {NUM_RECORDS} rows matching ML Engine features -> {OUTPUT_FILE}")
