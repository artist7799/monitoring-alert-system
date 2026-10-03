from datetime import datetime
from sqlalchemy import or_
from database.db import db
from models.device import Device
from models.event import Event
from models.alert import Alert
from models.system_status import SystemStatus
from models.enums import DeviceStatus, AlertStatus, AlertSeverity

class MonitoringService:
    @staticmethod
    def get_device_statuses(filters: dict, page: int = 1, per_page: int = 20):
        query = Device.query.filter_by(is_active=True)

        if filters.get("status"):
            status_val = filters["status"].upper()
            if status_val not in [s.value for s in DeviceStatus]:
                return False, "INVALID_STATUS", f"Status must be one of: {[s.value for s in DeviceStatus]}", 400
            query = query.filter(Device.status == status_val)

        if filters.get("location"):
            query = query.filter(Device.location.ilike(f"%{filters['location']}%"))

        if filters.get("search"):
            term = f"%{filters['search']}%"
            query = query.filter(
                or_(
                    Device.device_code.ilike(term),
                    Device.device_name.ilike(term),
                    Device.location.ilike(term),
                    Device.device_type.ilike(term)
                )
            )

        page = max(1, page)
        per_page = min(100, max(1, per_page))

        paginated = query.order_by(Device.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        devices_status_list = []
        for device in paginated.items:
            latest_status = SystemStatus.query.filter_by(device_id=device.id)\
                .order_by(SystemStatus.checked_at.desc())\
                .first()

            devices_status_list.append({
                "device_id": device.id,
                "device_code": device.device_code,
                "device_name": device.device_name,
                "location": device.location,
                "device_type": device.device_type,
                "status": device.status,
                "last_seen": device.last_seen.isoformat() if device.last_seen else None,
                "cpu_usage": latest_status.cpu_usage if latest_status else None,
                "memory_usage": latest_status.memory_usage if latest_status else None,
                "temperature": latest_status.temperature if latest_status else None,
                "uptime": latest_status.uptime if latest_status else None,
                "checked_at": latest_status.checked_at.isoformat() if (latest_status and latest_status.checked_at) else None
            })

        pagination_meta = {
            "page": paginated.page,
            "per_page": paginated.per_page,
            "total": paginated.total,
            "pages": paginated.pages
        }

        return True, {"devices": devices_status_list, "pagination": pagination_meta}, "Device statuses retrieved successfully", 200

    @staticmethod
    def get_single_device_status(device_id: int):
        device = db.session.get(Device, device_id)
        if not device or not device.is_active:
            return False, "DEVICE_NOT_FOUND", "Device not found", 404

        latest_status = SystemStatus.query.filter_by(device_id=device.id)\
            .order_by(SystemStatus.checked_at.desc())\
            .first()

        recent_events = Event.query.filter_by(device_id=device.id)\
            .order_by(Event.timestamp.desc())\
            .limit(5)\
            .all()

        open_alert_count = Alert.query.filter_by(
            device_id=device.id,
            status=AlertStatus.OPEN.value
        ).count()

        status_info = {
            "device_id": device.id,
            "device_code": device.device_code,
            "device_name": device.device_name,
            "location": device.location,
            "device_type": device.device_type,
            "status": device.status,
            "last_seen": device.last_seen.isoformat() if device.last_seen else None,
            "cpu_usage": latest_status.cpu_usage if latest_status else None,
            "memory_usage": latest_status.memory_usage if latest_status else None,
            "temperature": latest_status.temperature if latest_status else None,
            "uptime": latest_status.uptime if latest_status else None,
            "checked_at": latest_status.checked_at.isoformat() if (latest_status and latest_status.checked_at) else None,
            "open_alert_count": open_alert_count,
            "recent_events": [e.to_dict() for e in recent_events]
        }

        return True, status_info, "Single device status retrieved successfully", 200

    @staticmethod
    def get_system_overview():
        total_devices = Device.query.filter_by(is_active=True).count()
        online_devices = Device.query.filter_by(is_active=True, status=DeviceStatus.ONLINE.value).count()
        offline_devices = Device.query.filter_by(is_active=True, status=DeviceStatus.OFFLINE.value).count()
        warning_devices = Device.query.filter_by(is_active=True, status=DeviceStatus.WARNING.value).count()

        open_alerts = Alert.query.filter_by(status=AlertStatus.OPEN.value).count()
        critical_alerts = Alert.query.filter_by(
            status=AlertStatus.OPEN.value,
            severity=AlertSeverity.CRITICAL.value
        ).count()

        now_utc = datetime.utcnow()
        start_of_today_utc = datetime(now_utc.year, now_utc.month, now_utc.day, 0, 0, 0)
        events_today = Event.query.filter(Event.timestamp >= start_of_today_utc).count()

        overview_data = {
            "total_devices": total_devices,
            "online_devices": online_devices,
            "offline_devices": offline_devices,
            "warning_devices": warning_devices,
            "open_alerts": open_alerts,
            "critical_alerts": critical_alerts,
            "events_today": events_today
        }

        return True, overview_data, "System overview retrieved successfully", 200

    @staticmethod
    def get_recent_events(limit: int = 10):
        limit = min(100, max(1, limit))
        events = Event.query.order_by(Event.timestamp.desc()).limit(limit).all()
        return True, [e.to_dict() for e in events], "Recent events retrieved successfully", 200

    @staticmethod
    def get_recent_alerts(limit: int = 10):
        limit = min(100, max(1, limit))
        alerts = Alert.query.order_by(Alert.created_at.desc()).limit(limit).all()
        return True, [a.to_dict() for a in alerts], "Recent alerts retrieved successfully", 200
