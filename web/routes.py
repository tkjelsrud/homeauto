from flask import Blueprint, jsonify
import subprocess
from config import CONFIG
from integration.calendar import get_calendar
from integration.weather import get_weather
from integration.lights import get_zones
from integration.dinner import get_dinner
from integration.energy import get_tibber
from integration.waste import get_garbage

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
            "title": "Minne",
            "icon": "🖥",
            "data": memory_info
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@routes.route("/calendar", methods=["GET"])
def calendar():
    try:
        # Fetch and parse calendar data from CONFIG
        calendar_data = get_calendar(CONFIG['calendar'])

        sorted_events = sorted(calendar_data, key=lambda x: x["start"], reverse=False)

        return jsonify({
            "title": "Kalender",
            "icon": "📅",
            "data": sorted_events
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@routes.route("/lights", methods=["GET"])
def lights():
    try:
        # Fetch and parse calendar data from CONFIG
        zone_data = get_zones(CONFIG['PHILIPSHUE_HOST'], CONFIG['PHILIPSHUE_KEY'])

        return jsonify({
            "title": "Lys",
            "icon": "✨",
            "data": zone_data
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@routes.route("/dinner", methods=["GET"])
def dinner():
    try:
        # Fetch and parse calendar data from CONFIG
        dinner_data = get_dinner(CONFIG['DINNERURL'])

        return jsonify({
            "title": "Middager",
            "icon": "🍽️",
            "data": dinner_data
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@routes.route("/weather", methods=["GET"])
def weather():
    try:
        # Fetch and parse calendar data from CONFIG
        weather_data = get_weather(CONFIG['LAT'], CONFIG['LON'])

        return jsonify({
            "title": "Været",
            "icon": "🌤",
            "data": weather_data['data']
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@routes.route("/energy", methods=["GET"])
def energy():
    try:
        # Fetch and parse calendar data from CONFIG
        energy_data = get_tibber(CONFIG['TIBBER_TOKEN'])

        if "error" in energy_data:
            return jsonify(energy_data), 500  # Return proper HTTP status

        return jsonify({
            "title": "Strøm",
            "icon": "⚡",
            "data": energy_data
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@routes.route("/waste", methods=["GET"])
def waste():
    try:
        # Fetch and parse calendar data from CONFIG
        garbage_schedule = get_garbage()

        return jsonify({
            "title": "Søppelhenting",
            "icon": "♻️",
            "data": garbage_schedule
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@routes.route("/ruter", methods=["GET"])
def ruter():
    return jsonify({
        "title": "Buss: Stig",
        "icon": "🚌",
        "iframe": CONFIG['RUTER']
    })