from app.core.classical_ref import find_similar, load_classical
from scripts.regression_common import build_chart_from_gz


def test_load_classical_nonempty():
    cases = load_classical()
    assert len(cases) >= 680


def test_find_similar_by_pillars():
    chart = build_chart_from_gz("辛卯 丁酉 庚午 丙子", "male", day_master="庚")
    refs = find_similar(chart, limit=3, min_score=15)
    assert isinstance(refs, list)
    for r in refs:
        assert r.get("gz") and r.get("renping_excerpt")
