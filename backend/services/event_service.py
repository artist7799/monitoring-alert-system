from datetime import datetime
from sqlalchemy import or_
from database.db import db
from models.device import Device
from models.event import Event

ALLOWED_SORT_FIELDS = {
    "timestamp": Event.timestamp,
    "created_at": Event.created_at,
    "metric_value": Event.metric_value,
    "event_type": Event.event_type
}

class EventService:
    @staticmethod
    def create_event(data: dict):
        device_id = data.get("device_id")
        device = db.session.get(Device, device_id)
        
        if not device:
            return False, "DEVICE_NOT_FOUND", "Device not found", 404

        if not device.is_active:
            return False, "DEVICE_INACTIVE", "Cannot process events for an inactive device", 409

        # Handle optional timestamp
        raw_ts = data.get("timestamp")
        if raw_ts:
            if isinstance(raw_ts, str):
                try:
                    # Clean ISO format if trailing Z
                    ts_str = raw_ts.replace("Z", "+00:00")
                    event_ts = datetime.fromisoformat(ts_str)
                except ValueError:
                    return False, "INVALID_TIMESTAMP", "Invalid ISO datetime format for timestamp", 400
            elif isinstance(raw_ts, datetime):
                event_ts = raw_ts
            else:
                return False, "INVALID_TIMESTAMP", "Invalid timestamp type", 400
        else:
            event_ts = datetime.utcnow()

        try:
            # Update device last_seen timestamp
            device.last_seen = event_ts

            event = Event(
                device_id=device.id,
                event_type=data.get("event_type"),
                metric_name=data.get("metric_name", "").strip(),
                metric_value=float(data.get("metric_value")),
                unit=data.get("unit", "").strip(),
                message=data.get("message", "").strip() if data.get("message") else None,
                timestamp=event_ts
            )

            db.session.add(event)
            db.session.flush()  # Ensures event.id is available for Alert relationship

            from services.alert_service import AlertService
            generated_alert = AlertService.create_alert_from_event(event, device)

            db.session.commit()

            result_dict = event.to_dict()
            if generated_alert:
                result_dict["alert"] = generated_alert.to_dict()

            return True, result_dict, "Event created successfully", 201

        except Exception as e:
            db.session.rollback()
            return False, "DATABASE_ERROR", f"Failed to record event: {str(e)}", 500


    @staticmethod
    def get_events(filters: dict, page: int = 1, per_page: int = 20, sort_by: str = "timestamp", sort_order: str = "desc"):
        query = Event.query

        if filters.get("device_id"):
            try:
                dev_id = int(filters["device_id"])
                query = query.filter(Event.device_id == dev_id)
            except ValueError:
                return False, "INVALID_FILTER", "device_id must be an integer", 400

        if filters.get("event_type"):
            query = query.filter(Event.event_type == filters["event_type"])

        if filters.get("metric_name"):
            query = query.filter(Event.metric_name == filters["metric_name"])

        if filters.get("from_date"):
            try:
                from_dt_str = str(filters["from_date"]).replace("Z", "+00:00")
                if len(from_dt_str) == 10:  # YYYY-MM-DD
                    from_dt = datetime.strptime(from_dt_str, "%Y-%m-%d")
                else:
                    from_dt = datetime.fromisoformat(from_dt_str)
                query = query.filter(Event.timestamp >= from_dt)
            except ValueError:
                return False, "INVALID_DATE_FORMAT", "from_date must be YYYY-MM-DD or ISO format", 400

        if filters.get("to_date"):
            try:
                to_dt_str = str(filters["to_date"]).replace("Z", "+00:00")
                if len(to_dt_str) == 10:  # YYYY-MM-DD
                    to_dt = datetime.strptime(to_dt_str + " 23:59:59", "%Y-%m-%d %H:%M:%S")
                else:
                    to_dt = datetime.fromisoformat(to_dt_str)
                query = query.filter(Event.timestamp <= to_dt)
            except ValueError:
                return False, "INVALID_DATE_FORMAT", "to_date must be YYYY-MM-DD or ISO format", 400

        if filters.get("search"):
            term = f"%{filters['search']}%"
            query = query.filter(
                or_(
                    Event.event_type.ilike(term),
                    Event.metric_name.ilike(term),
                    Event.message.ilike(term),
                    Event.unit.ilike(term)
                )
            )

        # Sorting validation
        sort_by_clean = sort_by.lower().strip()
        if sort_by_clean not in ALLOWED_SORT_FIELDS:
            return False, "INVALID_SORT_FIELD", f"sort parameter must be one of: {list(ALLOWED_SORT_FIELDS.keys())}", 400

        sort_col = ALLOWED_SORT_FIELDS[sort_by_clean]
        sort_order_clean = sort_order.lower().strip()
        if sort_order_clean == "asc":
            query = query.order_by(sort_col.asc())
        elif sort_order_clean == "desc":
            query = query.order_by(sort_col.desc())
        else:
            return False, "INVALID_SORT_ORDER", "order parameter must be 'asc' or 'desc'", 400

        page = max(1, page)
        per_page = min(100, max(1, per_page))

        paginated = query.paginate(page=page, per_page=per_page, error_out=False)

        result_events = [e.to_dict() for e in paginated.items]
        pagination_meta = {
            "page": paginated.page,
            "per_page": paginated.per_page,
            "total": paginated.total,
            "pages": paginated.pages
        }

        return True, {"events": result_events, "pagination": pagination_meta}, "Events retrieved successfully", 200

    @staticmethod
    def get_event_by_id(event_id: int):
        event = db.session.get(Event, event_id)
        if not event:
            return False, "EVENT_NOT_FOUND", "Event not found", 404

        event_dict = event.to_dict()
        if event.device:
            event_dict["device"] = {
                "id": event.device.id,
                "device_code": event.device.device_code,
                "device_name": event.device.device_name,
                "location": event.device.location
            }

        return True, event_dict, "Event retrieved successfully", 200
