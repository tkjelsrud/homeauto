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

        if response.status_code != 200:
            return {"error": f"API request failed with status {response.status_code}"}
        
        data = response.json()
        if not data:
            return {"error": "Empty API response"}

        logging.info(data)  # ✅ Now this will be logged

        # Safely extract data using `.get()` to avoid `NoneType` errors
        viewer = data.get("data", {}).get("viewer", {})
        homes = viewer.get("homes", [])

        if not homes:
            return {"error": "No home data found in Tibber API response"}

        subscription = homes[0].get("currentSubscription", {})
        if not subscription:
            return {"error": "No current subscription data found"}

        price_info = subscription.get("priceInfo", {}).get("current", {})
        if not price_info:
            return {"error": "No current price data available"}

        # ✅ Successfully extracted price data
        return {
            "total": price_info.get("total", "N/A"),
            "energy": price_info.get("energy", "N/A"),
            "tax": price_info.get("tax", "N/A"),
            "timestamp": price_info.get("startsAt", "N/A")
        }

    except requests.RequestException as e:
        return {"error": f"Request error: {str(e)}"}
