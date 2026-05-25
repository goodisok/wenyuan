import pytest

from app.core.shensha import analyze as shensha_analyze
from app.core.yongshen import analyze as yongshen_analyze
from app.core.ziping import analyze as ziping_analyze


@pytest.fixture
def ref_chart():
    from app.core.bazi import BaziService, BirthInput

    return BaziService.build_chart(
        BirthInput("solar", 1990, 5, 15, 12, 30, "male")
    )


def test_ziping_returns_geju(ref_chart):
    geju = ziping_analyze(ref_chart)
    assert geju.get("type")
    assert geju.get("source")
    assert "purity" in geju


def test_yongshen_tendencies(ref_chart):
    from app.core.mingli import analyze as mingli_analyze

    ml = mingli_analyze(ref_chart)
    ys = yongshen_analyze(
        ref_chart,
        strength=ml["day_master_strength"],
        tiao_hou=ml["tiao_hou"],
        geju=ml["geju"],
    )
    assert ys.get("tendencies")
    assert ys.get("summary")
    assert "倾向" in ys.get("note", "")


def test_shensha_structure(ref_chart):
    sh = shensha_analyze(ref_chart)
    assert sh.get("kernel") == "三命通会"
    assert "items" in sh
    assert sh.get("summary")
    assert "by_pillar" in sh
    assert set(sh["by_pillar"].keys()) == {"year", "month", "day", "hour"}
    for names in sh["by_pillar"].values():
        assert isinstance(names, list)


def test_insight_has_geju_yongshen(ref_chart):
    ins = ref_chart["insight"]
    assert ins.get("geju")
    assert ins.get("yongshen")
    assert ins.get("shensha")
    assert len(ins.get("citations") or []) >= 4


def test_mingli_sources_complete(ref_chart):
    ml = ref_chart["insight"]["mingli"]
    for src in ("子平真诠", "三命通会", "渊海子平", "神峰通考"):
        assert src in ml.get("sources", [])
