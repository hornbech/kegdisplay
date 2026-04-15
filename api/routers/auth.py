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
