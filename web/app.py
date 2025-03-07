from flask import Flask
from integration.weather import get_weather

app = Flask(__name__)

@app.route("/")
def hello_world():
    w = get_weather()

    return "<p>Hello, World!</p><br/>" + w

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)