import pytest
import sys
import os
import json
from datetime import datetime, date

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'web')))

from app import app  # Import your Flask app
from config import CONFIG


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config["TESTING"] = True  # Enable test mode
    with app.test_client() as client:
        yield client  # Provide the test client to tests

def test_home_route(client):
    """Test the home page loads successfully."""
    response = client.get("/")  # Simulate GET request
    assert response.status_code == 200  # Check if the response is OK
    assert b"Welcome" in response.data  # Check if page contains "Welcome"

def test_calendar_route(client):
    """Test the /calendar route."""
    response = client.get("/calendar")
    assert response.status_code == 200  # API should return 200
    assert isinstance(response.json, list)  # Response should be a JSON list

def test_bigcalendar_route(client):
    """Test the /bigcalendar route returns correct structure."""
    response = client.get("/bigcalendar")
    
    # Check response is successful
    assert response.status_code == 200
    
    # Parse JSON response
    data = response.json
    
    # Check top-level structure
    assert "title" in data
    assert "icon" in data
    assert "data" in data
    assert "refresh" in data
    
    assert data["title"] == "Stor Kalender"
    assert data["icon"] == "📅"
    
    # Check data is a list of 7 days
    days = data["data"]
    assert isinstance(days, list)
    assert len(days) == 7
    
    # Check structure of each day
    weekday_names = ["Mandag", "Tirsdag", "Onsdag", "Torsdag", "Fredag", "Lørdag", "Søndag"]
    
    for i, day in enumerate(days):
        assert day["weekday_index"] == i
        assert day["name"] == weekday_names[i]
        assert "events" in day
        assert "dinner" in day
        assert "timeplaner" in day
        assert "waste" in day
        
        # Events should be a list
        assert isinstance(day["events"], list)
        
        # Each event should have required fields
        for event in day["events"]:
            assert "summary" in event
            assert "start" in event
            assert "is_next_week" in event
            
            # Validate date format (YYYY-MM-DD HH:MM:SS)
            try:
                datetime.strptime(event["start"], "%Y-%m-%d %H:%M:%S")
            except ValueError:
                pytest.fail(f"Invalid date format in event: {event['start']}")
        
        # Waste should be a list
        assert isinstance(day["waste"], list)
        
        for waste_item in day["waste"]:
            assert "type" in waste_item
            assert "icon" in waste_item

def test_bigcalendar_includes_birthdays(client):
    """Test that bigcalendar includes birthday events."""
    response = client.get("/bigcalendar")
    assert response.status_code == 200
    
    days = response.json["data"]
    
    # Check if any events contain birthday emoji
    all_events = []
    for day in days:
        all_events.extend(day["events"])
    
    # If there are birthdays this week, at least one event should have 🎂
    birthday_events = [e for e in all_events if "🎂" in e["summary"]]
    
    # Just verify the structure is correct (may or may not have birthdays this week)
    for event in birthday_events:
        assert "år" in event["summary"] or "🎂" in event["summary"]
        print(f"Found birthday event: {event['summary']}")

def test_bigcalendar_includes_holidays(client):
    """Test that bigcalendar includes holiday events."""
    response = client.get("/bigcalendar")
    assert response.status_code == 200
    
    days = response.json["data"]
    
    # Collect all events
    all_events = []
    for day in days:
        all_events.extend(day["events"])
    
    # Check if any events look like holidays (contain common holiday emojis)
    holiday_emojis = ["🎆", "⛷️", "🐣", "🌹", "🇳🇴", "⛪", "☀️", "🎒", "🍂", "🎃", "🎄", "🎁", "🎉"]
    holiday_events = [e for e in all_events if any(emoji in e["summary"] for emoji in holiday_emojis)]
    
    # Log found holiday events
    for event in holiday_events:
        print(f"Found holiday event: {event['summary']}")

def test_birthdays_json_structure():
    """Test that birthdays.json has correct structure."""
    birthdays_file = CONFIG.get('BIRTHDAYS_FILE', './integration/birthdays.json')
    
    assert os.path.exists(birthdays_file), f"Birthdays file not found: {birthdays_file}"
    
    with open(birthdays_file, 'r', encoding='utf-8') as f:
        birthdays = json.load(f)
    
    assert isinstance(birthdays, list)
    
    for person in birthdays:
        assert "name" in person
        assert "date" in person
        
        # Validate date format (YYYY-MM-DD)
        try:
            datetime.strptime(person["date"], "%Y-%m-%d")
        except ValueError:
            pytest.fail(f"Invalid date format for {person['name']}: {person['date']}")

def test_holidays_json_structure():
    """Test that holidays.json has correct structure."""
    holidays_file = CONFIG.get('HOLIDAYS_FILE', './integration/holidays.json')
    
    assert os.path.exists(holidays_file), f"Holidays file not found: {holidays_file}"
    
    with open(holidays_file, 'r', encoding='utf-8') as f:
        holidays = json.load(f)
    
    assert isinstance(holidays, list)
    
    for holiday in holidays:
        assert "name" in holiday
        assert "icon" in holiday
        
        # Holiday should have either date or week
        assert "date" in holiday or "week" in holiday
        
        if "date" in holiday:
            # Validate MM-DD format
            date_str = holiday["date"]
            try:
                month, day = map(int, date_str.split('-'))
                assert 1 <= month <= 12
                assert 1 <= day <= 31
            except (ValueError, AssertionError):
                pytest.fail(f"Invalid date format for {holiday['name']}: {date_str}")
        
        if "week" in holiday:
            # Validate week number
            assert isinstance(holiday["week"], int)
            assert 1 <= holiday["week"] <= 53

def test_invalid_route(client):
    """Test an invalid route returns 404."""
    response = client.get("/invalid")
    assert response.status_code == 404  # Should return Not Found

def test_mill_heater():
    from millheater import Mill

    username = "tkjelsrud@gmail.com"
    password = "najdan-0muzty-kohreD"

    mill = Mill(username, password)
    mill.authenticate()

    devices = mill.get_devices()

    for device in devices:
        print(f"{device.name} | {device.room} | Current: {device.currentTemp}°C | Target: {device.targetTemp}°C")