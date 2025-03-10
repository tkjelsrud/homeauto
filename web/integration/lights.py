import requests
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def get_zones(HUEHOST, APIKEY):
    URL = f"http://{HUEHOST}/api/{APIKEY}/groups"

    try:
        response = requests.get(URL)
        if response.status_code != 200:
            logging.error(f"Failed to retrieve zones. Status Code: {response.status_code}")
            return None

        zones_data = response.json()

        zones = []
        for zone_id, zone_info in zones_data.items():
            zone_name = zone_info.get("name", "Unknown")
            num_lights = len(zone_info.get("lights", []))

            # Determine on/off status (if any light is on, consider the zone "on")
            is_on = zone_info.get("state", {}).get("any_on", False)

            zones.append({
                "id": zone_id,
                "name": zone_name,
                "num_lights": num_lights,
                "status": "On" if is_on else "Off"
            })

        return zones

    except requests.RequestException as e:
        logging.error(f"Error connecting to Hue Bridge: {e}")
        return None