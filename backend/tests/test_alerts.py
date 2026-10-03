import pytest
from datetime import datetime, timedelta
from flask_jwt_extended import create_access_token
from app import create_app
from database.db import db
from database.seed import seed_database
from models import User, Device, Event, Alert, AlertSeverity, AlertStatus

@pytest.fixture
def alert_app():
    app = create_app(config_override={
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "JWT_SECRET_KEY": "test-jwt-secret-key-super-secret-32bytes-long!",
        "JWT_ACCESS_TOKEN_EXPIRES": timedelta(hours=1)
    })
    with app.app_context():
        db.create_all()
        seed_database()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(alert_app):
    return alert_app.test_client()

def get_token_for(app, email):
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        return create_access_token(identity=str(user.id))

# ==================== ALERT GENERATION ====================

def test_1_normal_temperature_no_alert(alert_app, client):
    token = get_token_for(alert_app, "admin@example.com")
    res = client.post("/api/events", headers={"Authorization": f"Bearer {token}"}, json={
        "device_id": 1,
        "event_type": "TEMPERATURE",
        "metric_name": "temperature",
        "metric_value": 65.0,
        "unit": "C"
    })
    assert res.status_code == 201
    data = res.get_json()["data"]
    assert "alert" not in data

def test_2_low_temperature_low_alert(alert_app, client):
    token = get_token_for(alert_app, "admin@example.com")
    res = client.post("/api/events", headers={"Authorization": f"Bearer {token}"}, json={
        "device_id": 1,
        "event_type": "TEMPERATURE",
        "metric_name": "temperature",
        "metric_value": 75.0,
        "unit": "C"
    })
    assert res.status_code == 201
    alert = res.get_json()["data"]["alert"]
    assert alert["severity"] == "LOW"
    assert alert["alert_type"] == "TEMPERATURE_THRESHOLD"

def test_3_high_temperature_high_alert(alert_app, client):
    token = get_token_for(alert_app, "admin@example.com")
    res = client.post("/api/events", headers={"Authorization": f"Bearer {token}"}, json={
        "device_id": 1,
        "event_type": "TEMPERATURE",
        "metric_name": "temperature",
        "metric_value": 85.0,
        "unit": "C"
    })
    assert res.status_code == 201
    alert = res.get_json()["data"]["alert"]
    assert alert["severity"] == "HIGH"

def test_4_critical_temperature_critical_alert(alert_app, client):
    token = get_token_for(alert_app, "admin@example.com")
    res = client.post("/api/events", headers={"Authorization": f"Bearer {token}"}, json={
        "device_id": 1,
        "event_type": "TEMPERATURE",
        "metric_name": "temperature",
        "metric_value": 95.0,
        "unit": "C"
    })
    assert res.status_code == 201
    alert = res.get_json()["data"]["alert"]
    assert alert["severity"] == "CRITICAL"

def test_5_high_cpu_high_alert(alert_app, client):
    token = get_token_for(alert_app, "admin@example.com")
    res = client.post("/api/events", headers={"Authorization": f"Bearer {token}"}, json={
        "device_id": 2,
        "event_type": "CPU_USAGE",
        "metric_name": "cpu_usage",
        "metric_value": 85.0,
        "unit": "%"
    })
    assert res.status_code == 201
    alert = res.get_json()["data"]["alert"]
    assert alert["severity"] == "HIGH"

def test_6_critical_cpu_critical_alert(alert_app, client):
    token = get_token_for(alert_app, "admin@example.com")
    res = client.post("/api/events", headers={"Authorization": f"Bearer {token}"}, json={
        "device_id": 2,
        "event_type": "CPU_USAGE",
        "metric_name": "cpu_usage",
        "metric_value": 95.0,
        "unit": "%"
    })
    assert res.status_code == 201
    alert = res.get_json()["data"]["alert"]
    assert alert["severity"] == "CRITICAL"

def test_7_high_memory_high_alert(alert_app, client):
    token = get_token_for(alert_app, "admin@example.com")
    res = client.post("/api/events", headers={"Authorization": f"Bearer {token}"}, json={
        "device_id": 2,
        "event_type": "MEMORY_USAGE",
        "metric_name": "memory_usage",
        "metric_value": 85.0,
        "unit": "%"
    })
    assert res.status_code == 201
    alert = res.get_json()["data"]["alert"]
    assert alert["severity"] == "HIGH"

def test_8_critical_memory_critical_alert(alert_app, client):
    token = get_token_for(alert_app, "admin@example.com")
    res = client.post("/api/events", headers={"Authorization": f"Bearer {token}"}, json={
        "device_id": 2,
        "event_type": "MEMORY_USAGE",
        "metric_name": "memory_usage",
        "metric_value": 95.0,
        "unit": "%"
    })
    assert res.status_code == 201
    alert = res.get_json()["data"]["alert"]
    assert alert["severity"] == "CRITICAL"

def test_9_smoke_critical_alert(alert_app, client):
    token = get_token_for(alert_app, "admin@example.com")
    res = client.post("/api/events", headers={"Authorization": f"Bearer {token}"}, json={
        "device_id": 1,
        "event_type": "SMOKE",
        "metric_name": "smoke_detector",
        "metric_value": 1.0,
        "unit": "binary",
        "message": "Smoke alarm"
    })
    assert res.status_code == 201
    alert = res.get_json()["data"]["alert"]
    assert alert["severity"] == "CRITICAL"
    assert alert["alert_type"] == "SMOKE_DETECTED"

def test_10_system_error_high_alert(alert_app, client):
    token = get_token_for(alert_app, "admin@example.com")
    res = client.post("/api/events", headers={"Authorization": f"Bearer {token}"}, json={
        "device_id": 2,
        "event_type": "SYSTEM_ERROR",
        "metric_name": "system",
        "metric_value": 500.0,
        "unit": "code",
        "message": "Kernel panic"
    })
    assert res.status_code == 201
    alert = res.get_json()["data"]["alert"]
    assert alert["severity"] == "HIGH"

# ==================== DUPLICATE PREVENTION ====================

def test_11_duplicate_prevention_same_event(alert_app):
    from services.alert_service import AlertService
    with alert_app.app_context():
        event = db.session.get(Event, 1)
        device = db.session.get(Device, 1)
        
        a1 = AlertService.create_alert_from_event(event, device)
        a2 = AlertService.create_alert_from_event(event, device)
        assert a1.id == a2.id

def test_12_unique_event_id_relationship(alert_app):
    with alert_app.app_context():
        event = db.session.get(Event, 1)
        alerts = Alert.query.filter_by(event_id=event.id).all()
        assert len(alerts) <= 1

# ==================== ALERT APIs & READING ====================

def test_13_admin_can_list_alerts(alert_app, client):
    token = get_token_for(alert_app, "admin@example.com")
    res = client.get("/api/alerts", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert len(res.get_json()["data"]) >= 4

def test_14_operator_can_list_alerts(alert_app, client):
    token = get_token_for(alert_app, "operator@example.com")
    res = client.get("/api/alerts", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200

def test_15_viewer_can_list_alerts(alert_app, client):
    token = get_token_for(alert_app, "viewer@example.com")
    res = client.get("/api/alerts", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200

def test_16_get_alert_by_id(alert_app, client):
    token = get_token_for(alert_app, "viewer@example.com")
    res = client.get("/api/alerts/1", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.get_json()["data"]["id"] == 1

def test_17_unknown_alert_404(alert_app, client):
    token = get_token_for(alert_app, "viewer@example.com")
    res = client.get("/api/alerts/99999", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 404
    assert res.get_json()["error"] == "ALERT_NOT_FOUND"

def test_18_filter_by_severity(alert_app, client):
    token = get_token_for(alert_app, "admin@example.com")
    res = client.get("/api/alerts?severity=CRITICAL", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    alerts = res.get_json()["data"]
    for a in alerts:
        assert a["severity"] == "CRITICAL"

def test_19_filter_by_status(alert_app, client):
    token = get_token_for(alert_app, "admin@example.com")
    res = client.get("/api/alerts?status=OPEN", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    alerts = res.get_json()["data"]
    for a in alerts:
        assert a["status"] == "OPEN"

def test_20_filter_by_device(alert_app, client):
    token = get_token_for(alert_app, "admin@example.com")
    res = client.get("/api/alerts?device_id=1", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    alerts = res.get_json()["data"]
    for a in alerts:
        assert a["device_id"] == 1

def test_21_filter_by_alert_type(alert_app, client):
    token = get_token_for(alert_app, "admin@example.com")
    # Trigger an alert first
    client.post("/api/events", headers={"Authorization": f"Bearer {token}"}, json={
        "device_id": 1, "event_type": "SMOKE", "metric_name": "smoke", "metric_value": 1.0, "unit": "b"
    })
    res = client.get("/api/alerts?alert_type=SMOKE_DETECTED", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    alerts = res.get_json()["data"]
    assert len(alerts) >= 1

def test_22_search_alerts(alert_app, client):
    token = get_token_for(alert_app, "admin@example.com")
    res = client.get("/api/alerts?search=Smoke", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    alerts = res.get_json()["data"]
    assert len(alerts) >= 1

def test_23_date_filtering(alert_app, client):
    token = get_token_for(alert_app, "admin@example.com")
    res = client.get("/api/alerts?from_date=2026-01-01&to_date=2026-12-31", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert len(res.get_json()["data"]) >= 4

def test_24_pagination(alert_app, client):
    token = get_token_for(alert_app, "admin@example.com")
    res = client.get("/api/alerts?page=1&per_page=2", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert len(res.get_json()["data"]) == 2

def test_25_sorting(alert_app, client):
    token = get_token_for(alert_app, "admin@example.com")
    res = client.get("/api/alerts?sort=severity&order=asc", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200

# ==================== RBAC & STATE TRANSITIONS ====================

def test_26_admin_can_acknowledge(alert_app, client):
    token = get_token_for(alert_app, "admin@example.com")
    res = client.post("/api/alerts/1/acknowledge", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.get_json()["data"]["status"] == "ACKNOWLEDGED"

def test_27_operator_can_acknowledge(alert_app, client):
    token = get_token_for(alert_app, "operator@example.com")
    res = client.post("/api/alerts/3/acknowledge", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.get_json()["data"]["status"] == "ACKNOWLEDGED"

def test_28_viewer_cannot_acknowledge(alert_app, client):
    token = get_token_for(alert_app, "viewer@example.com")
    res = client.post("/api/alerts/1/acknowledge", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403

def test_29_admin_can_resolve(alert_app, client):
    token = get_token_for(alert_app, "admin@example.com")
    res = client.post("/api/alerts/1/resolve", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.get_json()["data"]["status"] == "RESOLVED"

def test_30_operator_can_resolve(alert_app, client):
    token = get_token_for(alert_app, "operator@example.com")
    res = client.post("/api/alerts/3/resolve", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.get_json()["data"]["status"] == "RESOLVED"

def test_31_viewer_cannot_resolve(alert_app, client):
    token = get_token_for(alert_app, "viewer@example.com")
    res = client.post("/api/alerts/1/resolve", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403

def test_32_open_to_acknowledged(alert_app, client):
    token = get_token_for(alert_app, "admin@example.com")
    res = client.post("/api/alerts/4/acknowledge", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200

def test_33_open_to_resolved(alert_app, client):
    token = get_token_for(alert_app, "admin@example.com")
    res = client.post("/api/alerts/4/resolve", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200

def test_34_acknowledged_to_resolved(alert_app, client):
    token = get_token_for(alert_app, "admin@example.com")
    client.post("/api/alerts/4/acknowledge", headers={"Authorization": f"Bearer {token}"})
    res = client.post("/api/alerts/4/resolve", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200

def test_35_resolved_cannot_be_acknowledged(alert_app, client):
    token = get_token_for(alert_app, "admin@example.com")
    client.post("/api/alerts/4/resolve", headers={"Authorization": f"Bearer {token}"})
    res = client.post("/api/alerts/4/acknowledge", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 400
    assert res.get_json()["error"] == "INVALID_STATE_TRANSITION"

def test_36_resolved_cannot_be_resolved_again(alert_app, client):
    token = get_token_for(alert_app, "admin@example.com")
    client.post("/api/alerts/4/resolve", headers={"Authorization": f"Bearer {token}"})
    res = client.post("/api/alerts/4/resolve", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 400

def test_37_invalid_transition_error_format(alert_app, client):
    token = get_token_for(alert_app, "admin@example.com")
    client.post("/api/alerts/4/resolve", headers={"Authorization": f"Bearer {token}"})
    res = client.post("/api/alerts/4/acknowledge", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 400
    assert res.get_json()["success"] is False

# ==================== TIMESTAMPS & HISTORY ====================

def test_38_acknowledge_sets_acknowledged_at(alert_app, client):
    token = get_token_for(alert_app, "admin@example.com")
    res = client.post("/api/alerts/1/acknowledge", headers={"Authorization": f"Bearer {token}"})
    assert res.get_json()["data"]["acknowledged_at"] is not None

def test_39_resolve_sets_resolved_at(alert_app, client):
    token = get_token_for(alert_app, "admin@example.com")
    res = client.post("/api/alerts/1/resolve", headers={"Authorization": f"Bearer {token}"})
    assert res.get_json()["data"]["resolved_at"] is not None

def test_40_server_controls_timestamps(alert_app, client):
    token = get_token_for(alert_app, "admin@example.com")
    before = datetime.utcnow()
    res = client.post("/api/alerts/1/acknowledge", headers={"Authorization": f"Bearer {token}"})
    ack_at_str = res.get_json()["data"]["acknowledged_at"]
    assert ack_at_str is not None

def test_41_resolved_alerts_remain_available(alert_app, client):
    token = get_token_for(alert_app, "admin@example.com")
    client.post("/api/alerts/1/resolve", headers={"Authorization": f"Bearer {token}"})
    res = client.get("/api/alerts?status=RESOLVED", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert len(res.get_json()["data"]) >= 1

def test_42_alerts_remain_after_device_soft_delete(alert_app, client):
    token = get_token_for(alert_app, "admin@example.com")
    # Soft delete device 1
    client.delete("/api/devices/1", headers={"Authorization": f"Bearer {token}"})
    # Alerts linked to device 1 should still be readable
    res = client.get("/api/alerts?device_id=1", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert len(res.get_json()["data"]) >= 1
