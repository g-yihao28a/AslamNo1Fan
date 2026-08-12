from flask import Flask, jsonify, request
import psycopg2
import psycopg2.extras
import os

app = Flask(__name__)


# DATABASE CONNECTION

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "database"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME", "telco_churn_db"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgrespassword")
    )



# HEALTH CHECK


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "Database microservice is running"
    }), 200


# GET ALL CUSTOMERS


@app.route("/customers", methods=["GET"])
def get_customers():

    try:
        conn = get_db_connection()

        cursor = conn.cursor(
            cursor_factory=psycopg2.extras.RealDictCursor
        )

        cursor.execute("""
            SELECT *
            FROM customer_location
            LIMIT 100
        """)

        customers = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify(customers), 200

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
            FROM customer_location
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



# POST - CREATE


@app.route("/customers", methods=["POST"])
def create_customer():

    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "error": "No JSON data provided"
            }), 400

        customer_id = data.get("customer_id")
        city = data.get("city")
        state = data.get("state")

        if not customer_id or not city or not state:
            return jsonify({
                "error": "customer_id, city and state are required"
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO customer_location
            (customer_id, city, state)
            VALUES (%s, %s, %s)
        """, (
            customer_id,
            city,
            state
        ))

        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({
            "message": "Customer created successfully",
            "customer": {
                "customer_id": customer_id,
                "city": city,
                "state": state
            }
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500



# PUT - UPDATE

@app.route("/customers/<customer_id>", methods=["PUT"])
def update_customer(customer_id):

    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "error": "No JSON data provided"
            }), 400

        city = data.get("city")
        state = data.get("state")

        if not city or not state:
            return jsonify({
                "error": "city and state are required"
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE customer_location
            SET city = %s,
                state = %s
            WHERE customer_id = %s
        """, (
            city,
            state,
            customer_id
        ))

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
            DELETE FROM customer_location
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


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )