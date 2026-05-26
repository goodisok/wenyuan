# -*- coding: utf-8 -*-
"""AI 解读边界校验：应期年份、未发布断事等。"""
from __future__ import annotations

import re
from typing import Any

_YEAR_RE = re.compile(r"(19|20)\d{2}\s*年?")
_UNPUBLISHED_TOPICS = ("婚姻", "财运", "兄弟", "子女", "姊妹")


def _collect_year_windows(insight: dict[str, Any]) -> list[tuple[int, int]]:
    windows: list[tuple[int, int]] = []
    ds = insight.get("duanshi") or {}
    for item in ds.get("items") or []:
        for w in item.get("windows") or []:
            years = str(w.get("years", ""))
            m = re.search(r"(19|20)\d{2}\s*[-–—~至到]\s*(19|20)\d{2}", years)
            if m:
                windows.append((int(m.group(1)), int(m.group(2))))
                continue
            m2 = re.search(r"(19|20)\d{2}", years)
            if m2:
                y = int(m2.group(0))
                windows.append((y, y))
    sg = insight.get("sanguan") or {}
    for g in sg.get("gates") or []:
        for w in g.get("windows") or []:
            years = str(w.get("years", ""))
            m = re.search(r"(19|20)\d{2}\s*[-–—~至到]\s*(19|20)\d{2}", years)
            if m:
                windows.append((int(m.group(1)), int(m.group(2))))
    return windows


def _published_topics(insight: dict[str, Any]) -> set[str]:
    topics: set[str] = set()
    for item in (insight.get("duanshi") or {}).get("items") or []:
        t = item.get("topic")
        if t:
            topics.add(str(t))
    for g in (insight.get("sanguan") or {}).get("gates") or []:
        name = str(g.get("name", ""))
        if "父母" in name or g.get("id") == "parents":
            topics.add("父母")
    return topics


def validate_analysis(text: str, insight: dict[str, Any] | None) -> dict[str, Any]:
    """返回 warnings 列表；不修改原文。"""
    if not text or not insight:
        return {"ok": True, "warnings": []}
    warnings: list[str] = []
    windows = _collect_year_windows(insight)
    published = _published_topics(insight)

    for m in _YEAR_RE.finditer(text):
        y = int(m.group(0)[:4].replace("年", ""))
        if not windows:
            continue
        if not any(lo <= y <= hi for lo, hi in windows):
            warnings.append(f"提及年份 {y} 不在规则层应期窗口内")

    for topic in _UNPUBLISHED_TOPICS:
        if topic in published:
            continue
        if topic == "婚姻" and re.search(r"(离婚|婚变|克妻|克夫|再婚)", text):
            warnings.append("规则层未发布婚姻断语，却出现具体婚变断辞")
        if topic == "财运" and re.search(r"(破财|大发|暴富|负债)", text):
            warnings.append("规则层未发布财运断语，却出现具体财禄断辞")
        if topic in ("兄弟", "子女", "姊妹") and re.search(rf"({topic}|兄弟姊妹|子女).{{0,8}}(克|夭|无缘|离异)", text):
            warnings.append(f"规则层未发布{topic}相关高置信断语，却出现具体六亲断辞")

    return {"ok": len(warnings) == 0, "warnings": warnings[:8]}
