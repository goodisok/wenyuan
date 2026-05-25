import pytest

from app.core.bazi import BaziService, BirthInput
from app.core.sanguan import analyze as sanguan_analyze


@pytest.fixture
def user_chart():
    return BaziService.build_chart(
        BirthInput("solar", 1993, 12, 9, 18, 0, "male")
    )


def test_user_parents_gate_high_confidence(user_chart):
    sg = sanguan_analyze(user_chart)
    parent = next(g for g in sg["gates"] if g["id"] == "parents")
    assert parent["confidence"] == "高"
    assert parent["schools_agree"] >= 3
    assert "离异" in parent["verdict"] or "分居" in parent["verdict"]
    schools = {s["school"] for s in parent["signals"]}
    assert "盲派" in schools
    assert "子平" in schools
    assert "千里命稿" in schools


def test_insight_has_sanguan(user_chart):
    ins = user_chart["insight"]
    assert ins.get("sanguan")
    assert any("第一关" in h or "三关" in h for h in ins.get("highlights", []))


def test_sanguan_three_gates(user_chart):
    sg = sanguan_analyze(user_chart)
    assert len(sg["gates"]) == 3
    assert {g["id"] for g in sg["gates"]} == {"parents", "siblings", "children"}
