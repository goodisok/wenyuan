# -*- coding: utf-8 -*-
"""
流年流月 · 应期细化

将大运流年分析从年精度细化到月精度。
对每个流年计算刑冲合害触发，标记关键月份。
"""
from __future__ import annotations

from typing import Any
from datetime import datetime

from app.core.constants import DIZHI_CANGGAN, DIZHI_WUXING, TIANGAN_WUXING

KERNEL = "应期"

# 地支关系表
DIZHI_HE = {
    ("子", "丑"): "子丑合", ("丑", "子"): "子丑合",
    ("寅", "亥"): "寅亥合", ("亥", "寅"): "寅亥合",
    ("卯", "戌"): "卯戌合", ("戌", "卯"): "卯戌合",
    ("辰", "酉"): "辰酉合", ("酉", "辰"): "辰酉合",
    ("巳", "申"): "巳申合", ("申", "巳"): "巳申合",
    ("午", "未"): "午未合", ("未", "午"): "午未合",
}

DIZHI_CHONG = {
    ("子", "午"): "子午冲", ("午", "子"): "子午冲",
    ("丑", "未"): "丑未冲", ("未", "丑"): "丑未冲",
    ("寅", "申"): "寅申冲", ("申", "寅"): "寅申冲",
    ("卯", "酉"): "卯酉冲", ("酉", "卯"): "卯酉冲",
    ("辰", "戌"): "辰戌冲", ("戌", "辰"): "辰戌冲",
    ("巳", "亥"): "巳亥冲", ("亥", "巳"): "巳亥冲",
}

DIZHI_CHUAN = {
    ("子", "未"): "子未穿", ("未", "子"): "子未穿",
    ("丑", "午"): "丑午穿", ("午", "丑"): "丑午穿",
    ("寅", "巳"): "寅巳穿", ("巳", "寅"): "寅巳穿",
    ("卯", "辰"): "卯辰穿", ("辰", "卯"): "卯辰穿",
    ("申", "亥"): "申亥穿", ("亥", "申"): "申亥穿",
    ("酉", "戌"): "酉戌穿", ("戌", "酉"): "酉戌穿",
}

DIZHI_PO = {
    ("子", "酉"): "子酉破", ("酉", "子"): "子酉破",
    ("寅", "亥"): "寅亥破", ("亥", "寅"): "寅亥破",
    ("卯", "午"): "卯午破", ("午", "卯"): "卯午破",
    ("辰", "丑"): "辰丑破", ("丑", "辰"): "辰丑破",
    ("巳", "申"): "巳申破", ("申", "巳"): "巳申破",
    ("未", "戌"): "未戌破", ("戌", "未"): "未戌破",
}

# 天干关系
TIANGAN_HE = {
    ("甲", "己"): "甲己合", ("己", "甲"): "甲己合",
    ("乙", "庚"): "乙庚合", ("庚", "乙"): "乙庚合",
    ("丙", "辛"): "丙辛合", ("辛", "丙"): "丙辛合",
    ("丁", "壬"): "丁壬合", ("壬", "丁"): "丁壬合",
    ("戊", "癸"): "戊癸合", ("癸", "戊"): "戊癸合",
}

# 月份→月支
MONTH_TO_BRANCH = {
    1: "寅", 2: "卯", 3: "辰", 4: "巳", 5: "午", 6: "未",
    7: "申", 8: "酉", 9: "戌", 10: "亥", 11: "子", 12: "丑",
}

# 月支对应月支的天干（依年干而定）
MONTH_STEM = {
    ("甲", "寅"): "丙", ("乙", "寅"): "戊", ("丙", "寅"): "庚",
    ("丁", "寅"): "壬", ("戊", "寅"): "甲", ("己", "寅"): "丙",
    ("庚", "寅"): "戊", ("辛", "寅"): "庚", ("壬", "寅"): "壬",
    ("癸", "寅"): "甲",
}

# 简版：按月支的天干——60甲子月表
# 年干决定寅月天干: 甲丙戊庚壬→丙戊庚壬甲
MONTH_STEM_START = {"甲": "丙", "乙": "戊", "丙": "庚", "丁": "壬", "戊": "甲",
                    "己": "丙", "庚": "戊", "辛": "庚", "壬": "壬", "癸": "甲"}


def _get_month_ganzhi(year_stem: str, month_num: int) -> str:
    """根据年干和月份数字（1-12），返回该月的干支"""
    month_branch = MONTH_TO_BRANCH[month_num]
    start = MONTH_STEM_START.get(year_stem, "丙")
    stems = "丙戊庚壬甲丙戊庚壬甲"
    idx = (month_num - 1) % 10
    month_stem = stems[(stems.index(start) + idx) % 10]
    return month_stem + month_branch


def _branch_relation(a: str, b: str) -> str | None:
    """返回两个地支之间的关系"""
    key = (a, b)
    if key in DIZHI_HE: return DIZHI_HE[key]
    if key in DIZHI_CHONG: return DIZHI_CHONG[key]
    if key in DIZHI_CHUAN: return DIZHI_CHUAN[key]
    if key in DIZHI_PO: return DIZHI_PO[key]
    return None


def _stem_relation(a: str, b: str) -> str | None:
    key = (a, b)
    if key in TIANGAN_HE: return TIANGAN_HE[key]
    return None


def analyze_liunian(chart: dict[str, Any], year: int | None = None) -> dict[str, Any]:
    """
    分析指定流年（或当前年份）的详细应期。
    返回年/月级别的刑冲合害触发。
    """
    if year is None:
        year = datetime.now().year
    
    pillars = chart.get("pillars", [])
    if len(pillars) < 4:
        return {"year": year, "error": "命盘不完整"}
    
    meta = chart.get("meta", {})
    month_branch = pillars[1]["dizhi"]["name"]
    year_stem = pillars[0]["tiangan"]["name"]
    day_stem = pillars[2]["tiangan"]["name"]
    
    # 推算出生年份
    dayun_list = chart.get("dayun", [])
    birth_year = meta.get("birth_year", 0)
    if not birth_year and dayun_list:
        birth_year = dayun_list[0].get("start_year", 0) - dayun_list[0].get("start_age", 1) + 1
    if not birth_year:
        birth_year = year - 30  # fallback
    
    # 流年干支（简单推算：年干+年支）
    # 完整排流年干支需要 lunar-python，这里用简算
    # 年干支 = (年干索引 + (year - base_year)) % 10 + (年支索引 + (year - base_year)) % 12
    stems = "甲乙丙丁戊己庚辛壬癸"
    branches = "子丑寅卯辰巳午未申酉戌亥"
    
    base_stem_idx = stems.find(year_stem)
    base_branch_idx = branches.find(pillars[0]["dizhi"]["name"])
    
    year_diff = year - birth_year
    current_stem_idx = (base_stem_idx + year_diff) % 10
    current_branch_idx = (base_branch_idx + year_diff) % 12
    liunian_ganzhi = stems[current_stem_idx] + branches[current_branch_idx]
    liunian_stem = liunian_ganzhi[0]
    liunian_branch = liunian_ganzhi[1]
    
    # ── 流年与四柱关系分析 ──
    year_triggers = []
    for p in pillars:
        p_label = p["label"]
        p_stem = p["tiangan"]["name"]
        p_branch = p["dizhi"]["name"]
        
        # 天干关系
        sr = _stem_relation(liunian_stem, p_stem)
        if sr:
            year_triggers.append({"type": "天干", "relation": sr, "target": p_label, "detail": "%s遇流年%s" % (p_label, sr)})
        
        # 地支关系
        br = _branch_relation(liunian_branch, p_branch)
        if br:
            year_triggers.append({"type": "地支", "relation": br, "target": p_label, "detail": "%s遇流年%s" % (p_label, br)})
    
    # ── 流月分析（12个月）──
    months = []
    for m in range(1, 13):
        month_gz = _get_month_ganzhi(liunian_stem, m)
        month_stem_c = month_gz[0]
        month_branch_c = month_gz[1]
        month_branch_name = MONTH_TO_BRANCH[m]
        
        month_triggers = []
        for p in pillars:
            p_label = p["label"]
            p_stem = p["tiangan"]["name"]
            p_branch = p["dizhi"]["name"]
            
            # 月与四柱地支关系
            br = _branch_relation(month_branch_c, p_branch)
            if br:
                month_triggers.append({"relation": br, "target": p_label})
        
        if month_triggers:
            months.append({
                "month": m,
                "month_name": "%d月" % m,
                "ganzhi": month_gz,
                "triggers": month_triggers,
                "trigger_count": len(month_triggers),
            })
    
    # ── 关键月份排序──
    months.sort(key=lambda x: -x["trigger_count"])
    key_months = [m for m in months if m["trigger_count"] >= 1][:6]
    
    return {
        "year": year,
        "liunian_ganzhi": liunian_ganzhi,
        "triggers": year_triggers,
        "trigger_count": len(year_triggers),
        "key_months": key_months,
        "total_months_with_triggers": len(months),
        "summary": _build_summary(liunian_ganzhi, year_triggers, key_months),
    }


def _build_summary(ganzhi: str, triggers: list, key_months: list) -> str:
    parts = ["流年%s" % ganzhi]
    if triggers:
        parts.append("触发%s" % "、".join(t["relation"] for t in triggers[:4]))
        if len(triggers) > 4:
            parts[-1] += "等"
    if key_months:
        month_names = [m["month_name"] for m in key_months[:4]]
        parts.append("关键月份：%s" % "、".join(month_names))
    return "；".join(parts)


def analyze_dayun_detail(chart: dict[str, Any]) -> dict[str, Any]:
    """
    分析所有大运的详细应期
    """
    dayun_list = chart.get("dayun", [])
    if not dayun_list:
        current_detail = analyze_liunian(chart, datetime.now().year)
        return {"kernel": KERNEL, "dayun_details": [], "current_year_detail": current_detail}
    
    result = []
    for dy in dayun_list:
        gz = dy.get("ganzhi", "")
        start = dy.get("start_year", 0)
        end = dy.get("end_year", 0)
        
        dy_stem = gz[0] if gz else ""
        dy_branch = gz[1] if len(gz) > 1 else ""
        
        # 大运与四柱关系
        pillars = chart.get("pillars", [])
        triggers = []
        for p in pillars:
            p_stem = p["tiangan"]["name"]
            p_branch = p["dizhi"]["name"]
            
            if dy_stem:
                sr = _stem_relation(dy_stem, p_stem)
                if sr:
                    triggers.append("%s之%s" % (p["label"], sr))
            
            if dy_branch:
                br = _branch_relation(dy_branch, p_branch)
                if br:
                    triggers.append("%s遇大运%s" % (p["label"], br))
        
        result.append({
            "ganzhi": gz,
            "start_year": start,
            "end_year": end,
            "triggers": triggers,
            "trigger_count": len(triggers),
        })
    
    # 当前年份分析
    current_year = datetime.now().year
    current_detail = analyze_liunian(chart, current_year)
    
    return {
        "kernel": KERNEL,
        "dayun_details": result,
        "current_year_detail": current_detail,
    }
