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

    # ✅ 1️⃣ Run nmap first (since some routers block arp-scan)
    nmap_output = run_command("sudo nmap -sn 192.168.10.0/24")
    
    # ✅ 2️⃣ Extract live IPs from nmap
    active_ips = set(re.findall(r"Nmap scan report for (\d+\.\d+\.\d+\.\d+)", nmap_output))

    # ✅ 3️⃣ Run arp-scan to get MAC addresses & vendors
    arp_output = run_command("sudo arp-scan --localnet")

    devices = []
    arp_lines = arp_output.split("\n")
    for line in arp_lines:
        match = re.search(r"(\d+\.\d+\.\d+\.\d+)\s+([a-fA-F0-9:]+)\s+(.+)", line)
        if match:
            ip, mac, vendor = match.groups()
            status = "Online" if ip in active_ips else "Offline"  # Cross-check nmap
            devices.append({"ip": ip, "mac": mac, "vendor": vendor, "status": status})

    return devices