from functools import wraps
from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database.db import db
from models import User

def get_current_user():
    """Retrieve current User model instance from JWT identity (user ID)."""
    user_id = get_jwt_identity()
    if user_id is None:
        return None
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        pass
    return db.session.get(User, user_id)

def require_role(*roles):
    """
    Decorator to enforce role-based access control.
    Example usage:
        @require_role("ADMIN")
        @require_role("ADMIN", "OPERATOR")
    """
    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            user = get_current_user()
            if not user:
                return jsonify({
                    "success": False,
                    "message": "User not found or unauthenticated",
                    "error": "UNAUTHORIZED"
                }), 401

            if user.role not in roles:
                return jsonify({
                    "success": False,
                    "message": f"Access denied. Requires one of roles: {list(roles)}",
                    "error": "FORBIDDEN"
                }), 403

            return fn(*args, **kwargs)
        return wrapper
    return decorator
