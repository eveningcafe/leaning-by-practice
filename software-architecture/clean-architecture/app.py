# CLEAN ARCHITECTURE - Dependency Injection at entry point

import sys
sys.path.insert(0, "/app")

from flask import Flask

# Wire dependencies here (composition root)
from infrastructure.sqlite_repository import SQLiteUserRepository
# from infrastructure.postgres_repository import PostgresUserRepository
from application.user_service import UserService
from presentation.routes import create_routes

app = Flask(__name__)

# Dependency Injection: inject concrete implementation
# Option 1: SQLite
repo = SQLiteUserRepository()

# Option 2: PostgreSQL (uncomment to use)
# repo = PostgresUserRepository(
#     host="localhost",
#     port=5432,
#     database="mydb",
#     user="postgres",
#     password="secret"
# )

service = UserService(repo)  # Service receives interface, not concrete class
routes = create_routes(service)

app.register_blueprint(routes)


@app.route("/")
def index():
    return {
        "architecture": "clean",
        "layers": ["domain", "application", "infrastructure", "presentation"],
        "key": "dependency inversion"
    }


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
