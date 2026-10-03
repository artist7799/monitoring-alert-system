from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from middleware.auth_middleware import require_role
from schemas.device_schema import DeviceCreateSchema, DeviceUpdateSchema
from services.device_service import DeviceService
from utils.response import success_response, error_response

device_bp = Blueprint("devices", __name__)

create_schema = DeviceCreateSchema()
update_schema = DeviceUpdateSchema()

@device_bp.route("", methods=["POST"])
@require_role("ADMIN")
def create_device():
    """
    Create a new monitoring device (ADMIN only)
    ---
    tags:
      - Devices
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - device_code
            - device_name
            - location
            - device_type
          properties:
            device_code:
              type: string
              example: DEV004
            device_name:
              type: string
              example: Forest Sensor 04
            location:
              type: string
              example: Zone A
            device_type:
              type: string
              example: ENVIRONMENT_SENSOR
            status:
              type: string
              enum: [ONLINE, OFFLINE, WARNING]
              example: OFFLINE
    responses:
      201:
        description: Device created successfully
      400:
        description: Validation error
      401:
        description: Unauthorized
      403:
        description: Forbidden (Non-ADMIN users)
      409:
        description: Device code already exists
    """
    json_data = request.get_json() or {}
    errors = create_schema.validate(json_data)
    if errors:
        return error_response("Validation failed", "VALIDATION_ERROR", 400, errors=errors)

    success, result, message, status_code = DeviceService.create_device(json_data)
    if not success:
        return error_response(message, result, status_code)

    return success_response(data=result, message=message, status_code=status_code)


@device_bp.route("", methods=["GET"])
@jwt_required()
def list_devices():
    """
    List all devices with filtering and pagination
    ---
    tags:
      - Devices
    security:
      - Bearer: []
    parameters:
      - in: query
        name: status
        type: string
        enum: [ONLINE, OFFLINE, WARNING]
      - in: query
        name: location
        type: string
      - in: query
        name: device_type
        type: string
      - in: query
        name: search
        type: string
      - in: query
        name: page
        type: integer
        default: 1
      - in: query
        name: per_page
        type: integer
        default: 10
    responses:
      200:
        description: List of devices with pagination meta
      401:
        description: Unauthorized
    """
    status = request.args.get("status")
    location = request.args.get("location")
    device_type = request.args.get("device_type")
    search = request.args.get("search")

    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 10))
    except ValueError:
        page = 1
        per_page = 10

    filters = {
        "status": status,
        "location": location,
        "device_type": device_type,
        "search": search
    }

    success, result, message, status_code = DeviceService.get_devices(filters, page, per_page)
    
    return jsonify({
        "success": True,
        "message": message,
        "data": result["devices"],
        "pagination": result["pagination"]
    }), status_code


@device_bp.route("/<int:device_id>", methods=["GET"])
@jwt_required()
def get_device(device_id):
    """
    Get device details by ID
    ---
    tags:
      - Devices
    security:
      - Bearer: []
    parameters:
      - in: path
        name: device_id
        required: true
        type: integer
    responses:
      200:
        description: Device details
      404:
        description: Device not found
    """
    success, result, message, status_code = DeviceService.get_device_by_id(device_id)
    if not success:
        return error_response(message, result, status_code)

    return success_response(data=result, message=message, status_code=status_code)


@device_bp.route("/<int:device_id>", methods=["PUT"])
@require_role("ADMIN")
def update_device(device_id):
    """
    Update a device (ADMIN only)
    ---
    tags:
      - Devices
    security:
      - Bearer: []
    parameters:
      - in: path
        name: device_id
        required: true
        type: integer
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            device_name:
              type: string
            location:
              type: string
            device_type:
              type: string
            status:
              type: string
              enum: [ONLINE, OFFLINE, WARNING]
    responses:
      200:
        description: Device updated successfully
      400:
        description: Validation error
      403:
        description: Forbidden (Non-ADMIN users)
      404:
        description: Device not found
    """
    json_data = request.get_json() or {}
    errors = update_schema.validate(json_data)
    if errors:
        return error_response("Validation failed", "VALIDATION_ERROR", 400, errors=errors)

    success, result, message, status_code = DeviceService.update_device(device_id, json_data)
    if not success:
        return error_response(message, result, status_code)

    return success_response(data=result, message=message, status_code=status_code)


@device_bp.route("/<int:device_id>", methods=["DELETE"])
@require_role("ADMIN")
def delete_device(device_id):
    """
    Deactivate/Soft-delete a device (ADMIN only)
    ---
    tags:
      - Devices
    security:
      - Bearer: []
    parameters:
      - in: path
        name: device_id
        required: true
        type: integer
    responses:
      200:
        description: Device deactivated successfully
      403:
        description: Forbidden (Non-ADMIN users)
      404:
        description: Device not found
    """
    success, result, message, status_code = DeviceService.delete_device(device_id)
    if not success:
        return error_response(message, result, status_code)

    return success_response(data=result, message=message, status_code=status_code)


@device_bp.route("/<int:device_id>/status", methods=["GET"])
@jwt_required()
def get_device_status(device_id):
    """
    Get current status and metrics of a device
    ---
    tags:
      - Devices
    security:
      - Bearer: []
    parameters:
      - in: path
        name: device_id
        required: true
        type: integer
    responses:
      200:
        description: Device status and metrics
      404:
        description: Device not found
    """
    success, result, message, status_code = DeviceService.get_device_status(device_id)
    if not success:
        return error_response(message, result, status_code)

    return success_response(data=result, message=message, status_code=status_code)
