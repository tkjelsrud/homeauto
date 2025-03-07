from flask import Flask
from web.routes import main_blueprint

def create_app():
    app = Flask(__name__)
    app.config.from_object("web.config")

    # Register blueprints (modular routes)
    app.register_blueprint(main_blueprint)

    return app