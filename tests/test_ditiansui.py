import pytest

from app.core.bazi import BaziService, BirthInput
from app.core.changsheng import changsheng
from app.core.ditiansui import analyze, KERNEL


@pytest.fixture
def ref_chart():
    return BaziService.build_chart(
        BirthInput("solar", 1990, 5, 15, 12, 30, "male")
    )


def test_reference_pillars_1990():
    chart = BaziService.build_chart(
        BirthInput("solar", 1990, 5, 15, 12, 30, "male")
    )
    gz = [p["ganzhi"] for p in chart["pillars"]]
    assert gz == ["庚午", "辛巳", "庚辰", "壬午"]


def test_changsheng_geng_in_si():
    assert changsheng("庚", "巳") == "长生"


def test_changsheng_jia_in_hai():
    assert changsheng("甲", "亥") == "长生"


def test_ditiansui_kernel(ref_chart):
    dts = analyze(ref_chart)
    assert dts["kernel"] == KERNEL
    assert dts["de_ling"]["status"] in ("得令", "相令", "失令", "泄令", "休令")
    assert dts["tong_gen"]["summary"] in ("有根", "弱根", "无根")
    assert dts["day_master_strength"] in ("偏强", "平衡", "偏弱")


def test_insight_has_ditiansui(ref_chart):
    ins = ref_chart["insight"]
    assert ins["kernel"] == "子平综参"
    assert ins.get("mingli") or ins.get("ditiansui")
    assert ins.get("tiao_hou")
    assert ins.get("pattern")
    assert ins.get("highlights")


def test_pillars_have_changsheng(ref_chart):
    for p in ref_chart["pillars"]:
        assert p.get("changsheng")


def test_meta_jieqi(ref_chart):
    jq = ref_chart["meta"].get("jieqi")
    assert jq
    assert jq.get("prev")
    assert jq.get("next")
    assert isinstance(jq.get("current_jie"), str)
    assert isinstance(jq.get("current_qi"), str)


def test_sanhe_detection():
    pillars = [
        {"key": "year", "tiangan": {"name": "壬"}, "dizhi": {"name": "申", "canggan": []}},
        {"key": "month", "tiangan": {"name": "癸"}, "dizhi": {"name": "子", "canggan": []}},
        {"key": "day", "tiangan": {"name": "甲"}, "dizhi": {"name": "辰", "canggan": []}},
        {"key": "hour", "tiangan": {"name": "乙"}, "dizhi": {"name": "丑", "canggan": []}},
    ]
    from app.core.relations import compute_pillar_relations

    rel = compute_pillar_relations(pillars)
    assert "申子辰合水局" in rel
