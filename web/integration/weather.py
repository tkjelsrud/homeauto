import requests

def get_weather(LAT, LON):
    URL = f"https://api.met.no/weatherapi/locationforecast/2.0/compact?lat={LAT}&lon={LON}"
    HEADERS = {"User-Agent": "homeweather/1.0 (your@email.com)"}

    response = requests.get(URL, headers=HEADERS)
    if response.status_code == 200:
        data = response.json()
        timeseries = data["properties"]["timeseries"]

        forecast = []
        for i in [0, 3, 6]:  # Now, in 3 hours, and in 6 hours
            try:
                entry = timeseries[i]
                temp = entry["data"]["instant"]["details"]["air_temperature"]
                precipitation = entry["data"].get("next_1_hours", {}).get("summary", {}).get("symbol_code", "unknown")

                forecast.append({"hours": i, "temperature": f"{temp}°C", "symbol": precipitation})
            except IndexError:
                forecast.append({"hours": i, "temperature": "N/A", "symbol": "N/A"})

        return forecast
    else:
        return [{"hours": i, "temperature": "Ukjent temp.", "symbol": "unknown"} for i in [0, 3, 6]]