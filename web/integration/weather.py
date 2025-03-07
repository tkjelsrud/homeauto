import requests

def get_weather():
    LAT, LON = 59.94714276081971, 10.815522051014094  # Replace with your location
    URL = f"https://api.met.no/weatherapi/locationforecast/2.0/compact?lat={LAT}&lon={LON}"

    HEADERS = {"User-Agent": "homeweather/1.0 (your@email.com)"}

    response = requests.get(URL, headers=HEADERS)
    if response.status_code == 200:
        data = response.json()
        temp = data["properties"]["timeseries"][0]["data"]["instant"]["details"]["air_temperature"]
        print(f"Current temperature: {temp}°C")
    else:
        print("Failed to fetch weather data")