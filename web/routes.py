from flask import Blueprint, jsonify
import subprocess
from config import CONFIG
import requests
import icalendar
from datetime import datetime, timezone

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


        return jsonify(memory_info)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@routes.route("/calendar", methods=["GET"])
def calendar():
    try:
        # Fetch and parse calendar data
        response = requests.get(CONFIG['calendar'])
        calendar_data = icalendar.Calendar.from_ical(response.text)

        events = []
        now = datetime.now(timezone.utc)

        for component in calendar_data.walk():
            if component.name == "VEVENT":
                event_start = component.get("DTSTART").dt
                event_summary = component.get("SUMMARY")

                if isinstance(event_start, datetime):
                    event_start = event_start.replace(tzinfo=timezone.utc)

                # Show only today's events
                if event_start.date() == now.date():
                    events.append({"summary": event_summary, "start": event_start.isoformat()})

        return jsonify(events)

    except Exception as e:
        return jsonify({"error": str(e)}), 500