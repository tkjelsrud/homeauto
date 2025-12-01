import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from web.app import app  # Import your Flask app
from web.config import CONFIG


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