# homeauto
Home Automation using Raspberry PI, Zigbee and various sources


home_automation_project/
│── web/                 # Flask app (Frontend & API)
│   ├── static/          # CSS, JS, images
│   ├── templates/       # HTML templates (if using Jinja)
│   ├── __init__.py      # Initializes Flask app
│   ├── routes.py        # Defines API routes
│   ├── app.py           # Main entry point
│── integrations/        # Zigbee, power meter, network scanning logic
│   ├── influxdb_service.py  # Fetch/store data in InfluxDB
│   ├── zigbee_service.py    # Zigbee2MQTT handling
│   ├── han_reader.py        # Power meter integration
│   ├── network_scanner.py   # Scan connected devices
│── tests/              # Unit and integration tests
│   ├── test_routes.py  # Tests for Flask API
│   ├── test_zigbee.py  # Tests for Zigbee service
│── config/             # Configuration files (if needed)
│   ├── settings.yaml   # YAML config for API keys, ports, etc.
│── requirements.txt    # Python dependencies (or use poetry)
│── run.py              # Script to start the app
│── README.md           # Project documentation
│── .env                # Environment variables (if needed)