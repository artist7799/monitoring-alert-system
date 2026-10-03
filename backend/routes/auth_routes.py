from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from schemas.auth_schema import RegisterSchema, LoginSchema
from services.auth_service import AuthService
from utils.response import success_response, error_response

auth_bp = Blueprint("auth", __name__)

register_schema = RegisterSchema()
login_schema = LoginSchema()

@auth_bp.route("/register", methods=["POST"])
def register():
    """
    Register a new user
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - name
            - email
            - password
          properties:
            name:
              type: string
              example: John Doe
            email:
              type: string
              example: john@example.com
            password:
              type: string
              example: StrongPassword123
    responses:
      201:
        description: User registered successfully
      400:
        description: Validation error
      409:
        description: Email already exists
    """
    json_data = request.get_json() or {}
    errors = register_schema.validate(json_data)
    if errors:
        return error_response("Validation failed", "VALIDATION_ERROR", 400, errors=errors)

    success, result, message, status_code = AuthService.register_user(json_data)
    if not success:
        return error_response(message, result, status_code)

    return success_response(data=result, message=message, status_code=status_code)


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    User Login
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - email
            - password
          properties:
            email:
              type: string
              example: admin@example.com
            password:
              type: string
              example: admin123
    responses:
      200:
        description: Login successful
      401:
        description: Invalid credentials
    """
    json_data = request.get_json() or {}
    errors = login_schema.validate(json_data)
    if errors:
        return error_response("Validation failed", "VALIDATION_ERROR", 400, errors=errors)

    success, result, message, status_code = AuthService.login_user(json_data)
    if not success:
        return error_response(message, result, status_code)

    return success_response(data=result, message=message, status_code=status_code)


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def get_me():
    """
    Get current logged in user profile
    ---
    tags:
      - Authentication
    security:
      - Bearer: []
    responses:
      200:
        description: User profile retrieved successfully
      401:
        description: Unauthorized / Token missing or invalid
    """
    user_id = get_jwt_identity()
    success, result, message, status_code = AuthService.get_current_user_profile(user_id)
    if not success:
        return error_response(message, result, status_code)

    return success_response(data=result, message=message, status_code=status_code)
