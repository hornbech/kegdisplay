import os
# IMPORTANT: env vars must be set before importing auth — auth reads them at module load time
os.environ["ADMIN_USERNAME"] = "testadmin"
os.environ["ADMIN_PASSWORD_HASH"] = "$2b$12$11t/ygkdDgL6ZpMEV87OzerdDAzpO/52GToWXWWMMm2g4YmoctM9W"
os.environ["JWT_SECRET"] = "testsecret"
os.environ["JWT_EXPIRE_HOURS"] = "1"

import pytest
from jose import JWTError
from auth import verify_password, create_access_token, decode_token, authenticate_user, get_current_user


def test_verify_password_correct():
    assert verify_password("testpass123", os.environ["ADMIN_PASSWORD_HASH"]) is True


def test_verify_password_wrong():
    assert verify_password("wrongpass", os.environ["ADMIN_PASSWORD_HASH"]) is False


def test_create_and_decode_token():
    token = create_access_token({"sub": "testadmin"})
    payload = decode_token(token)
    assert payload["sub"] == "testadmin"


def test_authenticate_user_success():
    result = authenticate_user("testadmin", "testpass123")
    assert result is True


def test_authenticate_user_failure():
    result = authenticate_user("testadmin", "wrong")
    assert result is False


def test_get_current_user_valid_token():
    token = create_access_token({"sub": "testadmin"})
    assert get_current_user(token) == "testadmin"


def test_get_current_user_invalid_token():
    with pytest.raises(JWTError):
        get_current_user("not.a.valid.token")
