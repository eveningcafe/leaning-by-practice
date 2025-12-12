# PRESENTATION LAYER - HTTP Handlers

from flask import Blueprint, request, jsonify


def create_routes(user_service):
    api = Blueprint("api", __name__)

    @api.route("/users", methods=["GET"])
    def get_users():
        return jsonify(user_service.list_users())

    @api.route("/users/<int:user_id>", methods=["GET"])
    def get_user(user_id):
        try:
            return jsonify(user_service.get_user(user_id))
        except ValueError as e:
            return jsonify({"error": str(e)}), 404

    @api.route("/users", methods=["POST"])
    def create_user():
        data = request.json
        try:
            user = user_service.register(data.get("name"), data.get("email"))
            return jsonify(user), 201
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

    @api.route("/users/<int:user_id>", methods=["DELETE"])
    def delete_user(user_id):
        try:
            user_service.remove_user(user_id)
            return jsonify({"deleted": True})
        except ValueError as e:
            return jsonify({"error": str(e)}), 404

    return api
