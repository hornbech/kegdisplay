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


def test_delete_clears_ibu_ebc_recipe():
    token = get_token()
    kegs = client.get("/api/kegs").json()
    keg_id = next(k["id"] for k in kegs if k["slot"] == 2)
    client.put(f"/api/kegs/{keg_id}",
               headers={"Authorization": f"Bearer {token}"},
               json={"name": "Hoppy IPA", "style": "IPA", "abv": 6.0,
                     "color_hex": "#E8A020", "status": "on_tap",
                     "ibu": 60, "ebc": 12})
    r = client.delete(f"/api/kegs/{keg_id}",
                      headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert data["ibu"] is None
    assert data["ebc"] is None
    assert data["recipe_filename"] is None


def test_login_valid_credentials(monkeypatch):
    from auth import pwd_context
    pw_hash = pwd_context.hash("secretpass")
    monkeypatch.setenv("ADMIN_PASSWORD_HASH", pw_hash)
    r = client.post("/api/auth/login", json={"username": "admin", "password": "secretpass"})
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_login_invalid_credentials(monkeypatch):
    from auth import pwd_context
    pw_hash = pwd_context.hash("secretpass")
    monkeypatch.setenv("ADMIN_PASSWORD_HASH", pw_hash)
    r = client.post("/api/auth/login", json={"username": "admin", "password": "wrongpass"})
    assert r.status_code == 401


def test_record_visit():
    r = client.post("/api/stats/visit")
    assert r.status_code == 200
    data = r.json()
    assert data["visits"] >= 1


def test_heartbeat():
    r = client.post("/api/stats/heartbeat", json={"client_id": "test-client-abc"})
    assert r.status_code == 200
    data = r.json()
    assert data["online"] >= 1


def test_get_stats():
    r = client.get("/api/stats")
    assert r.status_code == 200
    data = r.json()
    assert "visits" in data
    assert "online" in data


def test_recipe_upload_and_delete(tmp_path, monkeypatch):
    import routers.kegs as kegs_router
    monkeypatch.setattr(kegs_router, "RECIPES_DIR", str(tmp_path))
    token = get_token()
    kegs = client.get("/api/kegs").json()
    keg_id = next(k["id"] for k in kegs if k["slot"] == 3)

    pdf_bytes = b"%PDF-1.4 fake content"
    r = client.post(
        f"/api/kegs/{keg_id}/recipe",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("recipe.pdf", pdf_bytes, "application/pdf")},
    )
    assert r.status_code == 200
    assert r.json()["recipe_filename"] == "recipe.pdf"

    r = client.delete(f"/api/kegs/{keg_id}/recipe",
                      headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["recipe_filename"] is None


def test_recipe_upload_requires_auth(tmp_path, monkeypatch):
    import routers.kegs as kegs_router
    monkeypatch.setattr(kegs_router, "RECIPES_DIR", str(tmp_path))
    kegs = client.get("/api/kegs").json()
    keg_id = kegs[0]["id"]
    r = client.post(
        f"/api/kegs/{keg_id}/recipe",
        files={"file": ("recipe.pdf", b"%PDF-1.4", "application/pdf")},
    )
    assert r.status_code == 401
