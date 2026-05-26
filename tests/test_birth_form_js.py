"""Ensure birth form JS loads and initIndexPage fills selects (headless)."""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "verify_birth_form.mjs"


def test_birth_form_init_script() -> None:
    node = shutil.which("node")
    if not node:
        return  # skip when Node.js not installed (CI without frontend toolchain)
    assert SCRIPT.is_file(), f"missing {SCRIPT}"
    proc = subprocess.run(
        [node, str(SCRIPT)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
