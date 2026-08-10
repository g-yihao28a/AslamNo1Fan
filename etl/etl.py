from pathlib import Path
import pandas as pd
import duckdb

# Mounted dataset folder
DATA_DIR = Path("/data")

# Read Excel file from mounted volume
services = pd.read_excel(DATA_DIR / "Telco_customer_churn_services.xlsx")

print("Loaded rows:", len(services))

# Write output to mounted folder
OUTPUT_DIR = Path("/output")
(OUTPUT_DIR / "etl_result.csv").write_text("example,data\n1,2")

print( DATA_DIR )
services = pd.read_excel(
    DATA_DIR / "Telco_customer_churn_services.xlsx")
demographics = pd.read_excel(
    DATA_DIR / "Telco_customer_churn_demographics.xlsx")
location = pd.read_excel(
    DATA_DIR / "Telco_customer_churn_location.xlsx")
population = pd.read_excel(
    DATA_DIR / "Telco_customer_churn_population.xlsx")
status = pd.read_excel(
    DATA_DIR / "Telco_customer_churn_status.xlsx")

df = services.merge(
    demographics,
    on="Customer ID",
    suffixes=("", "_demo"))
df = df.merge(
    location[["Customer ID", "Zip Code", "Latitude", "Longitude"]],
    on="Customer ID")
df = df.merge(
    population[["Zip Code", "Population"]],
    on="Zip Code",
    how="left")
df = df.merge(
    status[["Customer ID", "Churn Value"]],
    on="Customer ID")




con = duckdb.connect("/output/telco.duckdb")

con.register("telco_df", df)

con.execute("""
    CREATE OR REPLACE TABLE telco_churn AS
    SELECT * FROM telco_df
""")

con.close()