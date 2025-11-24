from flask import Blueprint, jsonify, render_template_string
import subprocess, os
from config import CONFIG
from integration.calendar import get_calendar
from integration.weather import get_weather
from integration.lights import get_zones
from integration.dinner import get_dinner
from integration.energy import get_hvakosterstrom
from integration.waste import get_garbage
from integration.network import get_network
from integration.bluesound import get_powernode
from integration.timeplan import get_dagens_timeplaner, get_dagens_dag

# Define a Blueprint for routes
routes = Blueprint("routes", __name__)

HOUR = 60 * 60
MINUTE = 60

def api_response(title, icon, data, refresh=1 * MINUTE):
    return jsonify({
        "title": title,
        "icon": icon,
        "data": data,
        "refresh": refresh  # Default 30s unless overridden
    })

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


        return api_response("Ressurser", "🖥", memory_info, 10)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@routes.route("/calendar", methods=["GET"])
def calendar():
    try:
        # Fetch and parse calendar data from CONFIG
        calendar_data = get_calendar(CONFIG['calendar'])

        sorted_events = sorted(calendar_data, key=lambda x: x["start"], reverse=False)

        return api_response("Kalender", "📅", sorted_events, 10 * MINUTE)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@routes.route("/lights", methods=["GET"])
def lights():
    try:
        # Fetch and parse calendar data from CONFIG
        zone_data = get_zones(CONFIG['PHILIPSHUE_HOST'], CONFIG['PHILIPSHUE_KEY'])

        return api_response("Lys", "✨", zone_data, 30)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@routes.route("/dinner", methods=["GET"])
def dinner():
    try:
        # Fetch and parse calendar data from CONFIG
        dinner_data = get_dinner(CONFIG['DINNERURL'])

        return api_response("Middager",  "🍽️", dinner_data, HOUR)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@routes.route("/timeplaner", methods=["GET"])
def timeplaner():
    try:
        # Fetch and parse calendar data from CONFIG
        dagen = get_dagens_dag()
        timeplaner = get_dagens_timeplaner(CONFIG['TIMEPLANER_MAPPE'])

        return api_response("Timeplaner: " + dagen,  "🍽️", timeplaner, HOUR)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@routes.route("/weather", methods=["GET"])
def weather():
    try:
        # Fetch and parse calendar data from CONFIG
        weather_data = get_weather(CONFIG['LAT'], CONFIG['LON'])

        return api_response("Været", "🌤", weather_data['data'])

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@routes.route("/energy", methods=["GET"])
def energy():
    try:
        # Fetch and parse calendar data from CONFIG
        energy_data = get_hvakosterstrom() #get_tibber(CONFIG['TIBBER_TOKEN'])

        if "error" in energy_data:
            return jsonify(energy_data), 500  # Return proper HTTP status

        return api_response("Strøm", "⚡", energy_data, MINUTE)

    except Exception as e:
        return jsonify({"error": str(e)}), 500




@routes.route("/waste", methods=["GET"])
def waste():
    try:
        # Fetch and parse calendar data from CONFIG
        garbage_schedule = get_garbage(CONFIG['GARBAGEURL'])

        return api_response("Søppelhenting", "♻️", garbage_schedule, HOUR)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@routes.route("/network", methods=["GET"])
def network():
    try:
        # Fetch and parse calendar data from CONFIG
        netwStr = CONFIG['network']
        network = get_network(netwStr)

        return api_response("Nettverk", "🌐", network, MINUTE * 5)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@routes.route("/music", methods=["GET"])
def bluesound():
    try:
        # Fetch and parse calendar data from CONFIG
        bluesound = get_powernode()

        return api_response("Bluesound", "🎵", bluesound, 10)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@routes.route("/ruter", methods=["GET"])
def ruter():
    return jsonify({
        "title": "Buss: Stig",
        "icon": "🚌",
        "iframe": CONFIG['RUTER']
    })

@routes.route('/update', methods=['GET'])
def update():
    try:
        # Change to your Flask app directory
        repo_path = os.path.dirname(os.path.abspath(__file__))

        # Run git pull and capture the output
        result = subprocess.run(
            ["git", "-C", repo_path, "pull"],
            capture_output=True, text=True, check=True
        )

        output = result.stdout + result.stderr  # Combine stdout and stderr

        # Simple HTML template for displaying the output
        html_template = """
        <html>
        <head>
            <title>Update Result</title>
            <style>
                body { font-family: Arial, sans-serif; padding: 20px; }
                pre { background: #f4f4f4; padding: 10px; border-radius: 5px; }
                a { display: inline-block; margin-top: 10px; text-decoration: none; color: blue; }
            </style>
        </head>
        <body>
            <h2>Git Update Output</h2>
            <pre>{{ output }}</pre>
            <a href="/">Back to Index</a>
        </body>
        </html>
        """

        return render_template_string(html_template, output=output)

    except subprocess.CalledProcessError as e:
        return f"""
        <html>
        <body>
            <h2>Update Failed</h2>
            <pre>{e.stderr}</pre>
            <a href="/">Back to Index</a>
        </body>
        </html>
        """, 500