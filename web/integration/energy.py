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
                    currentSubscription {
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

        return {
            "total": round(price_info.get("total", 0), 4),
            "energy": round(price_info.get("energy", 0), 4),
            "tax": round(price_info.get("tax", 0), 4),
            "timestamp": price_info.get("startsAt", "N/A")
        }

    except requests.RequestException as e:
        return {"error": f"Request error: {str(e)}"}
