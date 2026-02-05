#!/usr/bin/env python3
"""
Test script for Airthings Wave Plus integration via Bluetooth BLE

Setup på PI:
1. Install library: pip3 install airthings-ble
2. Finn MAC-adresse til Wave Plus:
   Run this script with --scan flag:
   python3 test_airthings.py --scan
   
   eller manuelt:
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

Usage:
  python3 test_airthings.py --scan    # Scan for Airthings devices
  python3 test_airthings.py           # Test connection (uses config.json)
"""

import asyncio
import sys
import argparse

async def scan_for_airthings(duration=10):
    """Scan for Airthings devices on Bluetooth network"""
    try:
        from bleak import BleakScanner
    except ImportError:
        print("ERROR: bleak not installed")
        print("Run: pip3 install bleak")
        print("\nAlternatively, use system commands:")
        print("  macOS: brew install blueutil && blueutil --inquiry")
        print("  Linux: sudo hcitool lescan")
        print("  Linux: sudo bluetoothctl → scan on")
        return []
    
    print(f"Scanning for Airthings devices for {duration} seconds...")
    print("Make sure your Airthings Wave device is powered on.\n")
    
    try:
        devices = await BleakScanner.discover(timeout=duration, return_adv=True)
        
        airthings_devices = []
        
        print("=== All Bluetooth LE Devices Found ===")
        for address, (device, adv_data) in devices.items():
            name = device.name or adv_data.local_name or "Unknown"
            rssi = adv_data.rssi
            
            # Check manufacturer data (Airthings company code is 0x0334)
            is_airthings = False
            manufacturer_info = ""
            if adv_data.manufacturer_data:
                for company_id, data in adv_data.manufacturer_data.items():
                    manufacturer_info = f" [Mfr: 0x{company_id:04X}]"
                    # Airthings company ID is 0x0334 (820 decimal)
                    if company_id == 0x0334:
                        is_airthings = True
                        name = f"{name} (AIRTHINGS!)"
            
            # Check service UUIDs
            service_info = ""
            if adv_data.service_uuids:
                service_info = f" [Services: {len(adv_data.service_uuids)}]"
            
            print(f"  {address} - {name} (RSSI: {rssi} dBm){manufacturer_info}{service_info}")
            
            # Check if it's an Airthings device
            if is_airthings or (name and ('airthings' in name.lower() or 'wave' in name.lower())):
                airthings_devices.append((address, name, rssi))
        
        if airthings_devices:
            print("\n" + "="*60)
            print("=== Found Airthings Wave Devices ===")
            print("="*60)
            for address, name, rssi in airthings_devices:
                print(f"\n✓ Device: {name}")
                print(f"  MAC Address: {address}")
                print(f"  Signal Strength: {rssi} dBm")
                print(f"\n  To use this device, add to config.json:")
                print(f'  "AIRTHINGS_MAC": "{address}"')
                print(f"\n  Or test directly:")
                print(f'  python3 test_airthings.py {address}')
        else:
            print("\n⚠️  No Airthings devices found")
            print("\nTroubleshooting:")
            print("1. Make sure device is powered on and has batteries")
            print("2. Press button on Wave device to wake it up")
            print("3. Move closer to the device")
            print("4. Check Bluetooth is enabled on this computer")
        
        return airthings_devices
        
    except Exception as e:
        print(f"ERROR during scan: {e}")
        print("\nFallback: Try manual scanning:")
        print("  macOS: Open System Preferences → Bluetooth")
        print("  Linux: sudo bluetoothctl → scan on")
        return []

import pytest

@pytest.mark.asyncio
async def test_airthings():
    try:
        from airthings_ble import AirthingsBluetoothDeviceData
    except ImportError:
        print("ERROR: airthings-ble not installed")
        print("Run: pip3 install airthings-ble")
        print("\nOr using virtual environment:")
        print("  source venv/bin/activate")
        print("  pip install airthings-ble")
        return
    
    # Load MAC address from config
    try:
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'web'))
        from config import CONFIG
        mac_address = CONFIG.get('AIRTHINGS_MAC')
    except Exception as e:
        print(f"ERROR: Could not load config: {e}")
        print("\nMake sure config.json exists with AIRTHINGS_MAC set")
        return
    
    if not mac_address or mac_address == "XX:XX:XX:XX:XX:XX":
        print("ERROR: AIRTHINGS_MAC not set in config.json!")
        print("\nTo find MAC address, run:")
        print("  python3 test_airthings.py --scan")
        print("\nThen add it to config.json:")
        print('  "AIRTHINGS_MAC": "YOUR-MAC-ADDRESS"')
        return
    
    print(f"Connecting to Airthings Wave Plus at {mac_address}...")
    
    try:
        from bleak import BleakScanner
        import logging
        
        # Create logger
        logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        
        # First, discover the device to get BLEDevice object
        print("Discovering device...")
        devices = await BleakScanner.discover(timeout=10, return_adv=True)
        
        ble_device = None
        for addr, (dev, adv_data) in devices.items():
            if addr.upper() == mac_address.upper():
                ble_device = dev
                print(f"Found device: {dev.name or 'Unknown'}")
                break
        
        if not ble_device:
            print(f"ERROR: Device {mac_address} not found during scan")
            print("Make sure the device is powered on and in range")
            return
        
        # Create Airthings BLE data handler
        airthings = AirthingsBluetoothDeviceData(logger=logger)
        
        # Update data from device
        print("Reading sensor data...")
        data = await airthings.update_device(ble_device)
        
        print("\n" + "="*50)
        print("=== Airthings Wave Plus Data ===")
        print("="*50)
        print(f"Device: {data.name}")
        print(f"Manufacturer: {data.manufacturer}")
        print()
        
        # Extract and display key measurements
        sensors = data.sensors
        
        # Temperature
        if 'temperature' in sensors:
            print(f"🌡️  Temperature: {sensors['temperature']:.1f}°C")
        
        # Humidity
        if 'humidity' in sensors:
            print(f"💧 Humidity: {sensors['humidity']:.1f}%")
        
        # Radon
        if 'radon_1day_avg' in sensors:
            radon_24h = sensors['radon_1day_avg']
            radon_level = sensors.get('radon_1day_level', 'unknown')
            print(f"☢️  Radon (24h): {radon_24h} Bq/m³ ({radon_level})")
        
        if 'radon_longterm_avg' in sensors:
            radon_lt = sensors['radon_longterm_avg']
            radon_lt_level = sensors.get('radon_longterm_level', 'unknown')
            print(f"☢️  Radon (long-term): {radon_lt} Bq/m³ ({radon_lt_level})")
        
        # Air Quality
        if 'co2' in sensors:
            print(f"🌫️  CO2: {sensors['co2']:.0f} ppm")
        
        if 'voc' in sensors:
            print(f"🌫️  VOC: {sensors['voc']:.0f} ppb")
        
        # Pressure
        if 'pressure' in sensors:
            print(f"🔽 Pressure: {sensors['pressure']:.2f} hPa")
        
        # Battery
        if 'battery' in sensors:
            print(f"🔋 Battery: {sensors['battery']}%")
        
        # Light
        if 'illuminance' in sensors:
            print(f"💡 Light: {sensors['illuminance']} lux")
        
        print("="*50)
        
        # Return structured data for API use
        result = {
            "device": data.name,
            "manufacturer": data.manufacturer,
            "sensors": sensors
        }
        
        return result
        
    except Exception as e:
        print(f"ERROR: {e}")
        print("\nTroubleshooting:")
        print("1. Check Bluetooth is enabled: sudo systemctl status bluetooth")
        print("2. Check Wave Plus is in range")
        print("3. Check MAC address is correct")
        print("4. Try: sudo hciconfig hci0 up")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Airthings Wave device scanner and tester'
    )
    parser.add_argument(
        '--scan',
        action='store_true',
        help='Scan for Airthings devices on Bluetooth network'
    )
    parser.add_argument(
        '--duration',
        type=int,
        default=10,
        help='Scan duration in seconds (default: 10)'
    )
    
    args = parser.parse_args()
    
    if args.scan:
        # Scan mode
        asyncio.run(scan_for_airthings(args.duration))
    else:
        # Test mode - reads MAC from config.json
        asyncio.run(test_airthings())
