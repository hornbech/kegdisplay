from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import Keg, Review
from schemas import ReviewCreate, ReviewOut
from auth import get_current_user
from jose import JWTError

router = APIRouter(tags=["reviews"])
_bearer = HTTPBearer(auto_error=False)


def _require_auth(credentials: HTTPAuthorizationCredentials = Depends(_bearer)) -> str:
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        return get_current_user(credentials.credentials)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.get("/api/kegs/{keg_id}/reviews", response_model=List[ReviewOut])
def list_reviews(keg_id: int, db: Session = Depends(get_db)):
    if not db.query(Keg).filter(Keg.id == keg_id).first():
        raise HTTPException(status_code=404, detail="Keg not found")
    return (
        db.query(Review)
        .filter(Review.keg_id == keg_id)
        .order_by(Review.created_at.desc())
        .all()
    )


@router.post("/api/kegs/{keg_id}/reviews", response_model=ReviewOut, status_code=201)
def create_review(keg_id: int, body: ReviewCreate, db: Session = Depends(get_db)):
    if not db.query(Keg).filter(Keg.id == keg_id).first():
        raise HTTPException(status_code=404, detail="Keg not found")
    review = Review(keg_id=keg_id, name=body.name, stars=body.stars, comment=body.comment)
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


@router.delete("/api/reviews/{review_id}", status_code=204)
def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    user: str = Depends(_require_auth),
):
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    db.delete(review)
    db.commit()
