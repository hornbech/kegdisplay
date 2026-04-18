from sqlalchemy import Column, Integer, Float, Text, DateTime
from datetime import datetime, timezone
from database import Base


def _utcnow():
    return datetime.now(timezone.utc)


class Keg(Base):
    __tablename__ = "kegs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    slot = Column(Integer, nullable=False, unique=True)
    name = Column(Text, nullable=False, default="")
    style = Column(Text, nullable=False, default="")
    abv = Column(Float, nullable=False, default=0.0)
    # Stored as ISO date strings (YYYY-MM-DD) to avoid SQLite date quirks
    brew_date = Column(Text, nullable=True)
    tap_date = Column(Text, nullable=True)
    volume_liters = Column(Float, nullable=False, default=19.0)
    color_hex = Column(Text, nullable=False, default="#C8860A")
    ibu = Column(Integer, nullable=True)
    ebc = Column(Integer, nullable=True)
    recipe_filename = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    untappd_url = Column(Text, nullable=True)
    status = Column(Text, nullable=False, default="empty")
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    def __repr__(self):
        return f"<Keg slot={self.slot} name={self.name!r} status={self.status!r}>"
