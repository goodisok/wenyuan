# -*- coding: utf-8 -*-
"""十二长生：以日干查地支。"""
from __future__ import annotations

BRANCHES = ("子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥")
CHANGSHENG_NAMES = ("长生", "沐浴", "冠带", "临官", "帝旺", "衰", "病", "死", "墓", "绝", "胎", "养")

# 阳干顺行、阴干逆行，长生起点（滴天髓/子平通例）
YANG_START: dict[str, str] = {
    "甲": "亥", "丙": "寅", "戊": "寅", "庚": "巳", "壬": "申",
}
YIN_START: dict[str, str] = {
    "乙": "午", "丁": "酉", "己": "酉", "辛": "子", "癸": "卯",
}

STRONG_STAGES = frozenset(("长生", "冠带", "临官", "帝旺"))
WEAK_STAGES = frozenset(("死", "墓", "绝", "胎"))


def _index(branch: str) -> int:
    return BRANCHES.index(branch)


def changsheng(day_stem: str, branch: str) -> str:
    if day_stem in YANG_START:
        start = _index(YANG_START[day_stem])
        pos = _index(branch)
        step = (pos - start) % 12
    elif day_stem in YIN_START:
        start = _index(YIN_START[day_stem])
        pos = _index(branch)
        step = (start - pos) % 12
    else:
        return ""
    return CHANGSHENG_NAMES[step]


def changsheng_score(day_stem: str, branch: str) -> float:
    name = changsheng(day_stem, branch)
    if name in STRONG_STAGES:
        return 1.0
    if name in ("衰", "病"):
        return 0.3
    if name in WEAK_STAGES:
        return -0.5
    if name == "沐浴":
        return 0.1
    return 0.0
