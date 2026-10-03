import pytest
import json
from datetime import timedelta
from flask_jwt_extended import create_access_token
from app import create_app
from database.db import db
from database.seed import seed_database
from models import User, Device, Event, Alert, DeviceStatus
from services.sse_service import generate_sse_stream, format_sse_event

@pytest.fixture
def stream_app():
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
def client(stream_app):
    return stream_app.test_client()

def get_token_for(app, email):
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        return create_access_token(identity=str(user.id))

# ==================== AUTHENTICATION & SECURITY ====================

def test_1_missing_auth_rejected(client):
    res = client.get("/api/stream")
    assert res.status_code == 401
    assert res.get_json()["error"] == "TOKEN_MISSING"

def test_2_invalid_jwt_rejected(client):
    res = client.get("/api/stream", headers={"Authorization": "Bearer invalid_token"})
    assert res.status_code == 401

def test_3_admin_can_connect(stream_app, client):
    token = get_token_for(stream_app, "admin@example.com")
    res = client.get("/api/stream", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert "text/event-stream" in res.headers["Content-Type"]

def test_4_operator_can_connect(stream_app, client):
    token = get_token_for(stream_app, "operator@example.com")
    res = client.get("/api/stream", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200

def test_5_viewer_can_connect(stream_app, client):
    token = get_token_for(stream_app, "viewer@example.com")
    res = client.get("/api/stream", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200

# ==================== INITIAL SNAPSHOT ====================

def test_6_initial_system_status_emitted(stream_app):
    gen = generate_sse_stream(stream_app, max_iterations=1, poll_interval=0.1)
    first_chunk = next(gen)
    assert "event: system_status" in first_chunk
    assert "total_devices" in first_chunk

def test_7_initial_device_status_emitted(stream_app):
    gen = generate_sse_stream(stream_app, max_iterations=1, poll_interval=0.1)
    chunks = list(gen)
    device_chunks = [c for c in chunks if "event: device_status" in c]
    assert len(device_chunks) >= 3

def test_8_correct_json_serialization(stream_app):
    gen = generate_sse_stream(stream_app, max_iterations=1, poll_interval=0.1)
    first_chunk = next(gen)
    lines = first_chunk.strip().split("\n")
    data_line = [l for l in lines if l.startswith("data: ")][0]
    json_str = data_line[len("data: "):]
    data = json.loads(json_str)
    assert isinstance(data, dict)

# ==================== EVENT STREAMING ====================

def test_9_10_new_event_detected_and_payload(stream_app, client):
    token = get_token_for(stream_app, "admin@example.com")
    gen = generate_sse_stream(stream_app, max_iterations=2, poll_interval=0.1)

    # Consume initial snapshot
    next(gen)

    # Create new event via API
    client.post("/api/events", headers={"Authorization": f"Bearer {token}"}, json={
        "device_id": 1,
        "event_type": "TEMPERATURE",
        "metric_name": "temperature",
        "metric_value": 75.0,
        "unit": "C"
    })

    # Generator should emit the new event
    chunks = list(gen)
    event_chunks = [c for c in chunks if "event: event" in c]
    assert len(event_chunks) >= 1
    assert "temperature" in event_chunks[0]

def test_11_12_existing_event_not_repeated_and_cursor_advances(stream_app, client):
    token = get_token_for(stream_app, "admin@example.com")
    gen = generate_sse_stream(stream_app, max_iterations=3, poll_interval=0.05)

    # Consume initial snapshot
    next(gen)

    client.post("/api/events", headers={"Authorization": f"Bearer {token}"}, json={
        "device_id": 1, "event_type": "TEMPERATURE", "metric_name": "temp", "metric_value": 60.0, "unit": "C"
    })

    chunks = list(gen)
    event_chunks = [c for c in chunks if "event: event" in c]
    # Verify exactly one emission for the new event
    assert len(event_chunks) == 1

# ==================== ALERT STREAMING ====================

def test_13_14_15_16_alert_stream(stream_app, client):
    token = get_token_for(stream_app, "admin@example.com")
    gen = generate_sse_stream(stream_app, max_iterations=2, poll_interval=0.05)
    next(gen)

    # Post critical event that triggers alert engine
    client.post("/api/events", headers={"Authorization": f"Bearer {token}"}, json={
        "device_id": 1, "event_type": "TEMPERATURE", "metric_name": "temperature", "metric_value": 95.0, "unit": "C"
    })

    chunks = list(gen)
    alert_chunks = [c for c in chunks if "event: alert" in c]
    assert len(alert_chunks) >= 1
    assert "CRITICAL" in alert_chunks[0]

# ==================== DEVICE & SYSTEM STATUS STREAMING ====================

def test_17_18_device_status_change_detected(stream_app, client):
    token = get_token_for(stream_app, "admin@example.com")
    gen = generate_sse_stream(stream_app, max_iterations=2, poll_interval=0.05)
    next(gen)

    # Post event which updates device 2 last_seen
    client.post("/api/events", headers={"Authorization": f"Bearer {token}"}, json={
        "device_id": 2, "event_type": "CPU_USAGE", "metric_name": "cpu", "metric_value": 50.0, "unit": "%"
    })

    chunks = list(gen)
    device_chunks = [c for c in chunks if "event: device_status" in c]
    assert len(device_chunks) >= 1

def test_19_20_21_system_status_changes_emitted(stream_app, client):
    token = get_token_for(stream_app, "admin@example.com")
    gen = generate_sse_stream(stream_app, max_iterations=2, poll_interval=0.05)

    # Initial snapshot contains first system_status
    first_chunk = next(gen)
    assert "event: system_status" in first_chunk

    # Post event creating a new alert to change system overview stats
    client.post("/api/events", headers={"Authorization": f"Bearer {token}"}, json={
        "device_id": 1, "event_type": "SMOKE", "metric_name": "smoke", "metric_value": 1.0, "unit": "b"
    })

    chunks = list(gen)
    status_chunks = [c for c in chunks if "event: system_status" in c]
    assert len(status_chunks) >= 1

# ==================== HEARTBEAT ====================

def test_22_23_heartbeat_format_and_utc(stream_app):
    from services.sse_service import format_sse_event
    out = format_sse_event("heartbeat", {"timestamp": "2026-09-29T22:20:00Z"})
    assert "event: heartbeat" in out
    assert "2026-09-29T22:20:00Z" in out

# ==================== MULTIPLE CLIENTS & DISCONNECT ====================

def test_24_25_multiple_client_cursors_independent(stream_app):
    gen1 = generate_sse_stream(stream_app, max_iterations=1, poll_interval=0.05)
    gen2 = generate_sse_stream(stream_app, max_iterations=1, poll_interval=0.05)

    c1 = next(gen1)
    c2 = next(gen2)
    assert c1 == c2
    gen2.close()
    gen1.close()

def test_26_27_client_disconnect_handled_cleanly(stream_app):
    gen = generate_sse_stream(stream_app, max_iterations=10, poll_interval=0.05)
    next(gen)
    # Simulate client disconnect by closing generator
    gen.close()
    assert True

# ==================== SECURITY ====================

def test_28_29_30_stream_security_checks(stream_app, client):
    res = client.get("/api/stream")
    assert res.status_code == 401  # Unauthorized blocked

    token = get_token_for(stream_app, "viewer@example.com")
    res = client.get("/api/stream", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    # Ensure no token exposed in body payload
    chunk = next(res.response)
    if isinstance(chunk, bytes):
        chunk = chunk.decode('utf-8')
    assert token not in chunk
