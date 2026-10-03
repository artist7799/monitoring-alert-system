import pytest
from datetime import timedelta
from flask_jwt_extended import create_access_token
from app import create_app
from database.db import db
from database.seed import seed_database
from models import User, Device, Event, Alert, SystemStatus, DeviceStatus

@pytest.fixture
def device_app():
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
def client(device_app):
    return device_app.test_client()

def get_token_for(app, email):
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        return create_access_token(identity=str(user.id))

# 1. Unauthenticated request rejected
def test_1_unauthenticated_request_rejected(client):
    res = client.get("/api/devices")
    assert res.status_code == 401
    assert res.get_json()["error"] == "TOKEN_MISSING"

# 2. ADMIN can create device
def test_2_admin_can_create_device(device_app, client):
    admin_token = get_token_for(device_app, "admin@example.com")
    res = client.post("/api/devices", headers={"Authorization": f"Bearer {admin_token}"}, json={
        "device_code": "DEV004",
        "device_name": "Forest Sensor 04",
        "location": "Zone A",
        "device_type": "ENVIRONMENT_SENSOR"
    })
    assert res.status_code == 201
    data = res.get_json()
    assert data["success"] is True
    assert data["data"]["device_code"] == "DEV004"
    assert data["data"]["status"] == "OFFLINE"

# 3. OPERATOR cannot create device
def test_3_operator_cannot_create_device(device_app, client):
    token = get_token_for(device_app, "operator@example.com")
    res = client.post("/api/devices", headers={"Authorization": f"Bearer {token}"}, json={
        "device_code": "DEV005",
        "device_name": "Op Device",
        "location": "Zone B",
        "device_type": "Compute"
    })
    assert res.status_code == 403

# 4. VIEWER cannot create device
def test_4_viewer_cannot_create_device(device_app, client):
    token = get_token_for(device_app, "viewer@example.com")
    res = client.post("/api/devices", headers={"Authorization": f"Bearer {token}"}, json={
        "device_code": "DEV006",
        "device_name": "Viewer Device",
        "location": "Zone C",
        "device_type": "Sensor"
    })
    assert res.status_code == 403

# 5. Duplicate device code rejected
def test_5_duplicate_device_code_rejected(device_app, client):
    token = get_token_for(device_app, "admin@example.com")
    res = client.post("/api/devices", headers={"Authorization": f"Bearer {token}"}, json={
        "device_code": "DEV001", # Existing code from seed
        "device_name": "Duplicate Sensor",
        "location": "Lab",
        "device_type": "Sensor"
    })
    assert res.status_code == 409
    assert res.get_json()["error"] == "DEVICE_EXISTS"

# 6. Invalid device data rejected
def test_6_invalid_device_data_rejected(device_app, client):
    token = get_token_for(device_app, "admin@example.com")
    res = client.post("/api/devices", headers={"Authorization": f"Bearer {token}"}, json={
        "device_code": "X", # Too short
        "device_name": ""
    })
    assert res.status_code == 400

# 7. ADMIN can list devices
def test_7_admin_can_list_devices(device_app, client):
    token = get_token_for(device_app, "admin@example.com")
    res = client.get("/api/devices", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert len(res.get_json()["data"]) >= 3

# 8. OPERATOR can list devices
def test_8_operator_can_list_devices(device_app, client):
    token = get_token_for(device_app, "operator@example.com")
    res = client.get("/api/devices", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200

# 9. VIEWER can list devices
def test_9_viewer_can_list_devices(device_app, client):
    token = get_token_for(device_app, "viewer@example.com")
    res = client.get("/api/devices", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200

# 10. Get existing device
def test_10_get_existing_device(device_app, client):
    token = get_token_for(device_app, "viewer@example.com")
    res = client.get("/api/devices/1", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.get_json()["data"]["device_code"] == "DEV001"

# 11. Get non-existing device returns 404
def test_11_get_non_existing_device_404(device_app, client):
    token = get_token_for(device_app, "viewer@example.com")
    res = client.get("/api/devices/99999", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 404
    assert res.get_json()["error"] == "DEVICE_NOT_FOUND"

# 12. Filtering works
def test_12_filtering_devices(device_app, client):
    token = get_token_for(device_app, "admin@example.com")
    res = client.get("/api/devices?status=ONLINE", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    items = res.get_json()["data"]
    for item in items:
        assert item["status"] == "ONLINE"

# 13. Search works
def test_13_search_devices(device_app, client):
    token = get_token_for(device_app, "admin@example.com")
    res = client.get("/api/devices?search=DEV002", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    items = res.get_json()["data"]
    assert len(items) >= 1
    assert items[0]["device_code"] == "DEV002"

# 14. Pagination works
def test_14_pagination_works(device_app, client):
    token = get_token_for(device_app, "admin@example.com")
    res = client.get("/api/devices?page=1&per_page=2", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.get_json()
    assert len(data["data"]) == 2
    assert data["pagination"]["per_page"] == 2
    assert data["pagination"]["total"] == 3

# 15. ADMIN can update device
def test_15_admin_can_update_device(device_app, client):
    token = get_token_for(device_app, "admin@example.com")
    res = client.put("/api/devices/1", headers={"Authorization": f"Bearer {token}"}, json={
        "device_name": "Updated Sensor Name",
        "location": "Updated Room 101",
        "status": "WARNING"
    })
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["device_name"] == "Updated Sensor Name"
    assert data["status"] == "WARNING"

# 16. OPERATOR cannot update device
def test_16_operator_cannot_update_device(device_app, client):
    token = get_token_for(device_app, "operator@example.com")
    res = client.put("/api/devices/1", headers={"Authorization": f"Bearer {token}"}, json={
        "device_name": "Hacked Name"
    })
    assert res.status_code == 403

# 17. VIEWER cannot update device
def test_17_viewer_cannot_update_device(device_app, client):
    token = get_token_for(device_app, "viewer@example.com")
    res = client.put("/api/devices/1", headers={"Authorization": f"Bearer {token}"}, json={
        "device_name": "Hacked Name"
    })
    assert res.status_code == 403

# 18. Invalid status update rejected
def test_18_invalid_status_update_rejected(device_app, client):
    token = get_token_for(device_app, "admin@example.com")
    res = client.put("/api/devices/1", headers={"Authorization": f"Bearer {token}"}, json={
        "status": "INVALID_STATUS"
    })
    assert res.status_code == 400

# 19. ADMIN can delete/deactivate device
def test_19_admin_can_delete_device(device_app, client):
    token = get_token_for(device_app, "admin@example.com")
    res = client.delete("/api/devices/3", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.get_json()["data"]["is_active"] is False

# 20. OPERATOR cannot delete device
def test_20_operator_cannot_delete_device(device_app, client):
    token = get_token_for(device_app, "operator@example.com")
    res = client.delete("/api/devices/1", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403

# 21. VIEWER cannot delete device
def test_21_viewer_cannot_delete_device(device_app, client):
    token = get_token_for(device_app, "viewer@example.com")
    res = client.delete("/api/devices/1", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403

# 22. Historical records preserved after soft delete
def test_22_historical_records_preserved(device_app, client):
    token = get_token_for(device_app, "admin@example.com")
    # Deactivate device 1
    client.delete("/api/devices/1", headers={"Authorization": f"Bearer {token}"})
    
    with device_app.app_context():
        # Verify events and alerts linked to device 1 are still present in database
        events = Event.query.filter_by(device_id=1).all()
        alerts = Alert.query.filter_by(device_id=1).all()
        assert len(events) >= 1
        assert len(alerts) >= 1

# 23. Authorized users can retrieve device status
def test_23_get_device_status(device_app, client):
    token = get_token_for(device_app, "operator@example.com")
    res = client.get("/api/devices/1/status", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["device_id"] == 1
    assert data["temperature"] == 85.5

# 24. Unknown device status returns 404
def test_24_unknown_device_status_404(device_app, client):
    token = get_token_for(device_app, "viewer@example.com")
    res = client.get("/api/devices/99999/status", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 404

# 25. Missing status history handled correctly
def test_25_missing_status_history_handled(device_app, client):
    token = get_token_for(device_app, "admin@example.com")
    # Create device with no SystemStatus entry
    create_res = client.post("/api/devices", headers={"Authorization": f"Bearer {token}"}, json={
        "device_code": "DEV_NO_METRICS",
        "device_name": "New Sensor No Metrics",
        "location": "Zone D",
        "device_type": "Sensor"
    })
    dev_id = create_res.get_json()["data"]["id"]

    res = client.get(f"/api/devices/{dev_id}/status", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["cpu_usage"] is None
    assert data["memory_usage"] is None
    assert data["temperature"] is None
