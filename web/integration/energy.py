import requests
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def get_tibber(token):
    """
    Fetches the current electricity price from Tibber API.
    
    :param token: Tibber API Bearer Token
    :return: JSON with price details or error message
    """
    url = "https://api.tibber.com/v1-beta/gql"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "query": """
        {
        viewer {
            homes {
            timeZone
            address {
                address1
                postalCode
                city
            }
            consumption(resolution: DAILY, last: 3) {
                nodes {
                from
                to
                cost
                unitPrice
                unitPriceVAT
                consumption
                consumptionUnit
                }
            }
            currentSubscription {
                status
                priceInfo {
                current {
                    total
                    energy
                    tax
                    startsAt
                }
                }
            }
            }
        }
        }
        """
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()

        logging.info(f"🔍 Full API Response: {data}")  # ✅ Debugging

        if not isinstance(data, dict):
            return {"error": "API response is not a dictionary"}

        if "data" not in data:
            return {"error": "No 'data' key found in response"}

        viewer = data["data"].get("viewer")
        if viewer is None:
            return {"error": "No 'viewer' key in response"}

        homes = viewer.get("homes", [])
        if not homes:
            return {"error": "No home data found in Tibber API response"}

        subscription = homes[0].get("currentSubscription")
        if subscription is None:
            return {"error": "No current subscription data found"}

        price_info = subscription.get("priceInfo", {}).get("current")
        if price_info is None:
            return {"error": "No current price data available"}

        consumption = homes[0].get("consumption")
        if consumption is None:
            return {"error": "No current consumption data found"}

        return {
            "total": round(price_info.get("total", 0), 4),
            "energy": round(price_info.get("energy", 0), 4),
            "tax": round(price_info.get("tax", 0), 4),
            "timestamp": price_info.get("startsAt", "N/A"),
            "consumption": consumption.get("nodes", [])
        }

    except requests.RequestException as e:
        return {"error": f"Request error: {str(e)}"}

def get_hvakosterstrom():
    #https://www.hvakosterstrommen.no/api/v1/prices/2025/09-01_NO1.json

    import requests
    from datetime import datetime, timedelta
    import pytz

    # Sett sone for korrekt sammenligning
    oslo_tz = pytz.timezone("Europe/Oslo")
    now = datetime.now(oslo_tz)
    today = now.date()
    hour = now.hour

    # Formater dato for URL
    url_date = today.strftime("%Y/%m-%d")
    url = f"https://www.hvakosterstrommen.no/api/v1/prices/{url_date}_NO1.json"

    # Hent prisdata
    response = requests.get(url)
    prices = response.json()

    # Finn "nåværende" og "neste" time
    current_price = None
    next_price = None
    max_price = None

    # Konverter til datetime for sammenligning
    def parse_time(timestr):
        return datetime.fromisoformat(timestr)

    # Finn relevante priser
    for price in prices:
        start = parse_time(price["time_start"]).astimezone(oslo_tz)
        if start.hour == hour and start.date() == today:
            current_price = price
        elif start.hour == hour + 1 and start.date() == today:
            next_price = price

    # Høyeste pris
    max_price = max(prices, key=lambda p: p["NOK_per_kWh"])

    # Vis resultat
    print("⚡ Pris denne timen:")
    print(f"{current_price['NOK_per_kWh']} kr/kWh ({current_price['time_start']} - {current_price['time_end']})")

    print("\n⏭️ Pris neste time:")
    print(f"{next_price['NOK_per_kWh']} kr/kWh ({next_price['time_start']} - {next_price['time_end']})")

    print("\n🔺 Høyeste pris i dag:")
    print(f"{max_price['NOK_per_kWh']} kr/kWh ({max_price['time_start']} - {max_price['time_end']})")

    #return {
    #    "total": round(price_info.get("total", 0), 4),
    #    "energy": round(price_info.get("energy", 0), 4),
    #    "tax": round(price_info.get("tax", 0), 4),
    #    "timestamp": price_info.get("startsAt", "N/A"),
    #    "consumption": consumption.get("nodes", [])
    #}