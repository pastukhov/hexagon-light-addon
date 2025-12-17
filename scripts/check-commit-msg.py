#!/usr/bin/env python3

from __future__ import annotations

import re
import sys
from pathlib import Path


CONVENTIONAL_RE = re.compile(
    r"^(?P<type>feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)"
    r"(?:\([^)]+\))?"
    r"(?P<breaking>!)?"
    r": "
    r"(?P<subject>.+)$"
)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: check-commit-msg.py <path-to-commit-msg-file>", file=sys.stderr)
        return 2

    msg_path = Path(argv[1])
    try:
        raw = msg_path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"Failed to read commit message file: {exc}", file=sys.stderr)
        return 2

    lines = [line.rstrip("\n") for line in raw.splitlines()]
    first_line = next((line for line in lines if line.strip()), "")

    if not first_line:
        print("Commit message is empty.", file=sys.stderr)
        return 1

    if first_line.startswith(("Merge ", "Revert ")):
        return 0

    match = CONVENTIONAL_RE.match(first_line)
    if match:
        return 0

    print("Commit message must follow Conventional Commits (used for SemVer automation).", file=sys.stderr)
    print("Examples:", file=sys.stderr)
    print("  feat: add BLE reconnect", file=sys.stderr)
    print("  fix: handle device timeout", file=sys.stderr)
    print("  feat!: change config flow schema", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

