import asyncio
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

async def get_airthings_data(mac_address):
    """
    Fetch sensor data from Airthings Wave device via Bluetooth
    
    Args:
        mac_address: Bluetooth MAC/UUID address of the Airthings device
        
    Returns:
        dict with sensor data or error message
    """
    try:
        from airthings_ble import AirthingsBluetoothDeviceData
        from bleak import BleakScanner
    except ImportError:
        logging.error("airthings-ble or bleak not installed")
        return {"error": "Airthings BLE library not installed"}
    
    try:
        # Create logger
        logger = logging.getLogger(__name__)
        
        # Discover the device to get BLEDevice object
        logging.info(f"Discovering Airthings device at {mac_address}...")
        devices = await BleakScanner.discover(timeout=10, return_adv=True)
        
        ble_device = None
        for addr, (dev, adv_data) in devices.items():
            if addr.upper() == mac_address.upper():
                ble_device = dev
                logging.info(f"Found device: {dev.name or 'Unknown'}")
                break
        
        if not ble_device:
            logging.error(f"Device {mac_address} not found during scan")
            return {"error": "Device not found - check if it's powered on and in range"}
        
        # Create Airthings BLE data handler
        airthings = AirthingsBluetoothDeviceData(logger=logger)
        
        # Update data from device
        logging.info("Reading sensor data...")
        data = await airthings.update_device(ble_device)
        
        # Extract sensor data
        sensors = data.sensors
        
        # Return formatted data
        result = {
            "device": data.name,
            "manufacturer": data.manufacturer,
            "temperature": sensors.get('temperature'),
            "humidity": sensors.get('humidity'),
            "radon_24h": sensors.get('radon_1day_avg'),
            "radon_24h_level": sensors.get('radon_1day_level'),
            "radon_longterm": sensors.get('radon_longterm_avg'),
            "radon_longterm_level": sensors.get('radon_longterm_level'),
            "co2": sensors.get('co2'),
            "voc": sensors.get('voc'),
            "pressure": sensors.get('pressure'),
            "battery": sensors.get('battery'),
            "illuminance": sensors.get('illuminance')
        }
        
        logging.info("Successfully retrieved Airthings data")
        return result
        
    except Exception as e:
        logging.error(f"Error reading Airthings data: {e}")
        return {"error": str(e)}

def get_airthings(mac_address):
    """
    Synchronous wrapper for get_airthings_data
    """
    return asyncio.run(get_airthings_data(mac_address))
