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
    _ensure_8_slots(db)
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
    for field in ["name", "style", "notes", "untappd_url", "brew_date", "tap_date"]:
        setattr(keg, field, None if field not in ["name", "style"] else "")
    keg.abv = 0.0
    keg.color_hex = "#555555"
    keg.status = "empty"
    keg.volume_liters = 19.0
    db.commit()
    db.refresh(keg)
    return keg
