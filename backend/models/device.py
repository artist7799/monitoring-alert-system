from datetime import datetime
from database.db import db
from models.enums import DeviceStatus

class Device(db.Model):
    __tablename__ = "devices"

    id = db.Column(db.Integer, primary_key=True)
    device_code = db.Column(db.String(100), unique=True, nullable=False, index=True)
    device_name = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(255), nullable=False)
    device_type = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), nullable=False, default=DeviceStatus.ONLINE.value)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    last_seen = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    events = db.relationship("Event", back_populates="device", lazy="select")
    alerts = db.relationship("Alert", back_populates="device", lazy="select")
    system_statuses = db.relationship("SystemStatus", back_populates="device", lazy="select")

    def to_dict(self):
        return {
            "id": self.id,
            "device_code": self.device_code,
            "device_name": self.device_name,
            "location": self.location,
            "device_type": self.device_type,
            "status": self.status,
            "is_active": self.is_active,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


    def __repr__(self):
        return f"<Device {self.device_code} - {self.device_name}>"
