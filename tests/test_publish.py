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


def test_publish_duanshi_tiers(user_chart):
    raw = duanshi_analyze(user_chart)
    sg = sanguan_analyze(user_chart)
    pub = publish_duanshi(raw, sg)
    tiers = {i["topic"]: i["publish_tier"] for i in pub["items"]}
    assert tiers.get("父母") == "assert"
    assert tiers.get("婚姻") == "hint"
    assert tiers.get("财运") == "hint"


def test_publish_sanguan_tiers(user_chart):
    raw = sanguan_analyze(user_chart)
    pub = publish_sanguan(raw)
    assert len(pub["gates"]) >= 1
    parents = next(g for g in pub["gates"] if g["id"] == "parents")
    assert parents["publish_tier"] == "assert"


def test_mingli_insight_includes_hint_topics(user_chart):
    ml = mingli_analyze(user_chart)
    topics = {i["topic"] for i in ml["duanshi"]["items"]}
    assert "父母" in topics
    assert "婚姻" in topics
    assert "财运" in topics


def test_user_insight_public_minimal(user_chart):
    from app.core.insight import public_insight

    full = user_chart["insight"]
    assert any(i["topic"] == "父母" for i in full["duanshi"]["items"])
    pub = public_insight(full)
    assert "duanshi" not in pub
    assert "highlights" not in pub
    assert pub.get("l2_questions")
    assert pub.get("current_dayun")
