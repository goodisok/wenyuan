# -*- coding: utf-8 -*-
"""BaziInsight 规则层摘要。"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from app.core.constants import DIZHI_CANGGAN, DIZHI_WUXING, TIANGAN_WUXING, WUXING_COLOR

WUXING_ORDER = ("木", "火", "土", "金", "水")
WUXING_GENERATES = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}


def _generates(a: str, b: str) -> bool:
    return WUXING_GENERATES.get(a) == b


def _supports(branch_wx: str, day_wx: str) -> bool:
    return branch_wx == day_wx or _generates(branch_wx, day_wx)


def _day_master_strength(chart: dict[str, Any]) -> str:
    meta = chart.get("meta", {})
    pillars = chart.get("pillars", [])
    day_wx = meta.get("day_master_wuxing", "")
    if not day_wx or len(pillars) < 4:
        return "平衡"

    month_dz = pillars[1]["dizhi"]["wuxing"]
    day_dz = pillars[2]["dizhi"]["wuxing"]
    day_master = meta.get("day_master", "")

    score = 0
    if _supports(month_dz, day_wx):
        score += 1
    if _supports(day_dz, day_wx):
        score += 1
    for p in pillars:
        if p["key"] == "day":
            continue
        tg = p["tiangan"]["name"]
        if TIANGAN_WUXING.get(tg) == day_wx:
            score += 1

    if score >= 2:
        return "偏强"
    if score == 0:
        return "偏弱"
    return "平衡"


def _current_dayun(dayun: list[dict[str, Any]]) -> dict[str, Any] | None:
    year = datetime.now().year
    for d in dayun:
        if d.get("start_year", 0) <= year <= d.get("end_year", 0):
            return {
                "ganzhi": d.get("ganzhi"),
                "start_year": d.get("start_year"),
                "end_year": d.get("end_year"),
            }
    return dayun[0] if dayun else None


def _current_liunian(dayun: list[dict[str, Any]]) -> dict[str, Any] | None:
    year = datetime.now().year
    for d in dayun:
        for ln in d.get("liunian", []):
            if ln.get("year") == year:
                return {"ganzhi": ln.get("ganzhi"), "year": ln.get("year")}
    return None


def build_insight(chart: dict[str, Any]) -> dict[str, Any]:
    meta = chart.get("meta", {})
    wx = chart.get("wuxing_stats", {})
    counts = {k: wx.get(k, 0) for k in WUXING_ORDER}
    max_val = max(counts.values()) if counts else 0
    min_val = min(counts.values()) if counts else 0
    strongest = [k for k, v in counts.items() if v == max_val and max_val > 0]
    weakest = [k for k, v in counts.items() if v == min_val]

    relations = chart.get("pillars_relations") or []

    return {
        "day_master": meta.get("day_master", ""),
        "day_master_wuxing": meta.get("day_master_wuxing", ""),
        "wuxing_counts": counts,
        "wuxing_strongest": strongest,
        "wuxing_weakest": weakest,
        "day_master_strength": _day_master_strength(chart),
        "day_master_strength_note": "倾向判断，非流派结论",
        "current_dayun": _current_dayun(chart.get("dayun", [])),
        "current_year_liunian": _current_liunian(chart.get("dayun", [])),
        "pillars_relations": relations,
    }


def suggest_l2_questions(insight: dict[str, Any]) -> list[str]:
    """L2 动态 chips（2～4 个）。"""
    questions: list[str] = []
    strongest = insight.get("wuxing_strongest") or []
    if strongest:
        questions.append(f"命局{strongest[0]}偏旺，日常宜如何调适？")
    weakest = insight.get("wuxing_weakest") or []
    if weakest and weakest[0] not in strongest:
        questions.append(f"五行{weakest[0]}较弱，可留意哪些方面？")
    cd = insight.get("current_dayun") or {}
    if cd.get("ganzhi"):
        questions.append(f"大运{cd['ganzhi']}阶段的重点是什么？")
    strength = insight.get("day_master_strength", "")
    if strength in ("偏强", "偏弱"):
        questions.append(f"日主{strength}，行事风格有何特点？")
    relations = insight.get("pillars_relations") or []
    if relations:
        questions.append(f"盘中有「{relations[0]}」，如何理解？")
    return questions[:4]
