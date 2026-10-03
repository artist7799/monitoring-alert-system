from datetime import datetime
from database.db import db

class Event(db.Model):
    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey("devices.id"), nullable=False, index=True)
    event_type = db.Column(db.String(50), nullable=False, index=True)
    metric_name = db.Column(db.String(100), nullable=False)
    metric_value = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20), nullable=True)
    message = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    device = db.relationship("Device", back_populates="events")
    alerts = db.relationship("Alert", back_populates="event")

    def to_dict(self):
        return {
            "id": self.id,
            "device_id": self.device_id,
            "event_type": self.event_type,
            "metric_name": self.metric_name,
            "metric_value": self.metric_value,
            "unit": self.unit,
            "message": self.message,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f"<Event {self.id} Device:{self.device_id} Type:{self.event_type}>"
