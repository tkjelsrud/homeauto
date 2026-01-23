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
                "status": "on" if is_on else "off"
            })

        return zones

    except requests.RequestException as e:
        logging.error(f"Error connecting to Hue Bridge: {e}")
        return None


def get_outdoor_sensor_temperatures(HUEHOST, APIKEY):
    """
    Find Philips Hue outdoor sensors and return their temperatures.
    
    Returns:
        list: Array of temperature readings in Celsius from outdoor sensors
    """
    URL = f"http://{HUEHOST}/api/{APIKEY}/sensors"

    try:
        response = requests.get(URL)
        if response.status_code != 200:
            logging.error(f"Failed to retrieve sensors. Status Code: {response.status_code}")
            return []

        sensors_data = response.json()
        temperatures = []

        for sensor_id, sensor_info in sensors_data.items():
            # Look for temperature sensors (type: ZLLTemperature or CLIPTemperature)
            sensor_type = sensor_info.get("type", "")
            sensor_name = sensor_info.get("name", "Unknown")
            
            # Check if it's a temperature sensor and if it's an outdoor sensor
            if "Temperature" in sensor_type:
                is_outdoor = "outdoor" in sensor_name.lower() or "ute" in sensor_name.lower()
                
                if is_outdoor:
                    state = sensor_info.get("state", {})
                    # Temperature is in 1/100th of degrees Celsius
                    temp_raw = state.get("temperature")
                    
                    if temp_raw is not None:
                        temp_celsius = temp_raw / 100.0
                        temperatures.append({
                            "id": sensor_id,
                            "name": sensor_name,
                            "temperature": temp_celsius
                        })
                        logging.info(f"Found outdoor sensor: {sensor_name} = {temp_celsius}°C")

        return temperatures

    except requests.RequestException as e:
        logging.error(f"Error connecting to Hue Bridge for sensors: {e}")
        return []