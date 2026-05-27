"""Remove Cursor co-author trailer from commit messages."""
from __future__ import annotations

import sys
from pathlib import Path

TRAILER = "Co-authored-by: Cursor <cursoragent@cursor.com>"


def strip_text(text: str) -> str:
    lines = [line for line in text.splitlines() if line.strip() != TRAILER]
    while lines and not lines[-1].strip():
        lines.pop()
    if not lines:
        return ""
    return "\n".join(lines) + "\n"


def main() -> None:
    if len(sys.argv) >= 2 and sys.argv[1] != "--stdin":
        path = Path(sys.argv[1])
        cleaned = strip_text(path.read_text(encoding="utf-8"))
        path.write_text(cleaned, encoding="utf-8", newline="\n")
        return
    sys.stdout.write(strip_text(sys.stdin.read()))


if __name__ == "__main__":
    main()
