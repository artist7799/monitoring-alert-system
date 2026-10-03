from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required

from flasgger import Swagger
from config import Config
from database.db import db, migrate

jwt = JWTManager()

def create_app(config_class=Config, config_override=None):
    app = Flask(__name__)
    app.config.from_object(config_class)

    if config_override:
        app.config.update(config_override)

    CORS(app)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": 'apispec',
                "route": '/apispec.json',
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/apidocs/"
    }
    Swagger(app, config=swagger_config)

    import models  # Ensure all SQLAlchemy models are registered

    from routes.auth_routes import auth_bp
    from routes.device_routes import device_bp
    from routes.event_routes import event_bp
    from routes.alert_routes import alert_bp
    from routes.status_routes import status_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(device_bp, url_prefix="/api/devices")
    app.register_blueprint(event_bp, url_prefix="/api/events")
    app.register_blueprint(alert_bp, url_prefix="/api/alerts")
    app.register_blueprint(status_bp, url_prefix="/api/status")

    from middleware.error_handler import register_error_handlers
    register_error_handlers(app, jwt=jwt)

    # Seed demo users on every startup (handles Werkzeug debug reloader correctly)
    with app.app_context():
        from database.seed import seed_database
        db.create_all()
        seed_database()

    @app.route("/api/stream", methods=["GET"])
    @jwt_required()
    def sse_stream():
        """
        Real-Time Server-Sent Events (SSE) Monitoring Stream
        ---
        tags:
          - Real-Time Monitoring
        security:
          - Bearer: []
        responses:
          200:
            description: Real-time SSE event stream (system_status, device_status, event, alert, heartbeat)
            headers:
              Content-Type:
                type: string
                example: text/event-stream
          401:
            description: Unauthorized / Invalid JWT token
        """
        from services.sse_service import generate_sse_stream
        from flask import Response, current_app

        app_obj = current_app._get_current_object()

        headers = {
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive"
        }

        return Response(generate_sse_stream(app_obj), headers=headers)

    @app.route("/health", methods=["GET"])
    def health_check():
        return {"status": "healthy", "service": "Real-Time Monitoring & Alert System API"}, 200

    return app

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        from database.seed import seed_database
        db.create_all()
        seed_database()
    app.run(host="0.0.0.0", port=5000, debug=True)
