from flask import Blueprint, jsonify, render_template_string
import subprocess, os, logging
from config import CONFIG
from integration.calendar import get_calendar, get_calendarweek
from integration.birthday import get_birthdays_week, get_holidays_week
from integration.weather import get_weather
from integration.lights import get_zones, get_outdoor_sensor_temperatures
from integration.dinner import get_dinner, get_dinnerweek
from integration.energy import get_hvakosterstrom
from integration.waste import get_garbage
from integration.network import get_network
from integration.bluesound import get_powernode
from integration.timeplan import get_dagens_timeplaner, get_dagens_dag
from integration.mill import authenticate, get_mill_devices
from integration.renovation import get_renovation_costs
from integration.trello import get_trello_tasks
from integration.airthings import get_airthings

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

@routes.route("/bigcalendar", methods=["GET"])
def bigcalendar():
    try:
        from datetime import datetime, timedelta
        import logging
        
        # Sett opp 7 tomme ukedager (mandag–søndag)
        days = [
            {
                "weekday_index": i,
                "name": ["Mandag", "Tirsdag", "Onsdag", "Torsdag", "Fredag", "Lørdag", "Søndag"][i],
                "events": [],
                "dinner": None,
                "timeplaner": None,
                "waste": []
            }
            for i in range(7)
        ]
        
        # Fetch calendar data with error handling
        calendar_data = []
        try:
            calendar_data = get_calendarweek(CONFIG['calendar'])
        except Exception as e:
            logging.error(f"Calendar fetch failed: {e}")
        
        # Fetch birthday data with error handling
        birthday_data = []
        try:
            birthdays_file = CONFIG.get('BIRTHDAYS_FILE', './integration/birthdays.json')
            birthday_data = get_birthdays_week(birthdays_file)
            logging.info(f"Loaded {len(birthday_data)} birthday events")
        except Exception as e:
            logging.error(f"Birthday fetch failed: {e}")
        
        # Fetch holiday data with error handling
        holiday_data = []
        try:
            holidays_file = CONFIG.get('HOLIDAYS_FILE', './integration/holidays.json')
            holiday_data = get_holidays_week(holidays_file)
            logging.info(f"Loaded {len(holiday_data)} holiday events")
        except Exception as e:
            logging.error(f"Holiday fetch failed: {e}")
        
        # Fetch dinner data with error handling
        dinner_data = {"days": []}
        try:
            dinner_data = get_dinnerweek(CONFIG['DINNERURL'])
        except Exception as e:
            logging.error(f"Dinner fetch failed: {e}")
        
        # Fetch waste data with error handling
        waste_data = {}
        try:
            waste_data = get_garbage(CONFIG['GARBAGEURL'])
        except Exception as e:
            logging.error(f"Waste fetch failed: {e}")

        # Middagsplan har alltid week_offset = 0 → denne ukens middag
        for dinner in dinner_data["days"]:
            idx = dinner["weekday_index"]
            days[idx]["dinner"] = dinner["description"]

        # Kalender:
        # ➤ legg inn ALLE events (også neste uke)
        # ➤ legg events på riktig weekday_index
        # ➤ marker om det er neste uke eller ikke
        for evt in calendar_data:
            idx = evt["weekday_index"]

            days[idx]["events"].append({
                "summary": evt["summary"],
                "start": evt["start"],
                "is_next_week": (evt["week_offset"] > 0)
            })
        
        # Bursdager:
        # ➤ legg inn bursdags-events på samme måte som kalender-events
        for bday in birthday_data:
            idx = bday["weekday_index"]
            
            days[idx]["events"].append({
                "summary": bday["summary"],
                "start": bday["start"],
                "is_next_week": (bday["week_offset"] > 0)
            })
        
        # Helligdager:
        # ➤ legg inn helligdags-events på samme måte
        for holiday in holiday_data:
            idx = holiday["weekday_index"]
            
            days[idx]["events"].append({
                "summary": holiday["summary"],
                "start": holiday["start"],
                "is_next_week": (holiday["week_offset"] > 0)
            })

        # Hent timeplaner for dagens dag (kun ukedager 0-4)
        try:
            today_index = datetime.now().weekday()
            if 0 <= today_index <= 4:  # Mandag til Fredag
                timeplaner_data = get_dagens_timeplaner(CONFIG['TIMEPLANER_MAPPE'])
                days[today_index]["timeplaner"] = timeplaner_data
        except Exception as e:
            logging.error(f"Timeplaner fetch failed: {e}")

        # Søppelhenting - legg til hvis det er denne uken
        today = datetime.now().date()
        monday_this_week = today - timedelta(days=today.weekday())
        sunday_this_week = monday_this_week + timedelta(days=6)

        waste_icons = {
            "Restavfall": "♻️",
            "Papir": "📄"
        }

        for waste_type, date_str in waste_data.items():
            if waste_type in ["Restavfall", "Papir"]:
                # Parse date (format: "11.03.2025")
                try:
                    day, month, year = date_str.split(".")
                    waste_date = datetime(int(year), int(month), int(day)).date()
                    
                    # Sjekk om datoen er i denne uken
                    if monday_this_week <= waste_date <= sunday_this_week:
                        weekday_idx = waste_date.weekday()
                        icon = waste_icons.get(waste_type, "🗑️")
                        days[weekday_idx]["waste"].append({
                            "type": waste_type,
                            "icon": icon
                        })
                except Exception as e:
                    pass  # Ignorer feil i datoformat

        return api_response(
            "Stor Kalender",
            "📅",
            days,
            10 * MINUTE
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@routes.route("/lights", methods=["GET"])
def lights():
    try:
        # Fetch zones and outdoor sensor temperatures
        zone_data = get_zones(CONFIG['PHILIPSHUE_HOST'], CONFIG['PHILIPSHUE_KEY'])
        outdoor_temps = get_outdoor_sensor_temperatures(CONFIG['PHILIPSHUE_HOST'], CONFIG['PHILIPSHUE_KEY'])
        
        # Combine data
        lights_data = {
            "zones": zone_data,
            "outdoor_sensors": outdoor_temps
        }

        return api_response("Lys", "✨", lights_data, 30)

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

@routes.route("/mill", methods=["GET"])
def mill():
    # Authenticate and get devices
    auth = authenticate(CONFIG['MILL_USERNAME'], CONFIG['MILL_PASSWORD'])
    if not auth:
        return api_response("Mill", "🔥", {"error": "Authentication failed"}, refresh=5*MINUTE)
    
    devices = get_mill_devices(auth['idToken'])
    
    # Group devices by room
    rooms = {}
    for device in devices:
        room = device['room']
        if room not in rooms:
            rooms[room] = []
        rooms[room].append(device)
    
    return api_response("Mill Varme", "🔥", {"rooms": rooms}, refresh=2*MINUTE)

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

@routes.route("/renovation", methods=["GET"])
def renovation():
    try:
        # Fetch renovation costs from Google Sheets CSV
        costs_data = get_renovation_costs(CONFIG['RENOVATION_CSV_URL'])
        
        # Fetch tasks from Trello "I arbeid" list
        tasks = []
        try:
            tasks = get_trello_tasks(
                CONFIG['TRELLO_API_KEY'],
                CONFIG['TRELLO_TOKEN'],
                CONFIG['TRELLO_BOARD_ID']
            )
        except Exception as e:
            logging.error(f"Trello fetch failed: {e}")
        
        # Combine data
        result = {
            "costs": costs_data,
            "tasks": tasks
        }
        
        return api_response("🏠 Oppussing", "🏠", result, 30 * MINUTE)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@routes.route("/airthings", methods=["GET"])
def airthings():
    try:
        mac_address = CONFIG.get('AIRTHINGS_MAC')
        if not mac_address:
            return jsonify({"error": "AIRTHINGS_MAC not configured"}), 500
        airthings_data = get_airthings(mac_address)
        if "error" in airthings_data:
            return jsonify(airthings_data), 500
        return api_response("Luftkvalitet", "🌬️", airthings_data, 15 * MINUTE)
    except Exception as e:
        logging.error(f"Airthings error: {e}")
        return jsonify({"error": str(e)}), 500