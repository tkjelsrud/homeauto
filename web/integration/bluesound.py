import requests
import xml.etree.ElementTree as ET

def get_powernode():
    URL = "http://powernode2.local:11000/Status"

    try:
        response = requests.get(URL, timeout=5)
        if response.status_code == 200:
            root = ET.fromstring(response.text)

            status_data = {
                "title": root.findtext("title1", "Unknown"),  # Currently playing source
                "state": root.findtext("state", "Unknown"),  # Playing/Paused
                "volume": root.findtext("volume", "Unknown"),  # Volume level
                "input": root.findtext("inputId", "Unknown"),  # Input source
                "db": root.findtext("db", "Unknown"),  # Decibel level
                "image": root.findtext("image", None)  # Cover image (if available)
            }

            return status_data
        
        else:
            return {"error": f"Failed to fetch status: {response.status_code}"}
    
    except requests.RequestException as e:
        return {"error": str(e)}