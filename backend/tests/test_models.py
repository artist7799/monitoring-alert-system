import pytest
from datetime import datetime
from database.db import db
from models.user import User
from models.device import Device
from models.event import Event
from models.alert import Alert
from models.system_status import SystemStatus
from models.enums import UserRole, DeviceStatus, EventType, AlertSeverity, AlertStatus

@pytest.fixture
def test_app():
    from app import create_app
    app = create_app(config_override={
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"
    })

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def db_session(test_app):
    with test_app.app_context():
        yield db.session

def test_create_user(db_session):
    user = User(
        name="Test User",
        email="test@example.com",
        password_hash="hashed_pw_secret",
        role=UserRole.ADMIN.value
    )
    db_session.add(user)
    db_session.commit()

    saved_user = User.query.filter_by(email="test@example.com").first()
    assert saved_user is not None
    assert saved_user.name == "Test User"
    assert saved_user.role == "ADMIN"
    assert saved_user.id is not None

def test_user_email_unique_constraint(db_session):
    u1 = User(name="User 1", email="dup@example.com", password_hash="pw1", role="VIEWER")
    u2 = User(name="User 2", email="dup@example.com", password_hash="pw2", role="OPERATOR")
    db_session.add(u1)
    db_session.commit()

    db_session.add(u2)
    with pytest.raises(Exception):
        db_session.commit()
    db_session.rollback()

def test_create_device_and_relationships(db_session):
    device = Device(
        device_code="DEV999",
        device_name="Test Sensor Node",
        location="Lab 1",
        device_type="IoT",
        status=DeviceStatus.ONLINE.value
    )
    db_session.add(device)
    db_session.commit()

    event = Event(
        device_id=device.id,
        event_type=EventType.TEMPERATURE.value,
        metric_name="temp",
        metric_value=72.5,
        unit="C",
        message="Normal temp"
    )
    db_session.add(event)
    db_session.commit()

    alert = Alert(
        event_id=event.id,
        device_id=device.id,
        title="Temp Warning",
        message="Temp is 72.5 C",
        severity=AlertSeverity.LOW.value,
        status=AlertStatus.OPEN.value
    )
    status = SystemStatus(
        device_id=device.id,
        status=DeviceStatus.ONLINE.value,
        cpu_usage=12.5,
        memory_usage=45.0
    )
    db_session.add_all([alert, status])
    db_session.commit()

    # Relationship assertions
    assert len(device.events) == 1
    assert device.events[0].metric_value == 72.5
    assert len(device.alerts) == 1
    assert device.alerts[0].title == "Temp Warning"
    assert len(device.system_statuses) == 1
    assert device.system_statuses[0].cpu_usage == 12.5

    # Reverse relationships
    assert event.device.device_code == "DEV999"
    assert alert.device.device_code == "DEV999"
    assert alert.event.metric_name == "temp"
    assert status.device.device_code == "DEV999"

def test_to_dict_methods(db_session):
    device = Device(
        device_code="DEV888",
        device_name="Dict Test Device",
        location="Lab 2",
        device_type="Server",
        status=DeviceStatus.WARNING.value
    )
    db_session.add(device)
    db_session.commit()

    d_dict = device.to_dict()
    assert d_dict["device_code"] == "DEV888"
    assert d_dict["status"] == "WARNING"
