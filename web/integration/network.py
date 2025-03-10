import subprocess
import re
#from flask import Blueprint, jsonify

def run_command(command):
    """Runs a shell command and returns the output as a string."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return str(e)

def get_network():
    """Scans the network and returns human-readable metrics."""

    # ✅ 1️⃣ Run arp-scan to get MAC addresses and manufacturers
    arp_output = run_command("sudo arp-scan --localnet")
    
    # ✅ 2️⃣ Run nmap to find live devices
    nmap_output = run_command("sudo nmap -sn 192.168.10.0/24")

    # ✅ 3️⃣ Parse arp-scan output
    devices = []
    arp_lines = arp_output.split("\n")
    for line in arp_lines:
        match = re.search(r"(\d+\.\d+\.\d+\.\d+)\s+([a-fA-F0-9:]+)\s+(.+)", line)
        if match:
            ip, mac, vendor = match.groups()
            devices.append({"ip": ip, "mac": mac, "vendor": vendor})

    # ✅ 4️⃣ Parse nmap output for device names
    nmap_lines = nmap_output.split("\n")
    active_ips = [line.split()[-1] for line in nmap_lines if "Nmap scan report" in line]

    # ✅ 5️⃣ Combine data
    network_data = []
    for device in devices:
        status = "Online" if device["ip"] in active_ips else "Offline"
        network_data.append({
            "IP Address": device["ip"],
            "MAC Address": device["mac"],
            "Vendor": device["vendor"],
            "Status": status
        })

    return network_data