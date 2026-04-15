import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Keg

@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_keg_table_exists(db):
    keg = Keg(slot=1, name="Test IPA", style="IPA", abv=6.5,
              brew_date="2026-03-01", volume_liters=19.0,
              color_hex="#C8860A", status="on_tap")
    db.add(keg)
    db.commit()
    assert db.query(Keg).count() == 1

def test_keg_defaults(db):
    keg = Keg(slot=1, name="Test", style="IPA", abv=5.0,
              brew_date="2026-01-01", color_hex="#aaa", status="empty")
    db.add(keg)
    db.commit()
    assert keg.volume_liters == 19.0
    assert keg.tap_date is None
    assert keg.notes is None
    assert keg.untappd_url is None
