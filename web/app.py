from flask import Flask, send_from_directory, render_template
from routes import routes
from config import CONFIG


app = Flask(__name__)
app.register_blueprint(routes)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/pihole/css/<path:filename>")
def pihole_css(filename):
    return send_from_directory("/var/www/html/admin/style", filename)

@app.route("/pihole/img/<path:filename>")
def pihole_img(filename):
    return send_from_directory("/var/www/html/admin/img", filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)