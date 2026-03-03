import logging
from flask import Flask, jsonify, request
from flask_cors import CORS
from app.extensions import limiter
from app.routes import playlist, users, admin


def create_app():
    app = Flask(__name__)
    CORS(app)

    #attach extensions
    limiter.init_app(app)

    # Register blueprints
    app.register_blueprint(playlist.bp)
    app.register_blueprint(users.bp)
    app.register_blueprint(admin.bp)

    # Logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    @app.before_request
    def log_request_info():
        logging.info(f"Request: {request.method} {request.url} from {request.remote_addr}")

    @app.errorhandler(Exception)
    def handle_exception(e):
        #log full error,return safe message to client
        logging.exception(f"Unhandled exception: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500

    return app