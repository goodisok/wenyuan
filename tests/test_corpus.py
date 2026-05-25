import pytest

from knowledge.corpus.loader import corpus_stats, load_all, match_corpus


def test_corpus_loads():
    items = load_all()
    stats = corpus_stats()
    assert stats["total"] == len(items)
    assert stats["total"] >= 150
    assert stats["by_book"].get("穷通宝鉴", 0) == 120


def test_corpus_match_qiongtong():
    hits = match_corpus(
        {"tiao_hou", "stem:甲", "month:酉"},
        day_stem="甲",
        month_branch="酉",
        limit=5,
        min_score=4,
    )
    assert hits
    assert any("甲" in h["text"] and "酉" in h.get("chapter", h["text"]) for h in hits)


def test_corpus_match_geju(ref_chart):
    ins = ref_chart["insight"]
    geju = ins.get("geju", {}).get("type", "")
    hits = match_corpus(
        {"geju", f"geju:{geju}", "pattern"},
        geju_type=geju,
        limit=5,
        min_score=4,
    )
    assert hits
    assert any(geju in h.get("text", "") or "格" in h.get("text", "") for h in hits)


def test_insight_corpus_meta(ref_chart):
    meta = ref_chart["insight"].get("corpus_meta") or {}
    assert meta.get("total", 0) >= 150
    cites = ref_chart["insight"].get("citations") or []
    assert len(cites) >= 6
    assert any(c.get("chapter") for c in cites)


@pytest.fixture
def ref_chart():
    from app.core.bazi import BaziService, BirthInput

    return BaziService.build_chart(
        BirthInput("solar", 1990, 5, 15, 12, 30, "male")
    )
