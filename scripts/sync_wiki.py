"""Sync goodisok/bazi-wiki into knowledge/bazi-wiki (excludes raw classics by default)."""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

WIKI_URL = "https://github.com/goodisok/bazi-wiki.git"
TARGET = Path(__file__).resolve().parents[1] / "knowledge" / "bazi-wiki"
KEEP_RAW = "--keep-raw" in sys.argv


def main() -> None:
    if TARGET.exists() and (TARGET / ".git").is_dir():
        subprocess.run(["git", "-C", str(TARGET), "pull", "--ff-only"], check=True)
    else:
        if TARGET.exists():
            shutil.rmtree(TARGET)
        TARGET.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "--depth", "1", WIKI_URL, str(TARGET)], check=True)

    raw = TARGET / "raw"
    if not KEEP_RAW and raw.exists():
        shutil.rmtree(raw)
        print("Removed raw/ (classic full texts — not loaded by runtime; use --keep-raw to retain).")

    from knowledge.corpus.wiki_loader import load_wiki_entries

    n = len(load_wiki_entries())
    print(f"Synced bazi-wiki → {TARGET} ({n} retrievable pages)")


if __name__ == "__main__":
    main()
