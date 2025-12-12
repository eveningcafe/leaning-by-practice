# CLEAN ARCHITECTURE - PostgreSQL Version
# Only difference: import PostgresUserRepository instead of SQLite

import sys
import os
sys.path.insert(0, "/app")

from flask import Flask

from infrastructure.postgres_repository import PostgresUserRepository  # Changed!
from application.user_service import UserService
from presentation.routes import create_routes

app = Flask(__name__)

# Swap: PostgreSQL instead of SQLite
repo = PostgresUserRepository(
    host=os.getenv("DB_HOST", "db"),
    port=int(os.getenv("DB_PORT", 5432)),
    database=os.getenv("DB_NAME", "mydb"),
    user=os.getenv("DB_USER", "user"),
    password=os.getenv("DB_PASSWORD", "secret")
)

service = UserService(repo)  # Same service, different repo!
routes = create_routes(service)

app.register_blueprint(routes)


@app.route("/")
def index():
    return {
        "architecture": "clean",
        "database": "postgresql",
        "key": "same business logic, different infrastructure"
    }


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
