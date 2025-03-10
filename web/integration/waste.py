# https://www.oslo.kommune.no/xmlhttprequest.php?service=ren.search&street=Årvollveien&number=34&letter=&street_id=18808
import requests

def get_garbage():
    URL = "https://www.oslo.kommune.no/xmlhttprequest.php?service=ren.search&street=Årvollveien&number=34&letter=&street_id=18808"  # Replace with actual API URL
    HEADERS = {"User-Agent": "homeauto/1.0 (your@email.com)"}  # Customize user agent

    response = requests.get(URL, headers=HEADERS)

    if response.status_code == 200:
        data = response.json()

        schedule = {}

        # ✅ Only process the first entry (to avoid duplicates)
        hentepunkts = data["data"]["result"][0]["HentePunkts"]

        for hentepunkt in hentepunkts:  # Only check unique pickup locations
            for tjeneste in hentepunkt["Tjenester"]:  # Services per location
                fraksjon = tjeneste["Fraksjon"]["Tekst"]  # "Restavfall" or "Papir"
                dato = tjeneste["TommeDato"]  # Pickup date

                if fraksjon in ["Restavfall", "Papir"] and fraksjon not in schedule:
                    schedule[fraksjon] = dato  # Save only the first match

        return schedule  # ✅ Example output: {'Restavfall': '11.03.2025', 'Papir': '19.03.2025'}

    else:
        return {"error": "Failed to fetch data"}
