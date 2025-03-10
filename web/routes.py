from flask import Blueprint, jsonify
import subprocess
from config import CONFIG
from integration.calendar import get_calendar
from integration.weather import get_weather

# Define a Blueprint for routes
routes = Blueprint("routes", __name__)

@routes.route("/memory", methods=["GET"])
def check_memory():
    try:
        # Run `free -h` command
        result = subprocess.run(["free", "-h"], capture_output=True, text=True)
        lines = result.stdout.split("\n")

        # Extract memory values
        mem_values = lines[1].split()  # Second line (Memory)
        swap_values = lines[2].split()  # Third line (Swap)

        # Return data as JSON
        memory_info = {
            "total": mem_values[1],     # Total Memory
            "used": mem_values[2],      # Used Memory
            "free": mem_values[3],      # Free Memory
            "shared": mem_values[4],    # Shared Memory
            "buff/cache": mem_values[5], # Buffers + Cache
            "available": mem_values[6], # Available Memory
            "swap_total": swap_values[1],  # Total Swap
            "swap_used": swap_values[2],   # Used Swap
            "swap_free": swap_values[3]    # Free Swap
        }


        return jsonify({
            "title": "🖥 Minne",
            "data": memory_info
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@routes.route("/calendar", methods=["GET"])
def calendar():
    try:
        # Fetch and parse calendar data from CONFIG
        calendar_data = get_calendar(CONFIG['calendar'])

        return jsonify({
            "title": "📅 Kalender",
            "data": calendar_data
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@routes.route("/weather", methods=["GET"])
def weather():
    try:
        # Fetch and parse calendar data from CONFIG
        weather_data = get_weather(CONFIG['LAT'], CONFIG['LON'])

        return jsonify({
            "title": "🌤 Været",
            "data": weather_data['data']
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@routes.route("/ruter", methods=["GET"])
def ruter():
    return jsonify({
        "title": "🚌 Buss: Stig",
        "iframe_url": CONFIG['RUTER']
    })