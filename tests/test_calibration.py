import pytest

from app.core.bazi import BaziService, BirthInput
from app.core.calibration import build_calibration_items, build_temperament


@pytest.fixture
def user_chart():
    return BaziService.build_chart(
        BirthInput("solar", 1993, 12, 9, 18, 0, "male")
    )


def test_temperament_items(user_chart):
    ins = user_chart["insight"]
    ml = ins.get("mingli") or ins
    temp = build_temperament(ml)
    assert temp.get("items")
    assert any(i["category"] == "temperament" for i in temp["items"])


def test_calibration_items_grouped(user_chart):
    ins = user_chart["insight"]
    ins = {**ins, "temperament": build_temperament(ins.get("mingli") or ins)}
    items = build_calibration_items(ins)
    assert items
    cats = {i["category"] for i in items}
    assert "temperament" in cats
    assert "event" in cats or "timing" in cats


def test_public_insight_omits_calibration(user_chart):
    from app.core.insight import public_insight

    pub = public_insight(user_chart["insight"])
    assert "temperament" not in pub
    assert "calibration_items" not in pub


def test_guanming_has_mangpai(user_chart):
    gm = user_chart["insight"]["guanming"]
    ids = {layer["id"] for layer in gm["layers"]}
    assert "mangpai" in ids
