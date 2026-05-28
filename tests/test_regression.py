import pytest

from scripts.regression_common import (
    build_chart_from_gz,
    geju_mentioned,
    parse_gz,
    polarity_aligned,
    score_ai_analysis,
    stem_shishen,
)


def test_parse_gz():
    assert parse_gz("辛卯 丁酉 庚午 丙子") == ["辛卯", "丁酉", "庚午", "丙子"]


def test_stem_shishen_day_master():
    assert stem_shishen("庚", "庚") == "日主"
    assert stem_shishen("庚", "甲") in ("偏财", "正财")


def test_build_chart_from_gz_structure():
    chart = build_chart_from_gz("辛卯 丁酉 庚午 丙子", "male", day_master="庚")
    assert len(chart["pillars"]) == 4
    assert chart["meta"]["day_master"] == "庚"
    assert chart["pillars_relations"] is not None


def test_build_chart_from_gz_mingli():
    from app.core.mingli import analyze as mingli_analyze

    chart = build_chart_from_gz("辛卯 丁酉 庚午 丙子", "male", day_master="庚")
    ml = mingli_analyze(chart)
    assert ml.get("geju")
    assert ml.get("dayun_detail", {}).get("current_year_detail", {}).get("year")


def test_score_ai_analysis_strength_mismatch():
    text = "此命身弱，宜印比扶身。" * 20
    insight = {"day_master_strength": "偏强", "geju": {"type": "正官格"}}
    score, issues = score_ai_analysis(text, insight)
    assert score < 10
    assert any("旺衰" in i for i in issues)


def test_geju_mentioned_partial():
    assert geju_mentioned("此造伤官透干", "伤官格")
    assert geju_mentioned("己甲化土成格", "己甲化土格")
    assert not geju_mentioned("正印当令", "伤官格")


def test_ai_regression_suite_classical_only():
    from scripts.regression_ai import load_ai_suite

    cases = load_ai_suite()
    assert len(cases) >= 50
    assert all(c.get("gz") for c in cases)
    assert not any(c.get("birth_date") for c in cases)
    assert not any(c.get("bucket") == "celebrity" for c in cases)


def test_score_ai_analysis_classic_allows_ancient_terms():
    text = "此造武职发用，官至边关。" * 15
    insight = {"day_master_strength": "偏强", "geju": {"type": "七杀格"}}
    score, issues = score_ai_analysis(text, insight, style="classic")
    assert score >= 8
    assert not any("古代断语" in i for i in issues)


def test_polarity_aligned():
    assert polarity_aligned("此人贵显，寿至八旬", ["格局清纯，贵气有余"]) is True
    assert polarity_aligned("刑冲破害，夭亡", ["格局清纯，贵气有余"]) is False
