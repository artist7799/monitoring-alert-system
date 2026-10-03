from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from services.monitoring_service import MonitoringService
from utils.response import success_response, error_response

status_bp = Blueprint("status", __name__)

@status_bp.route("/devices", methods=["GET"])
@jwt_required()
def list_device_statuses():
    """
    Get current status of active monitoring devices
    ---
    tags:
      - System Status
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
        name: search
        type: string
      - in: query
        name: page
        type: integer
        default: 1
      - in: query
        name: per_page
        type: integer
        default: 20
    responses:
      200:
        description: Device health status list with metrics
      400:
        description: Invalid status filter
      401:
        description: Unauthorized
    """
    filters = {
        "status": request.args.get("status"),
        "location": request.args.get("location"),
        "search": request.args.get("search")
    }

    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 20))
    except ValueError:
        page = 1
        per_page = 20

    success, result, message, status_code = MonitoringService.get_device_statuses(
        filters=filters,
        page=page,
        per_page=per_page
    )
    if not success:
        return error_response(message, result, status_code)

    return jsonify({
        "success": True,
        "message": message,
        "data": result["devices"],
        "pagination": result["pagination"]
    }), status_code


@status_bp.route("/devices/<int:device_id>", methods=["GET"])
@jwt_required()
def get_single_device_status(device_id):
    """
    Get status breakdown for a single device
    ---
    tags:
      - System Status
    security:
      - Bearer: []
    parameters:
      - in: path
        name: device_id
        required: true
        type: integer
    responses:
      200:
        description: Single device health status breakdown
      404:
        description: Device not found
    """
    success, result, message, status_code = MonitoringService.get_single_device_status(device_id)
    if not success:
        return error_response(message, result, status_code)

    return success_response(data=result, message=message, status_code=status_code)


@status_bp.route("/overview", methods=["GET"])
@status_bp.route("/summary", methods=["GET"])
@jwt_required()
def get_system_overview():
    """
    Get system-wide health and monitoring overview summary
    ---
    tags:
      - System Status
    security:
      - Bearer: []
    responses:
      200:
        description: System health summary counts
      401:
        description: Unauthorized
    """
    success, result, message, status_code = MonitoringService.get_system_overview()
    return success_response(data=result, message=message, status_code=status_code)


@status_bp.route("/recent-events", methods=["GET"])
@jwt_required()
def get_recent_events():
    """
    Get recent monitoring events
    ---
    tags:
      - System Status
    security:
      - Bearer: []
    parameters:
      - in: query
        name: limit
        type: integer
        default: 10
    responses:
      200:
        description: List of recent events
      401:
        description: Unauthorized
    """
    try:
        limit = int(request.args.get("limit", 10))
    except ValueError:
        limit = 10

    success, result, message, status_code = MonitoringService.get_recent_events(limit=limit)
    return success_response(data=result, message=message, status_code=status_code)


@status_bp.route("/recent-alerts", methods=["GET"])
@jwt_required()
def get_recent_alerts():
    """
    Get recent system alerts
    ---
    tags:
      - System Status
    security:
      - Bearer: []
    parameters:
      - in: query
        name: limit
        type: integer
        default: 10
    responses:
      200:
        description: List of recent alerts
      401:
        description: Unauthorized
    """
    try:
        limit = int(request.args.get("limit", 10))
    except ValueError:
        limit = 10

    success, result, message, status_code = MonitoringService.get_recent_alerts(limit=limit)
    return success_response(data=result, message=message, status_code=status_code)
