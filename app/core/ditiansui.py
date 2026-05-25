# -*- coding: utf-8 -*-
"""
滴天髓阐微 · 规则内核

以《滴天髓阐微》体用、通根、得令、寒暖燥湿、从化等纲要，
对四柱做程序化倾向判断，供 BaziInsight 与 AI 锚定。
"""
from __future__ import annotations

from typing import Any

from app.core.changsheng import changsheng, changsheng_score
from app.core.constants import DIZHI_CANGGAN, DIZHI_WUXING, TIANGAN_WUXING

KERNEL = "滴天髓阐微"

WUXING_ORDER = ("木", "火", "土", "金", "水")
WUXING_GENERATES = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
WUXING_CONTROLS = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}

# 十干体象（滴天髓原旨摘要）
STEM_NATURE: dict[str, dict[str, str]] = {
    "甲": {"yin_yang": "阳", "image": "参天巨木", "verse": "甲木参天，脱胎要火。春不容金，秋不容土。火炽乘龙，水宕骑虎。"},
    "乙": {"yin_yang": "阴", "image": "花草藤萝", "verse": "乙木虽柔，刲羊解牛。怀丙抱丁，跨凤乘猴。"},
    "丙": {"yin_yang": "阳", "image": "太阳之火", "verse": "丙火猛烈，欺霜侮雪。能煅庚金，逢辛反怯。土众成慈，水猖显节。"},
    "丁": {"yin_yang": "阴", "image": "灯烛炉焰", "verse": "丁火柔中，内性昭融。抱乙而孝，合壬而忠。"},
    "戊": {"yin_yang": "阳", "image": "城墙厚土", "verse": "戊土固重，既中且正。静翕动辟，万物司命。"},
    "己": {"yin_yang": "阴", "image": "田园湿土", "verse": "己土卑湿，中正蓄藏。不愁木盛，不畏水狂。"},
    "庚": {"yin_yang": "阳", "image": "刀剑顽金", "verse": "庚金带煞，刚健为最。得水而清，得火而锐。"},
    "辛": {"yin_yang": "阴", "image": "珠玉首饰", "verse": "辛金软柔，温润而清。畏土之叠，乐水之盈。"},
    "壬": {"yin_yang": "阳", "image": "江河之水", "verse": "壬水通河，能泄金气。刚中之德，周流不滞。"},
    "癸": {"yin_yang": "阴", "image": "雨露细水", "verse": "癸水至弱，达于天津。得龙而运，功化斯神。"},
}

# 月支气候（阐微重视寒暖燥湿）
MONTH_CLIMATE: dict[str, dict[str, str]] = {
    "寅": {"season": "春", "climate": "微寒", "note": "三阳开泰，木气渐生"},
    "卯": {"season": "春", "climate": "温", "note": "仲春木旺"},
    "辰": {"season": "春", "climate": "湿", "note": "季春土湿，木气余波"},
    "巳": {"season": "夏", "climate": "暖", "note": "初夏火渐长"},
    "午": {"season": "夏", "climate": "炎", "note": "仲夏火炽"},
    "未": {"season": "夏", "climate": "燥", "note": "季夏土燥，火土同旺"},
    "申": {"season": "秋", "climate": "凉", "note": "初秋金始生"},
    "酉": {"season": "秋", "climate": "清", "note": "仲秋金旺"},
    "戌": {"season": "秋", "climate": "燥", "note": "季秋土燥，金气余波"},
    "亥": {"season": "冬", "climate": "寒", "note": "初冬水始旺"},
    "子": {"season": "冬", "climate": "寒", "note": "仲冬水盛"},
    "丑": {"season": "冬", "climate": "湿", "note": "季冬湿土，寒气未除"},
}

# 调候倾向（简表：日干×月支，摘自阐微常用口诀）
TIAOHOU: dict[tuple[str, str], str] = {
    ("甲", "寅"): "初春尚寒，丙癸并用，以丙火为先",
    ("甲", "卯"): "羊刃当令，喜庚金制，丁火泄秀",
    ("甲", "辰"): "木气渐退，癸丙为要",
    ("丙", "子"): "水旺火弱，甲木引火为急",
    ("丙", "午"): "火炎土燥，壬水调候",
    ("庚", "子"): "水冷金寒，丁火暖局，丙火次之",
    ("庚", "巳"): "火旺金销，喜湿土晦火生金",
    ("壬", "子"): "水旺极寒，戊土制水，丙火暖局",
    ("癸", "丑"): "寒湿并重，丙火为先，甲木次之",
}

CANGGAN_WEIGHT = (1.0, 0.6, 0.3)


def _wx(stem: str) -> str:
    return TIANGAN_WUXING.get(stem, "")


def _generates(a: str, b: str) -> bool:
    return WUXING_GENERATES.get(a) == b


def _controls(a: str, b: str) -> bool:
    return WUXING_CONTROLS.get(a) == b


def _shishen_category(day_wx: str, other_wx: str) -> str:
    if day_wx == other_wx:
        return "比劫"
    if _generates(day_wx, other_wx):
        return "食伤"
    if _generates(other_wx, day_wx):
        return "印绶"
    if _controls(day_wx, other_wx):
        return "财星"
    if _controls(other_wx, day_wx):
        return "官杀"
    return "未知"


def _de_ling(day_stem: str, month_branch: str) -> dict[str, Any]:
    day_wx = _wx(day_stem)
    month_wx = DIZHI_WUXING.get(month_branch, "")
    main_hidden = DIZHI_CANGGAN.get(month_branch, [""])[0]
    main_wx = _wx(main_hidden)
    cs = changsheng(day_stem, month_branch)

    if month_wx == day_wx or main_wx == day_wx:
        status = "得令"
        score = 1.0
    elif _generates(month_wx, day_wx) or _generates(main_wx, day_wx):
        status = "相令"
        score = 0.6
    elif _controls(month_wx, day_wx) or _controls(main_wx, day_wx):
        status = "失令"
        score = -0.8
    elif _generates(day_wx, month_wx):
        status = "泄令"
        score = -0.4
    else:
        status = "休令"
        score = -0.2

    return {
        "status": status,
        "score": score,
        "month_branch": month_branch,
        "month_wuxing": month_wx,
        "main_qi": main_hidden,
        "changsheng": cs,
    }


def _tong_gen(day_stem: str, pillars: list[dict]) -> dict[str, Any]:
    day_wx = _wx(day_stem)
    roots: list[dict[str, Any]] = []
    total = 0.0
    for p in pillars:
        dz = p["dizhi"]["name"]
        label = p.get("label", "")
        cs = changsheng(day_stem, dz)
        cs_sc = changsheng_score(day_stem, dz)
        for i, cg in enumerate(DIZHI_CANGGAN.get(dz, [])):
            cg_wx = _wx(cg)
            w = CANGGAN_WEIGHT[i] if i < len(CANGGAN_WEIGHT) else 0.2
            cat = _shishen_category(day_wx, cg_wx)
            if cat in ("比劫", "印绶"):
                contrib = w * (1.2 if cat == "比劫" else 1.0)
                total += contrib
                roots.append({
                    "pillar": label,
                    "branch": dz,
                    "hidden_stem": cg,
                    "category": cat,
                    "weight": round(contrib, 2),
                    "changsheng": cs,
                })
        if cs_sc >= 0.5 and not any(r["branch"] == dz for r in roots):
            total += cs_sc * 0.5
            roots.append({
                "pillar": label,
                "branch": dz,
                "hidden_stem": "",
                "category": "长生旺地",
                "weight": round(cs_sc * 0.5, 2),
                "changsheng": cs,
            })

    return {
        "roots": roots,
        "score": round(total, 2),
        "summary": "有根" if total >= 0.8 else ("弱根" if total >= 0.3 else "无根"),
    }


def _de_zhu(day_stem: str, pillars: list[dict]) -> dict[str, Any]:
    day_wx = _wx(day_stem)
    helps: list[str] = []
    drains: list[str] = []
    score = 0.0
    for p in pillars:
        if p["key"] == "day":
            continue
        tg = p["tiangan"]["name"]
        tg_wx = _wx(tg)
        cat = _shishen_category(day_wx, tg_wx)
        label = p.get("label", "")
        if cat in ("比劫", "印绶"):
            helps.append(f"{label}{tg}({cat})")
            score += 0.7 if cat == "比劫" else 0.5
        elif cat in ("官杀", "财星", "食伤"):
            drains.append(f"{label}{tg}({cat})")
            score -= 0.5 if cat == "官杀" else 0.35

    return {
        "helps": helps,
        "drains": drains,
        "score": round(score, 2),
        "summary": "得助" if score >= 0.5 else ("受克泄" if score <= -0.5 else "中和"),
    }


def _climate(month_branch: str) -> dict[str, str]:
    base = MONTH_CLIMATE.get(month_branch, {"season": "", "climate": "中和", "note": ""})
    return dict(base)


def _tiao_hou(day_stem: str, month_branch: str, climate: dict[str, str]) -> str:
    key = (day_stem, month_branch)
    if key in TIAOHOU:
        return TIAOHOU[key]
    cl = climate.get("climate", "")
    wx = _wx(day_stem)
    if cl in ("寒", "湿") and wx in ("木", "火"):
        return "寒湿当令，宜火暖局（滴天髓：木火向阳）"
    if cl in ("炎", "燥") and wx in ("金", "水"):
        return "炎燥当令，宜水润金（滴天髓：金水相涵）"
    if cl == "燥" and wx == "土":
        return "燥土当权，宜水润泽"
    return "气候尚可，随大运流年调候"


def _detect_hua(day_stem: str, pillars: list[dict], wx_counts: dict[str, int | float]) -> dict[str, Any]:
    """从化/专旺倾向（简判，非定论）。"""
    day_wx = _wx(day_stem)
    total = sum(wx_counts.values()) or 1
    same = wx_counts.get(day_wx, 0)
    ratio = same / total
    month = pillars[1]["dizhi"]["name"]
    de = _de_ling(day_stem, month)

    if ratio >= 0.55 and de["score"] >= 0.6:
        return {"type": "专旺倾向", "note": f"{day_wx}气偏聚，宜顺其势，忌逆克（阐微体用）"}
    if ratio <= 0.15 and de["score"] <= -0.5:
        opp = max(wx_counts, key=lambda k: wx_counts[k])
        return {"type": "从势倾向", "note": f"日主弱而{opp}旺，宜论从势，不可强扶（阐微从化）"}
    return {"type": "正格", "note": "五行未极偏，以中和体用为纲"}


def _strength_label(score: float) -> str:
    if score >= 1.5:
        return "偏强"
    if score <= -0.8:
        return "偏弱"
    return "平衡"


def analyze(chart: dict[str, Any]) -> dict[str, Any]:
    meta = chart.get("meta", {})
    pillars = chart.get("pillars", [])
    day_stem = meta.get("day_master", "")
    day_wx = meta.get("day_master_wuxing", "")
    if not day_stem or len(pillars) < 4:
        return {"kernel": KERNEL, "error": "命盘不完整"}

    month_branch = pillars[1]["dizhi"]["name"]
    stem_info = STEM_NATURE.get(day_stem, {})
    de_ling = _de_ling(day_stem, month_branch)
    tong_gen = _tong_gen(day_stem, pillars)
    de_zhu = _de_zhu(day_stem, pillars)
    climate = _climate(month_branch)
    tiao_hou = _tiao_hou(day_stem, month_branch, climate)

    pillar_cs = [
        {
            "pillar": p.get("label"),
            "branch": p["dizhi"]["name"],
            "changsheng": changsheng(day_stem, p["dizhi"]["name"]),
        }
        for p in pillars
    ]

    wx_counts = chart.get("wuxing_stats", {})
    hua = _detect_hua(day_stem, pillars, wx_counts)

    total_score = de_ling["score"] + tong_gen["score"] * 0.8 + de_zhu["score"] * 0.6
    strength = _strength_label(total_score)

    return {
        "kernel": KERNEL,
        "stem_nature": {
            "stem": day_stem,
            "wuxing": day_wx,
            "yin_yang": stem_info.get("yin_yang", ""),
            "image": stem_info.get("image", ""),
            "verse": stem_info.get("verse", ""),
        },
        "de_ling": de_ling,
        "tong_gen": tong_gen,
        "de_zhu": de_zhu,
        "climate": climate,
        "tiao_hou": tiao_hou,
        "changsheng_map": pillar_cs,
        "pattern": hua,
        "strength_score": round(total_score, 2),
        "day_master_strength": strength,
        "method_note": "依滴天髓阐微体用、通根、得令、寒暖燥湿纲要，为倾向判断非唯一流派结论",
    }
