from flask import jsonify
from marshmallow import ValidationError
from flask_jwt_extended.exceptions import JWTExtendedException

def register_error_handlers(app, jwt=None):
    @app.errorhandler(ValidationError)
    def handle_marshmallow_validation(err):
        return jsonify({
            "success": False,
            "message": "Validation failed",
            "errors": err.messages
        }), 400

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({
            "success": False,
            "message": str(e.description) if hasattr(e, "description") else "Bad request",
            "error": "BAD_REQUEST"
        }), 400

    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify({
            "success": False,
            "message": "Unauthorized access",
            "error": "UNAUTHORIZED"
        }), 401

    @app.errorhandler(403)
    def forbidden(e):
        return jsonify({
            "success": False,
            "message": "Access forbidden",
            "error": "FORBIDDEN"
        }), 403

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({
            "success": False,
            "message": "Resource not found",
            "error": "NOT_FOUND"
        }), 404

    @app.errorhandler(409)
    def conflict(e):
        return jsonify({
            "success": False,
            "message": "Resource conflict",
            "error": "CONFLICT"
        }), 409

    @app.errorhandler(422)
    def unprocessable_entity(e):
        return jsonify({
            "success": False,
            "message": "Unprocessable request entity",
            "error": "UNPROCESSABLE_ENTITY"
        }), 422

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({
            "success": False,
            "message": "Internal server error",
            "error": "INTERNAL_SERVER_ERROR"
        }), 500

    if jwt:
        @jwt.expired_token_loader
        def expired_token_callback(jwt_header, jwt_payload):
            return jsonify({
                "success": False,
                "message": "Token has expired",
                "error": "TOKEN_EXPIRED"
            }), 401

        @jwt.invalid_token_loader
        def invalid_token_callback(error):
            return jsonify({
                "success": False,
                "message": "Signature verification failed or token invalid",
                "error": "INVALID_TOKEN"
            }), 401

        @jwt.unauthorized_loader
        def missing_token_callback(error):
            return jsonify({
                "success": False,
                "message": "Request does not contain an access token",
                "error": "TOKEN_MISSING"
            }), 401

        @jwt.revoked_token_loader
        def revoked_token_callback(jwt_header, jwt_payload):
            return jsonify({
                "success": False,
                "message": "Token has been revoked",
                "error": "TOKEN_REVOKED"
            }), 401
