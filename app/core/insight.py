# -*- coding: utf-8 -*-
"""BaziInsight 规则层摘要（子平综参）。"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from app.core.knowledge import retrieve as knowledge_retrieve
from app.core.mingli import analyze as mingli_analyze

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
    ml = mingli_analyze(chart)

    insight: dict[str, Any] = {
        "kernel": ml.get("kernel", "子平综参"),
        "sources": list(ml.get("sources", [])),
        "highlights": ml.get("highlights", []),
        "day_master": meta.get("day_master", ""),
        "day_master_wuxing": meta.get("day_master_wuxing", ""),
        "wuxing_counts": counts,
        "wuxing_strongest": strongest,
        "wuxing_weakest": weakest,
        "day_master_strength": ml.get("day_master_strength", "平衡"),
        "day_master_strength_note": ml.get("method_note", ""),
        "strength_score": ml.get("strength_score"),
        "stem_nature": ml.get("stem_nature"),
        "de_ling": ml.get("de_ling"),
        "tong_gen": ml.get("tong_gen"),
        "de_zhu": ml.get("de_zhu"),
        "climate": ml.get("climate"),
        "tiao_hou": ml.get("tiao_hou"),
        "qiongtong": ml.get("qiongtong"),
        "geju": ml.get("geju"),
        "yongshen": ml.get("yongshen"),
        "shensha": ml.get("shensha"),
        "shishen_summary": ml.get("shishen_summary"),
        "changsheng_map": ml.get("changsheng_map"),
        "pattern": ml.get("pattern"),
        "mingli": ml,
        "current_dayun": _current_dayun(chart.get("dayun", [])),
        "current_year_liunian": _current_liunian(chart.get("dayun", [])),
        "pillars_relations": relations,
    }
    citations = knowledge_retrieve(chart, insight)
    insight["citations"] = citations
    return insight


def suggest_l2_questions(insight: dict[str, Any]) -> list[str]:
    questions: list[str] = []
    geju = insight.get("geju") or {}
    if geju.get("type"):
        questions.append(f"「{geju['type']}」对我事业与人事有何倾向？")
    if insight.get("tiao_hou"):
        questions.append("此盘寒暖调候上，日常宜注意什么？")
    ys = insight.get("yongshen") or {}
    if ys.get("summary"):
        questions.append("喜用倾向与当前大运是否相合？")
    cd = insight.get("current_dayun") or {}
    if cd.get("ganzhi"):
        questions.append(f"大运{cd['ganzhi']}阶段的重点是什么？")
    tg = insight.get("tong_gen") or {}
    if tg.get("summary") == "无根":
        questions.append("日主根气较弱，行事风格有何特点？")
    strongest = insight.get("wuxing_strongest") or []
    if strongest:
        questions.append(f"命局{strongest[0]}偏旺，如何调适？")
    return questions[:5]
