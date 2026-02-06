import subprocess
import re
import sys
import threading

BATTERY_REGEX = re.compile(r"Battery[:=]?\s*([0-9]+\.[0-9]+)V", re.IGNORECASE)


def find_platformio_port():
    # Try to auto-discover the likely serial port from `pio device list`
    try:
        out = subprocess.check_output(["platformio", "device", "list"], encoding="utf-8")
    except Exception as e:
        print(f"Error running 'platformio device list': {e}")
        return None
    for line in out.splitlines():
        if "USB" in line or "UART" in line or "/dev/" in line or "COM" in line:
            port = line.split()[0]
            return port
    return None

def monitor_battery(port=None, baud=115200, min_voltage=3.3):
    """
    Monitors the ESP32 serial output for battery voltage lines.
    Prints live voltage, and warns if battery is below min_voltage.
    """
    if port is None:
        port = find_platformio_port()
        if not port:
            print("Unable to find ESP32 serial port. Please specify with --port.")
            sys.exit(1)

    cmd = [
        "platformio", "device", "monitor",
        "--port", port,
        "--baud", str(baud),
        "--quiet",
    ]
    print(f"[ESP32 Monitor] Running: {' '.join(cmd)}")
    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8", bufsize=1
    )
    low_battery_warned = False
    try:
        for line in process.stdout:
            line = line.strip()
            match = BATTERY_REGEX.search(line)
            if match:
                voltage = float(match.group(1))
                print(f"[ESP32] Battery: {voltage:.2f}V")
                if voltage < min_voltage:
                    if not low_battery_warned:
                        print(f"[ESP32][ALERT] Battery LOW: {voltage:.2f}V < {min_voltage:.2f}V")
                        low_battery_warned = True
                else:
                    low_battery_warned = False
    except KeyboardInterrupt:
        print("[ESP32 Monitor] Exiting")
    finally:
        process.terminate()

import shutil

if __name__ == "__main__":
    import argparse
    # Ensure PlatformIO is in PATH before anything else
    if shutil.which("platformio") is None:
        print("[ERROR] PlatformIO CLI not found in environment PATH. Please activate your virtual environment with 'source venv/bin/activate' before running this skill.")
        sys.exit(1)
    parser = argparse.ArgumentParser(description="Monitor ESP32 battery status via PlatformIO serial monitor.")
    parser.add_argument('--min_voltage', type=float, default=3.3, help='Voltage threshold for low battery alert.')
    parser.add_argument('--port', type=str, default=None, help='Serial port (override auto-discovery).')
    parser.add_argument('--baud', type=int, default=115200, help='Monitor baud rate (default 115200).')
    args = parser.parse_args()
    monitor_battery(port=args.port, baud=args.baud, min_voltage=args.min_voltage)
