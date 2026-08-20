from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
import psycopg2.extras
import os

app = Flask(__name__)

# Allow the API gateway (and, through it, the dashboard / ml model
# microservices) to call this service cross-origin.
CORS(app)


# DATABASE CONNECTION

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "database"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME", "telco_churn_db"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgrespassword"),
        connect_timeout=3,
    )


# HEALTH CHECK


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "Database microservice is running"
    }), 200


# The API gateway polls GET /health on every registered service (including
# this one) to build its aggregate /health report.
@app.route("/health", methods=["GET"])
def health_check():
    try:
        conn = get_db_connection()
        conn.close()
        return jsonify({
            "status": "Database microservice is running",
            "database": "reachable"
        }), 200
    except Exception as e:
        return jsonify({
            "status": "Database microservice is running",
            "database": "unreachable",
            "error": str(e)
        }), 503


# ---------------------------------------------------------------------------
# customers: a single combined table (location + demographics + services +
# status all in one row per customer_id) - there's only one dataset to read
# or write, so every route below just talks to `customers` directly. No more
# joining across tables on every read.
# ---------------------------------------------------------------------------

ALL_CUSTOMER_FIELDS = [
    # location
    "country", "state", "city", "zip_code", "lat_long", "latitude", "longitude",
    # demographics
    "gender", "age", "under_18", "senior_citizen", "partner",
    "dependents", "number_of_dependents",
    # services
    "tenure_in_months", "phone_service", "multiple_lines", "internet_service",
    "internet_type", "online_security", "online_backup", "device_protection",
    "tech_support", "streaming_tv", "streaming_movies", "contract",
    "paperless_billing", "payment_method", "monthly_charge", "total_charges",
    # status
    "satisfaction_score", "customer_status", "churn_label", "churn_value",
    "churn_score", "cltv", "churn_category", "churn_reason",
]


# GET ALL CUSTOMERS


@app.route("/customers", methods=["GET"])
def get_customers():

    try:
        # No hard cap by default - callers that want the whole dataset
        # (e.g. the ML model microservice) get it in one shot. ?limit=&
        # offset= are there for callers that want to page through it.
        limit = request.args.get("limit", type=int)
        offset = request.args.get("offset", type=int, default=0)

        query = "SELECT * FROM customers ORDER BY customer_id"
        params = []
        if limit is not None:
            query += " LIMIT %s OFFSET %s"
            params = [limit, offset]

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(query, params)
        customers = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify({
            "count": len(customers),
            "customers": customers
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# GET ONE CUSTOMER


@app.route("/customers/<customer_id>", methods=["GET"])
def get_customer(customer_id):

    try:
        conn = get_db_connection()

        cursor = conn.cursor(
            cursor_factory=psycopg2.extras.RealDictCursor
        )

        cursor.execute("""
            SELECT *
            FROM customers
            WHERE customer_id = %s
        """, (customer_id,))

        customer = cursor.fetchone()

        cursor.close()
        conn.close()

        if customer is None:
            return jsonify({
                "error": "Customer not found"
            }), 404

        return jsonify(customer), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# "Full" aliases, kept for backward compatibility with callers already
# pointed at /customers/full (e.g. the API gateway's proxy routes) - now
# that there's only one table, these return exactly the same data as
# /customers and /customers/<id> above.
@app.route("/customers/full", methods=["GET"])
def get_customers_full():
    return get_customers()


@app.route("/customers/full/<customer_id>", methods=["GET"])
def get_customer_full(customer_id):
    return get_customer(customer_id)


# POST - CREATE / UPSERT
#
# A single JSON body can carry any subset of ALL_CUSTOMER_FIELDS.
# Unknown/omitted fields are simply skipped. Re-posting the same
# customer_id updates the existing row instead of failing with a
# duplicate-key error, so this also works for line-by-line corrections.

def _upsert_customer_record(cursor, data):
    """Upsert one customer row from whichever recognized fields are
    present in `data`. `data` is a flat dict; unrecognized keys are
    ignored."""
    customer_id = data.get("customer_id")
    if not customer_id:
        raise ValueError("customer_id is required")

    present = [f for f in ALL_CUSTOMER_FIELDS if f in data]
    if not present:
        # Nothing but customer_id supplied - still create/keep the row.
        cursor.execute("""
            INSERT INTO customers (customer_id)
            VALUES (%s)
            ON CONFLICT (customer_id) DO NOTHING
        """, (customer_id,))
        return customer_id

    columns = ["customer_id"] + present
    values = [customer_id] + [data.get(f) for f in present]
    placeholders = ", ".join(["%s"] * len(columns))
    set_clause = ", ".join(f"{c} = EXCLUDED.{c}" for c in present)

    cursor.execute(f"""
        INSERT INTO customers ({", ".join(columns)})
        VALUES ({placeholders})
        ON CONFLICT (customer_id) DO UPDATE SET {set_clause}
    """, values)
    return customer_id


@app.route("/customers", methods=["POST"])
def create_customer():

    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "error": "No JSON data provided"
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            customer_id = _upsert_customer_record(cursor, data)
            conn.commit()
        except ValueError as e:
            conn.rollback()
            return jsonify({"error": str(e)}), 400
        finally:
            cursor.close()
            conn.close()

        return jsonify({
            "message": "Customer saved successfully",
            "customer_id": customer_id
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# POST - BULK UPLOAD (CSV file, one customer per row)
#
# Lets a whole file of customers be loaded in one request, e.g. from the
# dashboard or ml model microservice via the gateway's
# `/database/customers/upload` route. Expects multipart/form-data with a
# `file` field containing a CSV whose header row uses the same column
# names as ALL_CUSTOMER_FIELDS (customer_id is required in every row).


@app.route("/customers/upload", methods=["POST"])
def upload_customers():
    import csv
    import io

    if "file" not in request.files:
        return jsonify({"error": "No file provided (expected multipart field 'file')"}), 400

    upload = request.files["file"]
    if upload.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    try:
        raw = upload.read().decode("utf-8-sig")
    except UnicodeDecodeError:
        return jsonify({"error": "File must be UTF-8 encoded CSV"}), 400

    reader = csv.DictReader(io.StringIO(raw))
    if reader.fieldnames is None or "customer_id" not in reader.fieldnames:
        return jsonify({"error": "CSV must include a customer_id column"}), 400

    try:
        conn = get_db_connection()
    except Exception as e:
        return jsonify({"error": f"Could not connect to database: {e}"}), 503

    cursor = conn.cursor()

    saved, errors = [], []
    try:
        for i, row in enumerate(reader, start=2):  # row 1 is the header
            # Drop empty-string values so they don't overwrite existing data with blanks
            clean_row = {k: (v if v not in ("", None) else None) for k, v in row.items()}
            try:
                customer_id = _upsert_customer_record(cursor, clean_row)
                saved.append(customer_id)
            except ValueError as e:
                errors.append({"row": i, "error": str(e)})

        conn.commit()
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({"error": str(e)}), 500

    cursor.close()
    conn.close()

    return jsonify({
        "message": f"Processed {len(saved) + len(errors)} row(s)",
        "saved": len(saved),
        "customer_ids": saved,
        "errors": errors
    }), 201 if not errors else 207


# PUT - UPDATE
#
# Accepts any subset of ALL_CUSTOMER_FIELDS (previously this only allowed
# updating city/state).

@app.route("/customers/<customer_id>", methods=["PUT"])
def update_customer(customer_id):

    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "error": "No JSON data provided"
            }), 400

        present = [f for f in ALL_CUSTOMER_FIELDS if f in data]
        if not present:
            return jsonify({
                "error": f"No recognized fields provided. Expected one or more of: {ALL_CUSTOMER_FIELDS}"
            }), 400

        set_clause = ", ".join(f"{c} = %s" for c in present)
        values = [data.get(f) for f in present] + [customer_id]

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(f"""
            UPDATE customers
            SET {set_clause}
            WHERE customer_id = %s
        """, values)

        if cursor.rowcount == 0:
            cursor.close()
            conn.close()

            return jsonify({
                "error": "Customer not found"
            }), 404

        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({
            "message": "Customer updated successfully"
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# DELETE


@app.route("/customers/<customer_id>", methods=["DELETE"])
def delete_customer(customer_id):

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM customers
            WHERE customer_id = %s
        """, (customer_id,))

        if cursor.rowcount == 0:
            cursor.close()
            conn.close()

            return jsonify({
                "error": "Customer not found"
            }), 404

        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({
            "message": "Customer deleted successfully"
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------
# inference_logs
# ---------------------------------------------------------------------------

# POST - CREATE INFERENCE LOG
@app.route("/logs", methods=["POST"])
def create_log():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        customer_id = data.get("customer_id")
        churn_prob = data.get("churn_probability")
        predicted_churn = data.get("predicted_churn")

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO inference_logs 
            (customer_id, churn_probability, predicted_churn)
            VALUES (%s, %s, %s)
        """, (customer_id, churn_prob, predicted_churn))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"message": "Log saved successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# GET - LIST INFERENCE LOGS
#
# Lets the dashboard / ml prediction service read recent prediction history
# through the API instead of querying inference_logs directly. Mirrors the
# `load_inference_logs(limit=200)` query they used to run themselves.
@app.route("/logs", methods=["GET"])
def get_logs():
    try:
        limit = request.args.get("limit", type=int, default=200)

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("""
            SELECT inference_id, customer_id, churn_probability,
                   predicted_churn, model_version, created_at
            FROM inference_logs
            ORDER BY created_at DESC
            LIMIT %s
        """, (limit,))
        logs = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify({
            "count": len(logs),
            "logs": logs
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
