import os
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import jwt, JWTError

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"


def _secret_key() -> str:
    return os.getenv("JWT_SECRET", "changeme")


def _expire_hours() -> int:
    return int(os.getenv("JWT_EXPIRE_HOURS", "24"))


def _admin_username() -> str:
    return os.getenv("ADMIN_USERNAME", "admin")


def _admin_password_hash() -> str:
    return os.getenv("ADMIN_PASSWORD_HASH", "")


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    to_encode["exp"] = datetime.now(timezone.utc) + timedelta(hours=_expire_hours())
    return jwt.encode(to_encode, _secret_key(), algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, _secret_key(), algorithms=[ALGORITHM])


def authenticate_user(username: str, password: str) -> bool:
    if username != _admin_username():
        return False
    pw_hash = _admin_password_hash()
    if not pw_hash:
        return False
    return verify_password(password, pw_hash)


def get_current_user(token: str) -> str:
    """Raises JWTError if token is invalid. Returns username."""
    payload = decode_token(token)
    username = payload.get("sub")
    if not username:
        raise JWTError("No subject in token")
    return username
