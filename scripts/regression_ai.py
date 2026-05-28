# -*- coding: utf-8 -*-
"""AI regression over fixed suite (requires local server + API key)."""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.regression_common import (  # noqa: E402
    app_version,
    build_chart_from_gz,
    gender_to_code,
    score_ai_analysis,
    utc_now_iso,
    write_report,
)

SUITE_PATH = ROOT / "data" / "ai_regression_suite.json"
DEFAULT_BASE = "http://127.0.0.1:8000"


def load_ai_suite(path: Path | None = None, *, ids: list[str] | None = None) -> list[dict[str, Any]]:
    p = path or SUITE_PATH
    with p.open(encoding="utf-8") as f:
        data = json.load(f)
    cases = data.get("cases") or []
    if ids:
        wanted = set(ids)
        cases = [c for c in cases if c.get("id") in wanted]
    return cases


def _build_chart_payload(case: dict[str, Any]) -> dict[str, Any]:
    if case.get("gz"):
        return build_chart_from_gz(
            case["gz"],
            gender_to_code(case.get("gender", "male")),
            day_master=case.get("dm"),
        )
    from app.core.bazi import BaziService, BirthInput

    date_type = case.get("date_type", "solar")
    y, m, d = (int(x) for x in case["birth_date"].split("-"))
    h, mi = (int(x) for x in case["birth_time"].split(":"))
    bi = BirthInput(
        date_type=date_type,
        year=y,
        month=m,
        day=d,
        hour=h,
        minute=mi,
        gender=gender_to_code(case.get("gender", "male")),
        is_leap_month=bool(case.get("is_leap_month")),
    )
    return BaziService.build_chart(bi)


def _run_case(client: httpx.Client, base: str, case: dict[str, Any]) -> dict[str, Any]:
    from app.core.ai_validate import validate_analysis
    from app.core.insight import ensure_ai_insight

    cid = case.get("id", "?")
    label = case.get("name") or cid
    bucket = case.get("bucket", "?")
    ai_style = "classic" if bucket == "classical" else "modern"

    try:
        if case.get("gz"):
            chart = _build_chart_payload(case)
        else:
            r1 = client.post(
                f"{base}/api/chart",
                json={
                    "date_type": case.get("date_type", "solar"),
                    "birth_date": case["birth_date"],
                    "birth_time": case["birth_time"],
                    "gender": gender_to_code(case.get("gender", "male")),
                    "is_leap_month": bool(case.get("is_leap_month")),
                },
            )
            data = r1.json()
            if not data.get("success"):
                return {
                    "id": cid,
                    "name": label,
                    "bucket": bucket,
                    "error": data.get("error", r1.text[:120]),
                }
            chart = data["data"]

        r2 = client.post(
            f"{base}/api/analyze",
            json={"chart": chart, "style": ai_style},
        )
        ar = r2.json()
        if not ar.get("success"):
            return {
                "id": cid,
                "name": label,
                "bucket": bucket,
                "error": ar.get("error", "analyze failed"),
            }

        text = ar.get("analysis", "")
        full = ensure_ai_insight(chart)
        score, issues = score_ai_analysis(text, full, style=ai_style)
        vr = validate_analysis(text, full)
        geju_type = (full.get("geju") or {}).get("type", "?")
        return {
            "id": cid,
            "name": label,
            "bucket": bucket,
            "score": score,
            "issues": issues,
            "warnings": vr.get("warnings") or [],
            "warning_count": len(vr.get("warnings") or []),
            "len": len(text),
            "geju": geju_type,
            "strength": full.get("day_master_strength"),
        }
    except Exception as exc:
        return {"id": cid, "name": label, "bucket": bucket, "error": str(exc)}


def run_ai(
    base: str = DEFAULT_BASE,
    *,
    suite_path: Path | None = None,
    sleep_s: float = 0.5,
    ids: list[str] | None = None,
) -> dict[str, Any]:
    cases = load_ai_suite(suite_path, ids=ids)
    client = httpx.Client(timeout=240.0)
    try:
        health = client.get(f"{base}/health")
        if health.status_code != 200:
            raise RuntimeError(f"server health failed: {health.status_code}")
    except httpx.ConnectError as exc:
        raise RuntimeError(f"server not running at {base}") from exc

    results: list[dict[str, Any]] = []
    for case in cases:
        results.append(_run_case(client, base, case))
        time.sleep(sleep_s)
    client.close()

    ok = [r for r in results if "score" in r]
    errors = [r for r in results if r.get("error")]
    scores = [r["score"] for r in ok]
    warnings_total = sum(r.get("warning_count", 0) for r in ok)
    ungrounded_rate = round(warnings_total / len(ok), 4) if ok else 0.0

    by_bucket: dict[str, list[float]] = {}
    for r in ok:
        by_bucket.setdefault(r.get("bucket", "?"), []).append(r["score"])

    return {
        "kind": "ai",
        "version": app_version(),
        "generated_at": utc_now_iso(),
        "suite": str((suite_path or SUITE_PATH).relative_to(ROOT)),
        "total": len(results),
        "completed": len(ok),
        "errors": len(errors),
        "avg_score": round(sum(scores) / len(scores), 3) if scores else 0.0,
        "min_score": min(scores) if scores else 0.0,
        "warning_count": warnings_total,
        "ungrounded_rate": ungrounded_rate,
        "bucket_avg": {
            k: round(sum(v) / len(v), 3) for k, v in sorted(by_bucket.items())
        },
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="AI regression (fixed 35-case suite)")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=ROOT / "reports" / f"baseline_ai_v{app_version()}.json",
    )
    parser.add_argument("--base", default=DEFAULT_BASE)
    parser.add_argument("--suite", type=Path, default=SUITE_PATH)
    parser.add_argument(
        "--ids",
        default="",
        help="Comma-separated case ids (e.g. cel_ren,ord_golden_user) for quick iteration",
    )
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    id_list = [x.strip() for x in args.ids.split(",") if x.strip()] or None

    try:
        report = run_ai(args.base, suite_path=args.suite, ids=id_list)
    except RuntimeError as exc:
        report = {
            "kind": "ai",
            "version": app_version(),
            "generated_at": utc_now_iso(),
            "suite": str(args.suite.relative_to(ROOT)),
            "skipped": True,
            "skip_reason": str(exc),
            "total": 0,
            "completed": 0,
            "errors": 0,
            "avg_score": None,
            "warning_count": 0,
            "results": [],
        }
        write_report(args.output, report)
        if not args.quiet:
            print("SKIP AI regression:", exc)
            print(f"report -> {args.output}")
        return 0

    write_report(args.output, report)
    if not args.quiet:
        print(f"AI regression: {report['completed']}/{report['total']} completed")
        print(f"avg_score={report['avg_score']} warnings={report['warning_count']}")
        for k, v in (report.get("bucket_avg") or {}).items():
            print(f"  bucket {k}: avg={v}")
        print(f"report -> {args.output}")

    failed = [
        r
        for r in report.get("results") or []
        if r.get("error") or r.get("score", 10) < 7
    ]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
