import os
os.environ.setdefault("ADMIN_USERNAME", "admin")
os.environ.setdefault("ADMIN_PASSWORD_HASH", "")
os.environ.setdefault("JWT_SECRET", "testsecret")
os.environ.setdefault("JWT_EXPIRE_HOURS", "1")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from main import app
from database import Base, get_db

TEST_DB_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSession = sessionmaker(bind=engine)

def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(autouse=True)
def setup_db():
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)
    app.dependency_overrides.pop(get_db, None)

client = TestClient(app)

def get_token():
    from auth import create_access_token
    return create_access_token({"sub": "admin"})

def first_keg_id():
    return client.get("/api/kegs").json()[0]["id"]


def test_list_reviews_empty():
    keg_id = first_keg_id()
    r = client.get(f"/api/kegs/{keg_id}/reviews")
    assert r.status_code == 200
    assert r.json() == []


def test_post_review_minimal():
    keg_id = first_keg_id()
    r = client.post(f"/api/kegs/{keg_id}/reviews", json={"name": "Alice", "stars": 5})
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Alice"
    assert data["stars"] == 5
    assert data["comment"] is None
    assert data["keg_id"] == keg_id


def test_post_review_with_comment():
    keg_id = first_keg_id()
    r = client.post(f"/api/kegs/{keg_id}/reviews",
                    json={"name": "Bob", "stars": 4, "comment": "Lovely malt!"})
    assert r.status_code == 201
    assert r.json()["comment"] == "Lovely malt!"


def test_post_review_name_is_stripped():
    keg_id = first_keg_id()
    r = client.post(f"/api/kegs/{keg_id}/reviews", json={"name": "  Alice  ", "stars": 3})
    assert r.status_code == 201
    assert r.json()["name"] == "Alice"


def test_post_review_stars_out_of_range():
    keg_id = first_keg_id()
    r = client.post(f"/api/kegs/{keg_id}/reviews", json={"name": "Alice", "stars": 6})
    assert r.status_code == 422

    r = client.post(f"/api/kegs/{keg_id}/reviews", json={"name": "Alice", "stars": 0})
    assert r.status_code == 422


def test_post_review_empty_name():
    keg_id = first_keg_id()
    r = client.post(f"/api/kegs/{keg_id}/reviews", json={"name": "   ", "stars": 3})
    assert r.status_code == 422


def test_post_review_comment_too_long():
    keg_id = first_keg_id()
    r = client.post(f"/api/kegs/{keg_id}/reviews",
                    json={"name": "Alice", "stars": 3, "comment": "x" * 501})
    assert r.status_code == 422


def test_list_reviews_newest_first():
    keg_id = first_keg_id()
    client.post(f"/api/kegs/{keg_id}/reviews", json={"name": "Alice", "stars": 5})
    client.post(f"/api/kegs/{keg_id}/reviews", json={"name": "Bob", "stars": 2})
    reviews = client.get(f"/api/kegs/{keg_id}/reviews").json()
    assert len(reviews) == 2
    assert reviews[0]["name"] == "Bob"  # newest first


def test_delete_review_requires_auth():
    keg_id = first_keg_id()
    review_id = client.post(f"/api/kegs/{keg_id}/reviews",
                            json={"name": "Alice", "stars": 3}).json()["id"]
    r = client.delete(f"/api/reviews/{review_id}")
    assert r.status_code == 401


def test_delete_review_with_auth():
    token = get_token()
    keg_id = first_keg_id()
    review_id = client.post(f"/api/kegs/{keg_id}/reviews",
                            json={"name": "Alice", "stars": 3}).json()["id"]
    r = client.delete(f"/api/reviews/{review_id}",
                      headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 204
    assert client.get(f"/api/kegs/{keg_id}/reviews").json() == []


def test_delete_review_404():
    token = get_token()
    r = client.delete("/api/reviews/99999",
                      headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 404


def test_review_on_unknown_keg():
    r = client.post("/api/kegs/99999/reviews", json={"name": "Alice", "stars": 3})
    assert r.status_code == 404


def test_list_reviews_unknown_keg():
    r = client.get("/api/kegs/99999/reviews")
    assert r.status_code == 404
