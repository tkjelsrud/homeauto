import requests
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

BASE_URL = "https://api.millnorwaycloud.com"

def authenticate(username, password):
    """
    Authenticate with Mill API and return tokens
    Returns: dict with idToken and refreshToken
    """
    signin_url = f"{BASE_URL}/customer/auth/sign-in"
    signin_payload = {
        "login": username,
        "password": password
    }
    
    try:
        response = requests.post(signin_url, json=signin_payload)
        
        if response.status_code != 200:
            logging.error(f"Mill authentication failed: {response.text}")
            return None
        
        auth_data = response.json()
        return {
            "idToken": auth_data.get("idToken"),
            "refreshToken": auth_data.get("refreshToken")
        }
    except Exception as e:
        logging.error(f"Mill authentication error: {e}")
        return None

def get_mill_devices(id_token):
    """
    Get all Mill devices across all houses
    Returns: list of devices with room info
    """
    headers = {
        "Authorization": f"Bearer {id_token}"
    }
    
    try:
        # Get houses
        houses_url = f"{BASE_URL}/houses"
        response = requests.get(houses_url, headers=headers)
        
        if response.status_code != 200:
            logging.error(f"Failed to fetch houses: {response.text}")
            return []
        
        houses_data = response.json()
        
        # Extract own and shared houses
        if isinstance(houses_data, dict):
            own_houses = houses_data.get("ownHouses", [])
            shared_houses = houses_data.get("sharedHouses", [])
            all_houses = own_houses + shared_houses
        else:
            all_houses = houses_data
        
        # Collect all devices from all houses
        all_devices = []
        
        for house in all_houses:
            if isinstance(house, str):
                house_id = house
                house_name = house
            else:
                house_id = house.get("id")
                house_name = house.get("name", house_id)
            
            # Get devices for this house
            devices_url = f"{BASE_URL}/houses/{house_id}/devices"
            response = requests.get(devices_url, headers=headers)
            
            if response.status_code == 200:
                rooms_data = response.json()
                
                # Data is a list of rooms with devices
                for room in rooms_data:
                    room_name = room.get("roomName", "Unknown")
                    devices = room.get("devices", [])
                    
                    for device in devices:
                        # Extract relevant info
                        name = device.get("customName", "Unnamed")
                        device_type = device.get("deviceType", {}).get("childType", {}).get("name", "Unknown")
                        is_connected = device.get("isConnected", False)
                        
                        # Get metrics
                        metrics = device.get("lastMetrics", {})
                        temp_ambient = metrics.get("temperatureAmbient")
                        power = metrics.get("currentPower", 0)
                        humidity = metrics.get("humidity")
                        
                        # Get settings
                        settings = device.get("deviceSettings", {}).get("reported", {})
                        target_temp = settings.get("temperature_normal")
                        mode = settings.get("operation_mode", "unknown")
                        
                        all_devices.append({
                            "house": house_name,
                            "room": room_name,
                            "name": name,
                            "type": device_type,
                            "connected": is_connected,
                            "ambient_temp": temp_ambient,
                            "target_temp": target_temp,
                            "power": power,
                            "humidity": humidity,
                            "mode": mode
                        })
        
        return all_devices
        
    except Exception as e:
        logging.error(f"Error fetching Mill devices: {e}")
        return []
