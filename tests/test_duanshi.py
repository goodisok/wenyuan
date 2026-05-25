import pytest

from app.core.bazi import BaziService, BirthInput
from app.core.duanshi import analyze as duanshi_analyze


@pytest.fixture
def user_chart():
    return BaziService.build_chart(
        BirthInput("solar", 1993, 12, 9, 18, 0, "male")
    )


def test_ziyou_po_in_relations(user_chart):
    rel = user_chart["pillars_relations"]
    assert "子酉破" in rel


def test_user_parents_divorce_signal(user_chart):
    ds = duanshi_analyze(user_chart)
    parent = next(i for i in ds["items"] if i["topic"] == "父母")
    assert parent["level"] == "强"
    assert "离异" in parent["verdict"] or "分居" in parent["verdict"]
    assert any("子酉" in r for r in parent["reasons"])


def test_insight_has_duanshi(user_chart):
    ins = user_chart["insight"]
    assert ins.get("duanshi")
    assert any("断父母" in h for h in ins.get("highlights", []))
