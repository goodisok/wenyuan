# -*- coding: utf-8 -*-
"""
子平综参 · 命理规则层

综合子平排盘、滴天髓体用、穷通宝鉴调候等各家要义，
输出程序可验证的结构化摘要，供 UI 与 AI 锚定。
"""
from __future__ import annotations

from typing import Any

from app.core.ditiansui import analyze as ditiansui_analyze
from app.core.qiongtong import lookup as qiongtong_lookup

KERNEL = "子平综参"
METHOD_NOTE = "综合子平、滴天髓、穷通宝鉴等典籍要义，倾向判断，非唯一流派结论"


def _shishen_summary(pillars: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for p in pillars:
        ss = p.get("shishen", "")
        if ss and ss != "日主":
            counts[ss] = counts.get(ss, 0) + 1
        for cg in p.get("dizhi", {}).get("canggan", []):
            css = cg.get("shishen", "")
            if css:
                counts[css] = counts.get(css, 0) + 1
    return dict(sorted(counts.items(), key=lambda x: -x[1]))


def _plain_highlights(
    meta: dict[str, Any],
    dts: dict[str, Any],
    qt: dict[str, str],
    relations: list[str],
) -> list[str]:
    """面向用户的白话要点。"""
    lines: list[str] = []
    dm = meta.get("day_master", "")
    wx = meta.get("day_master_wuxing", "")
    de = dts.get("de_ling", {})
    tg = dts.get("tong_gen", {})
    cl = dts.get("climate", {})
    pat = dts.get("pattern", {})

    lines.append(
        f"日主{dm}（{wx}），月令{de.get('month_branch', '')}，"
        f"时令{de.get('status', '')}，根气{tg.get('summary', '')}。"
    )
    if cl.get("note"):
        lines.append(f"季节气候：{cl.get('season', '')}{cl.get('climate', '')}，{cl.get('note')}。")
    if qt.get("hint"):
        lines.append(f"穷通宝鉴：{qt['hint']}。")
    sn = dts.get("stem_nature", {})
    if sn.get("image"):
        lines.append(f"滴天髓体象：{sn['image']}。")
    if pat.get("type"):
        lines.append(f"格局倾向：{pat['type']} — {pat.get('note', '')}")
    if relations:
        lines.append(f"四柱关系：{'、'.join(relations[:5])}" + ("…" if len(relations) > 5 else ""))
    return lines


def analyze(chart: dict[str, Any]) -> dict[str, Any]:
    meta = chart.get("meta", {})
    pillars = chart.get("pillars", [])
    day_stem = meta.get("day_master", "")
    month_branch = pillars[1]["dizhi"]["name"] if len(pillars) > 1 else ""

    dts = ditiansui_analyze(chart)
    qt = qiongtong_lookup(day_stem, month_branch)
    relations = chart.get("pillars_relations") or []
    shishen = _shishen_summary(pillars)

    # 调候：穷通为主，滴天髓互参
    tiao_hou = qt["hint"]
    dts_tiao = dts.get("tiao_hou", "")
    if dts_tiao and dts_tiao != tiao_hou and "酌取" not in tiao_hou:
        tiao_hou = f"{tiao_hou}；滴天髓：{dts_tiao}"

    highlights = _plain_highlights(meta, dts, qt, relations)

    return {
        "kernel": KERNEL,
        "method_note": METHOD_NOTE,
        "day_master_strength": dts.get("day_master_strength", "平衡"),
        "strength_score": dts.get("strength_score"),
        "stem_nature": dts.get("stem_nature"),
        "de_ling": dts.get("de_ling"),
        "tong_gen": dts.get("tong_gen"),
        "de_zhu": dts.get("de_zhu"),
        "climate": dts.get("climate"),
        "tiao_hou": tiao_hou,
        "qiongtong": qt,
        "ditiansui": dts,
        "shishen_summary": shishen,
        "pattern": dts.get("pattern"),
        "changsheng_map": dts.get("changsheng_map"),
        "highlights": highlights,
        "sources": ["子平", "滴天髓", "穷通宝鉴"],
    }
