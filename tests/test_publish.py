import pytest

from app.core.bazi import BaziService, BirthInput
from app.core.duanshi import analyze as duanshi_analyze
from app.core.mingli import analyze as mingli_analyze
from app.core.publish import publish_duanshi, publish_sanguan
from app.core.sanguan import analyze as sanguan_analyze


@pytest.fixture
def user_chart():
    return BaziService.build_chart(
        BirthInput("solar", 1993, 12, 9, 18, 0, "male")
    )


def test_publish_duanshi_keeps_strong_only(user_chart):
    raw = duanshi_analyze(user_chart)
    sg = sanguan_analyze(user_chart)
    pub = publish_duanshi(raw, sg)
    topics = {i["topic"] for i in pub["items"]}
    assert topics == {"父母"}
    assert all(i["level"] == "强" for i in pub["items"])


def test_publish_sanguan_keeps_high_only(user_chart):
    raw = sanguan_analyze(user_chart)
    pub = publish_sanguan(raw)
    assert len(pub["gates"]) == 1
    assert pub["gates"][0]["id"] == "parents"
    assert pub["gates"][0]["confidence"] == "高"


def test_mingli_insight_excludes_weak_duanshi(user_chart):
    ml = mingli_analyze(user_chart)
    topics = {i["topic"] for i in ml["duanshi"]["items"]}
    assert "婚姻" not in topics
    assert "财运" not in topics
    gate_ids = {g["id"] for g in ml["sanguan"]["gates"]}
    assert gate_ids == {"parents"}


def test_user_insight_still_has_parents(user_chart):
    ins = user_chart["insight"]
    ds = ins["duanshi"]
    assert any(i["topic"] == "父母" for i in ds["items"])
    sg = ins["sanguan"]
    assert any(g["id"] == "parents" and g["confidence"] == "高" for g in sg["gates"])
