# MONOLITH - Everything in one application

from flask import Flask, jsonify, request
import sqlite3

app = Flask(__name__)
DATABASE = "/app/data/app.db"


def init_db():
    conn = sqlite3.connect(DATABASE)
    conn.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY, user_id INTEGER, item TEXT)")
    conn.commit()
    conn.close()


# ========== USER MODULE ==========
@app.route("/users", methods=["GET"])
def get_users():
    conn = sqlite3.connect(DATABASE)
    rows = conn.execute("SELECT id, name FROM users").fetchall()
    conn.close()
    return jsonify([{"id": r[0], "name": r[1]} for r in rows])


@app.route("/users", methods=["POST"])
def create_user():
    name = request.json.get("name")
    conn = sqlite3.connect(DATABASE)
    cursor = conn.execute("INSERT INTO users (name) VALUES (?)", (name,))
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return jsonify({"id": user_id, "name": name}), 201


# ========== ORDER MODULE ==========
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

    # Direct database check (same DB, simple!)
    conn = sqlite3.connect(DATABASE)
    user = conn.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        conn.close()
        return jsonify({"error": "User not found"}), 404

    cursor = conn.execute("INSERT INTO orders (user_id, item) VALUES (?, ?)", (user_id, item))
    order_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return jsonify({"id": order_id, "user_id": user_id, "item": item}), 201


@app.route("/")
def index():
    return {"type": "monolith", "modules": ["user", "order"], "database": "shared"}


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
