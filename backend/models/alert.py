from datetime import datetime
from database.db import db
from models.enums import AlertSeverity, AlertStatus

class Alert(db.Model):
    __tablename__ = "alerts"

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=True)
    device_id = db.Column(db.Integer, db.ForeignKey("devices.id"), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    alert_type = db.Column(db.String(100), nullable=True, index=True)
    message = db.Column(db.Text, nullable=True)
    severity = db.Column(db.String(20), nullable=False, default=AlertSeverity.LOW.value, index=True)
    status = db.Column(db.String(20), nullable=False, default=AlertStatus.OPEN.value, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    acknowledged_at = db.Column(db.DateTime, nullable=True)
    resolved_at = db.Column(db.DateTime, nullable=True)

    event = db.relationship("Event", back_populates="alerts")
    device = db.relationship("Device", back_populates="alerts")

    def to_dict(self):
        return {
            "id": self.id,
            "event_id": self.event_id,
            "device_id": self.device_id,
            "title": self.title,
            "alert_type": self.alert_type or self.title,
            "message": self.message,
            "severity": self.severity,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None
        }


    def __repr__(self):
        return f"<Alert {self.id} [{self.severity}] {self.title}>"
