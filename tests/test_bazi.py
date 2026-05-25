import pytest

from app.core.bazi import BaziService, BirthInput


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

    for p in chart["pillars"]:
        assert "ganzhi" in p
        assert "shishen" in p
        assert "nayin" in p
        assert p["tiangan"]["wuxing"] in ("木", "火", "土", "金", "水")


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
