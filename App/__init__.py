from flask import Flask
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    from app.routes import init_app_routes
    app = init_app_routes(app)

    return app