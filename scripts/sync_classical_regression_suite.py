# -*- coding: utf-8 -*-
"""Sync ai_regression_suite.json from test_suite_v4 classical entries."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUITE = ROOT / "data" / "test_suite_v4.json"
OUT = ROOT / "data" / "ai_regression_suite.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args()

    data = json.loads(SUITE.read_text(encoding="utf-8"))
    cases = []
    for i, c in enumerate(data.get("classical") or [], 1):
        if len(cases) >= args.limit:
            break
        gz = (c.get("gz") or "").strip()
        if not gz:
            continue
        cases.append(
            {
                "id": f"cls_{i:03d}",
                "bucket": "classical",
                "name": c.get("name", ""),
                "source": c.get("source", ""),
                "gz": gz,
                "dm": c.get("dm", ""),
                "gender": "male" if c.get("gender") in ("男", "male") else "female",
            }
        )
    payload = {
        "description": "AI regression: book-verified four pillars only (from test_suite_v4.classical)",
        "cases": cases,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(cases)} cases -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
