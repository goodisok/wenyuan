# -*- coding: utf-8 -*-
"""典籍知识检索：语料库 + 摘要片段混合检索。"""
from __future__ import annotations

from typing import Any

from knowledge.corpus.loader import corpus_stats, match_corpus
from knowledge.snippets import GEJU_SNIPPETS, SHISHEN_SNIPPETS, SNIPPETS

MAX_CITATIONS = 18


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


def _build_tags(insight: dict[str, Any], chart: dict[str, Any], pillars: list[dict]) -> set[str]:
    tags: set[str] = {"always"}
    if insight.get("tiao_hou") or (insight.get("qiongtong") or {}).get("hint"):
        tags.add("tiao_hou")
        tags.add("qiong-tong")
    if insight.get("day_master_strength") or insight.get("strength_score") is not None:
        tags.add("strength")
        tags.add("wang-shuai")
    if chart.get("pillars_relations") or insight.get("pillars_relations"):
        tags.add("relations")
        tags.add("wuxing")
    geju = insight.get("geju") or {}
    if geju.get("type"):
        tags.add("geju")
        tags.add("pattern")
        tags.add("ge-ju")
        tags.add(f"geju:{geju['type']}")
    body_pat = insight.get("pattern") or {}
    if body_pat.get("type"):
        tags.add("pattern")
    if insight.get("yongshen"):
        tags.add("yongshen")
    shensha = insight.get("shensha") or {}
    if shensha.get("items"):
        tags.add("shensha")
        tags.add("shen-sha")
    dom = _dominant_shishen(pillars)
    if dom:
        tags.add("shishen")
        tags.add("shi-shen")
        tags.add(f"ss:{dom}")
    if chart.get("dayun"):
        tags.add("dayun")
        tags.add("da-yun")
    if insight.get("duanshi"):
        tags.add("duanshi")
    sg = insight.get("sanguan") or {}
    if sg.get("gates"):
        tags.add("sanguan")
    if sg.get("chuan"):
        tags.add("chuan")
    meta = chart.get("meta", {})
    day_stem = meta.get("day_master", "")
    month_branch = pillars[1]["dizhi"]["name"] if len(pillars) > 1 else ""
    if day_stem:
        tags.add(f"stem:{day_stem}")
    if month_branch:
        tags.add(f"month:{month_branch}")
    return tags


def _append_snippets(
    out: list[dict[str, str]],
    seen: set[str],
    tags: set[str],
    geju_type: str,
    dom: str | None,
) -> None:
    if geju_type in GEJU_SNIPPETS:
        g = GEJU_SNIPPETS[geju_type]
        sid = str(g["id"])
        if sid not in seen:
            seen.add(sid)
            out.append({"id": sid, "source": str(g["source"]), "text": str(g["text"]), "kind": "snippet"})

    if dom and dom in SHISHEN_SNIPPETS:
        sid = f"ss_{dom}"
        if sid not in seen:
            seen.add(sid)
            out.append({
                "id": sid,
                "source": "渊海子平",
                "text": f"{dom}：{SHISHEN_SNIPPETS[dom]}",
                "kind": "snippet",
            })

    for snip in SNIPPETS:
        snip_tags = set(snip.get("tags") or [])
        if not (snip_tags & tags):
            continue
        sid = str(snip["id"])
        if sid in seen:
            continue
        seen.add(sid)
        out.append({
            "id": sid,
            "source": str(snip["source"]),
            "text": str(snip["text"]),
            "kind": "snippet",
        })


def retrieve(chart: dict[str, Any], insight: dict[str, Any] | None = None) -> list[dict[str, str]]:
    """混合检索：语料库打分优先，摘要片段补充。"""
    insight = insight or chart.get("insight") or {}
    meta = chart.get("meta", {})
    pillars = chart.get("pillars", [])
    day_stem = meta.get("day_master", "")
    month_branch = pillars[1]["dizhi"]["name"] if len(pillars) > 1 else ""
    geju = insight.get("geju") or {}
    geju_type = geju.get("type", "")
    dom = _dominant_shishen(pillars)
    strength = insight.get("day_master_strength", "")
    tags = _build_tags(insight, chart, pillars)

    corpus_hits = match_corpus(
        tags,
        day_stem=day_stem,
        month_branch=month_branch,
        geju_type=geju_type,
        dominant_shishen=dom,
        strength=strength,
        limit=MAX_CITATIONS,
        min_score=4,
    )

    seen = {c["id"] for c in corpus_hits}
    out = list(corpus_hits)

    if len(out) < MAX_CITATIONS:
        _append_snippets(out, seen, tags, geju_type, dom)

    return out[:MAX_CITATIONS]


def get_corpus_meta() -> dict[str, Any]:
    return corpus_stats()


def format_for_ai(citations: list[dict[str, str]]) -> str:
    if not citations:
        return ""
    lines = ["【典籍语料（批命须参此锚定，重要论断请标注书名章节）】"]
    for c in citations:
        src = c.get("source", "")
        chapter = c.get("chapter", "")
        prefix = f"《{src}》"
        if chapter:
            prefix += f"（{chapter}）"
        text = c.get("text", "")
        if c.get("kind") == "case" and c.get("pillars"):
            text = f"【例 {c['pillars']}】{text}"
        if c.get("commentary"):
            text = f"{text} 按：{c['commentary']}"
        lines.append(f"{prefix}{text}")
    return "\n".join(lines)
