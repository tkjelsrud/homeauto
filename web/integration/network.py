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
    """Runs nmap to detect active devices on the network"""
    command = "sudo nmap -sn 192.168.10.0/24"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)

    devices = []
    current_ip = None

    for line in result.stdout.split("\n"):
        ip_match = re.search(r"Nmap scan report for (\d+\.\d+\.\d+\.\d+)", line)
        if ip_match:
            current_ip = ip_match.group(1)

        if "Host is up" in line and current_ip:
            devices.append({"ip": current_ip, "status": "Up"})

    return devices
