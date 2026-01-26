import json
import os
from datetime import datetime, timedelta, date
import requests
import re
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def get_holidays_week(holidays_file):
    """
    Read holidays from JSON file and return holidays for this week and next week
    in calendar event format (with weekday_index and week_offset)
    """
    try:
        if not os.path.exists(holidays_file):
            logging.error(f"Holidays file not found: {holidays_file}")
            return []
        
        with open(holidays_file, 'r', encoding='utf-8') as f:
            holidays = json.load(f)
        
        today = date.today()
        this_iso_year, this_iso_week, _ = today.isocalendar()
        next_iso_week = this_iso_week + 1
        
        holiday_events = []
        
        for holiday in holidays:
            name = holiday.get('name', 'Ukjent')
            icon = holiday.get('icon', '📅')
            date_str = holiday.get('date')
            week_num = holiday.get('week')
            duration = holiday.get('duration', 1)
            
            # Handle week-based holidays (e.g., Vinterferie uke 8)
            if week_num:
                # Check if this holiday week matches current or next week
                for week_offset in range(duration):
                    check_week = week_num + week_offset
                    
                    if check_week == this_iso_week:
                        # Find Monday of this week
                        days_since_monday = today.weekday()
                        monday = today - timedelta(days=days_since_monday)
                        
                        # Add event for each day of the week
                        for day_offset in range(5):  # Monday to Friday
                            event_date = monday + timedelta(days=day_offset)
                            
                            holiday_events.append({
                                "summary": f"{icon} {name}",
                                "start": event_date.strftime("%Y-%m-%d 00:00:00"),
                                "weekday_index": event_date.weekday(),
                                "week_offset": 0,
                                "is_holiday": True
                            })
                    
                    elif check_week == next_iso_week:
                        # Find Monday of next week
                        days_until_next_monday = 7 - today.weekday()
                        next_monday = today + timedelta(days=days_until_next_monday)
                        
                        # Add event for each day of the week
                        for day_offset in range(5):  # Monday to Friday
                            event_date = next_monday + timedelta(days=day_offset)
                            
                            holiday_events.append({
                                "summary": f"{icon} {name}",
                                "start": event_date.strftime("%Y-%m-%d 00:00:00"),
                                "weekday_index": event_date.weekday(),
                                "week_offset": 1,
                                "is_holiday": True
                            })
            
            # Handle date-based holidays (MM-DD format)
            elif date_str:
                try:
                    month, day = map(int, date_str.split('-'))
                    
                    # Check this year and next year
                    holiday_this_year = date(today.year, month, day)
                    holiday_dates = [holiday_this_year]
                    
                    if holiday_this_year < today:
                        holiday_dates.append(date(today.year + 1, month, day))
                    
                    for holiday_date in holiday_dates:
                        event_iso_year, event_iso_week, _ = holiday_date.isocalendar()
                        
                        if not (
                            (event_iso_year == this_iso_year and event_iso_week == this_iso_week) or
                            (event_iso_year == this_iso_year and event_iso_week == next_iso_week)
                        ):
                            continue
                        
                        week_offset = event_iso_week - this_iso_week
                        
                        holiday_events.append({
                            "summary": f"{icon} {name}",
                            "start": holiday_date.strftime("%Y-%m-%d 00:00:00"),
                            "weekday_index": holiday_date.weekday(),
                            "week_offset": week_offset,
                            "is_holiday": True
                        })
                
                except (ValueError, TypeError) as e:
                    logging.warning(f"Invalid date format for {name}: {date_str}")
                    continue
        
        return holiday_events
        
    except json.JSONDecodeError as e:
        logging.error(f"Error parsing holidays JSON: {e}")
        return []
    except Exception as e:
        logging.error(f"Error reading holidays: {e}")
        return []


def get_birthdays_week(birthdays_file):
    """
    Read birthdays from JSON file and return birthdays for this week and next week
    in calendar event format (with weekday_index and week_offset)
    """
    try:
        # Read JSON file
        if not os.path.exists(birthdays_file):
            logging.error(f"Birthdays file not found: {birthdays_file}")
            return []
        
        with open(birthdays_file, 'r', encoding='utf-8') as f:
            birthdays = json.load(f)
        
        today = date.today()
        this_iso_year, this_iso_week, _ = today.isocalendar()
        next_iso_week = this_iso_week + 1
        
        birthday_events = []
        
        for person in birthdays:
            name = person.get('name', 'Ukjent')
            birth_date_str = person.get('date')
            
            if not birth_date_str:
                continue
            
            # Parse date string (format: YYYY-MM-DD)
            try:
                birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
            except ValueError:
                logging.warning(f"Invalid date format for {name}: {birth_date_str}")
                continue
            
            birth_year = birth_date.year
            day = birth_date.day
            month = birth_date.month
            
            # Calculate birthday for this year
            birthday_this_year = date(today.year, month, day)
            
            # If birthday has passed, check next year
            birthday_dates = [birthday_this_year]
            if birthday_this_year < today:
                birthday_dates.append(date(today.year + 1, month, day))
            
            for birthday_date in birthday_dates:
                # Check if birthday is in this week or next week
                event_iso_year, event_iso_week, _ = birthday_date.isocalendar()
                
                if not (
                    (event_iso_year == this_iso_year and event_iso_week == this_iso_week) or
                    (event_iso_year == this_iso_year and event_iso_week == next_iso_week)
                ):
                    continue
                
                # Calculate age if birth year is known
                age = birthday_date.year - birth_year if birth_year else None
                
                # Format summary
                if age:
                    summary = f"🎂 {name} ({age} år)"
                else:
                    summary = f"🎂 {name}"
                
                # Calculate week offset and weekday index
                week_offset = event_iso_week - this_iso_week
                weekday_index = birthday_date.weekday()
                
                # Format as all-day event
                formatted_start = birthday_date.strftime("%Y-%m-%d 00:00:00")
                
                birthday_events.append({
                    "summary": summary,
                    "start": formatted_start,
                    "weekday_index": weekday_index,
                    "week_offset": week_offset,
                    "is_birthday": True
                })
        
        return birthday_events
        
    except json.JSONDecodeError as e:
        logging.error(f"Error parsing birthdays JSON: {e}")
        return []
    except Exception as e:
        logging.error(f"Error reading birthdays: {e}")
        return []


def get_birthdays(BIRTHDAYURL):
    """Legacy function for backward compatibility - reads from URL"""
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