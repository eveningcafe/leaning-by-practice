# ORDER SERVICE - Discovers User Service via Consul

from flask import Flask, jsonify, request
import sqlite3
import consul
import requests
import atexit
import socket

app = Flask(__name__)
DATABASE = "/app/data/orders.db"
SERVICE_NAME = "order-service"
SERVICE_PORT = 5002

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


def discover_service(service_name):
    """Discover a service from Consul."""
    _, services = c.health.service(service_name, passing=True)
    if not services:
        return None
    # Return first healthy instance
    svc = services[0]["Service"]
    return f"http://{svc['Address']}:{svc['Port']}"


def init_db():
    conn = sqlite3.connect(DATABASE)
    conn.execute("CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY, user_id INTEGER, item TEXT)")
    conn.commit()
    conn.close()


@app.route("/health")
def health():
    return {"status": "healthy", "service": SERVICE_NAME}


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

    # Discover user-service from Consul
    user_service_url = discover_service("user-service")
    if not user_service_url:
        return jsonify({"error": "User service not found in Consul"}), 503

    # Call user-service directly (not via gateway!)
    try:
        resp = requests.get(f"{user_service_url}/users/{user_id}")
        if resp.status_code == 404:
            return jsonify({"error": "User not found"}), 404
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "User service unavailable"}), 503

    conn = sqlite3.connect(DATABASE)
    cursor = conn.execute("INSERT INTO orders (user_id, item) VALUES (?, ?)", (user_id, item))
    order_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return jsonify({
        "id": order_id,
        "user_id": user_id,
        "item": item,
        "discovered_from": user_service_url
    }), 201


@app.route("/")
def index():
    user_url = discover_service("user-service")
    return {
        "service": SERVICE_NAME,
        "port": SERVICE_PORT,
        "discovery": "consul",
        "user_service_discovered": user_url
    }


if __name__ == "__main__":
    init_db()
    register_service()
    atexit.register(deregister_service)
    app.run(host="0.0.0.0", port=SERVICE_PORT)
