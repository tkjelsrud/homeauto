import subprocess
import re
import time

network_cache = {
    "devices": [],
    "last_updated": 0
}

CACHE_DURATION = 600  # 10 minutes (600 seconds)

def run_command(command):
    """Runs a shell command and returns the output as a string."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return str(e)

def get_network():
    """Scans the network using nmap and returns a list of active devices with vendor names."""
    
    # ✅ 1️⃣ Check cache
    current_time = time.time()
    if current_time - network_cache["last_updated"] < CACHE_DURATION:
        return network_cache["devices"]

    # ✅ 2️⃣ Run `nmap` to find active devices (IP, MAC, and Vendor)
    nmap_output = run_command("sudo nmap -sn 192.168.10.0/24")

    devices = []
    current_device = {}

    # ✅ 3️⃣ Parse `nmap` output
    for line in nmap_output.split("\n"):
        ip_match = re.search(r"Nmap scan report for (\d+\.\d+\.\d+\.\d+)", line)
        mac_match = re.search(r"MAC Address: ([A-F0-9:]+) \((.*?)\)", line)

        if ip_match:
            if current_device:  # Store previous entry
                devices.append(current_device)
            current_device = {"ip": ip_match.group(1), "status": "Up", "mac": "Unknown", "vendor": "Unknown"}

        if mac_match:
            current_device["mac"] = mac_match.group(1)
            current_device["vendor"] = mac_match.group(2)

    # ✅ 4️⃣ Add the last found device
    if current_device:
        devices.append(current_device)

    # ✅ 5️⃣ Update cache
    network_cache["devices"] = devices
    network_cache["last_updated"] = current_time

    return devices