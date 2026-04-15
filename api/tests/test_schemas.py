import pytest
from schemas import KegOut, KegCreate, KegUpdate, KegStatusUpdate

def test_keg_create_requires_slot():
    with pytest.raises(Exception):
        KegCreate(name="IPA", style="IPA", abv=5.0,
                  brew_date="2026-01-01", color_hex="#aaa", status="on_tap")

def test_keg_out_has_id():
    keg = KegOut(id=1, slot=1, name="IPA", style="IPA", abv=5.0,
                 brew_date="2026-01-01", volume_liters=19.0,
                 color_hex="#aaa", status="on_tap",
                 created_at="2026-01-01T00:00:00",
                 updated_at="2026-01-01T00:00:00")
    assert keg.id == 1

def test_keg_status_update_valid_values():
    u = KegStatusUpdate(status="on_tap")
    assert u.status == "on_tap"

def test_keg_status_update_rejects_invalid():
    with pytest.raises(Exception):
        KegStatusUpdate(status="drinking")
