import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import Keg
from schemas import KegOut, KegUpdate, KegStatusUpdate
from auth import get_current_user
from jose import JWTError

router = APIRouter(prefix="/api/kegs", tags=["kegs"])
_bearer = HTTPBearer(auto_error=False)

RECIPES_DIR = os.getenv("RECIPES_DIR", "/data/recipes")
MAX_RECIPE_BYTES = 10 * 1024 * 1024  # 10 MB


def _recipe_path(keg_id: int) -> str:
    return os.path.join(RECIPES_DIR, f"{keg_id}.pdf")


def _require_auth(credentials: HTTPAuthorizationCredentials = Depends(_bearer)) -> str:
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        return get_current_user(credentials.credentials)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def _ensure_8_slots(db: Session):
    """Seed all 8 slots if any are missing. Queries only the slot column for efficiency."""
    existing = {row[0] for row in db.query(Keg.slot).all()}
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
    # slot is excluded from KegUpdate — it's a fixed URL path param, not client-settable
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
    _ensure_8_slots(db)
    keg = db.query(Keg).filter(Keg.id == keg_id).first()
    if not keg:
        raise HTTPException(status_code=404, detail="Keg not found")
    for field in ["name", "style", "notes", "untappd_url", "brew_date", "tap_date"]:
        setattr(keg, field, None if field not in ["name", "style"] else "")
    keg.abv = 0.0
    keg.color_hex = "#555555"
    keg.status = "empty"
    keg.volume_liters = 19.0
    keg.ibu = None
    keg.ebc = None
    if keg.recipe_filename:
        try:
            os.remove(_recipe_path(keg.id))
        except FileNotFoundError:
            pass
        keg.recipe_filename = None
    db.commit()
    db.refresh(keg)
    return keg


@router.post("/{keg_id}/recipe", response_model=KegOut)
async def upload_recipe(keg_id: int, file: UploadFile = File(...),
                        db: Session = Depends(get_db),
                        user: str = Depends(_require_auth)):
    keg = db.query(Keg).filter(Keg.id == keg_id).first()
    if not keg:
        raise HTTPException(status_code=404, detail="Keg not found")
    if file.content_type != "application/pdf" and not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    os.makedirs(RECIPES_DIR, exist_ok=True)
    path = _recipe_path(keg_id)
    size = 0
    with open(path, "wb") as out:
        while chunk := await file.read(64 * 1024):
            size += len(chunk)
            if size > MAX_RECIPE_BYTES:
                out.close()
                os.remove(path)
                raise HTTPException(status_code=413, detail="Recipe exceeds 10 MB limit")
            out.write(chunk)

    keg.recipe_filename = file.filename or f"recipe-{keg_id}.pdf"
    db.commit()
    db.refresh(keg)
    return keg


@router.delete("/{keg_id}/recipe", response_model=KegOut)
def delete_recipe(keg_id: int, db: Session = Depends(get_db),
                  user: str = Depends(_require_auth)):
    keg = db.query(Keg).filter(Keg.id == keg_id).first()
    if not keg:
        raise HTTPException(status_code=404, detail="Keg not found")
    try:
        os.remove(_recipe_path(keg_id))
    except FileNotFoundError:
        pass
    keg.recipe_filename = None
    db.commit()
    db.refresh(keg)
    return keg


@router.get("/{keg_id}/recipe")
def download_recipe(keg_id: int, db: Session = Depends(get_db)):
    keg = db.query(Keg).filter(Keg.id == keg_id).first()
    if not keg or not keg.recipe_filename:
        raise HTTPException(status_code=404, detail="No recipe on file")
    path = _recipe_path(keg_id)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Recipe file missing")
    return FileResponse(path, media_type="application/pdf", filename=keg.recipe_filename)
