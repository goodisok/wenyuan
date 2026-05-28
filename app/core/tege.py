# -*- coding: utf-8 -*-
"""
特格 · 特殊格局判定（优先于八正格）

根据《子平真诠》《滴天髓阐微》《渊海子平》各家论断，
系统化判定专旺格、从格、化气格等特殊格局。

优先级：专旺五格 → 从格四类 → 化气格 → 非特格（降级到八正格）
"""
from __future__ import annotations

from typing import Any

from app.core.constants import DIZHI_CANGGAN, DIZHI_WUXING, TIANGAN_WUXING

KERNEL = "特格"

# ── 专旺格基础映射 ──────────────────────────────────────────

ZHUANWANG: dict[str, dict[str, Any]] = {
    "甲": {
        "type": "曲直仁寿格",
        "wuxing": "木",
        "branches": frozenset(("寅", "卯", "亥")),
        "month": frozenset(("寅", "卯")),
        "he": "亥卯未",
        "hui": "寅卯辰",
        "desc": "甲/乙日，地支全木局或木旺，无金破格。顺木之势（子平真诠）",
    },
    "乙": {
        "type": "曲直仁寿格",
        "wuxing": "木",
        "branches": frozenset(("寅", "卯", "亥")),
        "month": frozenset(("寅", "卯")),
        "he": "亥卯未",
        "hui": "寅卯辰",
        "desc": "甲/乙日，地支全木局或木旺，无金破格。顺木之势（子平真诠）",
    },
    "丙": {
        "type": "炎上格",
        "wuxing": "火",
        "branches": frozenset(("巳", "午")),
        "month": frozenset(("巳", "午")),
        "he": "寅午戌",
        "hui": "巳午未",
        "desc": "丙/丁日，地支全火局或火旺，无水破格。顺火之势（子平真诠）",
    },
    "丁": {
        "type": "炎上格",
        "wuxing": "火",
        "branches": frozenset(("巳", "午")),
        "month": frozenset(("巳", "午")),
        "he": "寅午戌",
        "hui": "巳午未",
        "desc": "丙/丁日，地支全火局或火旺，无水破格。顺火之势（子平真诠）",
    },
    "戊": {
        "type": "稼穑格",
        "wuxing": "土",
        "branches": frozenset(("辰", "戌", "丑", "未")),
        "month": frozenset(("辰", "戌", "丑", "未")),
        "he": "",
        "hui": "",
        "desc": "戊/己日，地支辰戌丑未齐全或土旺。顺土之势（渊海子平）",
    },
    "己": {
        "type": "稼穑格",
        "wuxing": "土",
        "branches": frozenset(("辰", "戌", "丑", "未")),
        "month": frozenset(("辰", "戌", "丑", "未")),
        "he": "",
        "hui": "",
        "desc": "戊/己日，地支辰戌丑未齐全或土旺。顺土之势（渊海子平）",
    },
    "庚": {
        "type": "从革格",
        "wuxing": "金",
        "branches": frozenset(("申", "酉")),
        "month": frozenset(("申", "酉")),
        "he": "巳酉丑",
        "hui": "申酉戌",
        "desc": "庚/辛日，地支合金局或金旺，无火破格。顺金之势（子平真诠）",
    },
    "辛": {
        "type": "从革格",
        "wuxing": "金",
        "branches": frozenset(("申", "酉")),
        "month": frozenset(("申", "酉")),
        "he": "巳酉丑",
        "hui": "申酉戌",
        "desc": "庚/辛日，地支合金局或金旺，无火破格。顺金之势（子平真诠）",
    },
    "壬": {
        "type": "润下格",
        "wuxing": "水",
        "branches": frozenset(("亥", "子")),
        "month": frozenset(("亥", "子")),
        "he": "申子辰",
        "hui": "亥子丑",
        "desc": "壬/癸日，地支全水局或水旺，无土破格。顺水之势（子平真诠）",
    },
    "癸": {
        "type": "润下格",
        "wuxing": "水",
        "branches": frozenset(("亥", "子")),
        "month": frozenset(("亥", "子")),
        "he": "申子辰",
        "hui": "亥子丑",
        "desc": "壬/癸日，地支全水局或水旺，无土破格。顺水之势（子平真诠）",
    },
}

# ── 从格类型说明 ────────────────────────────────────────────

CONG_TYPES: dict[str, dict[str, Any]] = {
    "从杀格": {
        "shishen": "七杀",
        "dominant": ("七杀", "正官"),
        "desc": "日主极弱，官杀当令透干，全局官杀主导。顺杀之势（子平真诠）",
        "ai_suggestion": "真从杀者格局清纯，宜顺杀势；假从杀者大运见扶身为破格之期",
    },
    "从财格": {
        "shishen": "正财",
        "dominant": ("正财", "偏财"),
        "desc": "日主极弱，财星当令透干，全局财星主导。顺财之势（滴天髓）",
        "ai_suggestion": "真从财者富格，宜行财官食伤运；见比劫运破格",
    },
    "从儿格": {
        "shishen": "食神",
        "dominant": ("食神", "伤官"),
        "desc": "日主极弱，食伤当令透干，全局食伤主导。顺食伤之势（滴天髓）",
        "ai_suggestion": "从儿格喜顺泄，见印运破格；食伤生财为顺局",
    },
    "从旺格": {
        "shishen": "比肩",
        "dominant": ("比肩", "劫财", "正印", "偏印"),
        "desc": "日主极旺，全局比劫印绶主导，无克泄耗。顺旺势（滴天髓体用）",
        "ai_suggestion": "从旺格局，宜行印比运；见财官食伤为逆局破格",
    },
}

# ── 化气格 ───────────────────────────────────────────────────

HUAQI: dict[frozenset[str], dict[str, Any]] = {
    frozenset(("甲", "己")): {"hua": "土", "month": ("辰", "戌", "丑", "未"), "desc": "甲己合化土，化神当令得地"},
    frozenset(("乙", "庚")): {"hua": "金", "month": ("申", "酉"), "desc": "乙庚合化金，化神当令得地"},
    frozenset(("丙", "辛")): {"hua": "水", "month": ("亥", "子"), "desc": "丙辛合化水，化神当令得地"},
    frozenset(("丁", "壬")): {"hua": "木", "month": ("寅", "卯"), "desc": "丁壬合化木，化神当令得地"},
    frozenset(("戊", "癸")): {"hua": "火", "month": ("巳", "午"), "desc": "戊癸合化火，化神当令得地"},
}


# ═══════════════════════════════════════════════════════════
#  辅助函数
# ═══════════════════════════════════════════════════════════

def _extract_pillars(chart: dict[str, Any]) -> list[dict]:
    return chart.get("pillars", [])


def _day_stem(chart: dict[str, Any]) -> str:
    return chart.get("meta", {}).get("day_master", "")


def _day_wx(chart: dict[str, Any]) -> str:
    return chart.get("meta", {}).get("day_master_wuxing", "")


def _month_branch(pillars: list[dict]) -> str:
    return pillars[1]["dizhi"]["name"] if len(pillars) > 1 else ""


def _month_stem(pillars: list[dict]) -> str:
    return pillars[1]["tiangan"]["name"] if len(pillars) > 1 else ""


def _year_stem(pillars: list[dict]) -> str:
    return pillars[0]["tiangan"]["name"] if len(pillars) > 0 else ""


def _all_branches(pillars: list[dict]) -> list[str]:
    return [p["dizhi"]["name"] for p in pillars]


def _all_stems(pillars: list[dict]) -> list[str]:
    """四柱天干（不含日主？不，包含）"""
    return [p["tiangan"]["name"] for p in pillars]


def _stem_shishen_map(pillars: list[dict]) -> dict[str, str]:
    """天干 → 十神（含日主）"""
    return {p["tiangan"]["name"]: p["shishen"] for p in pillars}


def _all_shishen_stems(pillars: list[dict]) -> list[tuple[str, str]]:
    """(天干, 十神) 不含日主"""
    out = []
    for p in pillars:
        if p["key"] == "day":
            continue
        out.append((p["tiangan"]["name"], p["shishen"]))
    return out


def _hidden_shishen_counts(pillars: list[dict]) -> dict[str, float]:
    """统计藏干的十神类型加权个数"""
    counts: dict[str, float] = {}
    weights = (1.0, 0.6, 0.3)
    for p in pillars:
        for i, cg in enumerate(p["dizhi"]["canggan"]):
            ss = cg.get("shishen", "")
            if ss:
                w = weights[i] if i < len(weights) else 0.2
                counts[ss] = counts.get(ss, 0) + w
    return counts


def _stem_shishen_counts(pillars: list[dict]) -> dict[str, float]:
    """统计天干十神类型个数（不含日主）"""
    counts: dict[str, float] = {}
    for stem, ss in _all_shishen_stems(pillars):
        counts[ss] = counts.get(ss, 0) + 1
    return counts


def _total_shishen_counts(pillars: list[dict]) -> dict[str, float]:
    """天干+藏干的十神综合统计"""
    counts = _stem_shishen_counts(pillars)
    hidden = _hidden_shishen_counts(pillars)
    for ss, cnt in hidden.items():
        counts[ss] = counts.get(ss, 0) + cnt
    return counts


def _day_root_score(pillars: list[dict], day_stem: str) -> float:
    """日主通根得分（与 ditiansui._tong_gen 一致）"""
    day_wx = TIANGAN_WUXING.get(day_stem, "")
    weights = (1.0, 0.6, 0.3)
    total = 0.0
    for p in pillars:
        for i, cg in enumerate(p["dizhi"]["canggan"]):
            cg_wx = TIANGAN_WUXING.get(cg["name"], "")
            w = weights[i] if i < len(weights) else 0.2
            if cg_wx == day_wx or cg.get("shishen", "") in ("正印", "偏印", "比肩", "劫财"):
                total += w * 0.8
    return round(total, 2)


def _day_stem_help(pillars: list[dict], day_stem: str) -> list[str]:
    """天干生扶日主的十神和天干"""
    helps = []
    for stem, ss in _all_shishen_stems(pillars):
        if ss in ("正印", "偏印", "比肩", "劫财"):
            helps.append(stem)
    return helps


def _has_sanhe(branches: list[str], he_stems: str) -> bool:
    """检测地支是否有某三合局（至少两字算半合）"""
    if not he_stems:
        return False
    needed = set(he_stems)
    present = set(branches) & needed
    return len(present) >= 2


def _has_sanhui(branches: list[str], hui_stems: str) -> bool:
    """检测地支是否有某三会方"""
    if not hui_stems:
        return False
    needed = set(hui_stems)
    present = set(branches) & needed
    return len(present) >= 2


def _killer_present(pillars: list[dict], killer_wuxing: str) -> list[str]:
    """检测是否有克制专旺格的五行在天干或地支突出"""
    killers = []
    # 天干
    for stem, _ in _all_shishen_stems(pillars):
        wx = TIANGAN_WUXING.get(stem, "")
        if wx == killer_wuxing:
            killers.append(stem)
    # 地支
    for p in pillars:
        dz = p["dizhy"]["name"]
        dz_wx = DIZHI_WUXING.get(dz, "")
        if dz_wx == killer_wuxing:
            killers.append(dz)
    return killers


def _get_opp_wuxing(wx: str) -> str:
    """返回克制某五行的五行"""
    controls = {"木": "金", "火": "水", "土": "木", "金": "火", "水": "土"}
    return controls.get(wx, "")


# ═══════════════════════════════════════════════════════════
#  专旺五格判定
# ═══════════════════════════════════════════════════════════

def _check_zhuangwang(chart: dict[str, Any]) -> dict[str, Any] | None:
    """
    判定专旺五格：曲直仁寿/炎上/稼穑/从革/润下

    核心条件：
    1. 日主体性匹配（甲木→曲直、丙火→炎上等）
    2. 地支会合该五行局（三合/三会/至少两字）
    3. 月令在当旺之月
    4. 该五行占比 > 50%
    5. 无克破五行明显出现（如曲直格金不显）
    """
    day_stem = _day_stem(chart)
    if day_stem not in ZHUANWANG:
        return None

    zw = ZHUANWANG[day_stem]
    pillars = _extract_pillars(chart)
    branches = _all_branches(pillars)
    month_branch = _month_branch(pillars)
    wx_stats = chart.get("wuxing_stats", {})
    target_wx = zw["wuxing"]
    opp_wx = _get_opp_wuxing(target_wx)
    branches_set = frozenset(branches)
    target_branches = zw["branches"]

    evidence: list[str] = []

    # ── 条件1：月令是否在旺月 ──
    month_ok = month_branch in zw["month"]
    if month_ok:
        evidence.append(f"月令{month_branch}为{target_wx}旺地")

    # ── 条件2：三合/三会/至少两字 ──
    has_he = _has_sanhe(branches, zw.get("he", ""))
    has_hui = _has_sanhui(branches, zw.get("hui", ""))
    branch_count = len(branches_set & target_branches)

    if has_he:
        evidence.append(f"地支{zw['he']}合{target_wx}局")
    elif has_hui:
        evidence.append(f"地支{zw['hui']}会{target_wx}方")
    else:
        evidence.append(f"地支{target_wx}字{branch_count}支")

    # ── 条件3：该五行占比 ──
    target_pct = wx_stats.get(target_wx, 0) / max(sum(wx_stats.values()), 1)
    if target_pct >= 0.45:
        evidence.append(f"{target_wx}占比{target_pct:.0%}")
    else:
        # 占比不够，除非三合/三会全且有月令
        if not (has_he and month_ok) and not (has_hui and month_ok):
            return None

    # ── 条件4：克泄耗五行检查 ──
    # 专旺格不仅忌克，还忌泄（我生）和耗（我克）
    # 天干只允许出现生扶该五行的字（印/比劫）
    generates = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
    controls = {"木": "金", "火": "水", "土": "木", "金": "火", "水": "土"}
    
    opp_wx = controls.get(target_wx, "")  # 克我的（官杀）
    drain_wx = generates.get(target_wx, "")  # 我生的（食伤→泄）
    consume_wx = [k for k, v in controls.items() if v == target_wx]  # 我克的（财→耗）
    consume_wx = consume_wx[0] if consume_wx else ""
    
    # 定义禁神（天干中不能出现的五行）
    forbidden = set()
    if opp_wx: forbidden.add(opp_wx)
    if drain_wx: forbidden.add(drain_wx)
    if consume_wx: forbidden.add(consume_wx)
    
    # 天干禁神检查
    stem_forbidden = [(s, TIANGAN_WUXING.get(s, "")) for s in _all_stems(pillars) 
                      if TIANGAN_WUXING.get(s, "") in forbidden]
    
    # 天干有禁神 → 非真专旺，返回None
    # 禁神出现在天干表示格局有根本性的破格，不论是否休囚
    if stem_forbidden:
        evidence.append("天干见禁神%s，非纯净专旺格" % "、".join(s for s, w in stem_forbidden))
        return None
    
    # 无天干预神，可判定为真专旺
    purity = "真"
    opp_pct = 0

    # 反推：稼穑格不需要三合/三会
    if zw["type"] == "稼穑格":
        earth_branches = len(branches_set & frozenset(("辰", "戌", "丑", "未")))
        if earth_branches < 3 and target_pct < 0.50:
            return None
        if earth_branches >= 3:
            evidence.append(f"地支四土见{earth_branches}，土气极盛")
        purity = "真" if earth_branches >= 3 and opp_pct < 0.25 else "假"

    if purity != "真":
        # 假专旺（有破格因素）不作为格局覆盖，降级到八正格
        # AI的提示词中仍可通过 evidence 获取线索
        return None

    note = f'{zw["type"]}（{purity}）'
    purity_note = f"{purity}专旺，格局清纯"

    return {
        "type": zw["type"],
        "is_special": True,
        "confidence": 0.85 if purity == "真" else 0.70,
        "purity": purity,
        "origin": "专旺格",
        "evidence": evidence,
        "note": note,
        "desc": zw["desc"],
        "ai_suggestion": f"此命为{purity}专旺格，宜顺其旺势，忌逆克。大运见{opp_wx}为破格之期",
    }


# ═══════════════════════════════════════════════════════════
#  从格判定
# ═══════════════════════════════════════════════════════════

def _check_congge(chart: dict[str, Any]) -> dict[str, Any] | None:
    """
    判定从格：从杀/从财/从儿/从旺

    从杀/从财/从儿核心条件：
    1. 日主极弱：失令 + 无根(得分<0.3) + 无助(无比劫印透出)
    2. 某十神占绝对主导（当令透干）

    从旺格：
    1. 日主极旺：得令 + 多通根 + 多比劫印绶
    2. 无克泄耗或极少
    """
    day_stem = _day_stem(chart)
    pillars = _extract_pillars(chart)
    month_branch = _month_branch(pillars)
    wx_stats = chart.get("wuxing_stats", {})

    # ── 基础判断：日主强度 ──
    root_score = _day_root_score(pillars, day_stem)
    stem_helps = _day_stem_help(pillars, day_stem)
    total = sum(wx_stats.values())

    # 月令是否为日主五行
    day_wx = _day_wx(chart)
    month_wx = DIZHI_WUXING.get(month_branch, "")
    de_ling = month_wx == day_wx

    # ── 日主综合强度 ──
    is_extreme_weak = root_score < 0.3 and not stem_helps and not de_ling
    is_extreme_strong = root_score >= 1.5 and de_ling and len(stem_helps) >= 1

    if not is_extreme_weak and not is_extreme_strong:
        return None

    # ── 各十神统计 ──
    shishen_counts = _total_shishen_counts(pillars)

    # 分类汇总
    guan_count = shishen_counts.get("七杀", 0) + shishen_counts.get("正官", 0)
    cai_count = shishen_counts.get("正财", 0) + shishen_counts.get("偏财", 0)
    shi_count = shishen_counts.get("食神", 0) + shishen_counts.get("伤官", 0)
    yin_count = shishen_counts.get("正印", 0) + shishen_counts.get("偏印", 0)
    bi_count = shishen_counts.get("比肩", 0) + shishen_counts.get("劫财", 0)

    total_shishen = guan_count + cai_count + shi_count + yin_count + bi_count
    if total_shishen == 0:
        return None

    # ── 从旺格 ──
    if is_extreme_strong:
        ke_xie_hao = guan_count + cai_count + shi_count
        bi_yin_total = yin_count + bi_count
        if bi_yin_total > 0 and ke_xie_hao < bi_yin_total * 0.5:
            evidence = ["日主极旺：得令多根多比印"]
            wx_pct = wx_stats.get(day_wx, 0) / max(total, 1)
            evidence.append(f"{day_wx}占比{wx_pct:.0%}")
            if ke_xie_hao == 0:
                purity = "真"
                evidence.append("全局无比劫印绶以外的十神")
            else:
                purity = "假"
                evidence.append(f"有少量克泄耗({ke_xie_hao}处)")
            note = f"从旺格（{purity}），{CONG_TYPES['从旺格']['desc']}"
            return {
                "type": "从旺格",
                "is_special": True,
                "confidence": 0.85 if purity == "真" else 0.65,
                "purity": "真从旺" if purity == "真" else "假从旺",
                "origin": "从格判定",
                "evidence": evidence,
                "note": note,
                "ai_suggestion": CONG_TYPES["从旺格"]["ai_suggestion"],
            }
        return None

    # ── 从杀/从财/从儿（日主极弱） ──

    # 月令判断
    month_shishen = pillars[1]["shishen"]
    month_hidden_ss = {cg.get("shishen", "") for cg in pillars[1]["dizhi"]["canggan"]}

    # 天干透出
    stem_ss = _stem_shishen_counts(pillars)
    stem_guan = stem_ss.get("七杀", 0) + stem_ss.get("正官", 0)
    stem_cai = stem_ss.get("正财", 0) + stem_ss.get("偏财", 0)
    stem_shi = stem_ss.get("食神", 0) + stem_ss.get("伤官", 0)

    # 各类型候选得分
    candidates: list[tuple[str, float, str, list[str]]] = []

    # (1) 从杀格
    guan_score = guan_count
    guan_stem_ok = stem_guan >= 1 or month_shishen in ("七杀", "正官") or "七杀" in month_hidden_ss or "正官" in month_hidden_ss
    if guan_stem_ok and guan_count > cai_count + shi_count:
        evidence = ["日主极弱：无根无助失令"]
        evidence.append(f"官杀{guan_count}处占主导")
        if month_shishen in ("七杀", "正官"):
            evidence.append(f"月令{month_branch}为官杀")
        elif "七杀" in month_hidden_ss or "正官" in month_hidden_ss:
            evidence.append(f"月令{month_branch}藏官杀")
        if stem_guan >= 1:
            evidence.append(f"天干透官杀{int(stem_guan)}处")
        # 真从 vs 假从
        purity = "真" if yin_count == 0 and bi_count == 0 else "假"
        if purity == "假":
            evidence.append(f"见印比{int(yin_count+bi_count)}处，属假从")
        candidates.append(("从杀格", guan_score / max(total_shishen, 1), purity, evidence))

    # (2) 从财格
    cai_stem_ok = stem_cai >= 1 or month_shishen in ("正财", "偏财") or "正财" in month_hidden_ss or "偏财" in month_hidden_ss
    if cai_stem_ok and cai_count > guan_count + shi_count:
        evidence = ["日主极弱：无根无助失令"]
        evidence.append(f"财星{cai_count}处占主导")
        if month_shishen in ("正财", "偏财"):
            evidence.append(f"月令{month_branch}为财星")
        elif "正财" in month_hidden_ss or "偏财" in month_hidden_ss:
            evidence.append(f"月令{month_branch}藏财星")
        if stem_cai >= 1:
            evidence.append(f"天干透财{int(stem_cai)}处")
        purity = "真" if yin_count == 0 and bi_count == 0 else "假"
        if purity == "假":
            evidence.append(f"见印比{int(yin_count+bi_count)}处，属假从")
        candidates.append(("从财格", cai_count / max(total_shishen, 1), purity, evidence))

    # (3) 从儿格
    shi_stem_ok = stem_shi >= 1 or month_shishen in ("食神", "伤官") or "食神" in month_hidden_ss or "伤官" in month_hidden_ss
    if shi_stem_ok and shi_count > guan_count + cai_count:
        evidence = ["日主极弱：无根无助失令"]
        evidence.append(f"食伤{shi_count}处占主导")
        if month_shishen in ("食神", "伤官"):
            evidence.append(f"月令{month_branch}为食伤")
        elif "食神" in month_hidden_ss or "伤官" in month_hidden_ss:
            evidence.append(f"月令{month_branch}藏食伤")
        if stem_shi >= 1:
            evidence.append(f"天干透食伤{int(stem_shi)}处")
        purity = "真" if yin_count == 0 and bi_count == 0 else "假"
        if purity == "假":
            evidence.append(f"见印比{int(yin_count+bi_count)}处，属假从")
        candidates.append(("从儿格", shi_count / max(total_shishen, 1), purity, evidence))

    if not candidates:
        return None

    # 选得分最高的
    candidates.sort(key=lambda x: -x[1])
    best = candidates[0]

    if best[2] != "真":
        # 假从（有印比微根）不作为格局覆盖，降级到八正格
        return None

    return {
        "type": best[0],
        "is_special": True,
        "confidence": 0.85,
        "purity": f"真{best[0][1:]}",
        "origin": "从格判定",
        "evidence": best[3],
        "note": f"{best[0]}（{best[2]}从）",
        "desc": CONG_TYPES[best[0]]["desc"],
        "ai_suggestion": CONG_TYPES[best[0]]["ai_suggestion"],
    }


# ═══════════════════════════════════════════════════════════
#  化气格判定
# ═══════════════════════════════════════════════════════════

def _check_huaqi(chart: dict[str, Any]) -> dict[str, Any] | None:
    """
    化气格判定：天干合化。

    条件：
    1. 日干与月干或年干成五合（甲己、乙庚、丙辛、丁壬、戊癸）
    2. 合化之神当令（月支为化神旺地）
    3. 化神透出或得地
    """
    day_stem = _day_stem(chart)
    pillars = _extract_pillars(chart)
    month_branch = _month_branch(pillars)
    month_stem = _month_stem(pillars)
    year_stem = _year_stem(pillars)

    # 日干与月干或年干合
    partner = None
    for candidate in (month_stem, year_stem):
        if candidate and candidate != day_stem:
            key = frozenset((day_stem, candidate))
            if key in HUAQI:
                partner = candidate
                break

    if not partner:
        return None

    # 找到化气规则
    key = frozenset((day_stem, partner))
    hq = HUAQI[key]

    # 化神当令？
    hua_month = hq["month"]
    month_ok = month_branch in hua_month
    if not month_ok:
        # 月令不是化神旺地，化不成
        return None

    # 化神透干或得地
    hua_wx = hq["hua"]
    stems = _all_stems(pillars)
    # 天干有化神之五行
    stem_hua = [s for s in stems if TIANGAN_WUXING.get(s, "") == hua_wx]
    # 地支有化神之五行
    branches = _all_branches(pillars)
    branch_hua = [b for b in branches if DIZHI_WUXING.get(b, "") == hua_wx]

    evidence = [f"天干{day_stem}{partner}合"]
    evidence.append(f"月令{month_branch}为化神{hua_wx}旺地")
    if stem_hua:
        evidence.append(f"天干{''.join(stem_hua)}助化神")
    if branch_hua:
        evidence.append(f"地支{''.join(branch_hua)}助化神")

    note = f"{day_stem}{partner}合化{hua_wx}，化神当令得地。"
    return {
        "type": f"{day_stem}{partner}化{hua_wx}格",
        "is_special": True,
        "confidence": 0.70,
        "purity": "真",
        "origin": "化气格",
        "evidence": evidence,
        "note": note,
        "desc": hq['desc'],
        "ai_suggestion": f"化气格成，应以化神{hua_wx}为用，不宜逆化神之势",
    }


# ═══════════════════════════════════════════════════════════
#  主入口
# ═══════════════════════════════════════════════════════════

def analyze(chart: dict[str, Any]) -> dict[str, Any] | None:
    """
    特格判定的主入口。

    返回 None 表示非特格（降级到 ziping.py 的八正格判定）。
    返回 dict 表示检测到特格，格式与 ziping.analyze() 兼容。
    """
    # 按优先级依次检测
    checks = [
        ("专旺格", _check_zhuangwang),
        ("从格", _check_congge),
        ("化气格", _check_huaqi),
    ]

    for name, check_fn in checks:
        result = check_fn(chart)
        if result is not None:
            # 统一包装为与 ziping.analyze() 兼容的格式
            return _wrap_tege_result(result)

    return None


def _wrap_tege_result(tege: dict[str, Any]) -> dict[str, Any]:
    """将特格结果包装为与 ziping.analyze() 输出兼容的格式"""
    note = tege.get("note", "")
    desc = tege.get("desc", "")
    if desc and desc not in note:
        note += " " + desc
    
    return {
        "kernel": KERNEL,
        "type": tege["type"],
        "is_special": True,
        "shishen": CONG_TYPES.get(tege["type"], {}).get("shishen", ""),
        "origin": tege["origin"],
        "revealed": True,
        "purity": {
            "level": tege.get("purity", "真"),
            "note": note,
            "xiang_shen": [],
            "breaks": [],
        },
        "note": note,
        "source": "子平真诠",
        "confidence": tege.get("confidence", 0.7),
        "evidence": tege.get("evidence", []),
        "ai_suggestion": tege.get("ai_suggestion", ""),
    }


# 导出一个统一的接口，供 mingli.py 集成
def detect_special_pattern(chart: dict[str, Any]) -> dict[str, Any] | None:
    """
    统一特格检测接口。
    成功：返回特格 dict（可作为 geju 覆盖 ziping）
    失败：返回 None（走八正格）
    """
    return analyze(chart)
