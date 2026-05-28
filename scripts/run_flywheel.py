# -*- coding: utf-8 -*-
"""Run full verify → report flywheel (rules always; AI if server up)."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _run(cmd: list[str]) -> int:
    print("$", " ".join(cmd))
    return subprocess.call(cmd, cwd=ROOT)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run regression flywheel")
    parser.add_argument("--skip-ai", action="store_true")
    parser.add_argument("--compare-old-rules", type=Path, default=None)
    parser.add_argument("--compare-old-ai", type=Path, default=None)
    args = parser.parse_args()

    py = sys.executable
    code = _run([py, "-m", "pytest", "tests/", "-q", "--ignore=tests/test_birth_form_js.py"])
    if code != 0:
        return code

    code = _run([py, "scripts/regression_rules.py"])
    if code != 0:
        return code

    if args.compare_old_rules:
        from app import __version__

        new_rules = ROOT / "reports" / f"baseline_rules_v{__version__}.json"
        code = _run([py, "scripts/compare_baseline.py", str(args.compare_old_rules), str(new_rules)])
        if code != 0:
            return code

    if not args.skip_ai:
        code = _run([py, "scripts/regression_ai.py"])
        if code != 0:
            return code
        if args.compare_old_ai:
            from app import __version__

            new_ai = ROOT / "reports" / f"baseline_ai_v{__version__}.json"
            code = _run([py, "scripts/compare_baseline.py", str(args.compare_old_ai), str(new_ai)])
            if code != 0:
                return code

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
