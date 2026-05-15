from pydantic import BaseModel, Field, HttpUrl, field_validator
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
    avg_stars: Optional[float] = None
    review_count: int = 0


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginIn(BaseModel):
    username: str
    password: str


class ReviewCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    stars: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=500)

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("name must not be blank")
        return v

    model_config = {"from_attributes": True}


class ReviewOut(BaseModel):
    id: int
    keg_id: int
    name: str
    stars: int
    comment: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
