from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Literal
from datetime import datetime

StatusEnum = Literal["empty", "fermenting", "conditioning", "on_tap", "archived"]


class KegBase(BaseModel):
    slot: int = Field(..., ge=1, le=10)
    name: str = ""
    style: str = ""
    abv: float = Field(0.0, ge=0.0, le=100.0)
    # Stored as ISO date strings (YYYY-MM-DD)
    brew_date: Optional[str] = None
    tap_date: Optional[str] = None
    volume_liters: float = Field(19.0, gt=0, le=19)
    color_hex: str = Field("#C8860A", pattern=r"^#[0-9A-Fa-f]{3,6}$")
    ibu: Optional[int] = Field(None, ge=0, le=500)
    ebc: Optional[int] = Field(None, ge=0, le=500)
    recipe_filename: Optional[str] = None
    notes: Optional[str] = None
    untappd_url: Optional[HttpUrl] = None
    status: StatusEnum = "empty"

    model_config = {"from_attributes": True}


class KegCreate(KegBase):
    pass


class KegUpdate(BaseModel):
    """Full update body — slot is excluded (it's a URL path param, not client-settable).
    recipe_filename is read-only here — it's managed by the upload/delete endpoints."""
    name: str = ""
    style: str = ""
    abv: float = Field(0.0, ge=0.0, le=100.0)
    brew_date: Optional[str] = None
    tap_date: Optional[str] = None
    volume_liters: float = Field(19.0, gt=0, le=19)
    color_hex: str = Field("#C8860A", pattern=r"^#[0-9A-Fa-f]{3,6}$")
    ibu: Optional[int] = Field(None, ge=0, le=500)
    ebc: Optional[int] = Field(None, ge=0, le=500)
    notes: Optional[str] = None
    untappd_url: Optional[HttpUrl] = None
    status: StatusEnum = "empty"


class KegStatusUpdate(BaseModel):
    status: StatusEnum


class KegOut(KegBase):
    id: int
    created_at: datetime
    updated_at: datetime


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginIn(BaseModel):
    username: str
    password: str
