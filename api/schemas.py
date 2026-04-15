from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime, date

StatusEnum = Literal["empty", "conditioning", "on_tap", "archived"]

class KegBase(BaseModel):
    slot: int = Field(..., ge=1, le=8)
    name: str = ""
    style: str = ""
    abv: float = Field(0.0, ge=0.0, le=100.0)
    brew_date: Optional[str] = None
    tap_date: Optional[str] = None
    volume_liters: float = Field(19.0, gt=0)
    color_hex: str = "#C8860A"
    notes: Optional[str] = None
    untappd_url: Optional[str] = None
    status: StatusEnum = "empty"

class KegCreate(KegBase):
    pass

class KegUpdate(KegBase):
    pass

class KegStatusUpdate(BaseModel):
    status: StatusEnum

class KegOut(KegBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

class LoginIn(BaseModel):
    username: str
    password: str
