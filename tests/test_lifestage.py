# -*- coding: utf-8 -*-
from __future__ import annotations

from app.core.lifestage import build_lifestage
from app.core.reading import (
    apply_stage_presentation,
    build_output_format,
    public_l2_questions,
)


def test_stage_child_structure_not_verdict() -> None:
    insight = apply_stage_presentation(
        {
            "guanming": {"summary": "流通"},
            "duanshi": {
                "items": [
                    {
                        "topic": "婚姻",
                        "topic_id": "relationship",
                        "verdict": "晚婚",
                        "publish_tier": "hint",
                        "display_verdict": "结构倾向",
                        "level": "中",
                    }
                ],
                "liuqin": {"spouse": {"star": "正财", "locations": []}},
            },
            "sanguan": {"gates": []},
            "day_master": "甲",
            "day_master_wuxing": "木",
            "day_master_strength": "偏弱",
            "de_ling": {},
            "tong_gen": {},
        },
        10,
    )
    marriage = next(i for i in insight["duanshi"]["items"] if i["topic"] == "婚姻")
    assert marriage["display_tier"] == "structure"
    assert "晚婚" not in marriage["display_verdict"]


def test_public_l2_generic() -> None:
    qs = public_l2_questions(12)
    assert qs
    assert not any("断「" in q for q in qs)


def test_output_format_ai_centric() -> None:
    ls = build_lifestage(34)
    text = build_output_format({"life_stage": ls})
    assert "全盘定调" in text
    assert "直断" not in text or "程序术语" in text
