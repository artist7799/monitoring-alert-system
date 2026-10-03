from sqlalchemy import or_
from database.db import db
from models.device import Device
from models.system_status import SystemStatus
from models.enums import DeviceStatus

class DeviceService:
    @staticmethod
    def create_device(data: dict):
        device_code = data.get("device_code", "").upper().strip()
        device_name = data.get("device_name", "").strip()
        location = data.get("location", "").strip()
        device_type = data.get("device_type", "").strip()
        status = data.get("status", DeviceStatus.OFFLINE.value)

        existing = Device.query.filter_by(device_code=device_code).first()
        if existing:
            return False, "DEVICE_EXISTS", "Device code already exists", 409

        device = Device(
            device_code=device_code,
            device_name=device_name,
            location=location,
            device_type=device_type,
            status=status,
            is_active=True,
            last_seen=None
        )

        db.session.add(device)
        db.session.commit()

        return True, device.to_dict(), "Device created successfully", 201

    @staticmethod
    def get_devices(filters: dict, page: int = 1, per_page: int = 10):
        query = Device.query.filter_by(is_active=True)

        if filters.get("status"):
            query = query.filter(Device.status == filters["status"])

        if filters.get("location"):
            query = query.filter(Device.location.ilike(f"%{filters['location']}%"))

        if filters.get("device_type"):
            query = query.filter(Device.device_type == filters["device_type"])

        if filters.get("search"):
            term = f"%{filters['search']}%"
            query = query.filter(
                or_(
                    Device.device_code.ilike(term),
                    Device.device_name.ilike(term),
                    Device.location.ilike(term)
                )
            )

        page = max(1, page)
        per_page = min(100, max(1, per_page))

        paginated = query.order_by(Device.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        result_data = [d.to_dict() for d in paginated.items]
        pagination_meta = {
            "page": paginated.page,
            "per_page": paginated.per_page,
            "total": paginated.total,
            "pages": paginated.pages
        }

        return True, {"devices": result_data, "pagination": pagination_meta}, "Devices retrieved successfully", 200

    @staticmethod
    def get_device_by_id(device_id: int):
        device = db.session.get(Device, device_id)
        if not device or not device.is_active:
            return False, "DEVICE_NOT_FOUND", "Device not found", 404

        return True, device.to_dict(), "Device retrieved successfully", 200

    @staticmethod
    def update_device(device_id: int, data: dict):
        device = db.session.get(Device, device_id)
        if not device or not device.is_active:
            return False, "DEVICE_NOT_FOUND", "Device not found", 404

        if "device_name" in data:
            device.device_name = data["device_name"].strip()
        if "location" in data:
            device.location = data["location"].strip()
        if "device_type" in data:
            device.device_type = data["device_type"].strip()
        if "status" in data:
            device.status = data["status"]

        db.session.commit()

        return True, device.to_dict(), "Device updated successfully", 200

    @staticmethod
    def delete_device(device_id: int):
        device = db.session.get(Device, device_id)
        if not device or not device.is_active:
            return False, "DEVICE_NOT_FOUND", "Device not found", 404

        # Soft deletion strategy preserving events, alerts, and system_status history
        device.is_active = False
        device.status = DeviceStatus.OFFLINE.value

        db.session.commit()

        return True, device.to_dict(), "Device deactivated successfully", 200

    @staticmethod
    def get_device_status(device_id: int):
        device = db.session.get(Device, device_id)
        if not device or not device.is_active:
            return False, "DEVICE_NOT_FOUND", "Device not found", 404

        latest_status = SystemStatus.query.filter_by(device_id=device.id)\
            .order_by(SystemStatus.checked_at.desc())\
            .first()

        status_info = {
            "device_id": device.id,
            "device_code": device.device_code,
            "status": device.status,
            "last_seen": device.last_seen.isoformat() if device.last_seen else None,
            "cpu_usage": latest_status.cpu_usage if latest_status else None,
            "memory_usage": latest_status.memory_usage if latest_status else None,
            "temperature": latest_status.temperature if latest_status else None,
            "uptime": latest_status.uptime if latest_status else None,
            "checked_at": latest_status.checked_at.isoformat() if (latest_status and latest_status.checked_at) else None
        }

        return True, status_info, "Device status retrieved successfully", 200
