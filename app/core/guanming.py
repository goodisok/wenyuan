# -*- coding: utf-8 -*-
"""
观命总观 · 滴天髓天道/地道/人道

将盘上可直接读出的结构层信息汇总，供 UI 与 AI 优先展开。
人事断语仍由 duanshi / sanguan（publish 过滤）单独呈现。
"""
from __future__ import annotations

from typing import Any

KERNEL = "观命总观"
METHOD = "依滴天髓天道（天干）、地道（地支）、人道（旺衰根气）及子平格局、穷通调候综参"


def _shishen_line(summary: dict[str, int]) -> str:
    if not summary:
        return "十神分布未计"
    parts = [f"{k}{v}" for k, v in list(summary.items())[:6]]
    return "、".join(parts)


def _flow_note(relations: list[str], yongshen: dict[str, Any], pattern: dict[str, Any]) -> str:
    if not relations:
        base = "四柱地支未见明显刑冲合害破穿，气机相对单纯"
    elif len(relations) <= 2:
        base = f"见{'、'.join(relations)}，须论通关与做功"
    else:
        base = f"关系繁复：{'、'.join(relations[:4])}" + ("…" if len(relations) > 4 else "")
    ys = yongshen.get("summary", "")
    if ys:
        base += f"；喜用倾向：{ys}"
    pat = pattern.get("note", "")
    if pat and pattern.get("type") not in ("", "正格"):
        base += f"；{pat}"
    return base


def build_guanming(
    chart: dict[str, Any],
    *,
    dts: dict[str, Any],
    geju: dict[str, Any],
    yongshen: dict[str, Any],
    shensha: dict[str, Any],
    shishen_summary: dict[str, int],
    tiao_hou: str,
    relations: list[str],
    current_dayun: dict[str, Any] | None = None,
    current_liunian: dict[str, Any] | None = None,
) -> dict[str, Any]:
    meta = chart.get("meta", {})
    pillars = chart.get("pillars", [])
    dm = meta.get("day_master", "")
    wx = meta.get("day_master_wuxing", "")
    de = dts.get("de_ling", {})
    tg = dts.get("tong_gen", {})
    dz = dts.get("de_zhu", {})
    cl = dts.get("climate", {})
    body_pat = dts.get("pattern", {})
    sn = dts.get("stem_nature", {})
    purity = geju.get("purity", {})

    stems = " ".join(p.get("ganzhi", "")[:1] for p in pillars)
    branches = " ".join(p.get("ganzhi", "")[1:] for p in pillars if len(p.get("ganzhi", "")) > 1)

    layers: list[dict[str, Any]] = [
        {
            "id": "tiandao",
            "name": "天道",
            "subtitle": "天干、十神、外缘",
            "lines": [
                f"天干：{stems}",
                f"天干助损：{dz.get('summary', '—')}（得助{dz.get('helps', 0)}，受克泄{dz.get('drains', 0)}）",
                f"十神：{_shishen_line(shishen_summary)}",
            ],
        },
        {
            "id": "didao",
            "name": "地道",
            "subtitle": "地支、藏干、刑冲",
            "lines": [
                f"地支：{branches}",
                f"四柱关系：{'、'.join(relations) if relations else '未见显著刑冲合害破穿'}",
            ],
        },
        {
            "id": "rendao",
            "name": "人道",
            "subtitle": "得令、通根、旺衰",
            "lines": [
                f"日主{dm}（{wx}）月令{de.get('month_branch', '')}，{de.get('status', '')}",
                f"通根：{tg.get('summary', '—')}（得分{tg.get('score', '—')}）",
                f"强弱：{dts.get('day_master_strength', '平衡')}（评分{dts.get('strength_score', '—')}）",
            ],
        },
        {
            "id": "tiyong",
            "name": "体用气势",
            "subtitle": "格局与气势",
            "lines": [
                f"格局：{geju.get('type') or '未定'}（{geju.get('origin', '')}）清纯{purity.get('level', '平')}",
                f"体用：{body_pat.get('type', '正格')} — {body_pat.get('note', '')}",
                geju.get("note", "") or "—",
            ],
        },
        {
            "id": "tiaohou",
            "name": "调候寒暖",
            "subtitle": "穷通宝鉴 · 滴天髓",
            "lines": [
                f"气候：{cl.get('season', '')}{cl.get('climate', '')} — {cl.get('note', '')}",
                tiao_hou or "调候未录",
            ],
        },
        {
            "id": "liutong",
            "name": "流通",
            "subtitle": "五行气机",
            "lines": [_flow_note(relations, yongshen, body_pat)],
        },
    ]

    ss_items = shensha.get("items") or []
    if ss_items:
        names = "、".join(i["name"] for i in ss_items[:5])
        layers.append({
            "id": "shensha",
            "name": "神煞辅助",
            "subtitle": "参格局，不独断",
            "lines": [f"{names} — {shensha.get('note', '')[:80]}"],
        })

    dayun_lines: list[str] = []
    if current_dayun:
        dayun_lines.append(
            f"当前大运 {current_dayun.get('ganzhi')} "
            f"（{current_dayun.get('start_year')}—{current_dayun.get('end_year')}）"
        )
    if current_liunian:
        dayun_lines.append(f"当前流年 {current_liunian.get('ganzhi')}（{current_liunian.get('year')}）")
    qy = chart.get("qiyun", {})
    if qy.get("description"):
        dayun_lines.append(str(qy["description"])[:120])
    if dayun_lines:
        layers.append({
            "id": "dayun",
            "name": "大运气机",
            "subtitle": "运限引动",
            "lines": dayun_lines,
        })

    summary = (
        f"{dm}（{wx}）{dts.get('day_master_strength', '')}，"
        f"{geju.get('type') or '格局待定'}，"
        f"{body_pat.get('type', '正格')}"
    )
    if relations:
        summary += f"；见{'、'.join(relations[:2])}"

    return {
        "kernel": KERNEL,
        "method": METHOD,
        "summary": summary,
        "verse": sn.get("verse", ""),
        "image": sn.get("image", ""),
        "layers": layers,
    }
