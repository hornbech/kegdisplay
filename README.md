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
