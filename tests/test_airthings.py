#!/usr/bin/env python3
"""
Test script for Airthings Wave Plus integration via Bluetooth BLE

Setup på PI:
1. Install library: pip3 install airthings-ble
2. Finn MAC-adresse til Wave Plus:
   sudo hcitool lescan
   eller
   sudo bluetoothctl
   scan on
   (Se etter "Airthings Wave Plus" eller lignende)

3. Legg MAC-adresse i config.json:
   "AIRTHINGS_MAC": "XX:XX:XX:XX:XX:XX"

Wave Plus måler:
- Radon (Bq/m³)
- CO2 (ppm)
- VOC (ppb) - Volatile Organic Compounds
- Temperatur (°C)
- Luftfuktighet (%)
- Lufttrykk (hPa)
"""

import asyncio
import sys

async def test_airthings():
    try:
        from airthings_ble import AirthingsDevice
    except ImportError:
        print("ERROR: airthings-ble not installed")
        print("Run: pip3 install airthings-ble")
        return
    
    # MAC address må settes
    mac_address = "XX:XX:XX:XX:XX:XX"  # Replace with actual MAC
    
    if mac_address == "XX:XX:XX:XX:XX:XX":
        print("ERROR: Set MAC address first!")
        print("\nTo find MAC address:")
        print("  sudo hcitool lescan")
        print("  (or)")
        print("  sudo bluetoothctl")
        print("  scan on")
        return
    
    print(f"Connecting to Airthings Wave Plus at {mac_address}...")
    
    try:
        device = AirthingsDevice(mac_address)
        await device.update()
        
        print("\n=== Airthings Wave Plus Data ===")
        print(f"Radon (24h avg): {device.radon_1day_avg} Bq/m³")
        print(f"Radon (long term): {device.radon_longterm_avg} Bq/m³")
        print(f"CO2: {device.co2} ppm")
        print(f"VOC: {device.voc} ppb")
        print(f"Temperature: {device.temp}°C")
        print(f"Humidity: {device.humidity}%")
        print(f"Pressure: {device.pressure} hPa")
        
        # Return data structure for integration
        data = {
            "radon_24h": device.radon_1day_avg,
            "radon_longterm": device.radon_longterm_avg,
            "co2": device.co2,
            "voc": device.voc,
            "temp": device.temp,
            "humidity": device.humidity,
            "pressure": device.pressure
        }
        
        print("\nData structure for API:")
        print(data)
        
        return data
        
    except Exception as e:
        print(f"ERROR: {e}")
        print("\nTroubleshooting:")
        print("1. Check Bluetooth is enabled: sudo systemctl status bluetooth")
        print("2. Check Wave Plus is in range")
        print("3. Check MAC address is correct")
        print("4. Try: sudo hciconfig hci0 up")

if __name__ == "__main__":
    asyncio.run(test_airthings())
