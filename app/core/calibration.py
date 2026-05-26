# -*- coding: utf-8 -*-
"""历史校准项：性情核对（盘象倾向）+ 人事应期（用户参与式验证）。"""
from __future__ import annotations

from typing import Any


def build_temperament(ml: dict[str, Any]) -> dict[str, Any]:
    """据日干象意、十神、旺衰、体用生成可核对的性情描述（非西方量表）。"""
    sn = ml.get("stem_nature") or {}
    ss = ml.get("shishen_summary") or {}
    top_ss = next(iter(ss.keys()), "") if ss else ""
    strength = ml.get("day_master_strength", "")
    pattern = ml.get("pattern") or {}
    items: list[dict[str, str]] = []

    if sn.get("image"):
        items.append({
            "id": "tem-stem-image",
            "label": f"日干象意「{sn['image']}」与我的气质相近",
            "category": "temperament",
        })
    if top_ss:
        items.append({
            "id": "tem-dominant-ss",
            "label": f"十神以「{top_ss}」为多，处事风格与此相应",
            "category": "temperament",
        })
    if strength:
        items.append({
            "id": "tem-strength",
            "label": f"命局{strength}，精力与外放程度与此相符",
            "category": "temperament",
        })
    if pattern.get("type") and pattern.get("type") != "正格":
        items.append({
            "id": "tem-tiyong",
            "label": f"体用「{pattern['type']}」，行事节奏与此类似",
            "category": "temperament",
        })

    summary_parts = [sn.get("image", ""), f"十神偏{top_ss}" if top_ss else "", strength, pattern.get("type", "")]
    summary = " · ".join(p for p in summary_parts if p)

    return {
        "summary": summary or "据盘象倾向自我核对",
        "note": "据四柱结构生成的性情倾向描述，供自我核对，非心理测验结论",
        "items": items,
    }


def build_calibration_items(insight: dict[str, Any]) -> list[dict[str, str]]:
    """与 AI「历史校准」章及前端勾选面板对齐的结构化项。"""
    items: list[dict[str, str]] = []

    for t in (insight.get("temperament") or {}).get("items") or []:
        items.append(dict(t))

    gm = insight.get("guanming") or {}
    for layer in gm.get("layers") or []:
        if layer.get("id") != "mangpai":
            continue
        for i, line in enumerate(layer.get("lines") or []):
            items.append({
                "id": f"struct-mangpai-{i}",
                "label": f"结构象：{line}",
                "category": "structure",
            })

    for d in (insight.get("duanshi") or {}).get("items") or []:
        topic = str(d.get("topic", ""))
        items.append({
            "id": f"ev-{topic}",
            "label": f"【{topic}】{d.get('verdict', '')}",
            "category": "event",
        })
        for w in d.get("windows") or []:
            dy = w.get("dayun", "")
            items.append({
                "id": f"ev-w-{topic}-{dy}",
                "label": f"{topic}应期 {dy}（{w.get('years', '')}）",
                "category": "timing",
            })

    for g in (insight.get("sanguan") or {}).get("gates") or []:
        items.append({
            "id": f"sg-{g.get('id', '')}",
            "label": f"【{g.get('name', '')}】{g.get('verdict', '')}",
            "category": "liuqin",
        })

    return items
