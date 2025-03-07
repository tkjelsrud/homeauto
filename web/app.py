from flask import Flask
from web.routes import main_blueprint

app = Flask(__name__)
app.config.from_object("web.config")

# Register routes
app.register_blueprint(main_blueprint)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)