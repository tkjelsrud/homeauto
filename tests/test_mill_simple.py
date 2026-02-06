#!/usr/bin/env python
import requests
import json
import os
import sys
import pytest

def test_mill_new_api():
    """Test Mill Norway's new API
    
    Usage: python test_mill_simple.py <username> <password>
    Example: python test_mill_simple.py your@email.com yourpassword
    """
    
    username = os.environ.get("MILL_USERNAME")
    password = os.environ.get("MILL_PASSWORD")
    if not username or not password:
        pytest.skip("Missing MILL_USERNAME/MILL_PASSWORD in environment")
    
    base_url = "https://api.millnorwaycloud.com"
    
    # Step 1: Sign in to get tokens
    print("Signing in...")
    signin_url = f"{base_url}/customer/auth/sign-in"
    signin_payload = {
        "login": username,
        "password": password
    }
    
    response = requests.post(signin_url, json=signin_payload)
    print(f"Sign-in status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"Error: {response.text}")
        return
    
    auth_data = response.json()
    
    id_token = auth_data.get("idToken")
    refresh_token = auth_data.get("refreshToken")
    
    if not id_token:
        print("Error: No idToken found in response")
        print(f"Auth response: {json.dumps(auth_data, indent=2)}")
        return
    
    print(f"✓ Authenticated successfully")
    print(f"ID Token (valid 10 min): {id_token[:30]}...")
    print(f"Refresh Token (valid ~420 days): {refresh_token[:30]}...")
    print(f"\nNote: Save refresh token to config for long-term use!")
    
    # Step 2: Get houses
    print("\nFetching houses...")
    headers = {
        "Authorization": f"Bearer {id_token}"
    }
    
    # Get houses list
    houses_url = f"{base_url}/houses"
    response = requests.get(houses_url, headers=headers)
    
    print(f"Houses response status: {response.status_code}")
    print(f"Houses response: {response.text}")
    
    if response.status_code != 200:
        print(f"Error fetching houses: {response.text}")
        return
    
    houses_data = response.json()
    
    # Check if response is dict with ownHouses/sharedHouses
    if isinstance(houses_data, dict):
        own_houses = houses_data.get("ownHouses", [])
        shared_houses = houses_data.get("sharedHouses", [])
        all_houses = own_houses + shared_houses
    else:
        all_houses = houses_data
    
    print(f"✓ Found {len(all_houses)} house(s)\n")
    
    # Step 3: Get devices for each house
    for house in all_houses:
        if isinstance(house, str):
            house_id = house
            house_name = house
        else:
            house_id = house.get("houseId") or house.get("id")
            house_name = house.get("name", house_id)
        
        print(f"House: {house_name} (ID: {house_id})")
        
        # Get devices
        devices_url = f"{base_url}/houses/{house_id}/devices"
        response = requests.get(devices_url, headers=headers)
        
        if response.status_code == 200:
            rooms_data = response.json()
            
            # Data is a list of rooms, each with devices
            if isinstance(rooms_data, list):
                total_devices = sum(len(room.get('devices', [])) for room in rooms_data)
                print(f"  Found {total_devices} device(s) in {len(rooms_data)} room(s):")
                
                for room in rooms_data:
                    room_name = room.get('roomName', 'Unknown')
                    devices = room.get('devices', [])
                    
                    print(f"\n  Room: {room_name}")
                    for device in devices:
                        name = device.get('customName', 'Unnamed')
                        device_type = device.get('deviceType', {}).get('childType', {}).get('name', 'Unknown')
                        is_connected = device.get('isConnected', False)
                        
                        # Get last metrics
                        metrics = device.get('lastMetrics', {})
                        temp_ambient = metrics.get('temperatureAmbient', 'N/A')
                        temp_internal = metrics.get('temperature', 'N/A')
                        power = metrics.get('currentPower', 0)
                        humidity = metrics.get('humidity', 'N/A')
                        
                        # Get settings
                        settings = device.get('deviceSettings', {}).get('reported', {})
                        target_temp = settings.get('temperature_normal', 'N/A')
                        mode = settings.get('operation_mode', 'N/A')
                        
                        print(f"    - {name} ({device_type})")
                        print(f"      Connected: {'Yes' if is_connected else 'No'}")
                        print(f"      Ambient Temp: {temp_ambient}°C | Target: {target_temp}°C")
                        print(f"      Power: {power}W | Humidity: {humidity}%")
                        print(f"      Mode: {mode}")
            else:
                print(f"  Unexpected response format")
        else:
            print(f"  Error fetching devices: {response.text}")
        
        print("-" * 50)

if __name__ == "__main__":
    test_mill_new_api()
