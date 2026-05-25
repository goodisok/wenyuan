# -*- coding: utf-8 -*-
"""典籍知识检索：按命盘特征选取参考片段，供规则层与 AI 锚定。"""
from __future__ import annotations

from typing import Any

from app.core.qiongtong import lookup as qiongtong_lookup
from knowledge.snippets import GEJU_SNIPPETS, SHISHEN_SNIPPETS, SNIPPETS, STEM_MONTH_NOTES

MAX_CITATIONS = 12


def _dominant_shishen(pillars: list[dict]) -> str | None:
    counts: dict[str, int] = {}
    for p in pillars:
        ss = p.get("shishen", "")
        if ss and ss != "日主":
            counts[ss] = counts.get(ss, 0) + 1
        for cg in p.get("dizhi", {}).get("canggan", []):
            css = cg.get("shishen", "")
            if css:
                counts[css] = counts.get(css, 0) + 1
    if not counts:
        return None
    return max(counts, key=counts.get)


def _append(out: list[dict[str, str]], seen: set[str], item: dict[str, str]) -> None:
    sid = item.get("id", "")
    if sid in seen:
        return
    seen.add(sid)
    out.append(item)


def retrieve(chart: dict[str, Any], insight: dict[str, Any] | None = None) -> list[dict[str, str]]:
    """返回去重后的典籍片段，每项 {source, text, id}。"""
    insight = insight or chart.get("insight") or {}
    meta = chart.get("meta", {})
    pillars = chart.get("pillars", [])
    day_stem = meta.get("day_master", "")
    month_branch = pillars[1]["dizhi"]["name"] if len(pillars) > 1 else ""

    tags: set[str] = {"always"}
    if insight.get("tiao_hou") or (insight.get("qiongtong") or {}).get("hint"):
        tags.add("tiao_hou")
    if insight.get("day_master_strength") or insight.get("strength_score") is not None:
        tags.add("strength")
    if chart.get("pillars_relations") or insight.get("pillars_relations"):
        tags.add("relations")
        tags.add("wuxing")
    geju = insight.get("geju") or {}
    if geju.get("type"):
        tags.add("geju")
        tags.add("pattern")
    body_pat = insight.get("pattern") or {}
    if body_pat.get("type"):
        tags.add("pattern")
    if insight.get("yongshen"):
        tags.add("yongshen")
    shensha = insight.get("shensha") or {}
    if shensha.get("items"):
        tags.add("shensha")
    dom = _dominant_shishen(pillars)
    if dom:
        tags.add("shishen")
    if chart.get("dayun"):
        tags.add("dayun")

    seen: set[str] = set()
    out: list[dict[str, str]] = []

    qt = qiongtong_lookup(day_stem, month_branch)
    if qt.get("hint"):
        _append(out, seen, {
            "id": f"qiongtong_{day_stem}_{month_branch}",
            "source": "穷通宝鉴",
            "text": qt["hint"],
        })

    key = (day_stem, month_branch)
    if key in STEM_MONTH_NOTES:
        src, text = STEM_MONTH_NOTES[key]
        _append(out, seen, {"id": f"month_{day_stem}_{month_branch}", "source": src, "text": text})

    geju_type = geju.get("type", "")
    if geju_type in GEJU_SNIPPETS:
        g = GEJU_SNIPPETS[geju_type]
        _append(out, seen, {"id": str(g["id"]), "source": str(g["source"]), "text": str(g["text"])})

    if dom and dom in SHISHEN_SNIPPETS:
        _append(out, seen, {
            "id": f"ss_{dom}",
            "source": "渊海子平",
            "text": f"{dom}：{SHISHEN_SNIPPETS[dom]}",
        })

    for snip in SNIPPETS:
        snip_tags = set(snip.get("tags") or [])
        if not (snip_tags & tags):
            continue
        _append(out, seen, {
            "id": str(snip["id"]),
            "source": str(snip["source"]),
            "text": str(snip["text"]),
        })

    return out[:MAX_CITATIONS]


def format_for_ai(citations: list[dict[str, str]]) -> str:
    if not citations:
        return ""
    lines = ["【典籍参考摘要（批命须参此锚定，可标注出处）】"]
    for c in citations:
        lines.append(f"《{c['source']}》{c['text']}")
    return "\n".join(lines)
