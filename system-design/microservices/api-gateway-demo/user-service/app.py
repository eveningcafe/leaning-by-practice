# USER SERVICE - Separate service with own database

from flask import Flask, jsonify, request
import sqlite3

app = Flask(__name__)
DATABASE = "/app/data/users.db"


def init_db():
    conn = sqlite3.connect(DATABASE)
    conn.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT)")
    conn.commit()
    conn.close()


@app.route("/users", methods=["GET"])
def get_users():
    conn = sqlite3.connect(DATABASE)
    rows = conn.execute("SELECT id, name FROM users").fetchall()
    conn.close()
    return jsonify([{"id": r[0], "name": r[1]} for r in rows])


@app.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    conn = sqlite3.connect(DATABASE)
    row = conn.execute("SELECT id, name FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    if row:
        return jsonify({"id": row[0], "name": row[1]})
    return jsonify({"error": "User not found"}), 404


@app.route("/users", methods=["POST"])
def create_user():
    name = request.json.get("name")
    conn = sqlite3.connect(DATABASE)
    cursor = conn.execute("INSERT INTO users (name) VALUES (?)", (name,))
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return jsonify({"id": user_id, "name": name}), 201


@app.route("/")
def index():
    return {"service": "user-service", "port": 5001}


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5001)
