import time
import threading
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from database import get_db
from models import Stat

router = APIRouter(prefix="/api/stats", tags=["stats"])

# In-memory presence tracking. Single uvicorn worker per Dockerfile, so a plain dict + lock is enough.
_presence: dict[str, float] = {}
_presence_lock = threading.Lock()
PRESENCE_TTL_SECONDS = 60

VISIT_KEY = "visits"


class HeartbeatIn(BaseModel):
    client_id: str = Field(..., min_length=1, max_length=64)


class StatsOut(BaseModel):
    visits: int
    online: int


def _online_count(now: float) -> int:
    cutoff = now - PRESENCE_TTL_SECONDS
    with _presence_lock:
        stale = [cid for cid, ts in _presence.items() if ts < cutoff]
        for cid in stale:
            del _presence[cid]
        return len(_presence)


def _visits(db: Session) -> int:
    row = db.query(Stat).filter(Stat.key == VISIT_KEY).first()
    return row.value if row else 0


@router.get("", response_model=StatsOut)
def get_stats(db: Session = Depends(get_db)):
    return StatsOut(visits=_visits(db), online=_online_count(time.time()))


@router.post("/visit", response_model=StatsOut)
def record_visit(db: Session = Depends(get_db)):
    row = db.query(Stat).filter(Stat.key == VISIT_KEY).first()
    if row:
        row.value = row.value + 1
    else:
        row = Stat(key=VISIT_KEY, value=1)
        db.add(row)
    db.commit()
    return StatsOut(visits=row.value, online=_online_count(time.time()))


@router.post("/heartbeat", response_model=StatsOut)
def heartbeat(body: HeartbeatIn, db: Session = Depends(get_db)):
    now = time.time()
    with _presence_lock:
        _presence[body.client_id] = now
    return StatsOut(visits=_visits(db), online=_online_count(now))
