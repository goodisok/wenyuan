# -*- coding: utf-8 -*-
"""Tests for bazi-wiki integration."""
from __future__ import annotations

import pytest

from knowledge.corpus.loader import corpus_stats, load_all, match_corpus
from knowledge.corpus.wiki_loader import load_wiki_entries, wiki_available


@pytest.mark.skipif(not wiki_available(), reason="bazi-wiki not synced")
def test_wiki_loads():
    items = load_wiki_entries()
    assert len(items) >= 30
    assert all(i.get("id", "").startswith("wiki_") for i in items)
    assert all(i.get("text") for i in items)


@pytest.mark.skipif(not wiki_available(), reason="bazi-wiki not synced")
def test_wiki_case_has_pillars_and_geju_match():
    hits = match_corpus(
        {"geju", "ge-ju", "pattern", "ss:七杀", "ss:正印", "jing-dian", "di-tian"},
        geju_type="羊刃格",
        limit=8,
        min_score=4,
    )
    wiki_hits = [h for h in hits if h["id"].startswith("wiki_")]
    assert wiki_hits
    case = next((h for h in wiki_hits if "case-04" in h["id"]), None)
    assert case is not None
    assert case.get("pillars")
    assert "滴天髓" in case.get("source", "")


@pytest.mark.skipif(not wiki_available(), reason="bazi-wiki not synced")
def test_merged_corpus_includes_wiki(ref_chart):
    stats = corpus_stats()
    assert stats["by_book"].get("bazi-wiki", 0) >= 30
    assert stats["total"] >= 200
    cites = ref_chart["insight"].get("citations") or []
    assert any(c["id"].startswith("wiki_") for c in cites)


@pytest.fixture
def ref_chart():
    from app.core.bazi import BaziService, BirthInput

    return BaziService.build_chart(
        BirthInput("solar", 1990, 5, 15, 12, 30, "male")
    )
