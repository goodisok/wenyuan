# -*- coding: utf-8 -*-
from __future__ import annotations

from app.core.lifestage import build_lifestage, topic_priority
from app.core.reading import (
    apply_stage_presentation,
    build_output_format,
    rebuild_highlights,
    suggest_l2_questions,
)


def test_stage_child_hides_marriage_verdict_not_structure() -> None:
    insight = {
        "duanshi": {
            "items": [
                {
                    "topic": "父母",
                    "topic_id": "parents",
                    "verdict": "缘厚",
                    "publish_tier": "assert",
                    "display_verdict": "缘厚",
                    "level": "强",
                },
                {
                    "topic": "婚姻",
                    "topic_id": "relationship",
                    "verdict": "晚婚",
                    "publish_tier": "hint",
                    "display_verdict": "结构倾向",
                    "level": "中",
                },
            ],
            "liuqin": {"spouse": {"star": "正财", "locations": []}},
        },
        "sanguan": {
            "gates": [
                {
                    "id": "children",
                    "name": "第三关·子女",
                    "publish_tier": "assert",
                    "display_verdict": "有子",
                    "confidence": "高",
                }
            ]
        },
        "guanming": {"summary": "流通"},
        "day_master": "甲",
        "day_master_wuxing": "木",
        "day_master_strength": "偏弱",
        "de_ling": {},
        "tong_gen": {},
    }
    out = apply_stage_presentation(insight, 10)
    topics = {i["topic"] for i in out["duanshi"]["items"]}
    assert "父母" in topics
    marriage = next(i for i in out["duanshi"]["items"] if i["topic"] == "婚姻")
    assert marriage["display_tier"] == "structure"
    assert "晚婚" not in marriage["display_verdict"]
    child_gate = out["sanguan"]["gates"]
    assert len(child_gate) == 1
    assert child_gate[0]["display_tier"] == "structure"
    hl = " ".join(out["highlights"])
    assert "晚婚" not in hl or "宫位" in hl


def test_highlights_coherent_after_stage() -> None:
    insight = apply_stage_presentation(
        {
            "guanming": {"summary": "体用清晰"},
            "duanshi": {
                "items": [
                    {
                        "topic": "父母",
                        "topic_id": "parents",
                        "publish_tier": "assert",
                        "display_verdict": "父母缘厚",
                        "level": "强",
                    }
                ],
                "liuqin": {},
            },
            "sanguan": {"gates": []},
            "day_master": "庚",
            "day_master_wuxing": "金",
            "day_master_strength": "平衡",
            "de_ling": {},
            "tong_gen": {},
        },
        34,
    )
    assert any("父母缘厚" in h for h in insight["highlights"])
    assert any("当前关切" in h for h in insight["highlights"])


def test_output_format_child_no_marriage_chapter() -> None:
    ls = build_lifestage(8)
    ins = {"life_stage": ls}
    text = build_output_format(ins)
    assert "## 感情婚姻" not in text
    assert "童年" in text
