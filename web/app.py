from flask import Flask
from integration.weather import get_weather
from config import CONFIG

app = Flask(__name__)

@app.route("/")
def hello_world():
    w = get_weather(CONFIG['LAT'], CONFIG['LON'])

    return "<p>Hello, World!</p><br/>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)