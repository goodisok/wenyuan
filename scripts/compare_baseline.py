# -*- coding: utf-8 -*-
"""Compare two regression baseline JSON reports."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _load(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _fmt_delta(old: float | None, new: float | None, *, higher_is_better: bool) -> str:
    if old is None or new is None:
        return "n/a"
    d = new - old
    sign = "+" if d >= 0 else ""
    ok = (d >= 0) if higher_is_better else (d <= 0)
    tag = "OK" if ok or d == 0 else "REGRESSION"
    return f"{sign}{d:.4f} ({tag})"


def compare_rules(old: dict[str, Any], new: dict[str, Any]) -> tuple[list[str], bool]:
    lines: list[str] = []
    ok = True
    lines.append("=== Rules baseline ===")
    lines.append(
        f"pass_rate: {old.get('pass_rate')} -> {new.get('pass_rate')} "
        f"{_fmt_delta(old.get('pass_rate'), new.get('pass_rate'), higher_is_better=True)}"
    )
    if (new.get("pass_rate") or 0) < (old.get("pass_rate") or 0):
        ok = False

    om = old.get("metrics") or {}
    nm = new.get("metrics") or {}
    if om.get("renping_align_rate") is not None and nm.get("renping_align_rate") is not None:
        lines.append(
            f"renping_align_rate: {om.get('renping_align_rate')} -> {nm.get('renping_align_rate')} "
            f"{_fmt_delta(om.get('renping_align_rate'), nm.get('renping_align_rate'), higher_is_better=True)}"
        )
        if (nm.get("renping_align_rate") or 0) < (om.get("renping_align_rate") or 0):
            ok = False

    lines.append(f"failed: {old.get('failed')} -> {new.get('failed')}")
    if (new.get("failed") or 0) > (old.get("failed") or 0):
        ok = False
    return lines, ok


def compare_ai(old: dict[str, Any], new: dict[str, Any]) -> tuple[list[str], bool]:
    lines: list[str] = []
    ok = True
    lines.append("=== AI baseline ===")

    if old.get("skipped") or new.get("skipped"):
        lines.append("one or both reports skipped AI run — comparison limited")
        return lines, True

    lines.append(
        f"avg_score: {old.get('avg_score')} -> {new.get('avg_score')} "
        f"{_fmt_delta(old.get('avg_score'), new.get('avg_score'), higher_is_better=True)}"
    )
    if (new.get("avg_score") or 0) < (old.get("avg_score") or 0):
        ok = False

    lines.append(
        f"warning_count: {old.get('warning_count')} -> {new.get('warning_count')} "
        f"{_fmt_delta(old.get('warning_count'), new.get('warning_count'), higher_is_better=False)}"
    )
    if (new.get("warning_count") or 0) > (old.get("warning_count") or 0):
        ok = False

    lines.append(f"errors: {old.get('errors')} -> {new.get('errors')}")
    if (new.get("errors") or 0) > (old.get("errors") or 0):
        ok = False

    lines.append(
        f"min_score: {old.get('min_score')} -> {new.get('min_score')} "
        f"{_fmt_delta(old.get('min_score'), new.get('min_score'), higher_is_better=True)}"
    )
    if (new.get("min_score") or 0) < (old.get("min_score") or 0):
        ok = False

    ou = old.get("ungrounded_rate")
    nu = new.get("ungrounded_rate")
    if ou is not None or nu is not None:
        lines.append(
            f"ungrounded_rate: {ou} -> {nu} "
            f"{_fmt_delta(ou, nu, higher_is_better=False)}"
        )
        if (nu or 0) > (ou or 0):
            ok = False

    ob = old.get("bucket_avg") or {}
    nb = new.get("bucket_avg") or {}
    for bucket in sorted(set(ob) | set(nb)):
        lines.append(
            f"bucket {bucket}: {ob.get(bucket)} -> {nb.get(bucket)} "
            f"{_fmt_delta(ob.get(bucket), nb.get(bucket), higher_is_better=True)}"
        )
    return lines, ok


def compare_reports(old: dict[str, Any], new: dict[str, Any]) -> tuple[list[str], bool]:
    kind = new.get("kind") or old.get("kind")
    if kind == "rules":
        return compare_rules(old, new)
    if kind == "ai":
        return compare_ai(old, new)
    return [f"unknown report kind: {kind}"], False


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare regression baseline JSON files")
    parser.add_argument("old", type=Path, help="Previous baseline report")
    parser.add_argument("new", type=Path, help="New baseline report")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    old = _load(args.old)
    new = _load(args.new)
    if old.get("kind") != new.get("kind"):
        print(f"kind mismatch: {old.get('kind')} vs {new.get('kind')}", file=sys.stderr)
        return 2

    lines, ok = compare_reports(old, new)
    if not args.quiet:
        for line in lines:
            print(line)
        print("RESULT:", "PASS" if ok else "REGRESSION DETECTED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
