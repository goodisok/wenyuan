import pytest

from app.core.mingli import KERNEL, analyze
from app.core.qiongtong import QIONGTONG, lookup


def test_qiongtong_full_table():
    assert len(QIONGTONG) == 120


def test_qiongtong_lookup():
    r = lookup("庚", "巳")
    assert r["source"] == "穷通宝鉴"
    assert "丁" in r["hint"] or "壬" in r["hint"]


def test_mingli_kernel(ref_chart):
    ml = analyze(ref_chart)
    assert ml["kernel"] == KERNEL
    assert ml["kernel"] == "子平综参"
    assert "子平" in ml["sources"]
    assert "穷通宝鉴" in ml["sources"]
    assert "子平真诠" in ml["sources"]
    assert ml.get("geju")
    assert ml.get("yongshen")
    assert ml.get("shensha")
    assert len(ml["highlights"]) >= 3
    assert ml["qiongtong"]["hint"]


@pytest.fixture
def ref_chart():
    from app.core.bazi import BaziService, BirthInput

    return BaziService.build_chart(
        BirthInput("solar", 1990, 5, 15, 12, 30, "male")
    )


def test_insight_mingli(ref_chart):
    ins = ref_chart["insight"]
    assert ins["kernel"] == "子平综参"
    assert ins.get("highlights")
    assert ins.get("qiongtong")
