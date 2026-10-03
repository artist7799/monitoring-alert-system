from datetime import datetime, timedelta
import bcrypt
from database.db import db
from models.user import User
from models.device import Device
from models.event import Event
from models.alert import Alert
from models.system_status import SystemStatus
from models.enums import UserRole, DeviceStatus, EventType, AlertSeverity, AlertStatus

def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(plain_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def seed_database():
    """Seed initial development data into the database."""
    # Ensure database schema tables are created
    db.create_all()

    # 1. Upsert Demo Users to guarantee exact password hashes
    users_to_seed = [
        ("Admin User", "admin@example.com", "admin123", UserRole.ADMIN.value),
        ("Operator User", "operator@example.com", "operator123", UserRole.OPERATOR.value),
        ("Viewer User", "viewer@example.com", "viewer123", UserRole.VIEWER.value),
    ]

    for name, email, password, role in users_to_seed:
        user = User.query.filter_by(email=email).first()
        if user:
            user.password_hash = hash_password(password)
            user.name = name
            user.role = role
        else:
            new_user = User(
                name=name,
                email=email,
                password_hash=hash_password(password),
                role=role
            )
            db.session.add(new_user)
    
    db.session.commit()

    # 2. Devices (Seed if none exist)
    if not Device.query.first():
        d1 = Device(
            device_code="DEV001",
            device_name="Server Room Environmental Sensor",
            location="Server Room A",
            device_type="Environmental",
            status=DeviceStatus.ONLINE.value,
            last_seen=datetime.utcnow()
        )
        d2 = Device(
            device_code="DEV002",
            device_name="Primary Compute Host Node",
            location="Datacenter Rack 4",
            device_type="Compute",
            status=DeviceStatus.WARNING.value,
            last_seen=datetime.utcnow()
        )
        d3 = Device(
            device_code="DEV003",
            device_name="SAN Storage Controller",
            location="Storage Room B",
            device_type="Storage",
            status=DeviceStatus.OFFLINE.value,
            last_seen=datetime.utcnow() - timedelta(hours=2)
        )
        db.session.add_all([d1, d2, d3])
        db.session.commit()

        # 3. Events
        e1 = Event(
            device_id=d1.id,
            event_type=EventType.TEMPERATURE.value,
            metric_name="temperature",
            metric_value=85.5,
            unit="C",
            message="Temperature threshold exceeded on Server Room Sensor",
            timestamp=datetime.utcnow() - timedelta(minutes=30)
        )
        e2 = Event(
            device_id=d2.id,
            event_type=EventType.CPU_USAGE.value,
            metric_name="cpu_usage",
            metric_value=96.2,
            unit="%",
            message="CPU utilization critical on Compute Host",
            timestamp=datetime.utcnow() - timedelta(minutes=15)
        )
        e3 = Event(
            device_id=d2.id,
            event_type=EventType.MEMORY_USAGE.value,
            metric_name="memory_usage",
            metric_value=82.0,
            unit="%",
            message="High memory load detected",
            timestamp=datetime.utcnow() - timedelta(minutes=10)
        )
        e4 = Event(
            device_id=d1.id,
            event_type=EventType.SMOKE.value,
            metric_name="smoke_detector",
            metric_value=1.0,
            unit="binary",
            message="Smoke detected near Rack A1",
            timestamp=datetime.utcnow() - timedelta(minutes=5)
        )
        db.session.add_all([e1, e2, e3, e4])
        db.session.commit()

        # 4. Alerts
        a1 = Alert(
            event_id=e1.id,
            device_id=d1.id,
            title="High Temperature Warning",
            message="Sensor reading 85.5 C is above 80 C threshold",
            severity=AlertSeverity.HIGH.value,
            status=AlertStatus.OPEN.value,
            created_at=e1.timestamp
        )
        a2 = Alert(
            event_id=e2.id,
            device_id=d2.id,
            title="Critical CPU Load",
            message="CPU load reached 96.2%",
            severity=AlertSeverity.CRITICAL.value,
            status=AlertStatus.ACKNOWLEDGED.value,
            created_at=e2.timestamp,
            acknowledged_at=datetime.utcnow() - timedelta(minutes=10)
        )
        a3 = Alert(
            event_id=e3.id,
            device_id=d2.id,
            title="Memory Warning",
            message="Memory load reached 82.0%",
            severity=AlertSeverity.MEDIUM.value,
            status=AlertStatus.OPEN.value,
            created_at=e3.timestamp
        )
        a4 = Alert(
            event_id=e4.id,
            device_id=d1.id,
            title="Smoke Detection Emergency",
            message="Smoke alarm triggered in Server Room A",
            severity=AlertSeverity.CRITICAL.value,
            status=AlertStatus.OPEN.value,
            created_at=e4.timestamp
        )
        db.session.add_all([a1, a2, a3, a4])
        db.session.commit()

        # 5. System Statuses
        s1 = SystemStatus(
            device_id=d1.id,
            status=DeviceStatus.ONLINE.value,
            temperature=85.5,
            checked_at=datetime.utcnow()
        )
        s2 = SystemStatus(
            device_id=d2.id,
            status=DeviceStatus.WARNING.value,
            cpu_usage=96.2,
            memory_usage=82.0,
            checked_at=datetime.utcnow()
        )
        db.session.add_all([s1, s2])
        db.session.commit()

    print("Database seeding and user password synchronization completed successfully.")

if __name__ == "__main__":
    from app import create_app
    app = create_app()
    with app.app_context():
        seed_database()
