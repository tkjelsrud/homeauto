import requests
import datetime
from datetime import timedelta
import re
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def get_birthdays(BIRTHDAYURL):
    try:
        response = requests.get(BIRTHDAYURL)

        logging.info(f"Birthdays response: {response}") 

        if response.status_code != 200:
            return {"error": "Failed to fetch dinner plan"}

        raw_text = response.text.strip()
        lines = raw_text.split("\n")
        
        today = datetime.today().date()  # Get today's date
        seven_days_ahead = today + timedelta(days=7)  # 7 days ahead

        # Regex to match name, day, month, and optional year
        pattern = re.compile(r"(\w+) (\d{1,2}|\w)\.(\d{1,2})\.?(\d{2,4})?")

        upcoming_birthdays = []  # Store matches
        numDates = 0

        for line in lines:
            match = pattern.match(line.strip())
            if match:
                name, day, month, year = match.groups()

                if day.isdigit():  # Ignore "x" placeholders
                    day = int(day)
                    month = int(month)
                    numDates = numDates + 1
                    
                    # If year is missing, assume current year
                    if not year:
                        year = today.year
                    elif len(year) == 2:  # Convert 2-digit year to 4-digit (assuming 2000+)
                        year = int(f"20{year}")
                    else:
                        year = int(year)

                    # Convert to date object
                    birthday = datetime(year=today.year, month=month, day=day).date()

                    # If birthday has already passed this year, assume next year
                    if birthday < today:
                        birthday = datetime(year=today.year + 1, month=month, day=day).date()

                    # Check if the birthday is within the next 7 days
                    if today <= birthday <= seven_days_ahead:
                        upcoming_birthdays.append({"name": name, "date": birthday.strftime("%A, %d. %B")})

        if numDates == 0:
            return {"error": "No known birthdays - data issue"}
        else:
            return {"birthdays": upcoming_birthdays, "knownDates": numDates}

    except requests.RequestException as e:
        return {"error": str(e)}