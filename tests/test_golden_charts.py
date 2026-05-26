import json
from pathlib import Path

import pytest

from app.core.bazi import BaziService, BirthInput

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "golden_charts.json"


@pytest.fixture
def golden_cases():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", json.loads(FIXTURE.read_text(encoding="utf-8")), ids=lambda c: c["id"])
def test_golden_chart_pillars(case):
    inp = case["input"]
    bi = BirthInput(
        inp["date_type"],
        inp["year"],
        inp["month"],
        inp["day"],
        inp["hour"],
        inp["minute"],
        inp["gender"],
        is_leap_month=inp.get("is_leap_month", False),
    )
    chart = BaziService.build_chart(bi)
    got = [p["ganzhi"] for p in chart["pillars"]]
    assert got == case["pillars"], f"{case['id']}: {got} != {case['pillars']}"
    assert chart["meta"]["day_master"] == case["day_master"]
    assert chart["dayun"][0]["ganzhi"] == case["first_dayun"]


def test_golden_user_has_guanming(golden_cases):
    user = next(c for c in golden_cases if c["id"] == "user_default")
    bi = BirthInput("solar", user["input"]["year"], user["input"]["month"], user["input"]["day"],
                    user["input"]["hour"], user["input"]["minute"], user["input"]["gender"])
    chart = BaziService.build_chart(bi)
    gm = chart["insight"].get("guanming")
    assert gm and gm.get("layers")
    assert len(gm["layers"]) >= 6
