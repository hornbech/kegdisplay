import os
os.environ["ADMIN_USERNAME"] = "admin"
os.environ["ADMIN_PASSWORD_HASH"] = ""  # not needed for token generation in tests
os.environ["JWT_SECRET"] = "testsecret"
os.environ["JWT_EXPIRE_HOURS"] = "1"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from main import app
from database import Base, get_db

TEST_DB_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSession = sessionmaker(bind=engine)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def get_token():
    from auth import create_access_token
    return create_access_token({"sub": "admin"})


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200


def test_get_kegs_returns_8_slots():
    r = client.get("/api/kegs")
    assert r.status_code == 200
    assert len(r.json()) == 8


def test_get_keg_by_id():
    # Seed slots first, then look up slot 1 by its actual id from the list
    kegs = client.get("/api/kegs").json()
    slot1 = next(k for k in kegs if k["slot"] == 1)
    r = client.get(f"/api/kegs/{slot1['id']}")
    assert r.status_code == 200
    assert r.json()["slot"] == 1


def test_get_keg_404():
    r = client.get("/api/kegs/999")
    assert r.status_code == 404


def test_update_keg_requires_auth():
    r = client.put("/api/kegs/1", json={"name": "IPA", "style": "IPA",
                                        "abv": 5.0, "color_hex": "#aaaaaa", "status": "on_tap"})
    assert r.status_code == 401


def test_update_keg_with_auth():
    token = get_token()
    kegs = client.get("/api/kegs").json()
    keg_id = next(k["id"] for k in kegs if k["slot"] == 1)
    r = client.put(f"/api/kegs/{keg_id}",
                   headers={"Authorization": f"Bearer {token}"},
                   json={"name": "Summer IPA", "style": "IPA",
                         "abv": 5.5, "color_hex": "#E8A020", "status": "on_tap"})
    assert r.status_code == 200
    assert r.json()["name"] == "Summer IPA"


def test_patch_status_with_auth():
    token = get_token()
    kegs = client.get("/api/kegs").json()
    keg_id = next(k["id"] for k in kegs if k["slot"] == 1)
    r = client.patch(f"/api/kegs/{keg_id}",
                     headers={"Authorization": f"Bearer {token}"},
                     json={"status": "conditioning"})
    assert r.status_code == 200
    assert r.json()["status"] == "conditioning"


def test_delete_clears_keg():
    token = get_token()
    kegs = client.get("/api/kegs").json()
    keg_id = next(k["id"] for k in kegs if k["slot"] == 1)
    # First fill the keg
    client.put(f"/api/kegs/{keg_id}",
               headers={"Authorization": f"Bearer {token}"},
               json={"name": "Summer IPA", "style": "IPA", "abv": 5.5,
                     "color_hex": "#E8A020", "status": "on_tap"})
    # Now clear it
    r = client.delete(f"/api/kegs/{keg_id}",
                      headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "empty"
    assert data["name"] == ""
    assert data["slot"] == 1  # slot is preserved
