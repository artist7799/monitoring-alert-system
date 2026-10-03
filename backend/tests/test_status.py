import pytest
from datetime import datetime, timedelta
from flask_jwt_extended import create_access_token
from app import create_app
from database.db import db
from database.seed import seed_database
from models import User, Device, Event, Alert, SystemStatus, DeviceStatus

@pytest.fixture
def status_app():
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
def client(status_app):
    return status_app.test_client()

def get_token_for(app, email):
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        return create_access_token(identity=str(user.id))

# ==================== AUTHENTICATION ====================

def test_1_unauthenticated_device_status_rejected(client):
    res = client.get("/api/status/devices")
    assert res.status_code == 401

def test_2_unauthenticated_overview_rejected(client):
    res = client.get("/api/status/overview")
    assert res.status_code == 401

def test_3_unauthenticated_recent_events_rejected(client):
    res = client.get("/api/status/recent-events")
    assert res.status_code == 401

def test_4_unauthenticated_recent_alerts_rejected(client):
    res = client.get("/api/status/recent-alerts")
    assert res.status_code == 401

# ==================== RBAC ====================

def test_5_admin_can_view_status(status_app, client):
    token = get_token_for(status_app, "admin@example.com")
    res = client.get("/api/status/devices", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200

def test_6_operator_can_view_status(status_app, client):
    token = get_token_for(status_app, "operator@example.com")
    res = client.get("/api/status/devices", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200

def test_7_viewer_can_view_status(status_app, client):
    token = get_token_for(status_app, "viewer@example.com")
    res = client.get("/api/status/devices", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200

# ==================== DEVICE STATUS ====================

def test_8_existing_device_status_returned(status_app, client):
    token = get_token_for(status_app, "viewer@example.com")
    res = client.get("/api/status/devices/1", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["device_id"] == 1
    assert "status" in data

def test_9_unknown_device_404(status_app, client):
    token = get_token_for(status_app, "viewer@example.com")
    res = client.get("/api/status/devices/99999", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 404

def test_10_active_device_appears_in_status_list(status_app, client):
    token = get_token_for(status_app, "admin@example.com")
    res = client.get("/api/status/devices", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert len(res.get_json()["data"]) >= 3

def test_11_soft_deleted_device_excluded_from_status_list(status_app, client):
    token = get_token_for(status_app, "admin@example.com")
    client.delete("/api/devices/3", headers={"Authorization": f"Bearer {token}"})
    res = client.get("/api/status/devices", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    devices = res.get_json()["data"]
    device_ids = [d["device_id"] for d in devices]
    assert 3 not in device_ids

def test_12_device_last_seen_returned(status_app, client):
    token = get_token_for(status_app, "admin@example.com")
    res = client.get("/api/status/devices/1", headers={"Authorization": f"Bearer {token}"})
    assert res.get_json()["data"]["last_seen"] is not None

def test_13_device_with_no_last_seen_handled(status_app, client):
    token = get_token_for(status_app, "admin@example.com")
    create_res = client.post("/api/devices", headers={"Authorization": f"Bearer {token}"}, json={
        "device_code": "DEV_NEW",
        "device_name": "Never Seen Sensor",
        "location": "Zone X",
        "device_type": "Sensor"
    })
    dev_id = create_res.get_json()["data"]["id"]
    res = client.get(f"/api/status/devices/{dev_id}", headers={"Authorization": f"Bearer {token}"})
    assert res.get_json()["data"]["last_seen"] is None

def test_14_latest_cpu_metric_returned(status_app, client):
    token = get_token_for(status_app, "admin@example.com")
    res = client.get("/api/status/devices/2", headers={"Authorization": f"Bearer {token}"})
    assert res.get_json()["data"]["cpu_usage"] == 96.2

def test_15_latest_memory_metric_returned(status_app, client):
    token = get_token_for(status_app, "admin@example.com")
    res = client.get("/api/status/devices/2", headers={"Authorization": f"Bearer {token}"})
    assert res.get_json()["data"]["memory_usage"] == 82.0

def test_16_latest_temperature_returned(status_app, client):
    token = get_token_for(status_app, "admin@example.com")
    res = client.get("/api/status/devices/1", headers={"Authorization": f"Bearer {token}"})
    assert res.get_json()["data"]["temperature"] == 85.5

def test_17_latest_uptime_returned(status_app, client):
    token = get_token_for(status_app, "admin@example.com")
    res = client.get("/api/status/devices/1", headers={"Authorization": f"Bearer {token}"})
    assert "uptime" in res.get_json()["data"]

def test_18_missing_metrics_return_null(status_app, client):
    token = get_token_for(status_app, "admin@example.com")
    create_res = client.post("/api/devices", headers={"Authorization": f"Bearer {token}"}, json={
        "device_code": "DEV_NULL_METRICS",
        "device_name": "No Metrics Sensor",
        "location": "Zone Y",
        "device_type": "Sensor"
    })
    dev_id = create_res.get_json()["data"]["id"]
    res = client.get(f"/api/status/devices/{dev_id}", headers={"Authorization": f"Bearer {token}"})
    data = res.get_json()["data"]
    assert data["cpu_usage"] is None
    assert data["memory_usage"] is None

# ==================== FILTERING & SEARCH ====================

def test_19_filter_online(status_app, client):
    token = get_token_for(status_app, "admin@example.com")
    res = client.get("/api/status/devices?status=ONLINE", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    for d in res.get_json()["data"]:
        assert d["status"] == "ONLINE"

def test_20_filter_offline(status_app, client):
    token = get_token_for(status_app, "admin@example.com")
    res = client.get("/api/status/devices?status=OFFLINE", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    for d in res.get_json()["data"]:
        assert d["status"] == "OFFLINE"

def test_21_filter_warning(status_app, client):
    token = get_token_for(status_app, "admin@example.com")
    res = client.get("/api/status/devices?status=WARNING", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    for d in res.get_json()["data"]:
        assert d["status"] == "WARNING"

def test_22_invalid_status_rejected(status_app, client):
    token = get_token_for(status_app, "admin@example.com")
    res = client.get("/api/status/devices?status=INVALID_STATUS", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 400
    assert res.get_json()["error"] == "INVALID_STATUS"

def test_23_location_filter(status_app, client):
    token = get_token_for(status_app, "admin@example.com")
    res = client.get("/api/status/devices?location=Server%20Room", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert len(res.get_json()["data"]) >= 1

def test_24_search_by_device_code(status_app, client):
    token = get_token_for(status_app, "admin@example.com")
    res = client.get("/api/status/devices?search=DEV001", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.get_json()["data"][0]["device_code"] == "DEV001"

def test_25_search_by_device_name(status_app, client):
    token = get_token_for(status_app, "admin@example.com")
    res = client.get("/api/status/devices?search=Environmental", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert len(res.get_json()["data"]) >= 1

def test_26_search_by_location(status_app, client):
    token = get_token_for(status_app, "admin@example.com")
    res = client.get("/api/status/devices?search=Datacenter", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert len(res.get_json()["data"]) >= 1

# ==================== PAGINATION ====================

def test_27_pagination_works(status_app, client):
    token = get_token_for(status_app, "admin@example.com")
    res = client.get("/api/status/devices?page=1&per_page=2", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert len(res.get_json()["data"]) == 2

def test_28_default_pagination_works(status_app, client):
    token = get_token_for(status_app, "admin@example.com")
    res = client.get("/api/status/devices", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.get_json()["pagination"]["page"] == 1

def test_29_max_per_page_enforced(status_app, client):
    token = get_token_for(status_app, "admin@example.com")
    res = client.get("/api/status/devices?per_page=500", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.get_json()["pagination"]["per_page"] == 100

def test_30_invalid_pagination_handled(status_app, client):
    token = get_token_for(status_app, "admin@example.com")
    res = client.get("/api/status/devices?page=abc&per_page=xyz", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.get_json()["pagination"]["page"] == 1

# ==================== OVERVIEW & SUMMARY ====================

def test_31_total_devices_calculated(status_app, client):
    token = get_token_for(status_app, "admin@example.com")
    res = client.get("/api/status/overview", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.get_json()["data"]["total_devices"] == 3

def test_32_online_count_calculated(status_app, client):
    token = get_token_for(status_app, "admin@example.com")
    res = client.get("/api/status/overview", headers={"Authorization": f"Bearer {token}"})
    assert res.get_json()["data"]["online_devices"] == 1

def test_33_offline_count_calculated(status_app, client):
    token = get_token_for(status_app, "admin@example.com")
    res = client.get("/api/status/overview", headers={"Authorization": f"Bearer {token}"})
    assert res.get_json()["data"]["offline_devices"] == 1

def test_34_warning_count_calculated(status_app, client):
    token = get_token_for(status_app, "admin@example.com")
    res = client.get("/api/status/overview", headers={"Authorization": f"Bearer {token}"})
    assert res.get_json()["data"]["warning_devices"] == 1

def test_35_open_alert_count_calculated(status_app, client):
    token = get_token_for(status_app, "admin@example.com")
    res = client.get("/api/status/overview", headers={"Authorization": f"Bearer {token}"})
    assert res.get_json()["data"]["open_alerts"] == 3  # 3 open alerts in seed

def test_36_critical_alert_count_calculated(status_app, client):
    token = get_token_for(status_app, "admin@example.com")
    res = client.get("/api/status/overview", headers={"Authorization": f"Bearer {token}"})
    assert res.get_json()["data"]["critical_alerts"] == 1  # 1 critical open alert in seed

def test_37_events_today_calculated(status_app, client):
    token = get_token_for(status_app, "admin@example.com")
    res = client.get("/api/status/overview", headers={"Authorization": f"Bearer {token}"})
    assert "events_today" in res.get_json()["data"]

# ==================== RECENT DATA ====================

def test_38_recent_events_returned(status_app, client):
    token = get_token_for(status_app, "admin@example.com")
    res = client.get("/api/status/recent-events", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert len(res.get_json()["data"]) >= 4

def test_39_recent_events_newest_first(status_app, client):
    token = get_token_for(status_app, "admin@example.com")
    res = client.get("/api/status/recent-events?limit=5", headers={"Authorization": f"Bearer {token}"})
    events = res.get_json()["data"]
    if len(events) >= 2:
        assert events[0]["timestamp"] >= events[1]["timestamp"]

def test_40_recent_alerts_returned(status_app, client):
    token = get_token_for(status_app, "admin@example.com")
    res = client.get("/api/status/recent-alerts", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert len(res.get_json()["data"]) >= 4

def test_41_recent_alerts_newest_first(status_app, client):
    token = get_token_for(status_app, "admin@example.com")
    res = client.get("/api/status/recent-alerts?limit=5", headers={"Authorization": f"Bearer {token}"})
    alerts = res.get_json()["data"]
    if len(alerts) >= 2:
        assert alerts[0]["created_at"] >= alerts[1]["created_at"]

def test_42_limit_parameter_works(status_app, client):
    token = get_token_for(status_app, "admin@example.com")
    res = client.get("/api/status/recent-events?limit=2", headers={"Authorization": f"Bearer {token}"})
    assert len(res.get_json()["data"]) == 2

def test_43_maximum_limit_enforced(status_app, client):
    token = get_token_for(status_app, "admin@example.com")
    res = client.get("/api/status/recent-events?limit=500", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200

# ==================== HISTORICAL PRESERVATION ====================

def test_44_soft_deleted_device_historical_events_available(status_app, client):
    token = get_token_for(status_app, "admin@example.com")
    client.delete("/api/devices/1", headers={"Authorization": f"Bearer {token}"})
    res = client.get("/api/status/recent-events?limit=100", headers={"Authorization": f"Bearer {token}"})
    events = res.get_json()["data"]
    dev1_events = [e for e in events if e["device_id"] == 1]
    assert len(dev1_events) >= 1

def test_45_historical_alerts_remain_available(status_app, client):
    token = get_token_for(status_app, "admin@example.com")
    client.delete("/api/devices/1", headers={"Authorization": f"Bearer {token}"})
    res = client.get("/api/status/recent-alerts?limit=100", headers={"Authorization": f"Bearer {token}"})
    alerts = res.get_json()["data"]
    dev1_alerts = [a for a in alerts if a["device_id"] == 1]
    assert len(dev1_alerts) >= 1
