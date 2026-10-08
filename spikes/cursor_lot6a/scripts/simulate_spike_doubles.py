#!/usr/bin/env python3
"""Parcours spike avec double — aucun appel Cursor / aucun coût."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lib.fake_invoke import fake_invoker  # noqa: E402
from lib.smoke_flow import run_smoke_flow  # noqa: E402


def main() -> int:
    outcome = run_smoke_flow(
        root=ROOT,
        run_id="doubles-1",
        export_id="export-spike-fake",
        invoker=fake_invoker,
    )
    print("report_sha256", outcome.report_sha256)
    print("status", outcome.invoke.status)
    print("validation_exit", outcome.validation.exit_code)
    if outcome.validation.exit_code != 0:
        return 1
    print("SPIKE_DOUBLES_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
