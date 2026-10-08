#!/usr/bin/env python3
"""Garde seule : refuse sans ALLOW_CURSOR_SMOKE=1.

Le run payant est scripts/run_real_smoke.py (séparé).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COST = ROOT / "COST_SMOKE.md"


def main() -> int:
    if os.environ.get("ALLOW_CURSOR_SMOKE") != "1":
        print(
            "Refus : ALLOW_CURSOR_SMOKE=1 seulement après COST_SMOKE.md + GO Jérôme.",
            file=sys.stderr,
        )
        return 2
    if not COST.is_file():
        print("COST_SMOKE.md manquant", file=sys.stderr)
        return 2
    print("Garde OK — lancer ensuite: python scripts/run_real_smoke.py")
    print("(un send, zéro retry ; CURSOR_API_KEY requis)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
