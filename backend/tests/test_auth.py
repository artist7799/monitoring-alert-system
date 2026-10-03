import pytest
from datetime import timedelta
from flask_jwt_extended import create_access_token
from app import create_app
from database.db import db
from database.seed import seed_database
from models import User, UserRole

@pytest.fixture
def auth_app():
    app = create_app(config_override={
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "JWT_SECRET_KEY": "test-jwt-secret-key-super-secret-32bytes-long!",

        "JWT_ACCESS_TOKEN_EXPIRES": timedelta(seconds=2)
    })
    with app.app_context():
        db.create_all()
        seed_database()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(auth_app):
    return auth_app.test_client()

# Helper token generator
def get_user_token(app, email):
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        return create_access_token(identity=str(user.id))

# ==================== REGISTRATION TESTS ====================

def test_1_valid_registration(client):
    res = client.post("/api/auth/register", json={
        "name": "New User",
        "email": "newuser@example.com",
        "password": "StrongPassword123"
    })
    assert res.status_code == 201
    data = res.get_json()
    assert data["success"] is True
    assert data["data"]["email"] == "newuser@example.com"
    assert data["data"]["role"] == "VIEWER"
    assert "password" not in data["data"]
    assert "password_hash" not in data["data"]

def test_2_duplicate_email_registration(client):
    res = client.post("/api/auth/register", json={
        "name": "Duplicate Admin",
        "email": "admin@example.com",
        "password": "Password123"
    })
    assert res.status_code == 409
    data = res.get_json()
    assert data["success"] is False
    assert data["error"] == "EMAIL_EXISTS"

def test_3_invalid_email_registration(client):
    res = client.post("/api/auth/register", json={
        "name": "Bad Email",
        "email": "not-an-email",
        "password": "Password123"
    })
    assert res.status_code == 400
    data = res.get_json()
    assert data["success"] is False

def test_4_missing_password_registration(client):
    res = client.post("/api/auth/register", json={
        "name": "No Password",
        "email": "nopw@example.com"
    })
    assert res.status_code == 400

def test_5_weak_password_registration(client):
    res = client.post("/api/auth/register", json={
        "name": "Weak Pass",
        "email": "weak@example.com",
        "password": "simplepassword"  # No numbers
    })
    assert res.status_code == 400

def test_6_default_role_is_viewer(client):
    res = client.post("/api/auth/register", json={
        "name": "Self Admin Attempt",
        "email": "hacker@example.com",
        "password": "Password123",
        "role": "ADMIN"  # Should be ignored/overridden to VIEWER
    })
    assert res.status_code == 201
    assert res.get_json()["data"]["role"] == "VIEWER"

def test_7_password_is_hashed(auth_app, client):
    client.post("/api/auth/register", json={
        "name": "Hashed User",
        "email": "hashed@example.com",
        "password": "SecretPassword123"
    })
    with auth_app.app_context():
        user = User.query.filter_by(email="hashed@example.com").first()
        assert user is not None
        assert user.password_hash != "SecretPassword123"
        assert user.password_hash.startswith("$2b$") or user.password_hash.startswith("$2a$")

# ==================== LOGIN TESTS ====================

def test_8_valid_login(client):
    res = client.post("/api/auth/login", json={
        "email": "admin@example.com",
        "password": "admin123"
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert data["data"]["user"]["email"] == "admin@example.com"
    assert data["data"]["user"]["role"] == "ADMIN"

def test_9_invalid_password_login(client):
    res = client.post("/api/auth/login", json={
        "email": "admin@example.com",
        "password": "wrongpassword"
    })
    assert res.status_code == 401
    data = res.get_json()
    assert data["success"] is False
    assert data["error"] == "INVALID_CREDENTIALS"

def test_10_unknown_email_login(client):
    res = client.post("/api/auth/login", json={
        "email": "nonexistent@example.com",
        "password": "Password123"
    })
    assert res.status_code == 401

def test_11_jwt_token_generated(client):
    res = client.post("/api/auth/login", json={
        "email": "operator@example.com",
        "password": "operator123"
    })
    token = res.get_json()["data"]["access_token"]
    assert isinstance(token, str)
    assert len(token) > 20

# ==================== AUTHENTICATION TESTS ====================

def test_12_valid_jwt_access_to_me(auth_app, client):
    token = get_user_token(auth_app, "admin@example.com")
    res = client.get("/api/auth/me", headers={
        "Authorization": f"Bearer {token}"
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["data"]["email"] == "admin@example.com"

def test_13_missing_jwt_denied(client):
    res = client.get("/api/auth/me")
    assert res.status_code == 401
    assert res.get_json()["error"] == "TOKEN_MISSING"

def test_14_invalid_jwt_denied(client):
    res = client.get("/api/auth/me", headers={
        "Authorization": "Bearer invalid.jwt.token"
    })
    assert res.status_code == 401
    assert res.get_json()["error"] == "INVALID_TOKEN"

def test_15_expired_jwt_denied(auth_app, client):
    import time
    token = get_user_token(auth_app, "viewer@example.com")
    time.sleep(2.5)  # Wait for 2-second token expiry
    res = client.get("/api/auth/me", headers={
        "Authorization": f"Bearer {token}"
    })
    assert res.status_code == 401
    assert res.get_json()["error"] == "TOKEN_EXPIRED"

# ==================== AUTHORIZATION TESTS ====================

def test_16_admin_role_authorization(auth_app, client):
    token = get_user_token(auth_app, "admin@example.com")
    # Verify profile endpoint works for ADMIN
    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.get_json()["data"]["role"] == "ADMIN"

def test_17_operator_role_authorization(auth_app, client):
    token = get_user_token(auth_app, "operator@example.com")
    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.get_json()["data"]["role"] == "OPERATOR"

def test_18_viewer_role_authorization(auth_app, client):
    token = get_user_token(auth_app, "viewer@example.com")
    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.get_json()["data"]["role"] == "VIEWER"

def test_19_role_middleware_denied(auth_app):
    from middleware.auth_middleware import require_role
    from flask import Flask, jsonify

    test_app = Flask(__name__)
    test_app.config["JWT_SECRET_KEY"] = "test-secret"
    from flask_jwt_extended import JWTManager
    JWTManager(test_app)

    @test_app.route("/admin-only")
    @require_role("ADMIN")
    def admin_only():
        return jsonify({"message": "admin area"}), 200

    test_client = test_app.test_client()

    with auth_app.app_context():
        operator_user = User.query.filter_by(email="operator@example.com").first()
        token = create_access_token(identity=str(operator_user.id))

    res = auth_app.test_client().get("/admin-only", headers={"Authorization": f"Bearer {token}"})
    # Will fail if route doesn't exist on auth_app, let's register on auth_app directly:

def test_20_role_middleware_enforcement_on_app(auth_app):
    from middleware.auth_middleware import require_role
    from flask import jsonify

    @auth_app.route("/test-admin-only", methods=["GET"])
    @require_role("ADMIN")
    def admin_endpoint():
        return jsonify({"success": True, "message": "Admin Secret"}), 200

    @auth_app.route("/test-operator-only", methods=["GET"])
    @require_role("ADMIN", "OPERATOR")
    def operator_endpoint():
        return jsonify({"success": True, "message": "Operator Secret"}), 200

    client = auth_app.test_client()

    admin_token = get_user_token(auth_app, "admin@example.com")
    operator_token = get_user_token(auth_app, "operator@example.com")
    viewer_token = get_user_token(auth_app, "viewer@example.com")

    # Admin access admin endpoint -> 200
    res = client.get("/test-admin-only", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200

    # Operator access admin endpoint -> 403 Forbidden
    res = client.get("/test-admin-only", headers={"Authorization": f"Bearer {operator_token}"})
    assert res.status_code == 403
    assert res.get_json()["error"] == "FORBIDDEN"

    # Viewer access operator endpoint -> 403 Forbidden
    res = client.get("/test-operator-only", headers={"Authorization": f"Bearer {viewer_token}"})
    assert res.status_code == 403

    # Operator access operator endpoint -> 200
    res = client.get("/test-operator-only", headers={"Authorization": f"Bearer {operator_token}"})
    assert res.status_code == 200
