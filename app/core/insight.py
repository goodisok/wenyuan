# -*- coding: utf-8 -*-
"""BaziInsight 规则层摘要（子平综参）。"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from app.core.knowledge import get_corpus_meta, retrieve as knowledge_retrieve
from app.core.mingli import analyze as mingli_analyze
from app.core.reading import apply_stage_presentation, suggest_l2_questions

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
        "method_note": ml.get("method_note", ""),
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
        "duanshi": ml.get("duanshi"),
        "sanguan": ml.get("sanguan"),
        "guanming": ml.get("guanming"),
        "shishen_summary": ml.get("shishen_summary"),
        "dayun_detail": ml.get("dayun_detail"),
        "changsheng_map": ml.get("changsheng_map"),
        "pattern": ml.get("pattern"),
        "mingli": ml,
        "current_dayun": _current_dayun(chart.get("dayun", [])),
        "current_year_liunian": _current_liunian(chart.get("dayun", [])),
        "pillars_relations": relations,
    }
    citations = knowledge_retrieve(chart, insight)
    insight["citations"] = citations
    insight["corpus_meta"] = get_corpus_meta()
    age = int(meta.get("age") or 1)
    birth_year = None
    solar = (meta.get("birth_time") or {}).get("solar") or ""
    if len(solar) >= 4 and solar[:4].isdigit():
        birth_year = int(solar[:4])
    insight = apply_stage_presentation(insight, age)
    if birth_year:
        insight["birth_year"] = birth_year
    insight["l2_questions"] = suggest_l2_questions(insight)
    from app.core.ai_validate import collect_allowed_years, collect_dayun_years

    insight["citable_years"] = sorted(
        set(collect_allowed_years(insight)) | set(collect_dayun_years(chart))
    )
    if meta.get("source") == "gz_fixture":
        insight["is_classical_fixture"] = True
    from app.core.classical_ref import find_similar

    if not insight.get("is_classical_fixture"):
        insight["classical_refs"] = find_similar(chart, limit=2, min_score=28)
    else:
        insight["classical_refs"] = []
    return insight


def public_insight(insight: dict[str, Any]) -> dict[str, Any]:
    """返回客户端可见的最小 insight：运限摘要 + 通用追问 chips。

    完整规则层（观命、断事、典籍等）仅在服务端供 AI 使用，不返回浏览器。
    """
    from app.core.reading import public_l2_questions

    age = int(insight.get("age") or insight.get("life_stage", {}).get("age") or 1)
    return {
        "current_dayun": insight.get("current_dayun"),
        "current_year_liunian": insight.get("current_year_liunian"),
        "l2_questions": public_l2_questions(age),
    }


def ensure_ai_insight(chart: dict[str, Any], insight: dict[str, Any] | None = None) -> dict[str, Any]:
    """AI 请求始终使用服务端完整规则层。

    客户端传入的 insight（public 子集）会被忽略，避免与规则层脱节。
    """
    return build_insight(chart)


def ensure_citations(chart: dict[str, Any], insight: dict[str, Any] | None) -> dict[str, Any]:
    """兼容旧调用：AI 路由请用 ensure_ai_insight。"""
    return ensure_ai_insight(chart, insight)
