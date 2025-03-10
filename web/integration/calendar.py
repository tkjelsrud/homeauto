import requests, icalendar
from flask import jsonify
from datetime import datetime, timezone, date, timedelta

def is_summer_time(year, month, day):
    """Check if a given date in Norway falls within summer time (DST)."""
    # Find last Sunday of March
    last_sunday_march = max(
        day for day in range(25, 32)  # Last week of March
        if date(year, 3, day).weekday() == 6  # Sunday
    )
    
    # Find last Sunday of October
    last_sunday_october = max(
        day for day in range(25, 32)  # Last week of October
        if date(year, 10, day).weekday() == 6  # Sunday
    )

    # If date is between last Sunday of March and last Sunday of October → Summer time
    return (month > 3 or (month == 3 and day >= last_sunday_march)) and (month < 10 or (month == 10 and day < last_sunday_october))

def adjust_to_norwegian_time(event_datetime):
    """Convert UTC time to Norwegian local time, adjusting for summer time."""
    if isinstance(event_datetime, datetime):
        year, month, day = event_datetime.year, event_datetime.month, event_datetime.day
        offset_hours = 2 if is_summer_time(year, month, day) else 1  # UTC+2 in summer, UTC+1 in winter
        return event_datetime + timedelta(hours=offset_hours)
    return event_datetime  # Return unchanged if it's already a date object

def get_calendar(URL):
    response = requests.get(URL)
    calendar_data = icalendar.Calendar.from_ical(response.text)

    events = []
    now = datetime.now(timezone.utc).date()  # Convert to `date` type for comparison
    end_date = now + timedelta(days=7)  # 7 days ahead

    for component in calendar_data.walk():
        if component.name == "VEVENT":
            event_start = component.get("DTSTART").dt  # Can be `date` or `datetime`
            event_summary = component.get("SUMMARY")

            # Adjust for Norwegian time
            if isinstance(event_start, datetime):
                event_start = adjust_to_norwegian_time(event_start)
                formatted_start = event_start.strftime("%Y-%m-%d %H:%M:%S")  # Keep time format
                event_date = event_start.date()  # Extract just the date for comparison

            # Handle all-day events (date only)
            elif isinstance(event_start, date):
                formatted_start = event_start.strftime("%Y-%m-%d")
                event_date = event_start  # Already a date, no need to extract

            # Compare by date only
            if now <= event_date <= end_date:
                events.append({"summary": event_summary, "start": formatted_start})

    return events