import csv
import random


NUM_RECORDS = 10000
OUTPUT_FILE = "generated_customers.csv"

# Real California locations matching the dataset distribution
LOCATIONS = [
    {"city": "Los Angeles", "zip": "90001", "lat": 33.9731, "lng": -118.2479},
    {"city": "San Francisco", "zip": "94102", "lat": 37.7792, "lng": -122.4191},
    {"city": "San Diego", "zip": "92101", "lat": 32.7157, "lng": -117.1611},
    {"city": "San Jose", "zip": "95113", "lat": 37.3382, "lng": -121.8863},
    {"city": "Fresno", "zip": "93721", "lat": 36.7378, "lng": -119.7871},
    {"city": "Sacramento", "zip": "95814", "lat": 38.5816, "lng": -121.4944},
    {"city": "Long Beach", "zip": "90802", "lat": 33.7701, "lng": -118.1937},
    {"city": "Oakland", "zip": "94612", "lat": 37.8044, "lng": -122.2712},
    {"city": "Bakersfield", "zip": "93301", "lat": 35.3733, "lng": -119.0187},
    {"city": "Anaheim", "zip": "92805", "lat": 33.8366, "lng": -117.9143},
    {"city": "Frazier Park", "zip": "93225", "lat": 34.8277, "lng": -118.9991},
    {"city": "Glendale", "zip": "91206", "lat": 34.1625, "lng": -118.2039},
]

CHURN_REASONS = {
    "Competitor": [
        "Competitor made better offer",
        "Competitor offered higher download speeds",
        "Competitor offered more data",
    ],
    "Dissatisfaction": [
        "Network reliability was poor",
        "Product dissatisfaction",
        "Poor customer service",
    ],
    "Price": [
        "Price too high",
        "Extra data charges were too high",
        "Increase on contract renewal",
    ],
    "Attitude": [
        "Attitude of support person",
        "Attitude of service provider",
    ],
}

HEADERS = [
    "customer_id", "gender", "age", "under_18", "senior_citizen", "partner",
    "dependents", "number_of_dependents", "country", "state", "city", "zip_code",
    "latitude", "longitude", "lat_long", "phone_service", "multiple_lines",
    "internet_service", "internet_type", "online_security", "online_backup",
    "device_protection", "tech_support", "streaming_tv", "streaming_movies",
    "contract", "paperless_billing", "payment_method", "monthly_charge",
    "total_charges", "cltv", "customer_status", "churn_label", "churn_value",
    "churn_score", "churn_category", "churn_reason", "satisfaction_score"
]

rows = []
for i in range(1, NUM_RECORDS + 1):
    # Customer ID format (e.g., 00010-ABCDE)
    cust_id = f"{i:04d}-{''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=5))}"
    
    gender = random.choice(["Male", "Female"])
    age = random.randint(19, 80)
    under_18 = "Yes" if age < 18 else "No"
    senior_citizen = "Yes" if age >= 65 else "No"
    
    partner = random.choice(["Yes", "No"])
    has_deps = "Yes" if partner == "Yes" and random.random() > 0.5 else "No"
    num_deps = random.randint(1, 4) if has_deps == "Yes" else 0
    
    loc = random.choice(LOCATIONS)
    # Add minor random noise to coordinates
    lat = round(loc["lat"] + random.uniform(-0.02, 0.02), 6)
    lng = round(loc["lng"] + random.uniform(-0.02, 0.02), 6)
    lat_long = f"{lat}, {lng}"
    
    phone_svc = random.choice(["Yes", "No"])
    mult_lines = "Yes" if phone_svc == "Yes" and random.random() > 0.5 else "No"
    
    inet_svc = random.choice(["Yes", "No"])
    inet_type = random.choice(["Fiber Optic", "Cable", "DSL"]) if inet_svc == "Yes" else "None"
    
    sec = "Yes" if inet_svc == "Yes" and random.random() > 0.6 else "No"
    backup = "Yes" if inet_svc == "Yes" and random.random() > 0.5 else "No"
    protect = "Yes" if inet_svc == "Yes" and random.random() > 0.5 else "No"
    tech = "Yes" if inet_svc == "Yes" and random.random() > 0.6 else "No"
    tv = "Yes" if inet_svc == "Yes" and random.random() > 0.5 else "No"
    movies = "Yes" if inet_svc == "Yes" and random.random() > 0.5 else "No"
    
    contract = random.choice(["Month-to-Month", "One Year", "Two Year"])
    paperless = random.choice(["Yes", "No"])
    payment = random.choice(["Credit Card", "Bank Withdrawal", "Mailed Check"])
    
    tenure = random.randint(1, 72)
    base_charge = 20.0 + (30.0 if inet_svc == "Yes" else 0) + (15.0 if phone_svc == "Yes" else 0)
    monthly_charge = round(base_charge + random.uniform(5.0, 45.0), 2)
    total_charges = round(monthly_charge * tenure + random.uniform(10.0, 50.0), 2)
    cltv = random.randint(2000, 6500)
    
    # Realistic churn assignment: Month-to-Month contracts have higher churn likelihood. No cap on god bro
    churn_prob = 0.45 if contract == "Month-to-Month" else 0.10
    is_churned = random.random() < churn_prob
    
    if is_churned:
        status = "Churned"
        churn_label = "Yes"
        churn_value = 1
        churn_score = random.randint(65, 100)
        satisfaction = random.randint(1, 2)
        category = random.choice(list(CHURN_REASONS.keys()))
        reason = random.choice(CHURN_REASONS[category])
    else:
        status = "Joined" if tenure <= 3 else "Stayed"
        churn_label = "No"
        churn_value = 0
        churn_score = random.randint(10, 64)
        satisfaction = random.randint(3, 5)
        category = ""
        reason = ""
        
    rows.append([
        cust_id, gender, age, under_18, senior_citizen, partner, has_deps,
        num_deps, "United States", "California", loc["city"], loc["zip"],
        str(lat), str(lng), f'"{lat_long}"', phone_svc, mult_lines, inet_svc,
        inet_type, sec, backup, protect, tech, tv, movies, contract,
        paperless, payment, f"{monthly_charge:.2f}", f"{total_charges:.2f}",
        cltv, status, churn_label, churn_value, churn_score, category,
        reason, satisfaction
    ])

with open(OUTPUT_FILE, mode="w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
    writer.writerow(HEADERS)
    writer.writerows(rows)

print(f"Generated {NUM_RECORDS} records -> {OUTPUT_FILE}")