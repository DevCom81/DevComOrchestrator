from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AuthStatus:
    api_key_present: bool
    api_key_nonempty: bool
    shape_ok: bool
    shape_notes: tuple[str, ...]
    hint: str


def inspect_api_key_env() -> AuthStatus:
    """Never log or return the key value."""
    raw = os.environ.get("CURSOR_API_KEY")
    present = raw is not None
    nonempty = bool(raw and raw.strip())
    notes: list[str] = []
    shape_ok = True
    if not nonempty:
        shape_ok = False
        notes.append("empty")
        hint = (
            "Missing CURSOR_API_KEY. Create a user or service-account key at "
            "Cursor Dashboard → API Keys, then: export CURSOR_API_KEY=... "
            "(shell only; never commit; never put in prompt)."
        )
        return AuthStatus(present, False, False, tuple(notes), hint)
    if raw != raw.strip():
        shape_ok = False
        notes.append("leading_or_trailing_whitespace")
    if "\n" in raw or "\r" in raw:
        shape_ok = False
        notes.append("contains_newline")
    stripped = raw.strip()
    if stripped in {"...", "crsr_key", "your-key", "REPLACE_ME"}:
        shape_ok = False
        notes.append("placeholder_value")
    if not stripped.startswith("crsr_"):
        # Docs examples use crsr_… ; do not reject other prefixes hard —
        # only warn. Invalid keys still fail at the API.
        notes.append("prefix_not_crsr_underscore")
    hint = "CURSOR_API_KEY is set (value not shown)."
    if notes:
        hint += " shape_notes=" + ",".join(notes)
    return AuthStatus(
        api_key_present=present,
        api_key_nonempty=True,
        shape_ok=shape_ok,
        shape_notes=tuple(notes),
        hint=hint,
    )


def scrub_backend_env() -> list[str]:
    """Remove DevCom backend secrets from the current process before Agent.create."""
    removed: list[str] = []
    for name in list(os.environ):
        upper = name.upper()
        if upper.startswith("DEVCOM_") or upper in {
            "DATABASE_URL",
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
        }:
            os.environ.pop(name, None)
            removed.append(name)
    return removed
