import pytest
from jose import JWTError
from auth import verify_password, create_access_token, decode_token, authenticate_user, get_current_user

TEST_HASH = "$2b$12$11t/ygkdDgL6ZpMEV87OzerdDAzpO/52GToWXWWMMm2g4YmoctM9W"  # bcrypt of "testpass123"


@pytest.fixture(autouse=True)
def auth_env(monkeypatch):
    """Patch auth env vars per-test so module-level imports don't race."""
    monkeypatch.setenv("ADMIN_USERNAME", "testadmin")
    monkeypatch.setenv("ADMIN_PASSWORD_HASH", TEST_HASH)
    monkeypatch.setenv("JWT_SECRET", "testsecret")
    monkeypatch.setenv("JWT_EXPIRE_HOURS", "1")


def test_verify_password_correct():
    assert verify_password("testpass123", TEST_HASH) is True


def test_verify_password_wrong():
    assert verify_password("wrongpass", TEST_HASH) is False


def test_create_and_decode_token():
    token = create_access_token({"sub": "testadmin"})
    payload = decode_token(token)
    assert payload["sub"] == "testadmin"


def test_authenticate_user_success():
    assert authenticate_user("testadmin", "testpass123") is True


def test_authenticate_user_failure():
    assert authenticate_user("testadmin", "wrong") is False


def test_get_current_user_valid_token():
    token = create_access_token({"sub": "testadmin"})
    assert get_current_user(token) == "testadmin"


def test_get_current_user_invalid_token():
    with pytest.raises(JWTError):
        get_current_user("not.a.valid.token")
