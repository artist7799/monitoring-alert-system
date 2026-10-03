from datetime import datetime
from database.db import db
from models.enums import DeviceStatus

class SystemStatus(db.Model):
    __tablename__ = "system_status"

    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey("devices.id"), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default=DeviceStatus.ONLINE.value)
    cpu_usage = db.Column(db.Float, nullable=True)
    memory_usage = db.Column(db.Float, nullable=True)
    temperature = db.Column(db.Float, nullable=True)
    uptime = db.Column(db.Integer, nullable=True)
    checked_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    device = db.relationship("Device", back_populates="system_statuses")

    def to_dict(self):
        return {
            "id": self.id,
            "device_id": self.device_id,
            "status": self.status,
            "cpu_usage": self.cpu_usage,
            "memory_usage": self.memory_usage,
            "temperature": self.temperature,
            "uptime": self.uptime,
            "checked_at": self.checked_at.isoformat() if self.checked_at else None
        }

    def __repr__(self):
        return f"<SystemStatus Device:{self.device_id} Status:{self.status}>"
