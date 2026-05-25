# -*- coding: utf-8 -*-
"""
千里命稿 · 断事层

据宫位、六亲、刑冲合害破与大运，给出具体人事断语（分离、婚变、财运等应期）。
"""
from __future__ import annotations

from typing import Any

KERNEL = "千里命稿"

# 男命六亲（渊海子平常法）
LIUQIN_MALE = {
    "father": "偏财",
    "mother": "正印",
    "spouse": "正财",
    "child": "七杀",  # 男命以官杀为子，简取七杀
}
LIUQIN_FEMALE = {
    "father": "偏财",
    "mother": "正印",
    "spouse": "正官",
    "child": "食神",
}

DIZHI_CHUAN: dict[frozenset[str], str] = {
    frozenset(("子", "未")): "子未穿",
    frozenset(("丑", "午")): "丑午穿",
    frozenset(("寅", "巳")): "寅巳穿",
    frozenset(("卯", "辰")): "卯辰穿",
    frozenset(("申", "亥")): "申亥穿",
    frozenset(("酉", "戌")): "酉戌穿",
}

DIZHI_PO: dict[frozenset[str], str] = {
    frozenset(("子", "酉")): "子酉破",
    frozenset(("寅", "亥")): "寅亥破",
    frozenset(("卯", "午")): "卯午破",
    frozenset(("辰", "丑")): "辰丑破",
    frozenset(("巳", "申")): "巳申破",
    frozenset(("未", "戌")): "未戌破",
}

DIZHI_CHONG = {
    frozenset(("子", "午")): "子午冲",
    frozenset(("丑", "未")): "丑未冲",
    frozenset(("寅", "申")): "寅申冲",
    frozenset(("卯", "酉")): "卯酉冲",
    frozenset(("辰", "戌")): "辰戌冲",
    frozenset(("巳", "亥")): "巳亥冲",
}

TIANGAN_CHONG = {
    frozenset(("甲", "庚")): "甲庚冲",
    frozenset(("乙", "辛")): "乙辛冲",
    frozenset(("丙", "壬")): "丙壬冲",
    frozenset(("丁", "癸")): "丁癸冲",
}


def _pair_tag(a: str, b: str, mapping: dict[frozenset[str], str]) -> str | None:
    return mapping.get(frozenset((a, b)))


def _pillar_branches(pillars: list[dict]) -> dict[str, str]:
    return {p["key"]: p["dizhi"]["name"] for p in pillars if p.get("key")}


def _pillar_stems(pillars: list[dict]) -> dict[str, str]:
    return {p["key"]: p["tiangan"]["name"] for p in pillars if p.get("key")}


def _find_shishen(pillars: list[dict], name: str) -> list[str]:
    locs: list[str] = []
    for p in pillars:
        label = p.get("label", "")
        if p.get("shishen") == name:
            locs.append(f"{label}干{p['tiangan']['name']}")
        for cg in p.get("dizhi", {}).get("canggan", []):
            if cg.get("shishen") == name:
                locs.append(f"{label}支藏{cg['name']}({name})")
    return locs


def _year_month_harm(branches: dict[str, str], stems: dict[str, str]) -> list[str]:
    """年月柱地支/天干刑冲破害。"""
    tags: list[str] = []
    yb, mb = branches.get("year", ""), branches.get("month", "")
    ys, ms = stems.get("year", ""), stems.get("month", "")
    if yb and mb:
        for mapping in (DIZHI_CHONG, DIZHI_PO):
            t = _pair_tag(yb, mb, mapping)
            if t:
                tags.append(f"年月{t}")
    if ys and ms:
        t = _pair_tag(ys, ms, TIANGAN_CHONG)
        if t:
            tags.append(f"年月{t}")
    return tags


def _branch_hits(db: str, tb: str, label: str) -> list[tuple[str, int]]:
    """地支对宫位的作用：(描述, 权重)。"""
    hits: list[tuple[str, int]] = []
    if not db or not tb:
        return hits
    for mapping, verb, weight in (
        (DIZHI_CHONG, "冲", 4),
        (DIZHI_CHUAN, "穿", 4),
        (DIZHI_PO, "破", 3),
    ):
        if _pair_tag(db, tb, mapping):
            hits.append((f"{verb}{label}支{tb}", weight))
    if db == tb:
        hits.append((f"伏吟{label}支{tb}", 3))
    return hits


def _liunian_parent_hits(
    liunian: list[dict],
    year_b: str,
    month_b: str,
    *,
    limit: int = 3,
) -> list[str]:
    scored: list[tuple[int, str]] = []
    for ln in liunian or []:
        gz = ln.get("ganzhi", "")
        if len(gz) < 2:
            continue
        lb = gz[1]
        yr = ln.get("year")
        age = ln.get("age")
        for label, tb in (("年", year_b), ("月", month_b)):
            for desc, weight in _branch_hits(lb, tb, label):
                scored.append((weight, f"{yr}年(虚岁{age})流年{gz}{desc}"))
    scored.sort(key=lambda x: (-x[0], x[1]))
    return [s[1] for s in scored[:limit]]


def _dayun_triggers(
    dayun: list[dict],
    branches: dict[str, str],
    stems: dict[str, str] | None = None,
) -> list[dict[str, str]]:
    """大运/流年引动年、月支 → 应期（按年龄升序，优先早年）。"""
    stems = stems or {}
    year_b = branches.get("year", "")
    month_b = branches.get("month", "")
    year_s = stems.get("year", "")
    month_s = stems.get("month", "")
    ranked: list[tuple[int, int, dict[str, str]]] = []

    for d in dayun[:12]:
        dy = d.get("ganzhi", "")
        if len(dy) < 2:
            continue
        ds, db = dy[0], dy[1]
        note_parts: list[str] = []
        score = 0
        for label, tb in (("年", year_b), ("月", month_b)):
            for desc, weight in _branch_hits(db, tb, label):
                note_parts.append(f"大运{dy}{desc}")
                score += weight
        for label, ts in (("年", year_s), ("月", month_s)):
            tag = _pair_tag(ds, ts, TIANGAN_CHONG)
            if tag:
                note_parts.append(f"大运{dy}{tag}({label}干)")
                score += 2
        liu = _liunian_parent_hits(d.get("liunian") or [], year_b, month_b)
        if liu:
            note_parts.append("流年应期：" + "；".join(liu))
            score += len(liu)
        if not note_parts:
            continue
        start_age = int(d.get("start_age") or 0)
        ranked.append((
            start_age,
            -score,
            {
                "dayun": dy,
                "years": f"{d.get('start_year')}-{d.get('end_year')}",
                "ages": f"{d.get('start_age')}-{d.get('end_age')}岁",
                "note": "；".join(note_parts),
            },
        ))

    ranked.sort(key=lambda x: (x[0], x[1]))
    return [item for _, _, item in ranked[:8]]


def analyze(chart: dict[str, Any]) -> dict[str, Any]:
    meta = chart.get("meta", {})
    pillars = chart.get("pillars", [])
    gender = meta.get("gender", "male")
    relations = chart.get("pillars_relations") or []
    branches = _pillar_branches(pillars)
    stems = _pillar_stems(pillars)
    liuqin_map = LIUQIN_MALE if gender == "male" else LIUQIN_FEMALE

    father_star = liuqin_map["father"]
    mother_star = liuqin_map["mother"]
    spouse_star = liuqin_map["spouse"]
    father_locs = _find_shishen(pillars, father_star)
    mother_locs = _find_shishen(pillars, mother_star)
    spouse_locs = _find_shishen(pillars, spouse_star)

    ym_harm = _year_month_harm(branches, stems)
    dayun_trig = _dayun_triggers(chart.get("dayun", []), branches, stems)

    items: list[dict[str, Any]] = []

    # —— 父母 ——
    parent_score = 0
    parent_reasons: list[str] = []
    if ym_harm:
        parent_score += 3 * len(ym_harm)
        parent_reasons.extend([f"父母宫（年月）{h}，主家宅不安、父母缘薄或分离" for h in ym_harm])
    for r in relations:
        if "自刑" in r and "酉" in r and branches.get("year") == "酉":
            parent_score += 2
            parent_reasons.append("年支酉与命局酉自刑，父母宫自刑，主家庭内部矛盾、父母关系紧张")
        if "冲" in r and ("年" in r or "月" in r):
            parent_score += 2
            parent_reasons.append(f"四柱{r}，冲及父母宫位")

    # 子酉破：月支子与年/时支酉（父母宫常见组合）
    mb, yb, hb = branches.get("month"), branches.get("year"), branches.get("hour")
    if mb == "子" and yb == "酉":
        parent_score += 3
        parent_reasons.append("年支酉与月支子相破，父母宫破，主父母不和、离异或长期分居（千里命稿）")
    if mb == "子" and hb == "酉":
        parent_score += 1
        parent_reasons.append("月支子与时支酉相破，家宅后期亦多变动")

    if len(mother_locs) >= 2 and not father_locs:
        parent_score += 2
        parent_reasons.append(f"母星({mother_star})叠见而父星({father_star})不现，父缘弱、母权偏重，家庭结构易失衡")
    elif len(mother_locs) >= 2:
        parent_score += 1
        parent_reasons.append(f"母星({mother_star})重见，家庭决策多系于母")

    if parent_score >= 4:
        verdict = "父母有较明显离异、分居或长期冷战之象"
        level = "强"
    elif parent_score >= 2:
        verdict = "父母缘分薄，易争吵、分离或一方缺位"
        level = "中"
    else:
        verdict = "父母宫未见大破，家庭基础相对平稳"
        level = "弱"

    parent_windows = [w for w in dayun_trig if "年" in w.get("note", "")]
    items.append({
        "topic": "父母",
        "verdict": verdict,
        "level": level,
        "reasons": parent_reasons or ["年月未见重冲，父母宫无显著破格"],
        "windows": parent_windows[:4],
        "source": "千里命稿",
    })

    # —— 婚姻 ——
    marriage_score = 0
    marriage_reasons: list[str] = []
    day_branch = branches.get("day", "")
    if day_branch == branches.get("month"):
        marriage_score += 1
        marriage_reasons.append("日支与月支同气，桃花/internal 感情易早定或受家庭影响")
    for r in relations:
        if "冲" in r and ("日" in r or "卯酉" in r):
            marriage_score += 2
            marriage_reasons.append(f"{r}，婚姻宫动，主感情波折、分合")
        if "子卯" in r:
            marriage_score += 1
            marriage_reasons.append("子卯刑，桃花刑，感情是非")
    if not spouse_locs:
        marriage_reasons.append(f"{'夫' if gender == 'female' else '妻'}星({spouse_star})不现，姻缘宜晚或经波折")
    items.append({
        "topic": "婚姻",
        "verdict": "婚姻易有波折、晚成或经分合" if marriage_score >= 2 else "婚姻平平稳稳为主，看大运引动",
        "level": "强" if marriage_score >= 3 else ("中" if marriage_score >= 1 else "弱"),
        "reasons": marriage_reasons or ["婚姻宫未见大冲"],
        "windows": [w for w in dayun_trig if "日" in w.get("note", "")][:3],
        "source": "渊海子平",
    })

    # —— 财运 ——
    items.append({
        "topic": "财运",
        "verdict": "比劫重则争财，财星透则有机会" if len(_find_shishen(pillars, "比肩")) >= 2 else "随大运喜忌流转",
        "level": "中",
        "reasons": ["以财星、比劫与大运配合论"],
        "windows": dayun_trig[:3],
        "source": "子平",
    })

    summary_parts = [f"{i['topic']}:{i['verdict']}" for i in items[:2]]
    return {
        "kernel": KERNEL,
        "items": items,
        "summary": "；".join(summary_parts),
        "liuqin": {
            "father": {"star": father_star, "locations": father_locs},
            "mother": {"star": mother_star, "locations": mother_locs},
            "spouse": {"star": spouse_star, "locations": spouse_locs},
        },
        "year_month_harm": ym_harm,
    }
