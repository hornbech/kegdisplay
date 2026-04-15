from sqlalchemy import Column, Integer, Float, Text, DateTime
from datetime import datetime
from database import Base

class Keg(Base):
    __tablename__ = "kegs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    slot = Column(Integer, nullable=False, unique=True)
    name = Column(Text, nullable=False, default="")
    style = Column(Text, nullable=False, default="")
    abv = Column(Float, nullable=False, default=0.0)
    brew_date = Column(Text, nullable=True)
    tap_date = Column(Text, nullable=True)
    volume_liters = Column(Float, nullable=False, default=19.0)
    color_hex = Column(Text, nullable=False, default="#C8860A")
    notes = Column(Text, nullable=True)
    untappd_url = Column(Text, nullable=True)
    status = Column(Text, nullable=False, default="empty")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
