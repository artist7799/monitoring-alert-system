import pytest
from datetime import datetime, timedelta
from flask_jwt_extended import create_access_token
from app import create_app
from database.db import db
from database.seed import seed_database
from models import User, Device, Event, EventType

@pytest.fixture
def event_app():
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
def client(event_app):
    return event_app.test_client()

def get_token_for(app, email):
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        return create_access_token(identity=str(user.id))

# ==================== AUTHENTICATION & RBAC ====================

def test_1_unauthenticated_create_event_rejected(client):
    res = client.post("/api/events", json={
        "device_id": 1,
        "event_type": "TEMPERATURE",
        "metric_name": "temp",
        "metric_value": 75.0,
        "unit": "C"
    })
    assert res.status_code == 401

def test_2_unauthenticated_list_events_rejected(client):
    res = client.get("/api/events")
    assert res.status_code == 401

def test_3_admin_can_create_event(event_app, client):
    token = get_token_for(event_app, "admin@example.com")
    res = client.post("/api/events", headers={"Authorization": f"Bearer {token}"}, json={
        "device_id": 1,
        "event_type": "TEMPERATURE",
        "metric_name": "temperature",
        "metric_value": 78.5,
        "unit": "C",
        "message": "Admin event test"
    })
    assert res.status_code == 201
    assert res.get_json()["data"]["metric_value"] == 78.5

def test_4_operator_can_create_event(event_app, client):
    token = get_token_for(event_app, "operator@example.com")
    res = client.post("/api/events", headers={"Authorization": f"Bearer {token}"}, json={
        "device_id": 1,
        "event_type": "CPU_USAGE",
        "metric_name": "cpu_usage",
        "metric_value": 45.0,
        "unit": "%"
    })
    assert res.status_code == 201

def test_5_viewer_cannot_create_event(event_app, client):
    token = get_token_for(event_app, "viewer@example.com")
    res = client.post("/api/events", headers={"Authorization": f"Bearer {token}"}, json={
        "device_id": 1,
        "event_type": "TEMPERATURE",
        "metric_name": "temperature",
        "metric_value": 80.0,
        "unit": "C"
    })
    assert res.status_code == 403

def test_6_all_authenticated_roles_can_list_events(event_app, client):
    for email in ["admin@example.com", "operator@example.com", "viewer@example.com"]:
        token = get_token_for(event_app, email)
        res = client.get("/api/events", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200

# ==================== VALIDATION ====================

def test_7_missing_device_id(event_app, client):
    token = get_token_for(event_app, "admin@example.com")
    res = client.post("/api/events", headers={"Authorization": f"Bearer {token}"}, json={
        "event_type": "TEMPERATURE",
        "metric_name": "temp",
        "metric_value": 50.0,
        "unit": "C"
    })
    assert res.status_code == 400

def test_8_invalid_device_id_type(event_app, client):
    token = get_token_for(event_app, "admin@example.com")
    res = client.post("/api/events", headers={"Authorization": f"Bearer {token}"}, json={
        "device_id": "not_an_int",
        "event_type": "TEMPERATURE",
        "metric_name": "temp",
        "metric_value": 50.0,
        "unit": "C"
    })
    assert res.status_code == 400

def test_9_missing_event_type(event_app, client):
    token = get_token_for(event_app, "admin@example.com")
    res = client.post("/api/events", headers={"Authorization": f"Bearer {token}"}, json={
        "device_id": 1,
        "metric_name": "temp",
        "metric_value": 50.0,
        "unit": "C"
    })
    assert res.status_code == 400

def test_10_invalid_event_type(event_app, client):
    token = get_token_for(event_app, "admin@example.com")
    res = client.post("/api/events", headers={"Authorization": f"Bearer {token}"}, json={
        "device_id": 1,
        "event_type": "UNKNOWN_EVENT_TYPE",
        "metric_name": "temp",
        "metric_value": 50.0,
        "unit": "C"
    })
    assert res.status_code == 400

def test_11_missing_metric_name(event_app, client):
    token = get_token_for(event_app, "admin@example.com")
    res = client.post("/api/events", headers={"Authorization": f"Bearer {token}"}, json={
        "device_id": 1,
        "event_type": "TEMPERATURE",
        "metric_value": 50.0,
        "unit": "C"
    })
    assert res.status_code == 400

def test_12_invalid_metric_value(event_app, client):
    token = get_token_for(event_app, "admin@example.com")
    res = client.post("/api/events", headers={"Authorization": f"Bearer {token}"}, json={
        "device_id": 1,
        "event_type": "TEMPERATURE",
        "metric_name": "temp",
        "metric_value": "not_a_number",
        "unit": "C"
    })
    assert res.status_code == 400

def test_13_invalid_timestamp(event_app, client):
    token = get_token_for(event_app, "admin@example.com")
    res = client.post("/api/events", headers={"Authorization": f"Bearer {token}"}, json={
        "device_id": 1,
        "event_type": "TEMPERATURE",
        "metric_name": "temp",
        "metric_value": 50.0,
        "unit": "C",
        "timestamp": "invalid-timestamp"
    })
    assert res.status_code == 400

# ==================== DEVICE HANDLING & LAST_SEEN ====================

def test_14_unknown_device_404(event_app, client):
    token = get_token_for(event_app, "admin@example.com")
    res = client.post("/api/events", headers={"Authorization": f"Bearer {token}"}, json={
        "device_id": 99999,
        "event_type": "TEMPERATURE",
        "metric_name": "temp",
        "metric_value": 50.0,
        "unit": "C"
    })
    assert res.status_code == 404
    assert res.get_json()["error"] == "DEVICE_NOT_FOUND"

def test_15_inactive_device_409(event_app, client):
    token = get_token_for(event_app, "admin@example.com")
    # Soft delete device 1 first
    client.delete("/api/devices/1", headers={"Authorization": f"Bearer {token}"})

    res = client.post("/api/events", headers={"Authorization": f"Bearer {token}"}, json={
        "device_id": 1,
        "event_type": "TEMPERATURE",
        "metric_name": "temp",
        "metric_value": 50.0,
        "unit": "C"
    })
    assert res.status_code == 409
    assert res.get_json()["error"] == "DEVICE_INACTIVE"

def test_16_active_device_accepts_event(event_app, client):
    token = get_token_for(event_app, "admin@example.com")
    res = client.post("/api/events", headers={"Authorization": f"Bearer {token}"}, json={
        "device_id": 2,
        "event_type": "CPU_USAGE",
        "metric_name": "cpu",
        "metric_value": 88.0,
        "unit": "%"
    })
    assert res.status_code == 201

def test_17_event_stored_in_database(event_app, client):
    token = get_token_for(event_app, "admin@example.com")
    res = client.post("/api/events", headers={"Authorization": f"Bearer {token}"}, json={
        "device_id": 2,
        "event_type": "MEMORY_USAGE",
        "metric_name": "mem",
        "metric_value": 90.0,
        "unit": "%"
    })
    event_id = res.get_json()["data"]["id"]

    with event_app.app_context():
        ev = db.session.get(Event, event_id)
        assert ev is not None
        assert ev.metric_value == 90.0

def test_18_device_last_seen_updated(event_app, client):
    token = get_token_for(event_app, "admin@example.com")
    custom_ts = "2026-09-29T21:30:00"
    client.post("/api/events", headers={"Authorization": f"Bearer {token}"}, json={
        "device_id": 2,
        "event_type": "NETWORK",
        "metric_name": "throughput",
        "metric_value": 100.0,
        "unit": "Mbps",
        "timestamp": custom_ts
    })

    with event_app.app_context():
        dev = db.session.get(Device, 2)
        assert dev.last_seen is not None


def test_19_correct_response_returned(event_app, client):
    token = get_token_for(event_app, "admin@example.com")
    res = client.post("/api/events", headers={"Authorization": f"Bearer {token}"}, json={
        "device_id": 2,
        "event_type": "HUMIDITY",
        "metric_name": "humidity",
        "metric_value": 65.2,
        "unit": "%"
    })
    assert res.status_code == 201
    data = res.get_json()
    assert data["success"] is True
    assert data["data"]["metric_name"] == "humidity"
    assert "timestamp" in data["data"]

# ==================== READING & FILTERING ====================

def test_20_get_existing_event(event_app, client):
    token = get_token_for(event_app, "viewer@example.com")
    res = client.get("/api/events/1", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.get_json()["data"]["id"] == 1

def test_21_get_unknown_event_404(event_app, client):
    token = get_token_for(event_app, "viewer@example.com")
    res = client.get("/api/events/99999", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 404
    assert res.get_json()["error"] == "EVENT_NOT_FOUND"

def test_22_filter_by_device_id(event_app, client):
    token = get_token_for(event_app, "admin@example.com")
    res = client.get("/api/events?device_id=1", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    events = res.get_json()["data"]
    for ev in events:
        assert ev["device_id"] == 1

def test_23_filter_by_event_type(event_app, client):
    token = get_token_for(event_app, "admin@example.com")
    res = client.get("/api/events?event_type=TEMPERATURE", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    events = res.get_json()["data"]
    for ev in events:
        assert ev["event_type"] == "TEMPERATURE"

def test_24_filter_by_metric_name(event_app, client):
    token = get_token_for(event_app, "admin@example.com")
    res = client.get("/api/events?metric_name=cpu_usage", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    events = res.get_json()["data"]
    for ev in events:
        assert ev["metric_name"] == "cpu_usage"

def test_25_filter_by_date_range(event_app, client):
    token = get_token_for(event_app, "admin@example.com")
    from_date = "2026-01-01"
    to_date = "2026-12-31"
    res = client.get(f"/api/events?from_date={from_date}&to_date={to_date}", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert len(res.get_json()["data"]) >= 4

def test_26_search_events(event_app, client):
    token = get_token_for(event_app, "admin@example.com")
    res = client.get("/api/events?search=Smoke", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    events = res.get_json()["data"]
    assert len(events) >= 1
    assert "Smoke" in events[0]["message"] or events[0]["event_type"] == "SMOKE"

# ==================== PAGINATION & SORTING ====================

def test_27_pagination_works(event_app, client):
    token = get_token_for(event_app, "admin@example.com")
    res = client.get("/api/events?page=1&per_page=2", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.get_json()
    assert len(data["data"]) == 2
    assert data["pagination"]["per_page"] == 2

def test_28_max_per_page_enforced(event_app, client):
    token = get_token_for(event_app, "admin@example.com")
    res = client.get("/api/events?page=1&per_page=500", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.get_json()["pagination"]["per_page"] == 100

def test_29_invalid_pagination_handled(event_app, client):
    token = get_token_for(event_app, "admin@example.com")
    res = client.get("/api/events?page=abc&per_page=xyz", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.get_json()["pagination"]["page"] == 1

def test_30_sort_by_timestamp(event_app, client):
    token = get_token_for(event_app, "admin@example.com")
    res = client.get("/api/events?sort=timestamp&order=desc", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200

def test_31_sort_ascending(event_app, client):
    token = get_token_for(event_app, "admin@example.com")
    res = client.get("/api/events?sort=metric_value&order=asc", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200

def test_32_sort_descending(event_app, client):
    token = get_token_for(event_app, "admin@example.com")
    res = client.get("/api/events?sort=metric_value&order=desc", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200

def test_33_invalid_sort_field_rejected(event_app, client):
    token = get_token_for(event_app, "admin@example.com")
    res = client.get("/api/events?sort=invalid_column", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 400
    assert res.get_json()["error"] == "INVALID_SORT_FIELD"

# ==================== HISTORY ====================

def test_34_historical_events_remain_accessible_after_device_soft_delete(event_app, client):
    token = get_token_for(event_app, "admin@example.com")
    # Soft delete device 1
    client.delete("/api/devices/1", headers={"Authorization": f"Bearer {token}"})

    # Historical events for device 1 should still be listed in GET /api/events
    res = client.get("/api/events?device_id=1", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    events = res.get_json()["data"]
    assert len(events) >= 2
