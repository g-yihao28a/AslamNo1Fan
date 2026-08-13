from flask import Flask, jsonify, request
from config import config

app = Flask(__name__)

@app.route("/health", methods=["GET"])
def health_check():
    return {"status": "Database is running"}, 200


# Leave as last line, insert any additions above
if __name__ == "__main__":
    print(f"Database starting on http://localhost:{config.DATABASE_PORT}")
    app.run(host="0.0.0.0", port=config.DATABASE_PORT, debug=True)
    