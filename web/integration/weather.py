import requests
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def _fetch_timeseries(url, headers):
    """Helper to fetch timeseries from met.no endpoints with basic error handling."""
    try:
        resp = requests.get(url, headers=headers, timeout=8)
        if resp.status_code != 200:
            logging.error(f"Weather request failed {resp.status_code} for {url}")
            return None
        return resp.json().get("properties", {}).get("timeseries", [])
    except Exception as e:
        logging.error(f"Weather request error for {url}: {e}")
        return None


def get_weather(LAT, LON):
    """
    Fetch location forecast and overlay current temperature from nowcast.
    - Base: locationforecast (structure expected by frontend)
    - Override: replace instant.air_temperature with nowcast when available
    """
    HEADERS = {"User-Agent": "homeweather/1.0 (your@email.com)"}

    loc_url = f"https://api.met.no/weatherapi/locationforecast/2.0/compact?lat={LAT}&lon={LON}"
    now_url = f"https://api.met.no/weatherapi/nowcast/2.0/complete?lat={LAT}&lon={LON}"

    logging.info(f"Requesting locationforecast from {loc_url}")
    loc_series = _fetch_timeseries(loc_url, HEADERS) or []

    if not loc_series:
        return {"error": "No weather data available"}

    # Use first entry as base response
    base_entry = loc_series[0]

    # Try to fetch a more accurate current temperature from nowcast
    logging.info(f"Requesting nowcast from {now_url}")
    now_series = _fetch_timeseries(now_url, HEADERS) or []

    if now_series:
        now_entry = now_series[0]
        now_temp = (
            now_entry.get("data", {})
            .get("instant", {})
            .get("details", {})
            .get("air_temperature")
        )
        if now_temp is not None:
            try:
                base_entry.setdefault("data", {}).setdefault("instant", {}).setdefault("details", {})[
                    "air_temperature"
                ] = now_temp
                logging.info(f"Overrode air_temperature with nowcast: {now_temp}°C")
            except Exception:
                pass

    return base_entry