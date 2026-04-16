# Changelog

All notable changes to this project will be documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.0.0] — 2026-04-16

Initial release of Kegdisplay — a self-hosted homebrewing keg display.

### Added

**Frontend**
- Public display view: 4×2 grid of corny keg cards, responsive down to mobile
- SVG corny keg component with animated liquid fill levels per status
- KegCard component showing beer name, style, ABV, status badge, brew/tap dates, notes, and Untappd link
- Login page with JWT authentication
- Admin view: keg list with inline edit modal (all fields) and slot-clear action
- Admin layout with auth guard — redirects to `/login` if not authenticated
- Multi-stage Docker build (Node → nginx) serving static SvelteKit output on port 3000
- nginx proxies `/api/` to the FastAPI backend

**Backend**
- FastAPI application with SQLite storage (SQLAlchemy ORM)
- 8 corny keg slots, auto-seeded on first request
- `GET /api/kegs` — public list of all 8 slots
- `GET /api/kegs/{id}` — public single keg
- `PUT /api/kegs/{id}` — full keg update (auth required)
- `PATCH /api/kegs/{id}` — status-only update (auth required)
- `DELETE /api/kegs/{id}` — clear slot back to empty (auth required)
- `POST /api/auth/login` — returns JWT bearer token
- `GET /api/health` — health check
- Single admin user configured via `ADMIN_USERNAME` + `ADMIN_PASSWORD_HASH` env vars
- `hash_password.py` utility to generate bcrypt hashes for `.env`
- Pydantic v2 schemas with field validation (slot 1–8, ABV 0–100, valid status enum, HttpUrl for Untappd)

**Infrastructure**
- Docker Compose with two services: `api` (port 8000, SQLite on named volume) and `frontend` (port 3000)
- `.env.example` with all required variables documented
- `keg_data` named volume for persistent SQLite storage
