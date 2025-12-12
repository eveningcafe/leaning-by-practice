# ORDER SERVICE - Calls User Service via HTTP

from flask import Flask, jsonify, request
import sqlite3
import requests
import os

app = Flask(__name__)
DATABASE = "/app/data/orders.db"

# Gateway URL - all service calls go through gateway
GATEWAY = os.getenv("GATEWAY_URL", "http://api-gateway")


def init_db():
    conn = sqlite3.connect(DATABASE)
    conn.execute("CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY, user_id INTEGER, item TEXT)")
    conn.commit()
    conn.close()


@app.route("/orders", methods=["GET"])
def get_orders():
    conn = sqlite3.connect(DATABASE)
    rows = conn.execute("SELECT id, user_id, item FROM orders").fetchall()
    conn.close()
    return jsonify([{"id": r[0], "user_id": r[1], "item": r[2]} for r in rows])


@app.route("/orders", methods=["POST"])
def create_order():
    user_id = request.json.get("user_id")
    item = request.json.get("item")

    # HTTP call via Gateway (gateway routes to user-service)
    try:
        resp = requests.get(f"{GATEWAY}/users/{user_id}")
        if resp.status_code == 404:
            return jsonify({"error": "User not found"}), 404
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "User service unavailable"}), 503

    conn = sqlite3.connect(DATABASE)
    cursor = conn.execute("INSERT INTO orders (user_id, item) VALUES (?, ?)", (user_id, item))
    order_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return jsonify({"id": order_id, "user_id": user_id, "item": item}), 201


@app.route("/")
def index():
    return {"service": "order-service", "port": 5002, "gateway": GATEWAY}


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5002)
