# -*- coding: utf-8 -*-
"""渊海子平 · 喜用神倾向（扶抑/调候/通关，非唯一定论）。"""
from __future__ import annotations

from app.core.constants import TIANGAN_WUXING

KERNEL = "渊海子平"

STEM_TO_WX = TIANGAN_WUXING
WX_ORDER = ("木", "火", "土", "金", "水")


def _wx(stem: str) -> str:
    return STEM_TO_WX.get(stem, "")


def _tiao_hou_elements(hint: str) -> list[str]:
    """从调候文案提取五行倾向。"""
    found: list[str] = []
    for wx in WX_ORDER:
        if wx in hint:
            found.append(wx)
    for stem, wx in STEM_TO_WX.items():
        if stem in hint and wx not in found:
            found.append(wx)
    return found


def _tongguan_from_relations(relations: list[str]) -> str | None:
    """从刑冲合害推断通关五行。"""
    pairs = [
        (("寅", "申"), "水"),  # 金木
        (("卯", "酉"), "水"),
        (("巳", "亥"), "木"),  # 水火
        (("午", "子"), "木"),
        (("辰", "戌"), "金"),  # 土土
        (("丑", "未"), "金"),
    ]
    rel_text = " ".join(relations)
    for (a, b), tg in pairs:
        if (a in rel_text and b in rel_text) or f"{a}{b}" in rel_text.replace(" ", ""):
            return tg
    return None


def analyze(
    chart: dict[str, Any],
    *,
    strength: str,
    tiao_hou: str,
    geju: dict[str, Any] | None = None,
) -> dict[str, Any]:
    relations = chart.get("pillars_relations") or []
    wx_stats = chart.get("wuxing_stats", {})
    tendencies: list[dict[str, str]] = []

    if strength == "偏弱":
        tendencies.append({
            "method": "扶抑",
            "element": "印比",
            "reason": "日主偏弱，宜印绶生身、比劫帮身（渊海子平）",
            "source": "渊海子平",
        })
    elif strength == "偏强":
        tendencies.append({
            "method": "扶抑",
            "element": "食伤财官",
            "reason": "日主偏强，宜食伤泄秀、财星耗身或官杀制身（渊海子平）",
            "source": "渊海子平",
        })
    else:
        tendencies.append({
            "method": "扶抑",
            "element": "平衡",
            "reason": "日主中和，随大运流年喜忌流转（滴天髓）",
            "source": "滴天髓",
        })

    th_wx = _tiao_hou_elements(tiao_hou)
    if th_wx:
        tendencies.append({
            "method": "调候",
            "element": "、".join(th_wx),
            "reason": f"穷通调候：{tiao_hou[:40]}{'…' if len(tiao_hou) > 40 else ''}",
            "source": "穷通宝鉴",
        })

    tg = _tongguan_from_relations(relations)
    if tg:
        tendencies.append({
            "method": "通关",
            "element": tg,
            "reason": f"四柱有交战，宜{tg}气流通（滴天髓气势）",
            "source": "滴天髓",
        })

    if wx_stats:
        max_wx = max(wx_stats, key=lambda k: wx_stats.get(k, 0))
        min_wx = min(wx_stats, key=lambda k: wx_stats.get(k, 0))
        if wx_stats.get(max_wx, 0) - wx_stats.get(min_wx, 0) >= 3:
            tendencies.append({
                "method": "平衡",
                "element": min_wx,
                "reason": f"五行{max_wx}偏旺、{min_wx}偏弱，宜补{min_wx}（子平五行）",
                "source": "子平",
            })

    geju_type = (geju or {}).get("type", "")
    if geju_type and geju_type not in ("正格",):
        xiang = (geju or {}).get("purity", {}).get("xiang_shen") or []
        if xiang:
            tendencies.append({
                "method": "格局",
                "element": "、".join(xiang),
                "reason": f"{geju_type}宜见相神{'、'.join(xiang)}（子平真诠）",
                "source": "子平真诠",
            })

    summary_parts = [f"{t['method']}→{t['element']}" for t in tendencies[:4]]
    return {
        "kernel": KERNEL,
        "tendencies": tendencies,
        "summary": "；".join(summary_parts),
        "note": "以上为喜用神倾向参考，须合大运流年，不作唯一用神定论（PRODUCT 约定）",
    }
