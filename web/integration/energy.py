import requests

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
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract relevant price details
            homes = data.get("data", {}).get("viewer", {}).get("homes", [])
            if homes and "currentSubscription" in homes[0]:
                price_info = homes[0]["currentSubscription"]["priceInfo"]["current"]
                return {
                    "total": price_info["total"],
                    "energy": price_info["energy"],
                    "tax": price_info["tax"],
                    "timestamp": price_info["startsAt"]
                }
            else:
                return {"error": "No price data available"}
        else:
            return {"error": f"API request failed with status {response.status_code}"}
    
    except requests.RequestException as e:
        return {"error": f"Request error: {str(e)}"}

# Example Usage:
TIBBER_TOKEN = "your_tibber_api_token_here"
price_data = fetch_tibber_price(TIBBER_TOKEN)

print(price_data)  # ✅ Prints structured price data