import os
import warnings
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from database import engine, Base
from routers import kegs, auth as auth_router, stats as stats_router

RECIPES_DIR = os.getenv("RECIPES_DIR", "/data/recipes")

# New columns added after the initial schema. Idempotent: "duplicate column" errors are swallowed.
_ADD_COLUMNS = [
    "ALTER TABLE kegs ADD COLUMN ibu INTEGER",
    "ALTER TABLE kegs ADD COLUMN ebc INTEGER",
    "ALTER TABLE kegs ADD COLUMN recipe_filename TEXT",
]


def _run_column_migrations() -> None:
    with engine.begin() as conn:
        for stmt in _ADD_COLUMNS:
            try:
                conn.execute(text(stmt))
            except Exception:
                pass  # column already exists


@asynccontextmanager
async def lifespan(app: FastAPI):
    if os.getenv("JWT_SECRET", "changeme") == "changeme":
        warnings.warn(
            "JWT_SECRET is using the insecure default 'changeme'. Set a strong secret in .env.",
            stacklevel=1,
        )
    Base.metadata.create_all(bind=engine)
    _run_column_migrations()
    os.makedirs(RECIPES_DIR, exist_ok=True)
    yield

_raw_origins = os.getenv("CORS_ORIGINS", "*")
_origins = [o.strip() for o in _raw_origins.split(",")]

app = FastAPI(title="Kegdisplay API", docs_url="/api/docs", openapi_url="/api/openapi.json",
              lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(kegs.router)
app.include_router(auth_router.router)
app.include_router(stats_router.router)

@app.get("/api/health")
def health():
    return {"status": "ok"}
