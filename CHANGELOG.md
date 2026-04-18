# Changelog

All notable changes to this project will be documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.3.0] — 2026-04-18

### Added

- **`fermenting` keg status** (empty → fermenting → conditioning → on_tap → archived), with a dedicated admin dropdown option and status colour `#d4652b`

### Changed

- **Public display redesigned** — "Refined Craft Tavern" direction from the Claude Design handoff:
  - Radial chalkboard background with brass accents
  - "Bear Brew." wordmark in italic Playfair Display, with tagline (Est. 2019 · Copenhagen · Eight taps. No shortcuts.) and "currently pouring N/8" counter
  - Ornate "TAP NN" slot tags (brass when on-tap)
  - Stats row with hairline-divided ABV / age / fill meter
  - Tasting notes styled as italic pull-quotes
  - 2-column grid (responsive down to 1 column on mobile)
- **Keg SVG upgraded** to a polished corny: gradient body and liquid, surface-highlight ellipse, vertical shine, brass pressure post — reused unchanged on the admin page

---

## [1.2.0] — 2026-04-18

### Added

- **Info page** at `/info` with links to the API docs (`/api/docs`) and the GitHub project
- **Visitor counter** persisted in a new `stats` key/value table; deduped per browser session
- **Online-now counter** via lightweight heartbeat (20 s interval, 60 s presence window, in-memory)
- New endpoints: `GET /api/stats`, `POST /api/stats/visit`, `POST /api/stats/heartbeat`
- Header now shows an Info link alongside Admin

---

## [1.1.0] — 2026-04-18

### Added

- **IBU and EBC fields** on every keg (admin form + display badges)
- **Recipe PDF upload** per keg:
  - `POST /api/kegs/{id}/recipe` (auth, 10 MB PDF limit)
  - `DELETE /api/kegs/{id}/recipe` (auth)
  - `GET /api/kegs/{id}/recipe` (public, streams the PDF)
  - PDFs stored at `/data/recipes/{id}.pdf` on the existing `keg_data` volume
- Public display shows a **📄 Recipe** button that opens the PDF in an overlay (with "open in new tab" escape)
- Admin edit modal: beer-style dropdown (34 styles, SRM-mapped colours) replaces the raw colour picker
- Brewery renamed to **Bear Brew** (display, login, admin titles)

### Changed

- Idempotent `ALTER TABLE` on startup adds `ibu`, `ebc`, `recipe_filename` columns — existing databases upgrade in place, no data loss
- nginx `client_max_body_size` raised to 15 MB to accommodate recipe uploads
- Clearing a slot also removes its attached recipe

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
