# -*- coding: utf-8 -*-
"""BaziInsight 规则层摘要（滴天髓阐微内核）。"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from app.core.ditiansui import analyze as ditiansui_analyze

WUXING_ORDER = ("木", "火", "土", "金", "水")


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
    dts = ditiansui_analyze(chart)

    return {
        "kernel": dts.get("kernel", "滴天髓阐微"),
        "day_master": meta.get("day_master", ""),
        "day_master_wuxing": meta.get("day_master_wuxing", ""),
        "wuxing_counts": counts,
        "wuxing_strongest": strongest,
        "wuxing_weakest": weakest,
        "day_master_strength": dts.get("day_master_strength", "平衡"),
        "day_master_strength_note": dts.get("method_note", "倾向判断，非流派结论"),
        "strength_score": dts.get("strength_score"),
        "stem_nature": dts.get("stem_nature"),
        "de_ling": dts.get("de_ling"),
        "tong_gen": dts.get("tong_gen"),
        "de_zhu": dts.get("de_zhu"),
        "climate": dts.get("climate"),
        "tiao_hou": dts.get("tiao_hou"),
        "changsheng_map": dts.get("changsheng_map"),
        "pattern": dts.get("pattern"),
        "ditiansui": dts,
        "current_dayun": _current_dayun(chart.get("dayun", [])),
        "current_year_liunian": _current_liunian(chart.get("dayun", [])),
        "pillars_relations": relations,
    }


def suggest_l2_questions(insight: dict[str, Any]) -> list[str]:
    questions: list[str] = []
    tiao = insight.get("tiao_hou")
    if tiao:
        questions.append(f"依滴天髓，此盘调候如何理解？")
    pat = insight.get("pattern") or {}
    if pat.get("type") and pat["type"] != "正格":
        questions.append(f"格局倾向「{pat['type']}」，对我意味着什么？")
    cd = insight.get("current_dayun") or {}
    if cd.get("ganzhi"):
        questions.append(f"大运{cd['ganzhi']}阶段的重点是什么？")
    tg = insight.get("tong_gen") or {}
    if tg.get("summary") == "无根":
        questions.append("日主无根，行事上宜注意什么？")
    strongest = insight.get("wuxing_strongest") or []
    if strongest:
        questions.append(f"命局{strongest[0]}偏旺，日常宜如何调适？")
    weakest = insight.get("wuxing_weakest") or []
    if weakest and weakest[0] not in strongest:
        questions.append(f"五行{weakest[0]}较弱，可留意哪些方面？")
    return questions[:4]
