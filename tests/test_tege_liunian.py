import pytest

from app.core.bazi import BaziService, BirthInput
from app.core.liunian_detail import analyze_dayun_detail, analyze_liunian
from app.core.mingli import analyze as mingli_analyze
from app.core.tege import detect_special_pattern


@pytest.fixture
def ref_chart():
    return BaziService.build_chart(
        BirthInput("solar", 1990, 5, 15, 12, 30, "male")
    )


def test_mingli_has_dayun_detail(ref_chart):
    ml = mingli_analyze(ref_chart)
    dd = ml.get("dayun_detail") or {}
    assert dd.get("dayun_details")
    assert dd.get("current_year_detail")
    cy = dd["current_year_detail"]
    assert "liunian_ganzhi" in cy
    assert "key_months" in cy


def test_liunian_detail_current_year(ref_chart):
    detail = analyze_liunian(ref_chart)
    assert detail.get("year")
    assert detail.get("liunian_ganzhi")
    assert "triggers" in detail


def test_tege_detect_runs(ref_chart):
    # 普通命盘可能非特格
    result = detect_special_pattern(ref_chart)
    assert result is None or result.get("is_special") is True


def test_shensha_only_three_types(ref_chart):
    ml = mingli_analyze(ref_chart)
    allowed = {"禄神", "将星", "驿马"}
    for item in (ml.get("shensha") or {}).get("items") or []:
        assert item["name"] in allowed
    note = (ml.get("shensha") or {}).get("note", "")
    assert "不作分析依据" in note
