import pytest

from app.core.bazi import BaziService, BirthInput
from app.core.relations import compute_pillar_relations


@pytest.fixture
def solar_male():
    return BirthInput(
        date_type="solar",
        year=1990, month=5, day=15,
        hour=12, minute=30,
        gender="male",
    )


def test_validate_datetime():
    assert BaziService.validate_datetime(1990, 5, 15, 12, 30)
    assert not BaziService.validate_datetime(1990, 2, 30, 12, 30)


def test_build_chart_structure(solar_male):
    chart = BaziService.build_chart(solar_male)
    assert len(chart["pillars"]) == 4
    assert chart["meta"]["gender_label"] == "男"
    assert chart["meta"]["zodiac"]
    assert chart["meta"]["day_master"]
    assert len(chart["dayun"]) > 0
    assert chart.get("insight")
    assert chart.get("qiyun")
    assert "pillars_relations" in chart

    for p in chart["pillars"]:
        assert "ganzhi" in p
        assert "shishen" in p
        assert "nayin" in p
        assert "xunkong" in p
        assert p["tiangan"]["wuxing"] in ("木", "火", "土", "金", "水")
        for cg in p["dizhi"]["canggan"]:
            assert "shishen" in cg


def test_day_pillar_is_master(solar_male):
    chart = BaziService.build_chart(solar_male)
    day = next(p for p in chart["pillars"] if p["key"] == "day")
    assert day["shishen"] == "日主"


def test_invalid_date_raises():
    bad = BirthInput("solar", 1990, 13, 1, 12, 0, "male")
    with pytest.raises(ValueError):
        BaziService.build_chart(bad)


def test_wuxing_stats(solar_male):
    chart = BaziService.build_chart(solar_male)
    stats = chart["wuxing_stats"]
    assert set(stats.keys()) == {"木", "火", "土", "金", "水"}


def test_lunar_leap_month():
    leap = BirthInput(
        date_type="lunar",
        year=2020, month=4, day=1,
        hour=10, minute=0,
        gender="female",
        is_leap_month=True,
    )
    chart = BaziService.build_chart(leap)
    assert chart["meta"]["date_type"] == "lunar"
    assert chart["meta"]["is_leap_month"] is True


def test_lunar_normal_month():
    normal = BirthInput(
        date_type="lunar",
        year=1990, month=4, day=21,
        hour=8, minute=0,
        gender="female",
    )
    chart = BaziService.build_chart(normal)
    assert chart["meta"]["is_leap_month"] is False


def test_insight_fields(solar_male):
    chart = BaziService.build_chart(solar_male)
    ins = chart["insight"]
    assert ins["day_master"]
    assert ins["day_master_wuxing"]
    assert "wuxing_counts" in ins
    assert ins["day_master_strength"] in ("偏弱", "平衡", "偏强")
    assert ins.get("kernel") == "滴天髓阐微"
    assert ins.get("tiao_hou")


def test_pillar_relations():
    pillars = [
        {
            "key": "year",
            "tiangan": {"name": "甲"},
            "dizhi": {"name": "子", "canggan": []},
        },
        {
            "key": "month",
            "tiangan": {"name": "己"},
            "dizhi": {"name": "丑", "canggan": []},
        },
        {
            "key": "day",
            "tiangan": {"name": "丙"},
            "dizhi": {"name": "午", "canggan": []},
        },
        {
            "key": "hour",
            "tiangan": {"name": "辛"},
            "dizhi": {"name": "卯", "canggan": []},
        },
    ]
    rel = compute_pillar_relations(pillars)
    assert "甲己合" in rel
    assert "子丑合" in rel
    assert "子午冲" in rel
