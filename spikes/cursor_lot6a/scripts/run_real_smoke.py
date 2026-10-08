#!/usr/bin/env python3
"""Lance le smoke Cursor réel — UN send, zéro retry.

Prérequis :
  export CURSOR_API_KEY=...   # jamais commit
  export ALLOW_CURSOR_SMOKE=1 # après lecture COST_SMOKE.md + GO Jérôme

Ne pas exécuter depuis l'agent Cursor de DevCom sans GO humain.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lib.auth_check import inspect_api_key_env, scrub_backend_env  # noqa: E402
from lib.real_invoke import invoke_once  # noqa: E402
from lib.smoke_flow import run_smoke_flow  # noqa: E402

RUN_ID = "smoke-1"
EXPORT_ID = "export-spike-smoke-1"
COST = ROOT / "COST_SMOKE.md"


def main() -> int:
    if os.environ.get("ALLOW_CURSOR_SMOKE") != "1":
        print(
            "Refus: ALLOW_CURSOR_SMOKE=1 requis après COST_SMOKE.md + GO.",
            file=sys.stderr,
        )
        return 2
    if not COST.is_file():
        print("COST_SMOKE.md manquant", file=sys.stderr)
        return 2
    auth = inspect_api_key_env()
    if not auth.api_key_nonempty:
        print(auth.hint, file=sys.stderr)
        return 3
    removed = scrub_backend_env()
    if removed:
        print("scrubbed_env_keys:", ",".join(removed))
    api_key = os.environ["CURSOR_API_KEY"].strip()

    def invoker(worktree: Path, prompt: str):
        return invoke_once(worktree=worktree, prompt=prompt, api_key=api_key)

    from cursor_sdk import AuthenticationError, CursorSDKError

    try:
        outcome = run_smoke_flow(
            root=ROOT,
            run_id=RUN_ID,
            export_id=EXPORT_ID,
            invoker=invoker,
        )
    except AuthenticationError as exc:
        print(f"AuthenticationError: {exc}", file=sys.stderr)
        print(
            "Clé refusée — régénérer via Dashboard → API Keys ; "
            "relancer check_auth_and_models.py. Pas de contournement.",
            file=sys.stderr,
        )
        return 6
    except CursorSDKError as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 7
    print("status", outcome.invoke.status)
    print("agent_id", outcome.invoke.agent_id)
    print("run_id", outcome.invoke.run_id)
    print("report_sha256", outcome.report_sha256)
    print("validation_exit", outcome.validation.exit_code)
    print("artifacts", outcome.artifacts)
    if outcome.invoke.billed_usage_error:
        print("billed_usage_error", outcome.invoke.billed_usage_error)
    if outcome.validation.exit_code != 0:
        print("SMOKE_VALIDATION_FAILED", file=sys.stderr)
        return 1
    if outcome.invoke.status != "finished":
        print("SMOKE_STATUS_NOT_FINISHED", outcome.invoke.status, file=sys.stderr)
        return 1
    print("SMOKE_REAL_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
