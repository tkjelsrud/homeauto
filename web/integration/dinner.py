import requests
import datetime
import re
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Define shorthand mapping for Norwegian days
day_map = {
    "M": "Mandag",  # Mandag
    "T": "Tirsdag", # Placeholder (will resolve Tuesday/Thursday later)
    "O": "Onsdag", # Onsdag
    "T2": "Torsdag", # Placeholder for second "T"
    "F": "Fredag", # Fredag
    "L": "Lørdag", # Lørdag
    "S": "Søndag" # Søndag
}

def get_dinner(DINNERURL):
    response = requests.get(DINNERURL)

    logging.info(f"Response: {response}") 

    if response.status_code != 200:
        return {"error": "Failed to fetch dinner plan"}

    raw_text = response.text.strip()
    lines = raw_text.split("\n")
    entries = []

    # Step 1: Parse days and descriptions
    for line in lines:
        match = re.match(r"(VIKTIG|[MTOLFS]):\s*(.*)", line.strip())  # Match shorthand + text
        if match:
            shorthand, description = match.groups()

            if shorthand == "VIKTIG":
                logging.info(f"🔍 VIKTIG funnet: {description}") 
            else:
                # Determine if "T" is Tuesday or Thursday
                if shorthand == "T":
                    if "O" not in [e["shorthand"] for e in entries]:  
                        shorthand = "T"  # First "T" is Tuesday
                    else:
                        shorthand = "T2"  # Second "T" is Thursday

                entries.append({
                    "shorthand": shorthand,
                    "day": day_map[shorthand],  # Convert to full day name
                    "description": description
                })
        else:
            if len(entries) > 0:
                # We have found some days, so we stop now
                break

    logging.info(f"Dager: {entries}") 

    # Step 2: Assign Correct Dates
    today = datetime.date.today()
    weekday_map = ["Mandag", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    # Find next occurrence of first listed day
    first_day = entries[0]["day"]
    first_day_index = weekday_map.index(first_day)
    days_ahead = (first_day_index - today.weekday()) % 7  # Calculate offset

    start_date = today + datetime.timedelta(days=days_ahead)

    # Assign Dates
    for i, entry in enumerate(entries):
        entry["date"] = (start_date + datetime.timedelta(days=i)).strftime("%A, %d. %B")

    return entries  # ✅ Returns structured JSON data
