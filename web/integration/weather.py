import requests
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def get_weather(LAT, LON):
    URL = f"https://api.met.no/weatherapi/locationforecast/2.0/compact?lat={LAT}&lon={LON}"
    HEADERS = {"User-Agent": "homeweather/1.0 (your@email.com)"}

    logging.info(f"Requesting weather data from {URL}")  # ✅ Now this will be logged

    response = requests.get(URL, headers=HEADERS)
    if response.status_code == 200:
        data = response.json()
        timeseries = data["properties"]["timeseries"]

        if timeseries:
            return timeseries[0]  # Return the latest available weather entry

    return {"error": "No weather data available"}