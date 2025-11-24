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
    import requests
    from datetime import datetime, timedelta
    import pytz

    oslo_tz = pytz.timezone("Europe/Oslo")
    now = datetime.now(oslo_tz)
    today = now.date()

    # Hent dagens priser
    url_today = today.strftime("%Y/%m-%d")
    url_today = f"https://www.hvakosterstrommen.no/api/v1/prices/{url_today}_NO1.json"

    prices_today = requests.get(url_today).json()

    # Hent morgendagens priser (kan være tom før kl 13)
    tomorrow = today + timedelta(days=1)
    url_tomorrow = tomorrow.strftime("%Y/%m-%d")
    url_tomorrow = f"https://www.hvakosterstrommen.no/api/v1/prices/{url_tomorrow}_NO1.json"

    try:
        prices_tomorrow = requests.get(url_tomorrow).json()
        max_tomorrow = max(prices_tomorrow, key=lambda p: p["NOK_per_kWh"])
    except:
        max_tomorrow = None

    def parse_time(timestr):
        dt = datetime.fromisoformat(timestr.replace("Z", "+00:00"))
        return dt.astimezone(oslo_tz)

    # Finn nåværende og neste pris
    current_price = None
    next_price = None

    for i, price in enumerate(prices_today):
        start = parse_time(price["time_start"])
        end = parse_time(price["time_end"])

        if start <= now < end:
            current_price = price
            if i + 1 < len(prices_today):
                next_price = prices_today[i + 1]

    max_today = max(prices_today, key=lambda p: p["NOK_per_kWh"])

    return {
        "now": {
            "price": current_price["NOK_per_kWh"],
            "from": current_price["time_start"],
            "to": current_price["time_end"]
        },
        "next": {
            "price": next_price["NOK_per_kWh"] if next_price else None,
            "from": next_price["time_start"] if next_price else None,
            "to": next_price["time_end"] if next_price else None
        },
        "max_today": {
            "price": max_today["NOK_per_kWh"],
            "from": max_today["time_start"],
            "to": max_today["time_end"]
        },
        "max_tomorrow": {
            "price": max_tomorrow["NOK_per_kWh"] if max_tomorrow else None,
            "from": max_tomorrow["time_start"] if max_tomorrow else None,
            "to": max_tomorrow["time_end"] if max_tomorrow else None
        }
    }