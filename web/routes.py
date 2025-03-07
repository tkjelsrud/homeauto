from flask import Blueprint, jsonify

main_blueprint = Blueprint("main", __name__)

@main_blueprint.route("/")
def home():
    return jsonify({"message": "Welcome to the Home Automation API!"})

@main_blueprint.route("/power")
def get_power():
    # Simulated power usage data
    return jsonify({"power_usage": 150})