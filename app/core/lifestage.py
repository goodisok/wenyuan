# -*- coding: utf-8 -*-
"""人生阶段：只定义关切权重，不删除断语。"""
from __future__ import annotations

from typing import Any, Literal

Priority = Literal["primary", "secondary", "hidden"]

TOPIC_LABELS: dict[str, str] = {
    "personality": "性格禀赋",
    "parents": "父母家庭",
    "education": "学业成长",
    "relationship": "感情婚姻",
    "career_wealth": "事业财运",
    "children": "子女",
    "siblings": "兄弟姊妹",
    "health": "健康身心",
}

DUANSHI_TOPIC: dict[str, str] = {
    "父母": "parents",
    "婚姻": "relationship",
    "财运": "career_wealth",
}

GATE_TOPIC: dict[str, str] = {
    "parents": "parents",
    "siblings": "siblings",
    "children": "children",
}

STAGES: list[dict[str, Any]] = [
    {"id": "child", "label": "童年", "min_age": 1, "max_age": 12},
    {"id": "teen", "label": "少年", "min_age": 13, "max_age": 18},
    {"id": "youth", "label": "青年", "min_age": 19, "max_age": 28},
    {"id": "prime", "label": "壮年", "min_age": 29, "max_age": 45},
    {"id": "midlife", "label": "中老年", "min_age": 46, "max_age": 60},
    {"id": "senior", "label": "晚年", "min_age": 61, "max_age": 150},
]

STAGE_PRIORITIES: dict[str, dict[str, Priority]] = {
    "child": {
        "personality": "primary",
        "parents": "primary",
        "health": "primary",
        "education": "primary",
        "siblings": "secondary",
        "relationship": "hidden",
        "career_wealth": "hidden",
        "children": "hidden",
    },
    "teen": {
        "education": "primary",
        "personality": "primary",
        "parents": "primary",
        "health": "secondary",
        "siblings": "secondary",
        "relationship": "secondary",
        "career_wealth": "secondary",
        "children": "hidden",
    },
    "youth": {
        "career_wealth": "primary",
        "relationship": "primary",
        "personality": "primary",
        "education": "secondary",
        "health": "secondary",
        "parents": "secondary",
        "siblings": "secondary",
        "children": "hidden",
    },
    "prime": {
        "career_wealth": "primary",
        "relationship": "primary",
        "children": "primary",
        "health": "secondary",
        "personality": "secondary",
        "parents": "secondary",
        "siblings": "secondary",
        "education": "hidden",
    },
    "midlife": {
        "health": "primary",
        "children": "primary",
        "career_wealth": "primary",
        "relationship": "secondary",
        "personality": "secondary",
        "parents": "secondary",
        "siblings": "secondary",
        "education": "hidden",
    },
    "senior": {
        "health": "primary",
        "children": "primary",
        "personality": "primary",
        "career_wealth": "secondary",
        "relationship": "secondary",
        "parents": "secondary",
        "siblings": "secondary",
        "education": "hidden",
    },
}


def stage_for_age(age: int) -> dict[str, Any]:
    a = max(1, int(age))
    for s in STAGES:
        if s["min_age"] <= a <= s["max_age"]:
            return dict(s)
    return dict(STAGES[-1])


def topic_priority(stage_id: str, topic_id: str) -> Priority:
    return STAGE_PRIORITIES.get(stage_id, {}).get(topic_id, "secondary")


def build_lifestage(age: int) -> dict[str, Any]:
    stage = stage_for_age(age)
    sid = stage["id"]
    priorities = STAGE_PRIORITIES.get(sid, {})
    focus_areas: list[dict[str, str]] = []
    for topic_id, label in TOPIC_LABELS.items():
        pri = priorities.get(topic_id, "secondary")
        if pri == "hidden":
            continue
        focus_areas.append({"id": topic_id, "label": label, "priority": pri})
    focus_areas.sort(key=lambda x: (0 if x["priority"] == "primary" else 1, x["label"]))
    primary = [x["label"] for x in focus_areas if x["priority"] == "primary"]
    return {
        "age": age,
        "stage_id": sid,
        "stage_label": stage["label"],
        "focus_areas": focus_areas,
        "focus_summary": "、".join(primary) if primary else "、".join(x["label"] for x in focus_areas[:4]),
    }
