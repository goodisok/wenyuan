# -*- coding: utf-8 -*-
"""四柱刑冲合害关系（v1.0 范围）。"""
from __future__ import annotations

from itertools import combinations

PILLAR_LABELS = {"year": "年", "month": "月", "day": "日", "hour": "时"}

TIANGAN_HE: dict[frozenset[str], str] = {
    frozenset(("甲", "己")): "甲己合",
    frozenset(("乙", "庚")): "乙庚合",
    frozenset(("丙", "辛")): "丙辛合",
    frozenset(("丁", "壬")): "丁壬合",
    frozenset(("戊", "癸")): "戊癸合",
}

DIZHI_LIUHE: dict[frozenset[str], str] = {
    frozenset(("子", "丑")): "子丑合",
    frozenset(("寅", "亥")): "寅亥合",
    frozenset(("卯", "戌")): "卯戌合",
    frozenset(("辰", "酉")): "辰酉合",
    frozenset(("巳", "申")): "巳申合",
    frozenset(("午", "未")): "午未合",
}

DIZHI_CHONG: dict[frozenset[str], str] = {
    frozenset(("子", "午")): "子午冲",
    frozenset(("丑", "未")): "丑未冲",
    frozenset(("寅", "申")): "寅申冲",
    frozenset(("卯", "酉")): "卯酉冲",
    frozenset(("辰", "戌")): "辰戌冲",
    frozenset(("巳", "亥")): "巳亥冲",
}

DIZHI_HAI: dict[frozenset[str], str] = {
    frozenset(("子", "未")): "子未害",
    frozenset(("丑", "午")): "丑午害",
    frozenset(("寅", "巳")): "寅巳害",
    frozenset(("卯", "辰")): "卯辰害",
    frozenset(("申", "亥")): "申亥害",
    frozenset(("酉", "戌")): "酉戌害",
}

SANXING_PAIRS: dict[frozenset[str], str] = {
    frozenset(("寅", "巳")): "寅巳刑",
    frozenset(("巳", "申")): "巳申刑",
    frozenset(("寅", "申")): "寅申刑",
    frozenset(("丑", "戌")): "丑戌刑",
    frozenset(("戌", "未")): "戌未刑",
    frozenset(("丑", "未")): "丑未刑",
    frozenset(("子", "卯")): "子卯刑",
}

ZIXING_BRANCHES = frozenset(("辰", "午", "酉", "亥"))

# 三合局（ v1.1 ）
SANHE_GROUPS: list[tuple[frozenset[str], str]] = [
    (frozenset(("申", "子", "辰")), "申子辰合水局"),
    (frozenset(("亥", "卯", "未")), "亥卯未合木局"),
    (frozenset(("寅", "午", "戌")), "寅午戌合火局"),
    (frozenset(("巳", "酉", "丑")), "巳酉丑合金局"),
]

# 三会方
SANHUI_GROUPS: list[tuple[frozenset[str], str]] = [
    (frozenset(("寅", "卯", "辰")), "寅卯辰会东方木"),
    (frozenset(("巳", "午", "未")), "巳午未会南方火"),
    (frozenset(("申", "酉", "戌")), "申酉戌会西方金"),
    (frozenset(("亥", "子", "丑")), "亥子丑会北方水"),
]


def _pair_label(a: str, b: str, mapping: dict[frozenset[str], str]) -> str | None:
    return mapping.get(frozenset((a, b)))


def _zixing_label(branch: str) -> str:
    return f"{branch}{branch}自刑"


def compute_pillar_relations(pillars: list[dict]) -> list[str]:
    """返回去重后的关系标签，如「子丑合」「寅申冲」。"""
    stems: list[tuple[str, str]] = []
    branches: list[tuple[str, str]] = []
    for p in pillars:
        key = p.get("key", "")
        label = PILLAR_LABELS.get(key, key)
        tg = p.get("tiangan", {}).get("name", "")
        dz = p.get("dizhi", {}).get("name", "")
        if tg:
            stems.append((label, tg))
        if dz:
            branches.append((label, dz))

    found: set[str] = set()

    for (_, a), (_, b) in combinations(stems, 2):
        tag = _pair_label(a, b, TIANGAN_HE)
        if tag:
            found.add(tag)

    for (_, a), (_, b) in combinations(branches, 2):
        for mapping in (DIZHI_LIUHE, DIZHI_CHONG, DIZHI_HAI, SANXING_PAIRS):
            tag = _pair_label(a, b, mapping)
            if tag:
                found.add(tag)

    branch_names = [b for _, b in branches]
    branch_set = set(branch_names)
    for b in ZIXING_BRANCHES:
        if branch_names.count(b) >= 2:
            found.add(_zixing_label(b))

    for group, label in SANHE_GROUPS + SANHUI_GROUPS:
        hit = branch_set & group
        if len(hit) >= 2:
            if len(hit) == 3:
                found.add(label)
            else:
                partial = "".join(sorted(hit))
                found.add(f"{partial}半合")

    return sorted(found)
