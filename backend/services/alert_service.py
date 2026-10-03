from datetime import datetime
from sqlalchemy import or_
from database.db import db
from models.alert import Alert
from models.enums import AlertSeverity, AlertStatus, EventType

ALLOWED_ALERT_SORT_FIELDS = {
    "created_at": Alert.created_at,
    "severity": Alert.severity,
    "status": Alert.status,
    "alert_type": Alert.alert_type
}

class AlertService:
    @staticmethod
    def evaluate_event_for_alert(event, device):
        """Evaluate monitoring event against configurable alert rules."""
        e_type = event.event_type.upper() if event.event_type else ""
        m_name = event.metric_name.lower() if event.metric_name else ""
        val = event.metric_value

        # 1. Temperature Rule
        if e_type == EventType.TEMPERATURE.value or m_name == "temperature":
            if val < 70:
                return None
            elif 70 <= val < 80:
                return (
                    AlertSeverity.LOW.value,
                    "TEMPERATURE_THRESHOLD",
                    "Low Temperature Warning",
                    f"Temperature reading {val}°{event.unit or 'C'} reached low threshold on device {device.device_code}"
                )
            elif 80 <= val < 90:
                return (
                    AlertSeverity.HIGH.value,
                    "TEMPERATURE_THRESHOLD",
                    "High Temperature Warning",
                    f"Temperature reading {val}°{event.unit or 'C'} exceeded high threshold on device {device.device_code}"
                )
            else:  # val >= 90
                return (
                    AlertSeverity.CRITICAL.value,
                    "TEMPERATURE_THRESHOLD",
                    "Critical Temperature Emergency",
                    f"Temperature reading {val}°{event.unit or 'C'} exceeded critical threshold on device {device.device_code}"
                )

        # 2. Humidity Rule
        if e_type == EventType.HUMIDITY.value or m_name == "humidity":
            if val < 20:
                return (
                    AlertSeverity.LOW.value,
                    "HUMIDITY_THRESHOLD",
                    "Low Humidity Warning",
                    f"Humidity reading {val}% dropped below minimum threshold on device {device.device_code}"
                )
            elif 20 <= val <= 80:
                return None
            elif 80 < val <= 90:
                return (
                    AlertSeverity.HIGH.value,
                    "HUMIDITY_THRESHOLD",
                    "High Humidity Warning",
                    f"Humidity reading {val}% exceeded high threshold on device {device.device_code}"
                )
            else:  # val > 90
                return (
                    AlertSeverity.CRITICAL.value,
                    "HUMIDITY_THRESHOLD",
                    "Critical Humidity Emergency",
                    f"Humidity reading {val}% exceeded critical threshold on device {device.device_code}"
                )

        # 3. CPU Usage Rule
        if e_type == EventType.CPU_USAGE.value or m_name == "cpu_usage":
            if val < 80:
                return None
            elif 80 <= val < 90:
                return (
                    AlertSeverity.HIGH.value,
                    "CPU_THRESHOLD",
                    "High CPU Load",
                    f"CPU usage reached {val}% on device {device.device_code}"
                )
            else:  # val >= 90
                return (
                    AlertSeverity.CRITICAL.value,
                    "CPU_THRESHOLD",
                    "Critical CPU Load",
                    f"CPU usage reached {val}% on device {device.device_code}"
                )

        # 4. Memory Usage Rule
        if e_type == EventType.MEMORY_USAGE.value or m_name == "memory_usage":
            if val < 80:
                return None
            elif 80 <= val < 90:
                return (
                    AlertSeverity.HIGH.value,
                    "MEMORY_THRESHOLD",
                    "High Memory Load",
                    f"Memory usage reached {val}% on device {device.device_code}"
                )
            else:  # val >= 90
                return (
                    AlertSeverity.CRITICAL.value,
                    "MEMORY_THRESHOLD",
                    "Critical Memory Load",
                    f"Memory usage reached {val}% on device {device.device_code}"
                )

        # 5. Smoke Detection Rule
        if e_type == EventType.SMOKE.value or m_name in ["smoke", "smoke_detector"]:
            if val > 0:
                return (
                    AlertSeverity.CRITICAL.value,
                    "SMOKE_DETECTED",
                    "Smoke Detection Emergency",
                    f"Smoke alarm triggered by device {device.device_code} at location {device.location}"
                )
            return None

        # 6. System Error Rule
        if e_type == EventType.SYSTEM_ERROR.value:
            return (
                AlertSeverity.HIGH.value,
                "SYSTEM_ERROR",
                "System Error Reported",
                f"System error reported by device {device.device_code}: {event.message or 'Unknown error'}"
            )

        return None

    @staticmethod
    def create_alert_from_event(event, device):
        """Evaluate event and persist alert if a rule triggers, avoiding duplicates."""
        # Duplicate prevention check
        existing = Alert.query.filter_by(event_id=event.id).first()
        if existing:
            return existing

        eval_result = AlertService.evaluate_event_for_alert(event, device)
        if not eval_result:
            return None

        severity, alert_type, title, message = eval_result

        alert = Alert(
            event_id=event.id,
            device_id=device.id,
            title=title,
            alert_type=alert_type,
            message=message,
            severity=severity,
            status=AlertStatus.OPEN.value,
            created_at=event.timestamp or datetime.utcnow()
        )

        db.session.add(alert)
        return alert

    @staticmethod
    def get_alerts(filters: dict, page: int = 1, per_page: int = 20, sort_by: str = "created_at", sort_order: str = "desc"):
        query = Alert.query

        if filters.get("severity"):
            query = query.filter(Alert.severity == filters["severity"])

        if filters.get("status"):
            query = query.filter(Alert.status == filters["status"])

        if filters.get("device_id"):
            try:
                dev_id = int(filters["device_id"])
                query = query.filter(Alert.device_id == dev_id)
            except ValueError:
                return False, "INVALID_FILTER", "device_id must be an integer", 400

        if filters.get("alert_type"):
            query = query.filter(Alert.alert_type == filters["alert_type"])

        if filters.get("from_date"):
            try:
                from_dt_str = str(filters["from_date"]).replace("Z", "+00:00")
                if len(from_dt_str) == 10:
                    from_dt = datetime.strptime(from_dt_str, "%Y-%m-%d")
                else:
                    from_dt = datetime.fromisoformat(from_dt_str)
                query = query.filter(Alert.created_at >= from_dt)
            except ValueError:
                return False, "INVALID_DATE_FORMAT", "from_date must be YYYY-MM-DD or ISO format", 400

        if filters.get("to_date"):
            try:
                to_dt_str = str(filters["to_date"]).replace("Z", "+00:00")
                if len(to_dt_str) == 10:
                    to_dt = datetime.strptime(to_dt_str + " 23:59:59", "%Y-%m-%d %H:%M:%S")
                else:
                    to_dt = datetime.fromisoformat(to_dt_str)
                query = query.filter(Alert.created_at <= to_dt)
            except ValueError:
                return False, "INVALID_DATE_FORMAT", "to_date must be YYYY-MM-DD or ISO format", 400

        if filters.get("search"):
            term = f"%{filters['search']}%"
            query = query.filter(
                or_(
                    Alert.alert_type.ilike(term),
                    Alert.title.ilike(term),
                    Alert.message.ilike(term)
                )
            )

        sort_by_clean = sort_by.lower().strip()
        if sort_by_clean not in ALLOWED_ALERT_SORT_FIELDS:
            return False, "INVALID_SORT_FIELD", f"sort parameter must be one of: {list(ALLOWED_ALERT_SORT_FIELDS.keys())}", 400

        sort_col = ALLOWED_ALERT_SORT_FIELDS[sort_by_clean]
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

        result_alerts = [a.to_dict() for a in paginated.items]
        pagination_meta = {
            "page": paginated.page,
            "per_page": paginated.per_page,
            "total": paginated.total,
            "pages": paginated.pages
        }

        return True, {"alerts": result_alerts, "pagination": pagination_meta}, "Alerts retrieved successfully", 200

    @staticmethod
    def get_alert_by_id(alert_id: int):
        alert = db.session.get(Alert, alert_id)
        if not alert:
            return False, "ALERT_NOT_FOUND", "Alert not found", 404

        alert_dict = alert.to_dict()
        if alert.device:
            alert_dict["device"] = {
                "id": alert.device.id,
                "device_code": alert.device.device_code,
                "device_name": alert.device.device_name,
                "location": alert.device.location
            }
        if alert.event:
            alert_dict["event"] = alert.event.to_dict()

        return True, alert_dict, "Alert retrieved successfully", 200

    @staticmethod
    def acknowledge_alert(alert_id: int):
        alert = db.session.get(Alert, alert_id)
        if not alert:
            return False, "ALERT_NOT_FOUND", "Alert not found", 404

        if alert.status != AlertStatus.OPEN.value:
            return False, "INVALID_STATE_TRANSITION", f"Cannot acknowledge alert in '{alert.status}' status. Only OPEN alerts can be acknowledged.", 400

        alert.status = AlertStatus.ACKNOWLEDGED.value
        alert.acknowledged_at = datetime.utcnow()
        db.session.commit()

        return True, alert.to_dict(), "Alert acknowledged successfully", 200

    @staticmethod
    def resolve_alert(alert_id: int):
        alert = db.session.get(Alert, alert_id)
        if not alert:
            return False, "ALERT_NOT_FOUND", "Alert not found", 404

        if alert.status == AlertStatus.RESOLVED.value:
            return False, "INVALID_STATE_TRANSITION", "Alert is already RESOLVED.", 400

        alert.status = AlertStatus.RESOLVED.value
        alert.resolved_at = datetime.utcnow()
        db.session.commit()

        return True, alert.to_dict(), "Alert resolved successfully", 200
