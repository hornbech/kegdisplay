# Kegdisplay Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use godmode:task-runner to implement this plan task-by-task.

**Goal:** Build a self-hosted homebrewing keg display app with a FastAPI backend, SvelteKit frontend, SQLite storage, JWT auth, and Docker Compose deployment.

**Architecture:** Two Docker services — a FastAPI API (port 8000, SQLite on a named volume) and a pre-built SvelteKit app served by nginx (port 3000). Single admin user via env vars. Public display view, protected admin view.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy, python-jose, passlib[bcrypt], pytest, httpx; SvelteKit, Vite, Vitest; Docker Compose; nginx.

---

## Task 1: Project scaffold

**Files:**
- Create: `docker-compose.yml`
- Create: `.env.example`
- Create: `api/` (directory)
- Create: `frontend/` (directory)

**Step 1: Create docker-compose.yml**

```yaml
# docker-compose.yml
services:
  api:
    build: ./api
    ports:
      - "8000:8000"
    volumes:
      - keg_data:/data
    env_file: .env
    restart: unless-stopped

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - api
    restart: unless-stopped

volumes:
  keg_data:
```

**Step 2: Create .env.example**

```bash
# .env.example
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=
JWT_SECRET=changeme_use_a_long_random_string
JWT_EXPIRE_HOURS=24
```

**Step 3: Create directories**

```bash
mkdir -p api/routers api/tests frontend/src/routes/login frontend/src/routes/admin frontend/src/lib
```

**Step 4: Commit**

```bash
git add docker-compose.yml .env.example
git commit -m "feat: add project scaffold and docker-compose"
```

---

## Task 2: API — database and models

**Files:**
- Create: `api/database.py`
- Create: `api/models.py`
- Create: `api/tests/__init__.py`
- Create: `api/tests/test_models.py`

**Step 1: Write the failing test**

```python
# api/tests/test_models.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Keg

@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_keg_table_exists(db):
    keg = Keg(slot=1, name="Test IPA", style="IPA", abv=6.5,
              brew_date="2026-03-01", volume_liters=19.0,
              color_hex="#C8860A", status="on_tap")
    db.add(keg)
    db.commit()
    assert db.query(Keg).count() == 1

def test_keg_defaults(db):
    keg = Keg(slot=1, name="Test", style="IPA", abv=5.0,
              brew_date="2026-01-01", color_hex="#aaa", status="empty")
    db.add(keg)
    db.commit()
    assert keg.volume_liters == 19.0
    assert keg.tap_date is None
    assert keg.notes is None
    assert keg.untappd_url is None
```

**Step 2: Run test — expect failure**

```bash
cd api && python -m pytest tests/test_models.py -v
```
Expected: `ModuleNotFoundError: No module named 'models'`

**Step 3: Implement database.py**

```python
# api/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
import os

DATABASE_URL = f"sqlite:///{os.getenv('DATABASE_PATH', '/data/kegs.db')}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Step 4: Implement models.py**

```python
# api/models.py
from sqlalchemy import Column, Integer, Float, Text, DateTime, func
from datetime import datetime
from database import Base

class Keg(Base):
    __tablename__ = "kegs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    slot = Column(Integer, nullable=False, unique=True)
    name = Column(Text, nullable=False, default="")
    style = Column(Text, nullable=False, default="")
    abv = Column(Float, nullable=False, default=0.0)
    brew_date = Column(Text, nullable=True)
    tap_date = Column(Text, nullable=True)
    volume_liters = Column(Float, nullable=False, default=19.0)
    color_hex = Column(Text, nullable=False, default="#C8860A")
    notes = Column(Text, nullable=True)
    untappd_url = Column(Text, nullable=True)
    status = Column(Text, nullable=False, default="empty")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**Step 5: Run test — expect pass**

```bash
cd api && python -m pytest tests/test_models.py -v
```
Expected: `2 passed`

**Step 6: Commit**

```bash
git add api/database.py api/models.py api/tests/
git commit -m "feat: add database config and Keg model"
```

---

## Task 3: API — Pydantic schemas

**Files:**
- Create: `api/schemas.py`
- Create: `api/tests/test_schemas.py`

**Step 1: Write the failing test**

```python
# api/tests/test_schemas.py
import pytest
from schemas import KegOut, KegCreate, KegUpdate, KegStatusUpdate

def test_keg_create_requires_slot():
    with pytest.raises(Exception):
        KegCreate(name="IPA", style="IPA", abv=5.0,
                  brew_date="2026-01-01", color_hex="#aaa", status="on_tap")

def test_keg_out_has_id():
    keg = KegOut(id=1, slot=1, name="IPA", style="IPA", abv=5.0,
                 brew_date="2026-01-01", volume_liters=19.0,
                 color_hex="#aaa", status="on_tap",
                 created_at="2026-01-01T00:00:00",
                 updated_at="2026-01-01T00:00:00")
    assert keg.id == 1

def test_keg_status_update_valid_values():
    u = KegStatusUpdate(status="on_tap")
    assert u.status == "on_tap"

def test_keg_status_update_rejects_invalid():
    with pytest.raises(Exception):
        KegStatusUpdate(status="drinking")
```

**Step 2: Run test — expect failure**

```bash
cd api && python -m pytest tests/test_schemas.py -v
```
Expected: `ModuleNotFoundError: No module named 'schemas'`

**Step 3: Implement schemas.py**

```python
# api/schemas.py
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime, date

StatusEnum = Literal["empty", "conditioning", "on_tap", "archived"]

class KegBase(BaseModel):
    slot: int = Field(..., ge=1, le=8)
    name: str = ""
    style: str = ""
    abv: float = Field(0.0, ge=0.0, le=100.0)
    brew_date: Optional[str] = None
    tap_date: Optional[str] = None
    volume_liters: float = Field(19.0, gt=0)
    color_hex: str = "#C8860A"
    notes: Optional[str] = None
    untappd_url: Optional[str] = None
    status: StatusEnum = "empty"

class KegCreate(KegBase):
    pass

class KegUpdate(KegBase):
    pass

class KegStatusUpdate(BaseModel):
    status: StatusEnum

class KegOut(KegBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

class LoginIn(BaseModel):
    username: str
    password: str
```

**Step 4: Run test — expect pass**

```bash
cd api && python -m pytest tests/test_schemas.py -v
```
Expected: `4 passed`

**Step 5: Commit**

```bash
git add api/schemas.py api/tests/test_schemas.py
git commit -m "feat: add Pydantic schemas for keg API"
```

---

## Task 4: API — auth module

**Files:**
- Create: `api/auth.py`
- Create: `api/hash_password.py`
- Create: `api/tests/test_auth.py`

**Step 1: Write the failing test**

```python
# api/tests/test_auth.py
import os
os.environ["ADMIN_USERNAME"] = "testadmin"
os.environ["ADMIN_PASSWORD_HASH"] = "$2b$12$KIXsT5VNx2.gJULBp1VcuuyRvpQ6ELq/8XpE/s5r7Oq5BrO9SxCOa"
os.environ["JWT_SECRET"] = "testsecret"
os.environ["JWT_EXPIRE_HOURS"] = "1"

import pytest
from auth import verify_password, create_access_token, decode_token, authenticate_user

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
```

Note: generate the hash for "testpass123" by running:
```bash
python -c "from passlib.context import CryptContext; print(CryptContext(schemes=['bcrypt']).hash('testpass123'))"
```
Replace the hash in the test with the output.

**Step 2: Run test — expect failure**

```bash
cd api && python -m pytest tests/test_auth.py -v
```
Expected: `ModuleNotFoundError: No module named 'auth'`

**Step 3: Implement auth.py**

```python
# api/auth.py
import os
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import jwt, JWTError

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.getenv("JWT_SECRET", "changeme")
ALGORITHM = "HS256"
EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "24"))
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH", "")

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    to_encode["exp"] = datetime.utcnow() + timedelta(hours=EXPIRE_HOURS)
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

def authenticate_user(username: str, password: str) -> bool:
    if username != ADMIN_USERNAME:
        return False
    return verify_password(password, ADMIN_PASSWORD_HASH)

def get_current_user(token: str) -> str:
    """Raises JWTError if token is invalid. Returns username."""
    payload = decode_token(token)
    username = payload.get("sub")
    if not username:
        raise JWTError("No subject in token")
    return username
```

**Step 4: Implement hash_password.py**

```python
# api/hash_password.py
#!/usr/bin/env python3
"""Run this to generate your ADMIN_PASSWORD_HASH for .env"""
import sys
from passlib.context import CryptContext

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python hash_password.py <your_password>")
        sys.exit(1)
    ctx = CryptContext(schemes=["bcrypt"])
    print(ctx.hash(sys.argv[1]))
```

**Step 5: Run test — expect pass**

```bash
cd api && python -m pytest tests/test_auth.py -v
```
Expected: `5 passed`

**Step 6: Commit**

```bash
git add api/auth.py api/hash_password.py api/tests/test_auth.py
git commit -m "feat: add JWT auth and password hashing"
```

---

## Task 5: API — kegs router

**Files:**
- Create: `api/routers/kegs.py`
- Create: `api/routers/auth.py`
- Create: `api/routers/__init__.py`
- Create: `api/tests/test_kegs_api.py`

**Step 1: Write the failing test**

```python
# api/tests/test_kegs_api.py
import os
os.environ["ADMIN_USERNAME"] = "admin"
os.environ["ADMIN_PASSWORD_HASH"] = ""  # fill after hash_password.py
os.environ["JWT_SECRET"] = "testsecret"
os.environ["JWT_EXPIRE_HOURS"] = "1"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app
from database import Base, get_db

TEST_DB_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
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

def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200

def test_get_kegs_returns_8_slots():
    r = client.get("/api/kegs")
    assert r.status_code == 200
    assert len(r.json()) == 8

def test_get_keg_by_id():
    r = client.get("/api/kegs/1")
    assert r.status_code == 200
    assert r.json()["slot"] == 1

def test_get_keg_404():
    r = client.get("/api/kegs/999")
    assert r.status_code == 404

def get_token():
    from auth import create_access_token
    return create_access_token({"sub": "admin"})

def test_update_keg_requires_auth():
    r = client.put("/api/kegs/1", json={"slot": 1, "name": "IPA", "style": "IPA",
                                         "abv": 5.0, "color_hex": "#aaa", "status": "on_tap"})
    assert r.status_code == 401

def test_update_keg_with_auth():
    token = get_token()
    r = client.put("/api/kegs/1",
                   headers={"Authorization": f"Bearer {token}"},
                   json={"slot": 1, "name": "Summer IPA", "style": "IPA",
                         "abv": 5.5, "color_hex": "#E8A020", "status": "on_tap"})
    assert r.status_code == 200
    assert r.json()["name"] == "Summer IPA"

def test_patch_status_with_auth():
    token = get_token()
    r = client.patch("/api/kegs/1",
                     headers={"Authorization": f"Bearer {token}"},
                     json={"status": "conditioning"})
    assert r.status_code == 200
    assert r.json()["status"] == "conditioning"
```

**Step 2: Run test — expect failure (no main.py yet)**

```bash
cd api && python -m pytest tests/test_kegs_api.py -v
```
Expected: `ModuleNotFoundError: No module named 'main'`

**Step 3: Implement routers/auth.py**

```python
# api/routers/auth.py
from fastapi import APIRouter, HTTPException
from schemas import LoginIn, TokenOut
from auth import authenticate_user, create_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/login", response_model=TokenOut)
def login(body: LoginIn):
    if not authenticate_user(body.username, body.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": body.username})
    return TokenOut(access_token=token)
```

**Step 4: Implement routers/kegs.py**

```python
# api/routers/kegs.py
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import Keg
from schemas import KegOut, KegCreate, KegUpdate, KegStatusUpdate
from auth import get_current_user
from jose import JWTError

router = APIRouter(prefix="/api/kegs", tags=["kegs"])

def _require_auth(authorization: Optional[str] = Header(None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        return get_current_user(authorization.split(" ", 1)[1])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def _ensure_8_slots(db: Session):
    """Seed all 8 slots if they don't exist yet."""
    existing = {k.slot for k in db.query(Keg).all()}
    for slot in range(1, 9):
        if slot not in existing:
            db.add(Keg(slot=slot, name="", style="", abv=0.0,
                       color_hex="#555555", status="empty"))
    db.commit()

@router.get("", response_model=List[KegOut])
def list_kegs(db: Session = Depends(get_db)):
    _ensure_8_slots(db)
    return db.query(Keg).order_by(Keg.slot).all()

@router.get("/{keg_id}", response_model=KegOut)
def get_keg(keg_id: int, db: Session = Depends(get_db)):
    _ensure_8_slots(db)
    keg = db.query(Keg).filter(Keg.id == keg_id).first()
    if not keg:
        raise HTTPException(status_code=404, detail="Keg not found")
    return keg

@router.put("/{keg_id}", response_model=KegOut)
def update_keg(keg_id: int, body: KegUpdate, db: Session = Depends(get_db),
               user: str = Depends(_require_auth)):
    _ensure_8_slots(db)
    keg = db.query(Keg).filter(Keg.id == keg_id).first()
    if not keg:
        raise HTTPException(status_code=404, detail="Keg not found")
    for field, value in body.model_dump().items():
        setattr(keg, field, value)
    db.commit()
    db.refresh(keg)
    return keg

@router.patch("/{keg_id}", response_model=KegOut)
def update_keg_status(keg_id: int, body: KegStatusUpdate,
                      db: Session = Depends(get_db),
                      user: str = Depends(_require_auth)):
    keg = db.query(Keg).filter(Keg.id == keg_id).first()
    if not keg:
        raise HTTPException(status_code=404, detail="Keg not found")
    keg.status = body.status
    db.commit()
    db.refresh(keg)
    return keg

@router.delete("/{keg_id}", response_model=KegOut)
def clear_keg(keg_id: int, db: Session = Depends(get_db),
              user: str = Depends(_require_auth)):
    keg = db.query(Keg).filter(Keg.id == keg_id).first()
    if not keg:
        raise HTTPException(status_code=404, detail="Keg not found")
    slot = keg.slot
    for field in ["name", "style", "notes", "untappd_url", "brew_date", "tap_date"]:
        setattr(keg, field, None if field not in ["name", "style"] else "")
    keg.abv = 0.0
    keg.color_hex = "#555555"
    keg.status = "empty"
    keg.volume_liters = 19.0
    db.commit()
    db.refresh(keg)
    return keg
```

**Step 5: Implement main.py**

```python
# api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from routers import kegs, auth as auth_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Kegdisplay API", docs_url="/api/docs", openapi_url="/api/openapi.json")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(kegs.router)
app.include_router(auth_router.router)

@app.get("/api/health")
def health():
    return {"status": "ok"}
```

**Step 6: Run tests — expect pass**

```bash
cd api && python -m pytest tests/test_kegs_api.py -v
```
Expected: `7 passed`

**Step 7: Commit**

```bash
git add api/routers/ api/main.py
git commit -m "feat: add kegs CRUD and auth routers"
```

---

## Task 6: API — requirements.txt and Dockerfile

**Files:**
- Create: `api/requirements.txt`
- Create: `api/Dockerfile`

**Step 1: Create requirements.txt**

```txt
# api/requirements.txt
fastapi==0.115.0
uvicorn[standard]==0.30.6
sqlalchemy==2.0.35
pydantic==2.9.2
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
httpx==0.27.2
pytest==8.3.3
```

**Step 2: Create Dockerfile**

```dockerfile
# api/Dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Step 3: Verify the API builds**

```bash
docker build -t kegdisplay-api ./api
```
Expected: `Successfully built ...`

**Step 4: Commit**

```bash
git add api/requirements.txt api/Dockerfile
git commit -m "feat: add API Dockerfile and requirements"
```

---

## Task 7: Frontend — scaffold SvelteKit project

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/svelte.config.js`
- Create: `frontend/vite.config.js`
- Create: `frontend/src/app.html`
- Create: `frontend/src/app.css`

**Step 1: Create package.json**

```json
{
  "name": "kegdisplay-frontend",
  "version": "1.0.0",
  "scripts": {
    "dev": "vite dev",
    "build": "vite build",
    "preview": "vite preview",
    "test": "vitest run"
  },
  "devDependencies": {
    "@sveltejs/adapter-static": "^3.0.5",
    "@sveltejs/kit": "^2.5.0",
    "@sveltejs/vite-plugin-svelte": "^3.1.0",
    "svelte": "^4.2.18",
    "vite": "^5.3.4",
    "vitest": "^2.0.5"
  }
}
```

**Step 2: Create svelte.config.js**

```js
// frontend/svelte.config.js
import adapter from '@sveltejs/adapter-static';

export default {
  kit: {
    adapter: adapter({ fallback: 'index.html' }),
    paths: { base: '' }
  }
};
```

**Step 3: Create vite.config.js**

```js
// frontend/vite.config.js
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [sveltekit()],
  server: {
    proxy: {
      '/api': { target: 'http://api:8000', changeOrigin: true }
    }
  }
});
```

**Step 4: Create src/app.html**

```html
<!-- frontend/src/app.html -->
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <link rel="icon" href="%sveltekit.assets%/favicon.png" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@400;500&display=swap" rel="stylesheet" />
    %sveltekit.head%
  </head>
  <body>%sveltekit.body%</body>
</html>
```

**Step 5: Create src/app.css**

```css
/* frontend/src/app.css */
:root {
  --bg: #1a1a1a;
  --card: #2a2a2a;
  --accent: #C8860A;
  --accent-light: #E8A020;
  --text: #e8e0d0;
  --text-muted: #888;
  --success: #4a9e5c;
  --warning: #C8860A;
  --empty: #444;
  --radius: 12px;
  --font-heading: 'Playfair Display', serif;
  --font-body: 'Inter', sans-serif;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  background: var(--bg);
  color: var(--text);
  font-family: var(--font-body);
  min-height: 100vh;
}

h1, h2, h3 { font-family: var(--font-heading); }
```

**Step 6: Install dependencies and verify**

```bash
cd frontend && npm install
```
Expected: `added N packages`

**Step 7: Commit**

```bash
git add frontend/
git commit -m "feat: scaffold SvelteKit frontend"
```

---

## Task 8: Frontend — API client library

**Files:**
- Create: `frontend/src/lib/api.js`
- Create: `frontend/src/lib/api.test.js`

**Step 1: Write the failing test**

```js
// frontend/src/lib/api.test.js
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { getToken, setToken, clearToken, isLoggedIn } from './api.js';

beforeEach(() => {
  localStorage.clear();
});

describe('token helpers', () => {
  it('returns null when no token set', () => {
    expect(getToken()).toBeNull();
  });

  it('stores and retrieves token', () => {
    setToken('abc123');
    expect(getToken()).toBe('abc123');
  });

  it('clears token', () => {
    setToken('abc123');
    clearToken();
    expect(getToken()).toBeNull();
  });

  it('isLoggedIn true when token exists', () => {
    setToken('abc');
    expect(isLoggedIn()).toBe(true);
  });

  it('isLoggedIn false when no token', () => {
    expect(isLoggedIn()).toBe(false);
  });
});
```

**Step 2: Run test — expect failure**

```bash
cd frontend && npm test
```
Expected: `Cannot find module './api.js'`

**Step 3: Implement api.js**

```js
// frontend/src/lib/api.js
const BASE = '/api';

export const getToken = () => localStorage.getItem('keg_token');
export const setToken = (t) => localStorage.setItem('keg_token', t);
export const clearToken = () => localStorage.removeItem('keg_token');
export const isLoggedIn = () => !!getToken();

async function request(path, options = {}) {
  const token = getToken();
  const headers = { 'Content-Type': 'application/json', ...options.headers };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(`${BASE}${path}`, { ...options, headers });
  if (!res.ok) throw { status: res.status, detail: await res.json() };
  return res.json();
}

export const fetchKegs = () => request('/kegs');
export const fetchKeg = (id) => request(`/kegs/${id}`);
export const updateKeg = (id, data) => request(`/kegs/${id}`, { method: 'PUT', body: JSON.stringify(data) });
export const patchKegStatus = (id, status) => request(`/kegs/${id}`, { method: 'PATCH', body: JSON.stringify({ status }) });
export const clearKeg = (id) => request(`/kegs/${id}`, { method: 'DELETE' });
export const login = (username, password) =>
  request('/auth/login', { method: 'POST', body: JSON.stringify({ username, password }) });
```

**Step 4: Run test — expect pass**

```bash
cd frontend && npm test
```
Expected: `5 passed`

**Step 5: Commit**

```bash
git add frontend/src/lib/
git commit -m "feat: add API client library with token helpers"
```

---

## Task 9: Frontend — KegSvg component (SVG corny keg)

**Files:**
- Create: `frontend/src/lib/KegSvg.svelte`

**Step 1: Implement KegSvg.svelte**

The SVG depicts a simplified corny keg (cylinder with dome top, handles, pressure posts). The liquid fill is animated via a `<clipPath>` driven by the `fillPercent` prop (0–100). Empty kegs use a ghost/grey style.

```svelte
<!-- frontend/src/lib/KegSvg.svelte -->
<script>
  export let color = '#C8860A';
  export let status = 'empty';   // empty | conditioning | on_tap | archived

  // Fill level by status
  const fillMap = { empty: 0, conditioning: 85, on_tap: 70, archived: 20 };
  $: fillPercent = fillMap[status] ?? 0;
  $: isActive = status !== 'empty' && status !== 'archived';
  $: fillColor = isActive ? color : '#444';
  $: opacity = status === 'archived' ? 0.45 : 1;

  // SVG dimensions
  const W = 80, H = 140;
  const bodyY = 20, bodyH = 100, bodyW = 60, bodyX = 10;
  const fillH = (bodyH * fillPercent) / 100;
  const fillY = bodyY + bodyH - fillH;
</script>

<svg width={W} height={H} viewBox="0 0 {W} {H}" style="opacity:{opacity}">
  <defs>
    <clipPath id="keg-clip-{status}-{color.replace('#','')}">
      <rect x={bodyX} y={fillY} width={bodyW} height={fillH} />
    </clipPath>
  </defs>

  <!-- Keg body outline -->
  <rect x={bodyX} y={bodyY} width={bodyW} height={bodyH} rx="8"
        fill="#333" stroke="#555" stroke-width="2"/>

  <!-- Liquid fill -->
  {#if fillPercent > 0}
    <rect x={bodyX} y={bodyY} width={bodyW} height={bodyH} rx="8"
          fill={fillColor}
          clip-path="url(#keg-clip-{status}-{color.replace('#','')})"
          style="transition: all 0.6s ease"/>
    <!-- Shine -->
    <rect x={bodyX + 8} y={fillY + 4} width="6" height={fillH - 8} rx="3"
          fill="rgba(255,255,255,0.15)"
          clip-path="url(#keg-clip-{status}-{color.replace('#','')})"/>
  {/if}

  <!-- Dome top -->
  <ellipse cx={W/2} cy={bodyY} rx={bodyW/2} ry="10"
           fill="#3a3a3a" stroke="#555" stroke-width="2"/>

  <!-- Pressure post (top) -->
  <rect x={W/2 - 5} y="4" width="10" height="14" rx="3"
        fill="#666" stroke="#888" stroke-width="1"/>

  <!-- Handles (left & right) -->
  <path d="M{bodyX - 8},{bodyY + 20} Q{bodyX - 16},{bodyY + 35} {bodyX - 8},{bodyY + 50}"
        fill="none" stroke="#555" stroke-width="4" stroke-linecap="round"/>
  <path d="M{bodyX + bodyW + 8},{bodyY + 20} Q{bodyX + bodyW + 16},{bodyY + 35} {bodyX + bodyW + 8},{bodyY + 50}"
        fill="none" stroke="#555" stroke-width="4" stroke-linecap="round"/>

  <!-- Bottom ring -->
  <ellipse cx={W/2} cy={bodyY + bodyH} rx={bodyW/2} ry="8"
           fill="#3a3a3a" stroke="#555" stroke-width="2"/>

  <!-- Liquid surface ripple (only when filled) -->
  {#if fillPercent > 5}
    <ellipse cx={W/2} cy={fillY} rx={bodyW/2 - 2} ry="4"
             fill={fillColor} opacity="0.6"/>
  {/if}
</svg>
```

**Step 2: Verify it renders**
Open `npm run dev` and create a temporary test page that renders `<KegSvg status="on_tap" color="#E8A020" />` — visually verify the keg appears with amber fill, handles, and dome.

**Step 3: Commit**

```bash
git add frontend/src/lib/KegSvg.svelte
git commit -m "feat: add SVG corny keg component with animated fill"
```

---

## Task 10: Frontend — KegCard component

**Files:**
- Create: `frontend/src/lib/KegCard.svelte`

**Step 1: Implement KegCard.svelte**

```svelte
<!-- frontend/src/lib/KegCard.svelte -->
<script>
  import KegSvg from './KegSvg.svelte';
  export let keg;

  const statusLabel = { empty: 'Empty', conditioning: 'Conditioning', on_tap: 'On Tap', archived: 'Archived' };
  const statusColor = { empty: '#555', conditioning: '#C8860A', on_tap: '#4a9e5c', archived: '#666' };

  function formatDate(d) {
    if (!d) return null;
    return new Date(d).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
  }
</script>

<div class="card" class:empty={keg.status === 'empty'} class:archived={keg.status === 'archived'}>
  <div class="slot-badge">#{keg.slot}</div>

  <div class="keg-visual">
    <KegSvg color={keg.color_hex} status={keg.status} />
  </div>

  {#if keg.status === 'empty'}
    <p class="empty-label">Empty</p>
  {:else}
    <div class="info">
      <h3 class="beer-name">{keg.name}</h3>
      <p class="beer-style">{keg.style}</p>
      <div class="badges">
        <span class="badge abv">{keg.abv.toFixed(1)}% ABV</span>
        <span class="badge status" style="background:{statusColor[keg.status]}">
          {statusLabel[keg.status]}
        </span>
      </div>
      {#if keg.brew_date}
        <p class="date">Brewed {formatDate(keg.brew_date)}</p>
      {/if}
      {#if keg.tap_date}
        <p class="date">Tapped {formatDate(keg.tap_date)}</p>
      {/if}
      {#if keg.notes}
        <p class="notes">{keg.notes}</p>
      {/if}
      {#if keg.untappd_url}
        <a href={keg.untappd_url} target="_blank" rel="noopener" class="untappd-link">
          🍺 Untappd
        </a>
      {/if}
    </div>
  {/if}
</div>

<style>
  .card {
    background: var(--card);
    border-radius: var(--radius);
    padding: 1rem;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
    border: 1px solid #333;
    transition: transform 0.2s, box-shadow 0.2s;
    position: relative;
    min-height: 280px;
  }
  .card:hover { transform: translateY(-3px); box-shadow: 0 8px 24px rgba(0,0,0,0.4); }
  .card.empty { opacity: 0.5; border-style: dashed; }
  .card.archived { opacity: 0.6; }

  .slot-badge {
    position: absolute; top: 8px; left: 8px;
    background: #333; color: var(--text-muted);
    font-size: 0.7rem; padding: 2px 6px; border-radius: 4px;
  }

  .keg-visual { margin: 0.5rem 0; }

  .empty-label { color: var(--text-muted); font-size: 0.9rem; }

  .info { width: 100%; text-align: center; }
  .beer-name { font-family: var(--font-heading); font-size: 1.1rem; color: var(--accent-light); }
  .beer-style { font-size: 0.8rem; color: var(--text-muted); margin-bottom: 0.5rem; }

  .badges { display: flex; gap: 0.4rem; justify-content: center; flex-wrap: wrap; margin-bottom: 0.4rem; }
  .badge { font-size: 0.7rem; padding: 2px 8px; border-radius: 10px; font-weight: 500; }
  .badge.abv { background: #333; color: var(--accent-light); }
  .badge.status { color: #fff; }

  .date { font-size: 0.75rem; color: var(--text-muted); }
  .notes { font-size: 0.75rem; color: var(--text-muted); font-style: italic;
           max-height: 2.5em; overflow: hidden; text-overflow: ellipsis; margin-top: 0.25rem; }

  .untappd-link {
    display: inline-block; margin-top: 0.4rem;
    font-size: 0.75rem; color: var(--accent);
    text-decoration: none; border-bottom: 1px dotted var(--accent);
  }
</style>
```

**Step 2: Commit**

```bash
git add frontend/src/lib/KegCard.svelte
git commit -m "feat: add KegCard component with beer details and Untappd link"
```

---

## Task 11: Frontend — Display view (home page)

**Files:**
- Create: `frontend/src/routes/+page.svelte`

**Step 1: Implement +page.svelte**

```svelte
<!-- frontend/src/routes/+page.svelte -->
<script>
  import { onMount } from 'svelte';
  import KegCard from '$lib/KegCard.svelte';
  import { fetchKegs } from '$lib/api.js';

  let kegs = [];
  let error = null;
  let loading = true;

  onMount(async () => {
    try {
      kegs = await fetchKegs();
    } catch (e) {
      error = 'Could not load kegs. Is the API running?';
    } finally {
      loading = false;
    }
  });
</script>

<svelte:head><title>Jacob's Brewery</title></svelte:head>

<main>
  <header>
    <div class="header-inner">
      <div class="logo">🍺</div>
      <div>
        <h1>Jacob's Brewery</h1>
        <p class="tagline">What's on tap</p>
      </div>
      <a href="/admin" class="admin-link">Admin</a>
    </div>
    <div class="wood-strip"></div>
  </header>

  {#if loading}
    <div class="state-msg">Loading kegs…</div>
  {:else if error}
    <div class="state-msg error">{error}</div>
  {:else}
    <div class="grid">
      {#each kegs as keg (keg.id)}
        <KegCard {keg} />
      {/each}
    </div>
  {/if}
</main>

<style>
  @import '../app.css';

  main { min-height: 100vh; background: var(--bg); }

  header { background: #111; border-bottom: 3px solid var(--accent); }
  .header-inner {
    max-width: 1200px; margin: 0 auto; padding: 1.2rem 2rem;
    display: flex; align-items: center; gap: 1rem;
  }
  .logo { font-size: 2.5rem; }
  h1 { font-family: var(--font-heading); font-size: 2rem; color: var(--accent-light); }
  .tagline { color: var(--text-muted); font-size: 0.85rem; letter-spacing: 0.1em; text-transform: uppercase; }
  .admin-link {
    margin-left: auto; color: var(--text-muted); font-size: 0.8rem;
    text-decoration: none; border: 1px solid #444; padding: 4px 12px; border-radius: 6px;
  }
  .admin-link:hover { color: var(--accent); border-color: var(--accent); }

  .wood-strip {
    height: 8px;
    background: repeating-linear-gradient(90deg, #5c3d1e 0px, #7a5230 40px, #5c3d1e 80px);
    opacity: 0.6;
  }

  .grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1.5rem;
    max-width: 1200px;
    margin: 2rem auto;
    padding: 0 2rem;
  }

  @media (max-width: 900px) { .grid { grid-template-columns: repeat(2, 1fr); } }
  @media (max-width: 500px) { .grid { grid-template-columns: 1fr; } }

  .state-msg { text-align: center; padding: 4rem; color: var(--text-muted); }
  .state-msg.error { color: #e06060; }
</style>
```

**Step 2: Commit**

```bash
git add frontend/src/routes/+page.svelte
git commit -m "feat: add public display view with 4x2 keg grid"
```

---

## Task 12: Frontend — Login page

**Files:**
- Create: `frontend/src/routes/login/+page.svelte`

**Step 1: Implement login page**

```svelte
<!-- frontend/src/routes/login/+page.svelte -->
<script>
  import { login, setToken } from '$lib/api.js';
  import { goto } from '$app/navigation';

  let username = '', password = '', error = null, loading = false;

  async function handleLogin() {
    error = null;
    loading = true;
    try {
      const data = await login(username, password);
      setToken(data.access_token);
      goto('/admin');
    } catch (e) {
      error = 'Invalid username or password.';
    } finally {
      loading = false;
    }
  }
</script>

<svelte:head><title>Login — Jacob's Brewery</title></svelte:head>

<div class="page">
  <div class="card">
    <div class="logo">🍺</div>
    <h1>Admin Login</h1>
    <form on:submit|preventDefault={handleLogin}>
      <label>
        Username
        <input type="text" bind:value={username} required autocomplete="username" />
      </label>
      <label>
        Password
        <input type="password" bind:value={password} required autocomplete="current-password" />
      </label>
      {#if error}<p class="error">{error}</p>{/if}
      <button type="submit" disabled={loading}>
        {loading ? 'Logging in…' : 'Login'}
      </button>
    </form>
    <a href="/" class="back">← Back to display</a>
  </div>
</div>

<style>
  @import '../../app.css';
  .page { min-height: 100vh; display: flex; align-items: center; justify-content: center; background: var(--bg); }
  .card { background: var(--card); padding: 2.5rem; border-radius: var(--radius); width: 100%; max-width: 380px; text-align: center; border: 1px solid #333; }
  .logo { font-size: 3rem; margin-bottom: 0.5rem; }
  h1 { font-family: var(--font-heading); color: var(--accent-light); margin-bottom: 1.5rem; }
  form { display: flex; flex-direction: column; gap: 1rem; text-align: left; }
  label { display: flex; flex-direction: column; gap: 0.3rem; font-size: 0.85rem; color: var(--text-muted); }
  input { background: #1a1a1a; border: 1px solid #444; color: var(--text); padding: 0.6rem 0.8rem; border-radius: 6px; font-size: 1rem; }
  input:focus { outline: none; border-color: var(--accent); }
  button { background: var(--accent); color: #fff; border: none; padding: 0.75rem; border-radius: 6px; font-size: 1rem; cursor: pointer; margin-top: 0.5rem; }
  button:hover:not(:disabled) { background: var(--accent-light); }
  button:disabled { opacity: 0.6; cursor: default; }
  .error { color: #e06060; font-size: 0.85rem; }
  .back { display: block; margin-top: 1.5rem; color: var(--text-muted); font-size: 0.8rem; text-decoration: none; }
  .back:hover { color: var(--accent); }
</style>
```

**Step 2: Commit**

```bash
git add frontend/src/routes/login/
git commit -m "feat: add login page with JWT auth"
```

---

## Task 13: Frontend — Admin layout (auth guard) + admin view

**Files:**
- Create: `frontend/src/routes/admin/+layout.svelte`
- Create: `frontend/src/routes/admin/+page.svelte`

**Step 1: Implement admin layout (auth guard)**

```svelte
<!-- frontend/src/routes/admin/+layout.svelte -->
<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { isLoggedIn, clearToken } from '$lib/api.js';

  onMount(() => {
    if (!isLoggedIn()) goto('/login');
  });

  function logout() {
    clearToken();
    goto('/login');
  }
</script>

<nav>
  <a href="/">🍺 Display</a>
  <span>Admin</span>
  <button on:click={logout}>Logout</button>
</nav>

<slot />

<style>
  @import '../../app.css';
  nav { background: #111; border-bottom: 2px solid var(--accent); padding: 0.8rem 2rem; display: flex; align-items: center; gap: 1.5rem; }
  nav a { color: var(--text-muted); text-decoration: none; font-size: 0.9rem; }
  nav a:hover { color: var(--accent); }
  nav span { color: var(--accent-light); font-weight: 500; }
  nav button { margin-left: auto; background: transparent; border: 1px solid #444; color: var(--text-muted); padding: 4px 12px; border-radius: 6px; cursor: pointer; font-size: 0.8rem; }
  nav button:hover { border-color: var(--accent); color: var(--accent); }
</style>
```

**Step 2: Implement admin page**

```svelte
<!-- frontend/src/routes/admin/+page.svelte -->
<script>
  import { onMount } from 'svelte';
  import KegSvg from '$lib/KegSvg.svelte';
  import { fetchKegs, updateKeg, clearKeg } from '$lib/api.js';

  let kegs = [];
  let editing = null;   // keg object being edited
  let saving = false;
  let error = null;
  let successMsg = null;

  onMount(async () => {
    kegs = await fetchKegs();
  });

  function startEdit(keg) {
    editing = { ...keg };
  }

  function cancelEdit() {
    editing = null;
    error = null;
  }

  async function saveEdit() {
    saving = true; error = null; successMsg = null;
    try {
      const updated = await updateKeg(editing.id, editing);
      kegs = kegs.map(k => k.id === updated.id ? updated : k);
      editing = null;
      successMsg = 'Keg updated!';
      setTimeout(() => successMsg = null, 3000);
    } catch (e) {
      error = 'Save failed. Check all fields.';
    } finally {
      saving = false;
    }
  }

  async function handleClear(keg) {
    if (!confirm(`Clear slot ${keg.slot} (${keg.name || 'empty'})?`)) return;
    const updated = await clearKeg(keg.id);
    kegs = kegs.map(k => k.id === updated.id ? updated : k);
  }

  const statusOptions = ['empty', 'conditioning', 'on_tap', 'archived'];
</script>

<svelte:head><title>Admin — Jacob's Brewery</title></svelte:head>

<main>
  <div class="container">
    <h1>Keg Management</h1>
    {#if successMsg}<p class="success">{successMsg}</p>{/if}

    <div class="keg-list">
      {#each kegs as keg (keg.id)}
        <div class="keg-row">
          <div class="keg-preview">
            <KegSvg color={keg.color_hex} status={keg.status} />
            <span class="slot">Slot #{keg.slot}</span>
          </div>
          <div class="keg-summary">
            <strong>{keg.name || '—'}</strong>
            <span>{keg.style || '—'}</span>
            <span class="status-badge {keg.status}">{keg.status}</span>
          </div>
          <div class="keg-actions">
            <button on:click={() => startEdit(keg)}>Edit</button>
            <button class="danger" on:click={() => handleClear(keg)}>Clear</button>
          </div>
        </div>
      {/each}
    </div>
  </div>

  <!-- Edit modal -->
  {#if editing}
    <div class="modal-backdrop" on:click|self={cancelEdit}>
      <div class="modal">
        <h2>Edit Slot #{editing.slot}</h2>
        {#if error}<p class="error">{error}</p>{/if}

        <form on:submit|preventDefault={saveEdit}>
          <div class="form-grid">
            <label>Beer Name <input bind:value={editing.name} /></label>
            <label>Style <input bind:value={editing.style} /></label>
            <label>ABV (%) <input type="number" step="0.1" min="0" max="100" bind:value={editing.abv} /></label>
            <label>Volume (L) <input type="number" step="0.1" min="0" bind:value={editing.volume_liters} /></label>
            <label>Brew Date <input type="date" bind:value={editing.brew_date} /></label>
            <label>Tap Date <input type="date" bind:value={editing.tap_date} /></label>
            <label>
              Beer Colour
              <div class="color-row">
                <input type="color" bind:value={editing.color_hex} />
                <input type="text" bind:value={editing.color_hex} placeholder="#C8860A" style="width:100px" />
              </div>
            </label>
            <label>
              Status
              <select bind:value={editing.status}>
                {#each statusOptions as s}<option value={s}>{s}</option>{/each}
              </select>
            </label>
            <label class="full">Untappd URL (optional)
              <input type="url" bind:value={editing.untappd_url} placeholder="https://untappd.com/b/..." />
            </label>
            <label class="full">Notes
              <textarea rows="3" bind:value={editing.notes}></textarea>
            </label>
          </div>

          <div class="modal-actions">
            <button type="button" on:click={cancelEdit}>Cancel</button>
            <button type="submit" class="primary" disabled={saving}>
              {saving ? 'Saving…' : 'Save'}
            </button>
          </div>
        </form>
      </div>
    </div>
  {/if}
</main>

<style>
  @import '../../app.css';
  main { background: var(--bg); min-height: 100vh; padding-bottom: 4rem; }
  .container { max-width: 900px; margin: 0 auto; padding: 2rem; }
  h1 { font-family: var(--font-heading); color: var(--accent-light); margin-bottom: 1.5rem; }

  .keg-list { display: flex; flex-direction: column; gap: 0.75rem; }
  .keg-row { background: var(--card); border-radius: var(--radius); padding: 1rem 1.5rem; display: flex; align-items: center; gap: 1.5rem; border: 1px solid #333; }
  .keg-preview { display: flex; flex-direction: column; align-items: center; gap: 0.25rem; min-width: 60px; }
  .slot { font-size: 0.7rem; color: var(--text-muted); }
  .keg-summary { flex: 1; display: flex; flex-direction: column; gap: 0.2rem; }
  .keg-summary strong { color: var(--text); }
  .keg-summary span { font-size: 0.8rem; color: var(--text-muted); }
  .status-badge { font-size: 0.7rem; padding: 2px 8px; border-radius: 10px; width: fit-content; }
  .status-badge.on_tap { background: #4a9e5c22; color: #4a9e5c; }
  .status-badge.conditioning { background: #C8860A22; color: #C8860A; }
  .status-badge.empty { background: #44444422; color: #666; }
  .status-badge.archived { background: #33333322; color: #555; }
  .keg-actions { display: flex; gap: 0.5rem; }

  button { background: #333; color: var(--text); border: 1px solid #444; padding: 6px 14px; border-radius: 6px; cursor: pointer; font-size: 0.85rem; }
  button:hover { border-color: var(--accent); color: var(--accent); }
  button.danger:hover { border-color: #e06060; color: #e06060; }
  button.primary { background: var(--accent); color: #fff; border-color: var(--accent); }
  button.primary:hover { background: var(--accent-light); }

  .modal-backdrop { position: fixed; inset: 0; background: rgba(0,0,0,0.7); display: flex; align-items: center; justify-content: center; z-index: 100; padding: 1rem; }
  .modal { background: var(--card); border-radius: var(--radius); padding: 2rem; width: 100%; max-width: 600px; max-height: 90vh; overflow-y: auto; border: 1px solid #444; }
  .modal h2 { font-family: var(--font-heading); color: var(--accent-light); margin-bottom: 1.5rem; }

  .form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
  .form-grid .full { grid-column: 1 / -1; }
  label { display: flex; flex-direction: column; gap: 0.3rem; font-size: 0.85rem; color: var(--text-muted); }
  input, select, textarea { background: #1a1a1a; border: 1px solid #444; color: var(--text); padding: 0.5rem 0.75rem; border-radius: 6px; font-size: 0.9rem; width: 100%; }
  input:focus, select:focus, textarea:focus { outline: none; border-color: var(--accent); }
  textarea { resize: vertical; font-family: var(--font-body); }
  .color-row { display: flex; gap: 0.5rem; align-items: center; }
  input[type="color"] { width: 44px; height: 36px; padding: 2px; cursor: pointer; }

  .modal-actions { display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 1.5rem; }
  .success { color: #4a9e5c; font-size: 0.9rem; margin-bottom: 1rem; }
  .error { color: #e06060; font-size: 0.85rem; margin-bottom: 1rem; }
</style>
```

**Step 3: Commit**

```bash
git add frontend/src/routes/admin/
git commit -m "feat: add admin view with keg edit modal and auth guard"
```

---

## Task 14: Frontend — Dockerfile and nginx config

**Files:**
- Create: `frontend/Dockerfile`
- Create: `frontend/nginx.conf`

**Step 1: Create nginx.conf**

```nginx
# frontend/nginx.conf
server {
  listen 3000;
  root /usr/share/nginx/html;
  index index.html;

  location / {
    try_files $uri $uri/ /index.html;
  }

  location /api/ {
    proxy_pass http://api:8000/api/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
  }
}
```

**Step 2: Create Dockerfile**

```dockerfile
# frontend/Dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 3000
```

**Step 3: Build the frontend image**

```bash
docker build -t kegdisplay-frontend ./frontend
```
Expected: `Successfully built ...`

**Step 4: Commit**

```bash
git add frontend/Dockerfile frontend/nginx.conf
git commit -m "feat: add frontend Dockerfile with multi-stage build and nginx"
```

---

## Task 15: Integration — first full stack run

**Step 1: Generate your admin password hash**

```bash
cd api && python hash_password.py yourpassword
```
Copy the output hash.

**Step 2: Create .env from .env.example**

```bash
cp .env.example .env
```

Edit `.env`:
```
ADMIN_USERNAME=jacob
ADMIN_PASSWORD_HASH=<paste hash here>
JWT_SECRET=$(openssl rand -hex 32)
JWT_EXPIRE_HOURS=24
DATABASE_PATH=/data/kegs.db
```

**Step 3: Build and start all services**

```bash
docker compose up --build
```

**Step 4: Verify the API**

```bash
curl http://localhost:8000/api/health
```
Expected: `{"status":"ok"}`

```bash
curl http://localhost:8000/api/kegs
```
Expected: JSON array of 8 keg objects, all with `status: "empty"`

**Step 5: Verify the frontend**

Open `http://localhost:3000` — should see the 4×2 keg grid with 8 empty ghost kegs.

**Step 6: Verify login**

Open `http://localhost:3000/admin` — should redirect to `/login`.
Log in with your credentials — should reach the admin panel.

**Step 7: Add a test keg via admin UI**

- Click Edit on Slot 1
- Fill in name "Summer Saison", style "Saison", ABV 5.2, status "on_tap", colour `#E8A020`
- Save and return to `/` — keg card should show filled amber keg with beer details.

**Step 8: Commit .env.example (never commit .env)**

```bash
echo ".env" >> .gitignore
git add .gitignore
git commit -m "chore: add .env to gitignore"
```

---

## Task 16: Final polish — README

**Files:**
- Create: `README.md`

**Step 1: Create README.md**

```markdown
# Kegdisplay

Self-hosted homebrewing keg display. Shows 8 corny kegs with beer details on a beautiful dark dashboard.
Built with FastAPI + SvelteKit + Docker Compose.

## Quick Start

1. Clone the repo and `cd kegdisplay`
2. Generate your admin password hash:
   ```bash
   cd api && python hash_password.py yourpassword
   ```
3. Copy and fill in `.env`:
   ```bash
   cp .env.example .env
   # edit .env with your hash, a random JWT_SECRET, and your username
   ```
4. Start:
   ```bash
   docker compose up --build -d
   ```
5. Open `http://localhost:3000` — add your kegs at `http://localhost:3000/admin`

## Nginx Proxy Manager

Point your domain to `http://<host>:3000`. The frontend proxies `/api` to the backend automatically.

## Backup

```bash
docker run --rm -v kegdisplay_keg_data:/data -v $(pwd):/backup alpine \
  tar czf /backup/kegs-backup.tar.gz /data
```

## Future: Untappd Integration

See `docs/plans/2026-04-15-kegdisplay-design.md` — Future Features section.
```

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add README with quick start and backup instructions"
```

---

## Checklist

- [ ] Task 1: Project scaffold + docker-compose
- [ ] Task 2: Database and Keg model
- [ ] Task 3: Pydantic schemas
- [ ] Task 4: JWT auth + hash_password.py
- [ ] Task 5: Kegs CRUD router + main.py
- [ ] Task 6: API requirements.txt + Dockerfile
- [ ] Task 7: SvelteKit scaffold
- [ ] Task 8: API client library
- [ ] Task 9: KegSvg component
- [ ] Task 10: KegCard component
- [ ] Task 11: Display view (home)
- [ ] Task 12: Login page
- [ ] Task 13: Admin layout + admin view
- [ ] Task 14: Frontend Dockerfile + nginx
- [ ] Task 15: Integration — full stack run
- [ ] Task 16: README
