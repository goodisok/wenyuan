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


def test_user_parents_divorce_windows_plausible(user_chart):
    ds = duanshi_analyze(user_chart)
    parent = next(i for i in ds["items"] if i["topic"] == "父母")
    windows = parent.get("windows") or []
    assert windows, "父母离异应有应期窗口"
    first_age = int(str(windows[0]["ages"]).split("-")[0])
    assert first_age <= 25, f"最早应期不应在晚年: {windows[0]}"
    notes = " ".join(w["note"] for w in windows)
    assert any(k in notes for k in ("穿", "伏吟", "冲", "破", "流年"))
    assert "壬戌" in notes or "癸亥" in notes or "辛酉" in notes
    ins = user_chart["insight"]
    assert ins.get("duanshi")
    from app.core.insight import public_insight
    pub = public_insight(ins)
    assert "duanshi" not in pub
