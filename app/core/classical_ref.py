# -*- coding: utf-8 -*-
"""古籍命例库：从 test_suite 检索相似四柱与原评（仅书中 verified gz）。"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SUITE_PATH = ROOT / "data" / "test_suite_v4.json"


@lru_cache(maxsize=1)
def load_classical() -> list[dict[str, Any]]:
    with SUITE_PATH.open(encoding="utf-8") as f:
        data = json.load(f)
    out: list[dict[str, Any]] = []
    for c in data.get("classical") or []:
        gz = (c.get("gz") or "").strip()
        if not gz or len(gz.split()) != 4:
            continue
        ren = (c.get("renping") or "").strip()
        if len(ren) < 20:
            continue
        out.append(
            {
                "name": c.get("name", ""),
                "gz": gz,
                "dm": c.get("dm", ""),
                "source": c.get("source", ""),
                "renping_excerpt": _clean_renping(ren),
            }
        )
    return out


def _clean_renping(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    if len(text) > 280:
        text = text[:280].rstrip() + "…"
    return text


def _pillar_set(gz: str) -> set[str]:
    return set(gz.split())


def _score_similar(query_gz: str, dm: str, case: dict[str, Any]) -> int:
    q = _pillar_set(query_gz)
    t = _pillar_set(case["gz"])
    overlap = len(q & t)
    score = overlap * 10
    if case.get("dm") == dm:
        score += 5
    if q & t:
        # 月柱、日柱权重更高
        qp = query_gz.split()
        tp = case["gz"].split()
        if len(qp) > 1 and len(tp) > 1 and qp[1] == tp[1]:
            score += 8
        if len(qp) > 2 and len(tp) > 2 and qp[2] == tp[2]:
            score += 6
    return score


def find_similar(
    chart: dict[str, Any],
    *,
    limit: int = 3,
    min_score: int = 15,
) -> list[dict[str, Any]]:
    pillars = chart.get("pillars") or []
    if len(pillars) < 4:
        return []
    gz = " ".join(p["ganzhi"] for p in pillars)
    dm = chart.get("meta", {}).get("day_master", "")
    ranked: list[tuple[int, dict[str, Any]]] = []
    for case in load_classical():
        if case["gz"] == gz:
            continue
        s = _score_similar(gz, dm, case)
        if s >= min_score:
            ranked.append((s, case))
    ranked.sort(key=lambda x: -x[0])
    return [
        {
            "score": s,
            "name": c["name"],
            "gz": c["gz"],
            "source": c["source"],
            "renping_excerpt": c["renping_excerpt"],
        }
        for s, c in ranked[:limit]
    ]


def format_for_ai(refs: list[dict[str, Any]]) -> str:
    if not refs:
        return ""
    lines = ["【相似古籍命例（须参证逻辑，勿照抄原评）】"]
    for r in refs:
        lines.append(
            f"· {r.get('name', '')} {r['gz']}（{r.get('source', '')}）"
            f" — {r.get('renping_excerpt', '')}"
        )
    return "\n".join(lines)
