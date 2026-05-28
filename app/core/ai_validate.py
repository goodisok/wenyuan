# -*- coding: utf-8 -*-
"""AI 解读边界校验：应期年份、未发布断事等。"""
from __future__ import annotations

import re
from typing import Any

_YEAR_RE = re.compile(r"(19|20)\d{2}\s*年?")
_STRICT_TOPICS = ("婚姻", "财运", "兄弟", "子女", "姊妹", "父母")

_GATE_TOPIC = {
    "parents": "父母",
    "siblings": "兄弟",
    "children": "子女",
}


def collect_dayun_years(chart: dict[str, Any]) -> list[int]:
    years: set[int] = set()
    for dy in chart.get("dayun") or []:
        start = int(dy.get("start_year") or 0)
        end = int(dy.get("end_year") or 0)
        if start and end >= start:
            years.update(range(start, end + 1))
    return sorted(years)


def collect_citable_years(insight: dict[str, Any], chart: dict[str, Any] | None = None) -> list[int]:
    """直断应期 ∪ 大运区间 — 供提示词与校验共用。"""
    if insight.get("citable_years") and chart is None:
        return list(insight["citable_years"])
    years = set(collect_allowed_years(insight))
    if chart is not None:
        years.update(collect_dayun_years(chart))
    return sorted(years)


def collect_allowed_years(insight: dict[str, Any]) -> list[int]:
    """直断应期窗口内的公元年份（供 AI 提示词锚定）。"""
    years: set[int] = set()
    for lo, hi in _collect_year_windows(insight):
        for y in range(lo, hi + 1):
            years.add(y)
    return sorted(years)


def _collect_year_windows(insight: dict[str, Any]) -> list[tuple[int, int]]:
    windows: list[tuple[int, int]] = []
    ds = insight.get("duanshi") or {}
    for item in ds.get("items") or []:
        if item.get("display_tier") != "assert":
            continue
        for w in item.get("windows") or []:
            years = str(w.get("years", ""))
            m = re.search(r"((?:19|20)\d{2})\s*[-–—~至到]\s*((?:19|20)\d{2})", years)
            if m:
                windows.append((int(m.group(1)), int(m.group(2))))
                continue
            m2 = re.search(r"(?:19|20)\d{2}", years)
            if m2:
                y = int(m2.group(0))
                windows.append((y, y))
    sg = insight.get("sanguan") or {}
    for g in sg.get("gates") or []:
        if g.get("display_tier") != "assert":
            continue
        for w in g.get("windows") or []:
            years = str(w.get("years", ""))
            m = re.search(r"((?:19|20)\d{2})\s*[-–—~至到]\s*((?:19|20)\d{2})", years)
            if m:
                windows.append((int(m.group(1)), int(m.group(2))))
                continue
            m2 = re.search(r"(?:19|20)\d{2}", years)
            if m2:
                y = int(m2.group(0))
                windows.append((y, y))
    return windows


def _assert_topics(insight: dict[str, Any]) -> set[str]:
    topics: set[str] = set()
    for item in (insight.get("duanshi") or {}).get("items") or []:
        if item.get("display_tier") == "assert":
            t = item.get("topic")
            if t:
                topics.add(str(t))
    for g in (insight.get("sanguan") or {}).get("gates") or []:
        if g.get("display_tier") == "assert":
            tid = _GATE_TOPIC.get(str(g.get("id", "")))
            if tid:
                topics.add(tid)
    return topics


def validate_analysis(text: str, insight: dict[str, Any] | None) -> dict[str, Any]:
    """返回 warnings 列表；不修改原文。"""
    if not text or not insight:
        return {"ok": True, "warnings": []}
    warnings: list[str] = []
    allowed = set(collect_allowed_years(insight))
    published = _assert_topics(insight)
    strength = str(insight.get("day_master_strength") or "")
    exempt_years: set[int] = set()
    if insight.get("birth_year"):
        exempt_years.add(int(insight["birth_year"]))

    for m in _YEAR_RE.finditer(text):
        y = int(m.group(0)[:4].replace("年", ""))
        if y in exempt_years:
            continue
        if not allowed:
            warnings.append(f"无可引直断年份却提及 {y}")
            continue
        if y not in allowed:
            warnings.append(f"提及年份 {y} 不在直断应期窗口内")

    if strength in ("平衡", "中和") and ("身强" in text or "身弱" in text):
        warnings.append(f"规则层为{strength}，勿写身强/身弱/偏强/偏弱")
    elif "身强" in text and "身弱" in text:
        warnings.append("同时出现身强与身弱，表述须统一")

    if "婚姻" not in published and re.search(r"(必离|必定离婚|婚变|克妻|克夫|必.*再婚)", text):
        warnings.append("规则层无婚姻直断，却出现具体婚变断辞")
    if "财运" not in published and re.search(
        r"(必.*破财|必.*发财|必.*暴富|必.*负债|大财|财富爆发|财务自由|倾家荡产|一夜暴富)",
        text,
    ):
        warnings.append("规则层无财运直断，却出现具体财禄断辞")
    if "父母" not in published and re.search(
        r"(父母[^。，；]{0,12}(必|定|早亡|克害)|"
        r"(克|刑|害|冲)[^。，；]{0,6}父母|父[^。，；]{0,6}(早亡|必克)|母[^。，；]{0,6}(早亡|必克))",
        text,
    ):
        warnings.append("规则层无父母直断，却出现具体父母吉凶断辞")
    for topic in ("兄弟", "子女"):
        if topic not in published and re.search(
            rf"({topic}|兄弟姊妹).{{0,8}}(必|定|克|夭|无缘)", text
        ):
            warnings.append(f"规则层无{topic}直断，却出现具体六亲断辞")

    return {"ok": len(warnings) == 0, "warnings": warnings[:8]}
