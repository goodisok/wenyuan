import pytest

from app.core.knowledge import format_for_ai, retrieve
from app.core.bazi import BaziService, BirthInput


@pytest.fixture
def ref_chart():
    return BaziService.build_chart(
        BirthInput("solar", 1990, 5, 15, 12, 30, "male")
    )


def test_retrieve_returns_citations(ref_chart):
    ins = ref_chart["insight"]
    cites = retrieve(ref_chart, ins)
    assert cites
    assert all("source" in c and "text" in c for c in cites)
    assert any("滴天髓" in c["source"] for c in cites)
    assert any(c["id"].startswith("wiki_") for c in cites)


def test_insight_has_citations(ref_chart):
    cites = ref_chart["insight"].get("citations") or []
    assert len(cites) >= 4
    sources = {c["source"] for c in cites}
    assert "穷通宝鉴" in sources


def test_format_for_ai(ref_chart):
    cites = retrieve(ref_chart, ref_chart["insight"])
    text = format_for_ai(cites)
    assert "典籍语料" in text
    assert "《" in text
