# -*- coding: utf-8 -*-
"""Validate rule layer + AI output quality (classical gz cases only)."""
from __future__ import annotations

import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

BASE = "http://127.0.0.1:8000"

from scripts.regression_ai import load_ai_suite
from scripts.regression_common import build_chart_from_gz, gender_to_code, score_ai_analysis

# Quick sample: first 5 book-verified classical cases
AI_SAMPLE = load_ai_suite()[:5]


def rule_layer_checks() -> list[str]:
    from app.core.bazi import BaziService, BirthInput
    from app.core.mingli import analyze as mingli_analyze
    from app.core.tege import detect_special_pattern
    from app.core.liunian_detail import analyze_dayun_detail

    errors: list[str] = []
    chart = BaziService.build_chart(BirthInput("solar", 1990, 5, 15, 12, 30, "male"))
    ml = mingli_analyze(chart)
    if not ml.get("geju"):
        errors.append("mingli missing geju")
    if not ml.get("dayun_detail"):
        errors.append("mingli missing dayun_detail")
    elif not ml["dayun_detail"].get("current_year_detail"):
        errors.append("dayun_detail missing current_year_detail")

    sh = ml.get("shensha") or {}
    allowed = {"禄神", "将星", "驿马"}
    for item in sh.get("items") or []:
        if item.get("name") not in allowed:
            errors.append(f"unexpected shensha: {item.get('name')}")

    zw = BaziService.build_chart(BirthInput("solar", 1980, 8, 15, 12, 0, "male"))
    _ = detect_special_pattern(zw)
    _ = analyze_dayun_detail(zw)
    return errors


def ai_checks() -> tuple[list[dict], float]:
    from app.core.insight import ensure_ai_insight

    results: list[dict] = []
    client = httpx.Client(timeout=120.0)
    try:
        health = client.get(f"{BASE}/health")
        if health.status_code != 200:
            raise RuntimeError(f"server not up: {health.status_code}")
    except httpx.ConnectError as e:
        raise RuntimeError(f"server not running at {BASE}") from e

    for case in AI_SAMPLE:
        name = case.get("name", case.get("id", "?"))
        chart = build_chart_from_gz(
            case["gz"],
            gender_to_code(case.get("gender", "male")),
            day_master=case.get("dm"),
        )
        r2 = client.post(
            f"{BASE}/api/analyze",
            json={"chart": chart, "style": "classic"},
        )
        ar = r2.json()
        if not ar.get("success"):
            results.append({"name": name, "error": ar.get("error", "analyze failed")})
            continue
        text = ar.get("analysis", "")
        full = ensure_ai_insight(chart)
        score, issues = score_ai_analysis(text, full, style="classic")
        geju_type = (full.get("geju") or {}).get("type", "?")
        dd = full.get("dayun_detail") or {}
        results.append(
            {
                "name": name,
                "score": score,
                "issues": issues,
                "len": len(text),
                "geju": geju_type,
                "strength": full.get("day_master_strength"),
                "liunian_triggers": len((dd.get("current_year_detail") or {}).get("triggers") or []),
            }
        )
        time.sleep(0.5)
    client.close()
    scores = [r["score"] for r in results if "score" in r]
    avg = sum(scores) / len(scores) if scores else 0
    return results, avg


def main() -> int:
    print("=== Rule layer ===")
    rl_errors = rule_layer_checks()
    if rl_errors:
        for e in rl_errors:
            print("FAIL", e)
        return 1
    print("OK")

    print("\n=== AI quality (classical sample) ===")
    try:
        results, avg = ai_checks()
    except RuntimeError as e:
        print("SKIP AI:", e)
        return 0
    for r in results:
        if r.get("error"):
            print(f"  {r['name']}: ERROR {r['error']}")
        else:
            print(
                f"  {r['name']}: {r['score']}/10 "
                f"geju={r['geju']} strength={r.get('strength')} issues={r.get('issues')}"
            )
    print(f"avg={avg:.2f}/10")
    failed = [r for r in results if r.get("score", 10) < 7 or r.get("error")]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
