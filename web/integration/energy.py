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

        # Extracting relevant data
        homes = data.get("data", {}).get("viewer", {}).get("homes", [])
        if not homes:
            return {"error": "No home data found in Tibber API response"}

        price_info = homes[0].get("currentSubscription", {}).get("priceInfo", {}).get("current", {})

        if not price_info:
            return {"error": "No current price data available"}

        return {
            "total": round(price_info.get("total", 0), 4),  # Rounded for better readability
            "energy": round(price_info.get("energy", 0), 4),
            "tax": round(price_info.get("tax", 0), 4),
            "timestamp": price_info.get("startsAt", "N/A")
        }

    except requests.RequestException as e:
        return {"error": f"Request error: {str(e)}"}