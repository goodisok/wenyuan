# -*- coding: utf-8 -*-
"""
过三关 · 多维验证

综参盲派（穿、宫位做功）、子平（十神六亲）、千里命稿（断事应期），
对父母 / 兄弟 / 子女三关交叉验证，输出置信度与各家信号。
"""
from __future__ import annotations

from typing import Any

from app.core.duanshi import (
    DIZHI_CHONG,
    DIZHI_PO,
    LIUQIN_FEMALE,
    LIUQIN_MALE,
    _dayun_triggers,
    _find_shishen,
    _pair_tag,
    _pillar_branches,
    _pillar_stems,
    _year_month_harm,
)

KERNEL = "过三关·多维验证"

# 盲派六穿
DIZHI_CHUAN: dict[frozenset[str], str] = {
    frozenset(("子", "未")): "子未穿",
    frozenset(("丑", "午")): "丑午穿",
    frozenset(("寅", "巳")): "寅巳穿",
    frozenset(("卯", "辰")): "卯辰穿",
    frozenset(("申", "亥")): "申亥穿",
    frozenset(("酉", "戌")): "酉戌穿",
}


def _chuan_between(a: str, b: str) -> str | None:
    return _pair_tag(a, b, DIZHI_CHUAN)


def _pillar_chuan(branches: dict[str, str], key_a: str, key_b: str) -> str | None:
    ba, bb = branches.get(key_a, ""), branches.get(key_b, "")
    if not ba or not bb:
        return None
    tag = _chuan_between(ba, bb)
    if tag:
        labels = {"year": "年", "month": "月", "day": "日", "hour": "时"}
        return f"{labels.get(key_a, key_a)}{labels.get(key_b, key_b)}{tag}"
    return None


def _confidence(signals: list[dict[str, Any]], score: int) -> tuple[str, int]:
    schools_hit = {s["school"] for s in signals if s.get("hit")}
    n = len(schools_hit)
    if n >= 3 and score >= 5:
        return "高", n
    if n >= 2 and score >= 3:
        return "中", n
    if score >= 2 or n >= 1:
        return "低", n
    return "无", n


def _gate_result(
    gate_id: str,
    name: str,
    verdict: str,
    signals: list[dict[str, Any]],
    score: int,
    windows: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    conf, n_schools = _confidence(signals, score)
    return {
        "id": gate_id,
        "name": name,
        "verdict": verdict,
        "confidence": conf,
        "schools_agree": n_schools,
        "score": score,
        "signals": [s for s in signals if s.get("hit")],
        "windows": windows or [],
    }


def _shishen_counts(pillars: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for p in pillars:
        ss = p.get("shishen", "")
        if ss and ss != "日主":
            counts[ss] = counts.get(ss, 0) + 1
        for cg in p.get("dizhi", {}).get("canggan", []):
            css = cg.get("shishen", "")
            if css:
                counts[css] = counts.get(css, 0) + 1
    return counts


def _parents_gate(
    pillars: list[dict],
    branches: dict[str, str],
    stems: dict[str, str],
    gender: str,
    relations: list[str],
    dayun_trig: list[dict[str, str]],
) -> dict[str, Any]:
    lq = LIUQIN_MALE if gender == "male" else LIUQIN_FEMALE
    father, mother = lq["father"], lq["mother"]
    father_locs = _find_shishen(pillars, father)
    mother_locs = _find_shishen(pillars, mother)

    signals: list[dict[str, Any]] = []
    score = 0

    ym_chuan = _pillar_chuan(branches, "year", "month")
    if ym_chuan:
        signals.append({"school": "盲派", "hit": True, "text": f"年月{ym_chuan}，父母宫穿，主分离离异（盲派重穿）"})
        score += 4
    else:
        signals.append({"school": "盲派", "hit": False, "text": "年月无穿"})

    ym_harm = _year_month_harm(branches, stems)
    if ym_harm:
        signals.append({"school": "子平", "hit": True, "text": f"父母宫{'、'.join(ym_harm)}，家宅不安"})
        score += 3
    else:
        signals.append({"school": "子平", "hit": False, "text": "年月无冲破"})

    yb, mb = branches.get("year"), branches.get("month")
    if yb and mb and _pair_tag(yb, mb, DIZHI_PO):
        signals.append({"school": "千里命稿", "hit": True, "text": f"年{yb}月{mb}相破，父母不和离异"})
        score += 3

    if any("自刑" in r and "酉" in r for r in relations) and branches.get("year") == "酉":
        signals.append({"school": "盲派", "hit": True, "text": "年支酉自刑，父母宫内耗严重"})
        score += 2

    if len(mother_locs) >= 2 and not father_locs:
        signals.append({"school": "子平", "hit": True, "text": f"母星{mother}叠见、父星{father}不现，母强父弱易失衡"})
        score += 2
    elif not father_locs:
        signals.append({"school": "子平", "hit": True, "text": f"父星{father}不现，父缘薄"})
        score += 1

    if score >= 5:
        verdict = "父母离异、分居或长期冷战（多维印证）"
    elif score >= 3:
        verdict = "父母缘分薄，争吵分离或一方缺位"
    else:
        verdict = "父母宫平稳，未见显著破格"

    windows = [w for w in dayun_trig if "年" in w.get("note", "")]
    return _gate_result("parents", "第一关·父母", verdict, signals, score, windows)


def _siblings_gate(
    pillars: list[dict],
    branches: dict[str, str],
    stems: dict[str, str],
    gender: str,
    relations: list[str],
) -> dict[str, Any]:
    month_p = pillars[1] if len(pillars) > 1 else {}
    month_stem_ss = month_p.get("shishen", "")
    month_branch = branches.get("month", "")

    signals: list[dict[str, Any]] = []
    score = 0

    # 盲派：男看月干为兄弟
    if gender == "male":
        if month_stem_ss == "比肩":
            signals.append({"school": "盲派", "hit": True, "text": "月干为比肩，有兄弟（盲派月干兄弟）"})
            score += 2
        elif month_stem_ss == "劫财":
            signals.append({"school": "盲派", "hit": True, "text": "月干为劫财，有兄弟同气"})
            score += 2
        if month_stem_ss in ("正官", "七杀"):
            signals.append({"school": "盲派", "hit": True, "text": "月柱官杀，克兄弟，主兄弟少或离散"})
            score += 2
    else:
        if month_stem_ss in ("比肩", "劫财"):
            signals.append({"school": "盲派", "hit": True, "text": "月干比劫，有姐妹（盲派月干姐妹）"})
            score += 2

    ss = _shishen_counts(pillars)
    bijie = ss.get("比肩", 0) + ss.get("劫财", 0)
    if bijie >= 3:
        signals.append({"school": "子平", "hit": True, "text": f"比劫重（{bijie}），兄弟姊妹多或同气强"})
        score += 2
    elif bijie == 0:
        signals.append({"school": "子平", "hit": True, "text": "比劫不现，兄弟缘薄或独子"})
        score += 2

    day_stem = stems.get("day", "")
    month_stem = stems.get("month", "")
    if day_stem and month_stem and day_stem == month_stem and branches.get("day") != branches.get("month"):
        signals.append({"school": "盲派", "hit": True, "text": "日月天干同而地支异，兄弟有但易有隔阂"})
        score += 1

    if day_stem and month_stem and day_stem == month_stem and branches.get("day") == branches.get("month"):
        signals.append({"school": "盲派", "hit": True, "text": "日月柱同干支，伏吟，兄弟缘深或排行需细论"})
        score += 1

    for r in relations:
        if "刑" in r or "冲" in r:
            if month_branch and month_branch in r:
                signals.append({"school": "千里命稿", "hit": True, "text": f"月柱逢{r}，兄弟宫动，主离散或健康"})
                score += 2
                break

    if score >= 4:
        verdict = "有兄弟姊妹，但易离散、争财或健康波折"
    elif score >= 2:
        verdict = "兄弟姊妹缘存在，数量与排行需合大运细断"
    else:
        verdict = "兄弟宫平稳，或独子、少兄弟"

    return _gate_result("siblings", "第二关·兄弟", verdict, signals, score)


def _children_gate(
    pillars: list[dict],
    branches: dict[str, str],
    gender: str,
    relations: list[str],
    dayun_trig: list[dict[str, str]],
) -> dict[str, Any]:
    lq = LIUQIN_MALE if gender == "male" else LIUQIN_FEMALE
    child_star = lq["child"]
    child_locs = _find_shishen(pillars, child_star)
    hour_p = pillars[3] if len(pillars) > 3 else {}
    hour_ss = hour_p.get("shishen", "")

    signals: list[dict[str, Any]] = []
    score = 0

    if child_locs:
        signals.append({"school": "子平", "hit": True, "text": f"子女星{child_star}现于{','.join(child_locs[:3])}"})
        score += 2
    else:
        signals.append({"school": "子平", "hit": True, "text": f"子女星{child_star}不现，得子宜晚或看大运"})
        score += 1

    if gender == "male" and hour_ss in ("正印", "偏印"):
        signals.append({"school": "盲派", "hit": True, "text": "时柱印旺，男命时上印，子女来得晚或宜女"})
        score += 1
    if gender == "female" and hour_ss in ("伤官", "食神"):
        signals.append({"school": "盲派", "hit": True, "text": "时柱食伤，女命子女星在时，有子之象"})
        score += 2

    hb = branches.get("hour", "")
    db = branches.get("day", "")
    chuan = _chuan_between(hb, db) if hb and db else None
    if chuan:
        signals.append({"school": "盲派", "hit": True, "text": f"日时{chuan}，子女宫与夫妻宫穿，主子息波折"})
        score += 2

    for r in relations:
        if "冲" in r and ("时" in r or hb in r):
            signals.append({"school": "千里命稿", "hit": True, "text": f"时柱相关{r}，子女宫动"})
            score += 2
            break

    if score >= 4:
        verdict = "子女有，但时柱动，宜晚育或经波折"
    elif score >= 2:
        verdict = "子女缘中等，男女及数量看大运引动"
    else:
        verdict = "子女宫较稳，有子之象"

    windows = [w for w in dayun_trig if "时" in w.get("note", "") or "日" in w.get("note", "")][:3]
    return _gate_result("children", "第三关·子女", verdict, signals, score, windows)


def analyze(chart: dict[str, Any]) -> dict[str, Any]:
    meta = chart.get("meta", {})
    pillars = chart.get("pillars", [])
    gender = meta.get("gender", "male")
    relations = chart.get("pillars_relations") or []
    branches = _pillar_branches(pillars)
    stems = _pillar_stems(pillars)
    dayun_trig = _dayun_triggers(chart.get("dayun", []), branches)

    chuan_list: list[str] = []
    for ka, kb in (("year", "month"), ("year", "day"), ("year", "hour"), ("month", "day"), ("month", "hour"), ("day", "hour")):
        c = _pillar_chuan(branches, ka, kb)
        if c:
            chuan_list.append(c)

    gates = [
        _parents_gate(pillars, branches, stems, gender, relations, dayun_trig),
        _siblings_gate(pillars, branches, stems, gender, relations),
        _children_gate(pillars, branches, gender, relations, dayun_trig),
    ]

    high = [g for g in gates if g["confidence"] == "高"]
    summary = f"三关验证：{len(high)}关高置信" if high else f"三关验证：{'、'.join(g['name']+g['confidence'] for g in gates)}"

    return {
        "kernel": KERNEL,
        "gates": gates,
        "chuan": chuan_list,
        "summary": summary,
        "method": "盲派穿象 + 子平六亲 + 千里应期，交叉印证",
    }
