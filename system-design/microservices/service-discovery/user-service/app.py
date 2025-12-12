# USER SERVICE - Registers with Consul

from flask import Flask, jsonify, request
import sqlite3
import consul
import atexit
import socket

app = Flask(__name__)
DATABASE = "/app/data/users.db"
SERVICE_NAME = "user-service"
SERVICE_PORT = 5001

# Consul client
c = consul.Consul(host="consul")


def get_ip():
    return socket.gethostbyname(socket.gethostname())


def register_service():
    """Register this service with Consul."""
    c.agent.service.register(
        name=SERVICE_NAME,
        service_id=f"{SERVICE_NAME}-{get_ip()}",
        address=get_ip(),
        port=SERVICE_PORT,
        check=consul.Check.http(f"http://{get_ip()}:{SERVICE_PORT}/health", interval="10s")
    )
    print(f"Registered {SERVICE_NAME} at {get_ip()}:{SERVICE_PORT}")


def deregister_service():
    """Deregister on shutdown."""
    c.agent.service.deregister(f"{SERVICE_NAME}-{get_ip()}")
    print(f"Deregistered {SERVICE_NAME}")


def init_db():
    conn = sqlite3.connect(DATABASE)
    conn.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT)")
    conn.commit()
    conn.close()


@app.route("/health")
def health():
    return {"status": "healthy", "service": SERVICE_NAME}


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
    return {"service": SERVICE_NAME, "port": SERVICE_PORT, "discovery": "consul"}


if __name__ == "__main__":
    init_db()
    register_service()
    atexit.register(deregister_service)
    app.run(host="0.0.0.0", port=SERVICE_PORT)
