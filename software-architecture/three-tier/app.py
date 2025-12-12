# THREE-TIER ARCHITECTURE
# Presentation → Business → Data

import sys
sys.path.insert(0, "/app")

from flask import Flask
from data.user_repository import init_db
from presentation.routes import api

app = Flask(__name__)
app.register_blueprint(api)


@app.route("/")
def index():
    return {"architecture": "three-tier", "layers": ["presentation", "business", "data"]}


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
