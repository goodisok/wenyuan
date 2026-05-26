import pytest

from app.core.bazi import BaziService, BirthInput
from app.core.guanming import build_guanming
from app.core.mingli import analyze as mingli_analyze


@pytest.fixture
def user_chart():
    return BaziService.build_chart(
        BirthInput("solar", 1993, 12, 9, 18, 0, "male")
    )


def test_guanming_layers(user_chart):
    ml = mingli_analyze(user_chart)
    gm = ml["guanming"]
    ids = {layer["id"] for layer in gm["layers"]}
    assert "tiandao" in ids
    assert "mangpai" in ids
    assert "didao" in ids
    assert "rendao" in ids
    assert "tiyong" in ids
    assert gm.get("summary")


def test_highlights_start_with_guanming(user_chart):
    ml = mingli_analyze(user_chart)
    assert ml["highlights"][0].startswith("【观命总观】")
