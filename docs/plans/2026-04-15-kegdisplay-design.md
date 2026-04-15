# Kegdisplay — Design Document
**Date:** 2026-04-15
**Author:** Jacob Horfarter Hornbech

---

## Overview

A self-hosted homebrewing keg display and management app. Visually depicts 8 corny kegs with beer details (name, style, ABV, brew date, tap date, colour, notes, Untappd link). Public display view for parties and TV display; protected admin view for managing keg data.

---

## Architecture

### Stack
- **Backend:** Python FastAPI + SQLAlchemy + SQLite
- **Frontend:** SvelteKit (static build, served by nginx)
- **Auth:** JWT (python-jose + passlib/bcrypt), single admin user via env vars
- **Containerisation:** Docker Compose (2 services)

### Services

```
Nginx Proxy Manager (existing)
  ├── frontend  — SvelteKit/nginx  — port 3000
  └── api       — FastAPI          — port 8000
                       └── /data/kegs.db (named volume)
```

- Frontend is a pre-built static SvelteKit app served by nginx
- API is a FastAPI app with SQLite persisted to a Docker named volume
- Proxy manager routes `kegdisplay.domain` to frontend and `/api` to backend
- SQLite backup = single file copy from the volume

### Docker Compose

```yaml
services:
  api:
    build: ./api
    ports: ["8000:8000"]
    volumes: [keg_data:/data]
    env_file: .env

  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    depends_on: [api]

volumes:
  keg_data:
```

---

## Authentication

- Single admin user; credentials set via `.env`:
  ```
  ADMIN_USERNAME=jacob
  ADMIN_PASSWORD_HASH=<bcrypt hash>
  JWT_SECRET=<random string>
  JWT_EXPIRE_HOURS=24
  ```
- A `hash_password.py` helper script generates the bcrypt hash from a plain password
- Login endpoint returns a 24h JWT stored in browser `localStorage`
- **Display view (`/`)** — public, no auth required
- **Admin view (`/admin`)** — SvelteKit route guard redirects to `/login` if no valid token

---

## Data Model

**Table: `kegs`**

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | INTEGER | PK, autoincrement | |
| `slot` | INTEGER | NOT NULL, UNIQUE, 1–8 | Fixed display position |
| `name` | TEXT | NOT NULL | Beer name |
| `style` | TEXT | NOT NULL | e.g. IPA, Saison, Stout |
| `abv` | REAL | NOT NULL | Alcohol %, e.g. 5.2 |
| `brew_date` | DATE | NOT NULL | |
| `tap_date` | DATE | nullable | When put on tap |
| `volume_liters` | REAL | NOT NULL, default 19.0 | Corny keg default |
| `color_hex` | TEXT | NOT NULL | Beer colour for fill visual |
| `notes` | TEXT | nullable | Tasting notes, recipe notes |
| `untappd_url` | TEXT | nullable | Link to Untappd beer entry |
| `status` | TEXT | NOT NULL | `empty`/`conditioning`/`on_tap`/`archived` |
| `created_at` | DATETIME | auto | |
| `updated_at` | DATETIME | auto | |

All 8 slots always exist in the DB. Empty slots have `status = 'empty'` and minimal fields.

---

## API Endpoints

### Public
```
GET  /api/kegs           → list all 8 kegs
GET  /api/kegs/{id}      → single keg detail
GET  /api/health         → healthcheck
GET  /api/docs           → Swagger UI (FastAPI built-in)
```

### Protected (JWT Bearer token required)
```
POST   /api/auth/login         → { username, password } → JWT token
POST   /api/kegs               → create/fill a keg slot
PUT    /api/kegs/{id}          → update all keg fields
PATCH  /api/kegs/{id}/status   → update status only
DELETE /api/kegs/{id}          → clear slot (reset to empty)
```

### Keg response shape
```json
{
  "id": 1,
  "slot": 3,
  "name": "Summer Saison",
  "style": "Saison",
  "abv": 5.2,
  "brew_date": "2026-03-01",
  "tap_date": "2026-04-10",
  "volume_liters": 19.0,
  "color_hex": "#E8A020",
  "notes": "Light, citrusy, dry finish",
  "untappd_url": "https://untappd.com/b/...",
  "status": "on_tap",
  "created_at": "2026-04-01T10:00:00Z",
  "updated_at": "2026-04-15T08:30:00Z"
}
```

---

## Frontend UI/UX

### Display View (`/`) — public
- 4×2 grid of 8 keg cards
- Each card: SVG corny keg illustration with animated liquid fill in `color_hex`, beer name, style, ABV badge, brew/tap dates, status badge, Untappd icon (if set)
- Empty slots: ghost/outline keg with "Empty" label
- Dark theme: background `#1a1a1a`, cards `#2a2a2a`, amber accents `#C8860A`
- Craft-style heading font (Google Fonts)
- Subtle wood-grain texture header strip
- Fully responsive (phone, tablet, TV)

### Admin View (`/admin`) — protected
- Login page (`/login`): username + password form
- Keg list with Edit / Clear buttons per slot
- Edit form: all fields, hex colour picker, status dropdown
- Changes reflect immediately on display view

---

## Future Features (not in v1)

- **Untappd live check-in integration:** Connect Jacob's Untappd account via the Untappd API so that when party guests check in one of his beers, the check-in count and ratings appear live on the keg card. Requires Untappd app registration at https://untappd.com/api/docs.

---

## Project Structure

```
kegdisplay/
├── docker-compose.yml
├── .env.example
├── api/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   ├── database.py
│   ├── auth.py
│   ├── routers/
│   │   ├── kegs.py
│   │   └── auth.py
│   └── hash_password.py
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── svelte.config.js
    ├── vite.config.js
    └── src/
        ├── routes/
        │   ├── +page.svelte        (display view)
        │   ├── login/+page.svelte
        │   └── admin/
        │       ├── +layout.svelte  (auth guard)
        │       └── +page.svelte    (admin view)
        ├── lib/
        │   ├── KegCard.svelte
        │   ├── KegSvg.svelte
        │   └── api.js
        └── app.css
```
