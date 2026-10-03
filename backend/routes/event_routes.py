from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from middleware.auth_middleware import require_role
from schemas.event_schema import EventCreateSchema
from services.event_service import EventService
from utils.response import success_response, error_response

event_bp = Blueprint("events", __name__)

create_schema = EventCreateSchema()

@event_bp.route("", methods=["POST"])
@require_role("ADMIN", "OPERATOR")
def create_event():
    """
    Create a new monitoring event (ADMIN or OPERATOR)
    ---
    tags:
      - Events
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - device_id
            - event_type
            - metric_name
            - metric_value
            - unit
          properties:
            device_id:
              type: integer
              example: 1
            event_type:
              type: string
              enum: [TEMPERATURE, HUMIDITY, SMOKE, CPU_USAGE, MEMORY_USAGE, NETWORK, SYSTEM_ERROR]
              example: TEMPERATURE
            metric_name:
              type: string
              example: temperature
            metric_value:
              type: number
              example: 85.5
            unit:
              type: string
              example: C
            message:
              type: string
              example: Temperature exceeded normal level
            timestamp:
              type: string
              example: 2026-09-29T21:30:00Z
    responses:
      201:
        description: Event created successfully
      400:
        description: Validation error / Invalid timestamp
      401:
        description: Unauthorized
      403:
        description: Forbidden (VIEWER users)
      404:
        description: Device not found
      409:
        description: Device inactive
    """
    json_data = request.get_json() or {}
    errors = create_schema.validate(json_data)
    if errors:
        return error_response("Validation failed", "VALIDATION_ERROR", 400, errors=errors)

    success, result, message, status_code = EventService.create_event(json_data)
    if not success:
        return error_response(message, result, status_code)

    return success_response(data=result, message=message, status_code=status_code)


@event_bp.route("", methods=["GET"])
@jwt_required()
def list_events():
    """
    List events with filtering, search, pagination, and sorting
    ---
    tags:
      - Events
    security:
      - Bearer: []
    parameters:
      - in: query
        name: device_id
        type: integer
      - in: query
        name: event_type
        type: string
      - in: query
        name: metric_name
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
        default: timestamp
        enum: [timestamp, created_at, metric_value, event_type]
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
        description: Paginated list of events
      400:
        description: Invalid filter/sort parameters
      401:
        description: Unauthorized
    """
    filters = {
        "device_id": request.args.get("device_id"),
        "event_type": request.args.get("event_type"),
        "metric_name": request.args.get("metric_name"),
        "from_date": request.args.get("from_date"),
        "to_date": request.args.get("to_date"),
        "search": request.args.get("search")
    }

    sort_by = request.args.get("sort", "timestamp")
    sort_order = request.args.get("order", "desc")

    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 20))
    except ValueError:
        page = 1
        per_page = 20

    success, result, message, status_code = EventService.get_events(
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
        "data": result["events"],
        "pagination": result["pagination"]
    }), status_code


@event_bp.route("/<int:event_id>", methods=["GET"])
@jwt_required()
def get_event(event_id):
    """
    Get event details by ID
    ---
    tags:
      - Events
    security:
      - Bearer: []
    parameters:
      - in: path
        name: event_id
        required: true
        type: integer
    responses:
      200:
        description: Event details
      404:
        description: Event not found
    """
    success, result, message, status_code = EventService.get_event_by_id(event_id)
    if not success:
        return error_response(message, result, status_code)

    return success_response(data=result, message=message, status_code=status_code)
