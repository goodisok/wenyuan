# -*- coding: utf-8 -*-
"""Validate rule layer + AI output quality (portable)."""
from __future__ import annotations

import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

BASE = "http://127.0.0.1:8000"

MODERN_CASES = [
    ("马云", 1964, 9, 10, "male"),
    ("马化腾", 1971, 10, 29, "male"),
    ("董明珠", 1954, 8, 10, "female"),
    ("任正非", 1944, 10, 25, "male"),
    ("雷军", 1969, 12, 16, "male"),
]

ANCIENT_TERMS = ["官至", "七品", "朱门", "武职", "发用", "纳妾", "封侯", "状元", "进士"]


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


def _strength_consistent(text: str, strength: str) -> bool:
    if not strength:
        return True
    mentions_strong = "身强" in text or "偏强" in text or "旺" in text
    mentions_weak = "身弱" in text or "偏弱" in text
    if strength in ("偏强", "身强", "强"):
        return not (mentions_weak and not mentions_strong)
    if strength in ("偏弱", "身弱", "弱"):
        return not (mentions_strong and not mentions_weak)
    return True


def score_analysis(text: str, insight: dict | None = None) -> tuple[float, list[str]]:
    issues: list[str] = []
    score = 10.0
    if any(t in text for t in ANCIENT_TERMS):
        bad = [t for t in ANCIENT_TERMS if t in text]
        issues.append(f"古代断语: {bad}")
        score -= 2
    if insight:
        strength = str(insight.get("day_master_strength") or "")
        if not _strength_consistent(text, strength):
            issues.append(f"旺衰与规则层不一致({strength})")
            score -= 2
        geju = (insight.get("geju") or {}).get("type", "")
        if geju and geju not in text:
            issues.append(f"未提及格局类型({geju})")
            score -= 0.5
    if "身强" in text and "身弱" in text:
        issues.append("同时出现身强与身弱")
        score -= 2
    if len(text) < 300:
        issues.append("过短")
        score -= 1
    return max(score, 0), issues


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

    for name, y, m, d, gender in MODERN_CASES:
        r1 = client.post(
            f"{BASE}/api/chart",
            json={
                "date_type": "solar",
                "birth_date": f"{y}-{m:02d}-{d:02d}",
                "birth_time": "12:00",
                "gender": gender,
            },
        )
        data = r1.json()
        if not data.get("success"):
            results.append({"name": name, "error": data.get("message", r1.text[:120])})
            continue
        chart = data["data"]

        r2 = client.post(
            f"{BASE}/api/analyze",
            json={"chart": chart, "style": "modern"},
        )
        ar = r2.json()
        if not ar.get("success"):
            results.append({"name": name, "error": ar.get("error", "analyze failed")})
            continue
        text = ar.get("analysis", "")
        full = ensure_ai_insight(chart)
        score, issues = score_analysis(text, full)
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

    print("\n=== AI quality (sample) ===")
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
