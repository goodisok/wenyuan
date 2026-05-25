# -*- coding: utf-8 -*-
"""结构化典籍语料库加载与匹配。"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from knowledge.corpus.wiki_loader import load_wiki_entries

CORPUS_DIR = Path(__file__).resolve().parent / "data"

MONTH_NAMES = {
    "寅": "正月", "卯": "二月", "辰": "三月", "巳": "四月", "午": "五月", "未": "六月",
    "申": "七月", "酉": "八月", "戌": "九月", "亥": "十月", "子": "十一月", "丑": "十二月",
}


def _load_json(name: str) -> list[dict[str, Any]]:
    path = CORPUS_DIR / name
    if not path.is_file():
        return []
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else []


def _qiongtong_entries() -> list[dict[str, Any]]:
    from app.core.qiongtong import QIONGTONG

    out: list[dict[str, Any]] = []
    for (stem, branch), hint in QIONGTONG.items():
        month_label = MONTH_NAMES.get(branch, branch)
        out.append({
            "id": f"qt_{stem}_{branch}",
            "source": "穷通宝鉴",
            "book": "穷通宝鉴",
            "chapter": f"{stem}日{month_label}（{branch}月）",
            "kind": "tiao_hou",
            "tags": ["tiao_hou", f"stem:{stem}", f"month:{branch}"],
            "match": {"day_stem": stem, "month_branch": branch},
            "text": f"论{stem}日生于{month_label}：{hint}。调候为急，不可专论旺衰而忽寒暖。",
        })
    return out


@lru_cache(maxsize=1)
def load_all() -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    entries.extend(_qiongtong_entries())
    for fname in (
        "ditiansui.json",
        "ziping.json",
        "yuanhai.json",
        "sanming.json",
        "qianli_cases.json",
    ):
        entries.extend(_load_json(fname))
    entries.extend(load_wiki_entries())
    return entries


def corpus_stats() -> dict[str, int]:
    items = load_all()
    by_book: dict[str, int] = {}
    for e in items:
        book = str(e.get("book") or e.get("source") or "unknown")
        by_book[book] = by_book.get(book, 0) + 1
    return {"total": len(items), "by_book": by_book}


def _score_entry(
    entry: dict[str, Any],
    tags: set[str],
    *,
    day_stem: str,
    month_branch: str,
    geju_type: str,
    dominant_shishen: str | None,
    strength: str,
) -> int:
    score = 0
    entry_tags = set(entry.get("tags") or [])
    score += len(entry_tags & tags) * 3

    match = entry.get("match") or {}
    if match.get("day_stem") == day_stem:
        score += 4
    if match.get("month_branch") == month_branch:
        score += 4
    if day_stem and month_branch:
        if match.get("day_stem") == day_stem and match.get("month_branch") == month_branch:
            score += 12
    if geju_type and (entry.get("geju") == geju_type or match.get("geju") == geju_type):
        score += 10
    if dominant_shishen:
        if entry.get("shishen") == dominant_shishen:
            score += 6
        if f"ss:{dominant_shishen}" in entry_tags:
            score += 6
    if geju_type and f"geju:{geju_type}" in entry_tags:
        score += 8
    if strength and match.get("strength") == strength:
        score += 3
    if entry.get("kind") == "case" and (geju_type or dominant_shishen):
        score += 2
    if "always" in entry_tags:
        score += 1
    return score


def match_corpus(
    tags: set[str],
    *,
    day_stem: str = "",
    month_branch: str = "",
    geju_type: str = "",
    dominant_shishen: str | None = None,
    strength: str = "",
    limit: int = 15,
    min_score: int = 3,
) -> list[dict[str, str]]:
    """按命盘特征打分检索语料，返回 citation 列表。"""
    ranked: list[tuple[int, dict[str, Any]]] = []
    for entry in load_all():
        sc = _score_entry(
            entry, tags,
            day_stem=day_stem,
            month_branch=month_branch,
            geju_type=geju_type,
            dominant_shishen=dominant_shishen,
            strength=strength,
        )
        if sc >= min_score:
            ranked.append((sc, entry))

    ranked.sort(key=lambda x: (-x[0], str(x[1].get("id", ""))))
    out: list[dict[str, str]] = []
    seen: set[str] = set()
    for sc, entry in ranked:
        eid = str(entry.get("id", ""))
        if eid in seen:
            continue
        seen.add(eid)
        item: dict[str, str] = {
            "id": eid,
            "source": str(entry.get("source", "")),
            "text": str(entry.get("text", "")),
            "score": str(sc),
        }
        if entry.get("chapter"):
            item["chapter"] = str(entry["chapter"])
        if entry.get("kind"):
            item["kind"] = str(entry["kind"])
        if entry.get("commentary"):
            item["commentary"] = str(entry["commentary"])
        if entry.get("pillars"):
            item["pillars"] = str(entry["pillars"])
        out.append(item)
        if len(out) >= limit:
            break
    return out
