from flask import Flask, send_from_directory, render_template
from integration.weather import get_weather
from routes import routes
from config import CONFIG

def create_app():
    app = Flask(__name__)

    # Register Blueprint
    app.register_blueprint(routes)

    return app

@app.route("/")
def home():
    return render_template("index.html")

#@app.route("/")
#def hello_world():
#    w = get_weather(CONFIG['LAT'], CONFIG['LON'])
#
#    return "<p>Hello, World!</p><br/>" + w + " : " + str(CONFIG)

@app.route("/pihole/css/<path:filename>")
def pihole_css(filename):
    return send_from_directory("/var/www/html/admin/style", filename)

@app.route("/pihole/img/<path:filename>")
def pihole_img(filename):
    return send_from_directory("/var/www/html/admin/img", filename)

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)