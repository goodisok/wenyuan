# -*- coding: utf-8 -*-
"""
神煞（精简版）· 仅保留有五行原理支撑的三种

命理断事应以五行生克制化、格局旺衰、刑冲合害为根本，
神煞仅作传统备注，不作为分析依据。

保留原则：
- 禄神：十二长生"临官"之位，本质是五行旺衰
- 将星：三合局中字，地支结构推导
- 驿马：三合局对冲位，地支结构推导

其余神煞（天乙贵人、文昌、桃花、华盖、天月德、红艳、亡神等）
均为经验归纳，无底层五行逻辑，已移除。
"""
from __future__ import annotations

from typing import Any

KERNEL = "三命通会"

# ── 禄神（日干查地支）：十二长生"临官"位 ──
LUSHEN: dict[str, str] = {
    "甲": "寅", "乙": "卯", "丙": "巳", "丁": "午", "戊": "巳",
    "己": "午", "庚": "申", "辛": "酉", "壬": "亥", "癸": "子",
}

# ── 将星（年支或日支查）：三合局中字 ──
JIANGXING: dict[str, str] = {
    "寅": "午", "午": "午", "戌": "午",
    "申": "子", "子": "子", "辰": "子",
    "巳": "酉", "酉": "酉", "丑": "酉",
    "亥": "卯", "卯": "卯", "未": "卯",
}

# ── 驿马（年支或日支查）：三合局对冲位 ──
YIMA: dict[str, str] = {
    "申": "寅", "子": "寅", "辰": "寅",
    "寅": "申", "午": "申", "戌": "申",
    "巳": "亥", "酉": "亥", "丑": "亥",
    "亥": "巳", "卯": "巳", "未": "巳",
}

SHENSHA_NOTE: dict[str, str] = {
    "禄神": "临官之位，五行旺地；主福禄所归（十二长生）",
    "将星": "三合中字，气势集中；主领导有势（三命通会）",
    "驿马": "三合对冲，主动之象；主奔波变动（三命通会）",
}

SHENSHA_MODERN: dict[str, str] = {
    "禄神": "稳定收入、职业福禄",
    "将星": "管理能力、领导潜力",
    "驿马": "出差调动、人生变动",
}


def _branches(chart: dict[str, Any]) -> list[tuple[str, str]]:
    pillars = chart.get("pillars", [])
    out: list[tuple[str, str]] = []
    for p in pillars:
        dz = p.get("dizhi", {}).get("name", "")
        if dz:
            out.append((p.get("label", ""), dz))
    return out


def _find_in_branches(target: str, branches: list[tuple[str, str]]) -> list[str]:
    return [label for label, dz in branches if dz == target]


def analyze(chart: dict[str, Any]) -> dict[str, Any]:
    meta = chart.get("meta", {})
    pillars = chart.get("pillars", [])
    day_stem = meta.get("day_master", "")
    if not day_stem or len(pillars) < 4:
        return {"kernel": KERNEL, "items": [], "summary": "", "count": 0,
                "note": "神煞为传统备注，不作分析依据。应以五行生克制化、格局旺衰为根本判断。"}

    day_branch = pillars[2]["dizhi"]["name"]
    year_branch = pillars[0]["dizhi"]["name"]
    branches = _branches(chart)

    items: list[dict[str, str]] = []

    # ── 禄神（日干查地支）──
    ls = LUSHEN.get(day_stem, "")
    if ls:
        hits = _find_in_branches(ls, branches)
        if hits:
            items.append({
                "name": "禄神",
                "position": "、".join(hits),
                "note": SHENSHA_NOTE["禄神"],
                "modern": SHENSHA_MODERN["禄神"],
            })

    # ── 将星（日支优先，年支备选）──
    for base_name, base_branch in (("日支", day_branch), ("年支", year_branch)):
        jx = JIANGXING.get(base_branch, "")
        if jx and _find_in_branches(jx, branches):
            items.append({
                "name": "将星",
                "position": f"以{base_name}查遇{jx}",
                "note": SHENSHA_NOTE["将星"],
                "modern": SHENSHA_MODERN["将星"],
            })
            break

    # ── 驿马（日支优先，年支备选）──
    for base_name, base_branch in (("日支", day_branch), ("年支", year_branch)):
        ym = YIMA.get(base_branch, "")
        if ym and _find_in_branches(ym, branches):
            items.append({
                "name": "驿马",
                "position": f"以{base_name}查遇{ym}",
                "note": SHENSHA_NOTE["驿马"],
                "modern": SHENSHA_MODERN["驿马"],
            })
            break

    summary = "、".join(i["name"] for i in items) if items else "未显"
    
    by_pillar: dict[str, list[str]] = {k: [] for k in ("year", "month", "day", "hour")}
    label_to_key = {"年柱": "year", "月柱": "month", "日柱": "day", "时柱": "hour"}
    for it in items:
        pos = it.get("position", "")
        for label, key in label_to_key.items():
            if label in pos and it["name"] not in by_pillar[key]:
                by_pillar[key].append(it["name"])

    return {
        "kernel": KERNEL,
        "items": items,
        "by_pillar": by_pillar,
        "summary": summary,
        "count": len(items),
        "note": "神煞为传统备注，不作分析依据。应以五行生克制化、格局旺衰为根本判断。",
    }
