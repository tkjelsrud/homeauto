import requests

# dnb_tech = get_fund_data("F0GBR04NHA", "DNB Teknologi")
# klp_global = get_fund_data("F0GBR06R4F", "KLP AksjeGlobal Indeks V")
# alfred berg gambak F0GBR04NHA

def get_fund():
    url = "https://www.alfredberg.no/wp-json/morningstar/v1/fund/detail"
    payload = {
        "nonce": "0b3da3eaef",
        "language": "nb-NO",
        "sec_id": "F0GBR04NHA",
        "currency": "NOK"
    }
    headers = {
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        
        # Extract required data
        fund_name = data.get("data", {}).get("Name", "Unknown Fund")
        weekly_movement = data.get("data", {}).get("TrailingPerformance", {}).get("W1", "N/A")
        ytd_movement = data.get("data", {}).get("TrailingPerformance", {}).get("M255", "N/A")  # Year-to-date (assumed to be M255)
        
        return {
            "Fund Name": fund_name,
            "Weekly Change": weekly_movement,
            "Year-to-Date Change": ytd_movement
        }
    
    return {"error": "Failed to fetch data"}

# Example Usage
fund_info = get_fund_data()
print(fund_info)