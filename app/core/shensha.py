# -*- coding: utf-8 -*-
"""三命通会 · 常用神煞（辅助参考，不作单论）。"""
from __future__ import annotations

from typing import Any

KERNEL = "三命通会"

# 天乙贵人：日干查地支
TIANYI: dict[str, tuple[str, ...]] = {
    "甲": ("丑", "未"), "戊": ("丑", "未"), "庚": ("丑", "未"),
    "乙": ("子", "申"), "己": ("子", "申"),
    "丙": ("亥", "酉"), "丁": ("亥", "酉"),
    "壬": ("卯", "巳"), "癸": ("卯", "巳"),
    "辛": ("寅", "午"),
}

# 文昌：日干查地支
WENCHANG: dict[str, str] = {
    "甲": "巳", "乙": "午", "丙": "申", "丁": "酉", "戊": "申",
    "己": "酉", "庚": "亥", "辛": "子", "壬": "寅", "癸": "卯",
}

# 驿马、桃花、华盖：以年支或日支查
YIMA = {"申": "寅", "子": "寅", "辰": "寅", "寅": "申", "午": "申", "戌": "申",
        "巳": "亥", "酉": "亥", "丑": "亥", "亥": "巳", "卯": "巳", "未": "巳"}
TAOHUA = {"申": "酉", "子": "酉", "辰": "酉", "寅": "卯", "午": "卯", "戌": "卯",
          "巳": "午", "酉": "午", "丑": "午", "亥": "子", "卯": "子", "未": "子"}
HUAGAI = {"申": "辰", "子": "辰", "辰": "辰", "寅": "戌", "午": "戌", "戌": "戌",
          "巳": "丑", "酉": "丑", "丑": "丑", "亥": "未", "卯": "未", "未": "未"}

SHENSHA_DESC: dict[str, str] = {
    "天乙贵人": "逢凶化吉，贵人相助（三命通会）",
    "文昌": "聪明好学，文才出众（三命通会）",
    "驿马": "主动迁移，奔波变动（三命通会）",
    "桃花": "异性缘、才艺人缘（三命通会）",
    "华盖": "孤高学术、宗教艺术（三命通会）",
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
        return {"kernel": KERNEL, "items": [], "summary": ""}

    day_branch = pillars[2]["dizhi"]["name"]
    year_branch = pillars[0]["dizhi"]["name"]
    branches = _branches(chart)
    items: list[dict[str, str]] = []

    for pos in TIANYI.get(day_stem, ()):
        hits = _find_in_branches(pos, branches)
        if hits:
            items.append({
                "name": "天乙贵人",
                "position": "、".join(hits),
                "note": SHENSHA_DESC["天乙贵人"],
            })
            break

    wc = WENCHANG.get(day_stem, "")
    if wc:
        hits = _find_in_branches(wc, branches)
        if hits:
            items.append({
                "name": "文昌",
                "position": "、".join(hits),
                "note": SHENSHA_DESC["文昌"],
            })

    for base_name, base_branch in (("日支", day_branch), ("年支", year_branch)):
        ym = YIMA.get(base_branch, "")
        if ym and _find_in_branches(ym, branches):
            items.append({
                "name": "驿马",
                "position": f"以{base_name}查遇{ym}",
                "note": SHENSHA_DESC["驿马"],
            })
            break

    for base_name, base_branch in (("日支", day_branch), ("年支", year_branch)):
        th = TAOHUA.get(base_branch, "")
        if th and _find_in_branches(th, branches):
            items.append({
                "name": "桃花",
                "position": f"以{base_name}查遇{th}",
                "note": SHENSHA_DESC["桃花"],
            })
            break

    for base_name, base_branch in (("日支", day_branch), ("年支", year_branch)):
        hg = HUAGAI.get(base_branch, "")
        if hg and _find_in_branches(hg, branches):
            items.append({
                "name": "华盖",
                "position": f"以{base_name}查遇{hg}",
                "note": SHENSHA_DESC["华盖"],
            })
            break

    seen: set[str] = set()
    unique: list[dict[str, str]] = []
    for it in items:
        if it["name"] in seen:
            continue
        seen.add(it["name"])
        unique.append(it)

    summary = "、".join(i["name"] for i in unique) if unique else "未显常用神煞"
    by_pillar: dict[str, list[str]] = {k: [] for k in ("year", "month", "day", "hour")}
    label_to_key = {"年柱": "year", "月柱": "month", "日柱": "day", "时柱": "hour"}
    for it in unique:
        pos = it.get("position", "")
        for label, key in label_to_key.items():
            if label in pos and it["name"] not in by_pillar[key]:
                by_pillar[key].append(it["name"])
    return {
        "kernel": KERNEL,
        "items": unique,
        "by_pillar": by_pillar,
        "summary": summary,
        "note": "神煞为辅助，须配合格局旺衰综合判断（协纪辨方书）",
    }
