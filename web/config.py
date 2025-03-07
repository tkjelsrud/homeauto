import os
import json

# Define the path to config.json (always at root level)
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../config.json")

# Load the configuration file
def load_config():
    with open(CONFIG_PATH, "r") as config_file:
        return json.load(config_file)

# Global config variable
CONFIG = load_config()