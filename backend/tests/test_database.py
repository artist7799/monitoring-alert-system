import pytest
from app import create_app
from database.db import db
from database.seed import seed_database
from models import User, Device, Event, Alert, SystemStatus

@pytest.fixture
def db_app():
    app = create_app(config_override={
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"
    })
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

def test_database_seeding_and_idempotency(db_app):
    with db_app.app_context():
        # First seed execution
        seed_database()
        assert User.query.count() == 3
        assert Device.query.count() == 3
        assert Event.query.count() == 4
        assert Alert.query.count() == 4
        assert SystemStatus.query.count() == 2

        # Second seed execution (idempotency check)
        seed_database()
        assert User.query.count() == 3
        assert Device.query.count() == 3
        assert Event.query.count() == 4
        assert Alert.query.count() == 4
        assert SystemStatus.query.count() == 2

def test_sqlalchemy_relationship_queries(db_app):
    with db_app.app_context():
        seed_database()
        dev1 = Device.query.filter_by(device_code="DEV001").first()
        assert dev1 is not None
        assert len(dev1.events) == 2
        assert len(dev1.alerts) == 2
        assert len(dev1.system_statuses) == 1

        dev2 = Device.query.filter_by(device_code="DEV002").first()
        assert dev2 is not None
        assert len(dev2.events) == 2
        assert len(dev2.alerts) == 2
        assert len(dev2.system_statuses) == 1
