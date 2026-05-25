# -*- coding: utf-8 -*-
"""断语发布：仅输出高置信、多维印证的内容。"""
from __future__ import annotations

from typing import Any

TOPIC_TO_GATE = {"父母": "parents"}


def publish_duanshi(duanshi: dict[str, Any], sanguan: dict[str, Any]) -> dict[str, Any]:
    """断事层：仅保留力度「强」，或与过三关「高」置信同题印证的项。"""
    gates = {g["id"]: g for g in (sanguan.get("gates") or [])}
    published: list[dict[str, Any]] = []
    for item in duanshi.get("items") or []:
        if item.get("level") == "强":
            published.append(item)
            continue
        gate_id = TOPIC_TO_GATE.get(str(item.get("topic", "")))
        if gate_id and gates.get(gate_id, {}).get("confidence") == "高":
            published.append(item)
    out = dict(duanshi)
    out["items"] = published
    if published:
        out["summary"] = "；".join(f"{i['topic']}:{i['verdict']}" for i in published)
    else:
        out["summary"] = ""
    out["publish_note"] = "仅发布力度「强」或与过三关高置信同题印证的断语"
    return out


def publish_sanguan(sanguan: dict[str, Any]) -> dict[str, Any]:
    """过三关：仅保留置信「高」的关。"""
    published = [g for g in (sanguan.get("gates") or []) if g.get("confidence") == "高"]
    out = dict(sanguan)
    out["gates"] = published
    out["summary"] = (
        f"三关验证：{len(published)}关高置信"
        if published
        else "三关验证：暂无高置信断语（中低置信不发布）"
    )
    if not published:
        out["chuan"] = []
    out["publish_note"] = "仅发布置信「高」、多家印证的关"
    return out
