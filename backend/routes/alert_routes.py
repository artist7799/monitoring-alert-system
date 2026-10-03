from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from middleware.auth_middleware import require_role
from services.alert_service import AlertService
from utils.response import success_response, error_response

alert_bp = Blueprint("alerts", __name__)

@alert_bp.route("", methods=["GET"])
@jwt_required()
def list_alerts():
    """
    List alerts with filtering, search, pagination, and sorting
    ---
    tags:
      - Alerts
    security:
      - Bearer: []
    parameters:
      - in: query
        name: severity
        type: string
        enum: [LOW, MEDIUM, HIGH, CRITICAL]
      - in: query
        name: status
        type: string
        enum: [OPEN, ACKNOWLEDGED, RESOLVED]
      - in: query
        name: device_id
        type: integer
      - in: query
        name: alert_type
        type: string
      - in: query
        name: from_date
        type: string
        example: 2026-09-01
      - in: query
        name: to_date
        type: string
        example: 2026-09-29
      - in: query
        name: search
        type: string
      - in: query
        name: sort
        type: string
        default: created_at
        enum: [created_at, severity, status, alert_type]
      - in: query
        name: order
        type: string
        default: desc
        enum: [asc, desc]
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
        description: Paginated list of alerts
      400:
        description: Invalid filter/sort parameters
      401:
        description: Unauthorized
    """
    filters = {
        "severity": request.args.get("severity"),
        "status": request.args.get("status"),
        "device_id": request.args.get("device_id"),
        "alert_type": request.args.get("alert_type"),
        "from_date": request.args.get("from_date"),
        "to_date": request.args.get("to_date"),
        "search": request.args.get("search")
    }

    sort_by = request.args.get("sort", "created_at")
    sort_order = request.args.get("order", "desc")

    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 20))
    except ValueError:
        page = 1
        per_page = 20

    success, result, message, status_code = AlertService.get_alerts(
        filters=filters,
        page=page,
        per_page=per_page,
        sort_by=sort_by,
        sort_order=sort_order
    )
    if not success:
        return error_response(message, result, status_code)

    return jsonify({
        "success": True,
        "message": message,
        "data": result["alerts"],
        "pagination": result["pagination"]
    }), status_code


@alert_bp.route("/<int:alert_id>", methods=["GET"])
@jwt_required()
def get_alert(alert_id):
    """
    Get alert details by ID
    ---
    tags:
      - Alerts
    security:
      - Bearer: []
    parameters:
      - in: path
        name: alert_id
        required: true
        type: integer
    responses:
      200:
        description: Alert details including device and event context
      404:
        description: Alert not found
    """
    success, result, message, status_code = AlertService.get_alert_by_id(alert_id)
    if not success:
        return error_response(message, result, status_code)

    return success_response(data=result, message=message, status_code=status_code)


@alert_bp.route("/<int:alert_id>/acknowledge", methods=["POST"])
@require_role("ADMIN", "OPERATOR")
def acknowledge_alert(alert_id):
    """
    Acknowledge an OPEN alert (ADMIN or OPERATOR)
    ---
    tags:
      - Alerts
    security:
      - Bearer: []
    parameters:
      - in: path
        name: alert_id
        required: true
        type: integer
    responses:
      200:
        description: Alert acknowledged successfully
      400:
        description: Invalid state transition (e.g. alert already acknowledged or resolved)
      401:
        description: Unauthorized
      403:
        description: Forbidden (VIEWER users)
      404:
        description: Alert not found
    """
    success, result, message, status_code = AlertService.acknowledge_alert(alert_id)
    if not success:
        return error_response(message, result, status_code)

    return success_response(data=result, message=message, status_code=status_code)


@alert_bp.route("/<int:alert_id>/resolve", methods=["POST"])
@require_role("ADMIN", "OPERATOR")
def resolve_alert(alert_id):
    """
    Resolve an OPEN or ACKNOWLEDGED alert (ADMIN or OPERATOR)
    ---
    tags:
      - Alerts
    security:
      - Bearer: []
    parameters:
      - in: path
        name: alert_id
        required: true
        type: integer
    responses:
      200:
        description: Alert resolved successfully
      400:
        description: Invalid state transition (e.g. alert already resolved)
      401:
        description: Unauthorized
      403:
        description: Forbidden (VIEWER users)
      404:
        description: Alert not found
    """
    success, result, message, status_code = AlertService.resolve_alert(alert_id)
    if not success:
        return error_response(message, result, status_code)

    return success_response(data=result, message=message, status_code=status_code)
