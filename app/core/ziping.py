# -*- coding: utf-8 -*-
"""
子平真诠 · 格局判定

月令取格、建禄羊刃、格局清纯与破格倾向（程序简判，供锚定 AI）。
"""
from __future__ import annotations

from typing import Any

from app.core.changsheng import changsheng
from app.core.constants import TIANGAN_WUXING

KERNEL = "子平真诠"

YANG_STEMS = frozenset("甲丙戊庚壬")

# 八正格十神
NORMAL_GEJU = {
    "正官": "正官格",
    "七杀": "七杀格",
    "正财": "正财格",
    "偏财": "偏财格",
    "正印": "正印格",
    "偏印": "偏印格",
    "食神": "食神格",
    "伤官": "伤官格",
}

GEJU_NOTES: dict[str, str] = {
    "正官格": "主端正贵气，忌伤官破格（三命通会）",
    "七杀格": "主刚烈果断，宜食神制杀或印星化杀（三命通会）",
    "正财格": "主勤劳持家，忌比劫争财（三命通会）",
    "偏财格": "主机遇偏财，宜身强任财（渊海子平）",
    "正印格": "主聪慧好学，官印相生为贵（子平真诠）",
    "偏印格": "主偏学灵性，忌枭神夺食（三命通会）",
    "食神格": "主食禄丰厚，宜泄秀生财（渊海子平）",
    "伤官格": "主才华外露，伤官见官为破格常见（三命通会）",
    "建禄格": "月令临官，身强宜泄耗，不作普通外格论（子平真诠）",
    "羊刃格": "月令帝旺，阳干为刃，宜官杀制或食伤泄（渊海子平）",
}

# 相神：格局 → 辅助十神
XIANGSHEN: dict[str, list[str]] = {
    "正官格": ["正印", "正财"],
    "七杀格": ["食神", "正印"],
    "正财格": ["正官", "食神"],
    "偏财格": ["正官", "伤官"],
    "正印格": ["正官", "比肩"],
    "偏印格": ["七杀", "比肩"],
    "食神格": ["正财", "比肩"],
    "伤官格": ["正财", "正印"],
}

CONFLICTS: dict[str, list[str]] = {
    "正官格": ["伤官", "七杀"],
    "七杀格": ["正官", "财星过旺"],
    "食神格": ["偏印"],
    "伤官格": ["正官"],
}


def _stem_shishen_on_pillars(pillars: list[dict]) -> list[tuple[str, str, str]]:
    """(柱名, 天干, 十神) 不含日主。"""
    out: list[tuple[str, str, str]] = []
    for p in pillars:
        if p.get("key") == "day":
            continue
        ss = p.get("shishen", "")
        tg = p.get("tiangan", {}).get("name", "")
        if ss and tg:
            out.append((p.get("label", ""), tg, ss))
    return out


def _month_command_shishen(month_pillar: dict) -> list[tuple[str, str]]:
    """月令候选十神：(来源, 十神)。"""
    cands: list[tuple[str, str]] = []
    mss = month_pillar.get("shishen", "")
    if mss and mss != "日主":
        cands.append(("月干", mss))
    for cg in month_pillar.get("dizhi", {}).get("canggan", []):
        css = cg.get("shishen", "")
        if css:
            cands.append(("月令藏干", css))
    return cands


def _is_revealed(pillars: list[dict], shishen: str) -> bool:
    for p in pillars:
        if p.get("key") == "day":
            continue
        if p.get("shishen") == shishen:
            return True
    return False


def _assess_purity(
    geju_type: str,
    shishen: str,
    pillars: list[dict],
    relations: list[str],
) -> dict[str, Any]:
    """格局清纯 / 破格倾向。"""
    stem_ss = _stem_shishen_on_pillars(pillars)
    present = {ss for _, _, ss in stem_ss}
    conflicts = CONFLICTS.get(geju_type, [])
    breaks: list[str] = []
    for c in conflicts:
        if c in present:
            breaks.append(f"见{c}，有破格倾向")

    month_branch = pillars[1]["dizhi"]["name"] if len(pillars) > 1 else ""
    for r in relations:
        if month_branch and month_branch in r and ("冲" in r or "刑" in r):
            breaks.append(f"月令逢{r}，格局受冲")

    xiang = XIANGSHEN.get(geju_type, [])
    helpers = [x for x in xiang if x in present]

    if breaks:
        level = "杂"
        note = "；".join(breaks[:3])
    elif helpers:
        level = "清"
        note = f"有相神{'、'.join(helpers)}辅助，格局较清（子平真诠）"
    else:
        level = "平"
        note = "用神单一，相神未显，宜看大运补辅"

    return {"level": level, "note": note, "xiang_shen": helpers, "breaks": breaks}


def analyze(chart: dict[str, Any]) -> dict[str, Any]:
    meta = chart.get("meta", {})
    pillars = chart.get("pillars", [])
    if len(pillars) < 4:
        return {"kernel": KERNEL, "error": "命盘不完整"}

    day_stem = meta.get("day_master", "")
    month_pillar = pillars[1]
    month_branch = month_pillar["dizhi"]["name"]
    relations = chart.get("pillars_relations") or []

    cs = changsheng(day_stem, month_branch)
    if cs == "临官":
        geju_type = "建禄格"
        return {
            "kernel": KERNEL,
            "type": geju_type,
            "shishen": "比肩",
            "origin": "月令临官",
            "revealed": True,
            "purity": _assess_purity(geju_type, "比肩", pillars, relations),
            "note": GEJU_NOTES[geju_type],
            "source": "子平真诠",
        }
    if cs == "帝旺" and day_stem in YANG_STEMS:
        geju_type = "羊刃格"
        return {
            "kernel": KERNEL,
            "type": geju_type,
            "shishen": "劫财",
            "origin": "月令帝旺",
            "revealed": True,
            "purity": _assess_purity(geju_type, "劫财", pillars, relations),
            "note": GEJU_NOTES[geju_type],
            "source": "渊海子平",
        }

    for origin, ss in _month_command_shishen(month_pillar):
        if ss not in NORMAL_GEJU:
            continue
        geju_type = NORMAL_GEJU[ss]
        revealed = _is_revealed(pillars, ss) or origin == "月干"
        purity = _assess_purity(geju_type, ss, pillars, relations)
        note = GEJU_NOTES.get(geju_type, "")
        if not revealed:
            note = f"{'、'.join(note.split('，')[:1])}；{ss}未透干，作虚格参考"
        return {
            "kernel": KERNEL,
            "type": geju_type,
            "shishen": ss,
            "origin": origin,
            "revealed": revealed,
            "purity": purity,
            "note": note,
            "source": "三命通会",
        }

    return {
        "kernel": KERNEL,
        "type": "正格",
        "shishen": "",
        "origin": "月令",
        "revealed": False,
        "purity": {"level": "平", "note": "未取到明确外格，以旺衰体用论", "xiang_shen": [], "breaks": []},
        "note": "五行未取专格，综合子平旺衰与调候（滴天髓体用）",
        "source": "子平",
    }
