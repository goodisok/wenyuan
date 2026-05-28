# -*- coding: utf-8 -*-
"""Rule-layer regression over test_suite_v4 classical cases (no AI / no server)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.regression_common import (  # noqa: E402
    SHENSHA_ALLOWED,
    app_version,
    build_chart_from_gz,
    gender_to_code,
    load_test_suite,
    polarity_aligned,
    utc_now_iso,
    write_report,
)


def _check_case(case: dict[str, Any]) -> dict[str, Any]:
    name = case.get("name", "?")
    gz = case.get("gz", "")
    dm = case.get("dm", "")
    gender = gender_to_code(case.get("gender", "male"))
    errors: list[str] = []
    warnings: list[str] = []
    ml: dict[str, Any] = {}

    try:
        chart = build_chart_from_gz(gz, gender, day_master=dm or None)
        from app.core.mingli import analyze as mingli_analyze

        ml = mingli_analyze(chart)
    except Exception as exc:
        return {
            "name": name,
            "gz": gz,
            "ok": False,
            "errors": [f"exception: {exc}"],
            "warnings": [],
        }

    if not ml.get("geju"):
        errors.append("missing geju")
    if ml.get("day_master_strength") in (None, ""):
        errors.append("missing day_master_strength")
    meta_dm = (chart.get("meta") or {}).get("day_master", "")
    if dm and meta_dm != dm:
        errors.append(f"day_master mismatch expected={dm} got={meta_dm}")

    dd = ml.get("dayun_detail") or {}
    cyd = dd.get("current_year_detail") or {}
    if not cyd.get("year"):
        errors.append("dayun_detail missing current_year_detail")

    sh = ml.get("shensha") or {}
    for item in sh.get("items") or []:
        if item.get("name") not in SHENSHA_ALLOWED:
            errors.append(f"unexpected shensha: {item.get('name')}")

    renping = case.get("renping") or ""
    aligned = polarity_aligned(renping, ml.get("highlights") or [])
    if aligned is False:
        warnings.append("renping polarity vs highlights mismatch")

    return {
        "name": name,
        "gz": gz,
        "ok": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "geju": (ml.get("geju") or {}).get("type"),
        "strength": ml.get("day_master_strength"),
        "renping_aligned": aligned,
    }


def run_rules(limit: int | None = None, *, include_all: bool = False) -> dict[str, Any]:
    suite = load_test_suite()
    cases = suite.get("classical") or []
    if limit is not None:
        cases = cases[:limit]

    results = [_check_case(c) for c in cases]
    passed = [r for r in results if r["ok"]]
    failed = [r for r in results if not r["ok"]]
    aligned = [r for r in results if r.get("renping_aligned") is True]
    misaligned = [r for r in results if r.get("renping_aligned") is False]
    scored = aligned + misaligned

    payload: dict[str, Any] = {
        "kind": "rules",
        "version": app_version(),
        "generated_at": utc_now_iso(),
        "suite": "data/test_suite_v4.json",
        "subset": "classical",
        "total": len(results),
        "passed": len(passed),
        "failed": len(failed),
        "pass_rate": round(len(passed) / len(results), 4) if results else 0.0,
        "metrics": {
            "geju_present_rate": round(
                sum(1 for r in results if r.get("geju")) / len(results), 4
            )
            if results
            else 0.0,
            "renping_align_rate": round(len(aligned) / len(scored), 4) if scored else None,
            "renping_scored": len(scored),
        },
        "failures": failed[:50],
    }
    if include_all:
        payload["results"] = results
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Rule-layer regression (classical suite)")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=ROOT / "reports" / f"baseline_rules_v{app_version()}.json",
    )
    parser.add_argument("--limit", type=int, default=None, help="Only run first N cases")
    parser.add_argument("--full", action="store_true", help="Include per-case results in report")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    report = run_rules(limit=args.limit, include_all=args.full)
    write_report(args.output, report)

    if not args.quiet:
        print(f"Rules regression: {report['passed']}/{report['total']} passed")
        print(f"pass_rate={report['pass_rate']}")
        m = report["metrics"]
        if m.get("renping_align_rate") is not None:
            print(f"renping_align_rate={m['renping_align_rate']} (n={m['renping_scored']})")
        print(f"report -> {args.output}")

    return 0 if report["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
