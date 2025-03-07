from flask import Blueprint, jsonify
import subprocess

# Define a Blueprint for routes
routes = Blueprint("routes", __name__)

@routes.route("/memory", methods=["GET"])
def check_memory():
    try:
        # Run `free -h` command
        result = subprocess.run(["free", "-h"], capture_output=True, text=True)
        lines = result.stdout.split("\n")

        # Extract memory values
        headers = lines[0].split()
        memory_values = lines[1].split()

        memory_info = {
            headers[0]: memory_values[0],   # "Mem:"
            headers[1]: memory_values[1],   # Total
            headers[2]: memory_values[2],   # Used
            headers[3]: memory_values[3],   # Free
            headers[4]: memory_values[4],   # Shared
            headers[5]: memory_values[5],   # Buffers
            headers[6]: memory_values[6]    # Available
        }

        return jsonify(memory_info)

    except Exception as e:
        return jsonify({"error": str(e)}), 500