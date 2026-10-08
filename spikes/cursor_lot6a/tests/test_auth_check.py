from __future__ import annotations

import os

from lib.auth_check import inspect_api_key_env


def test_missing_key(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.delenv("CURSOR_API_KEY", raising=False)
    status = inspect_api_key_env()
    assert not status.api_key_nonempty
    assert not status.shape_ok


def test_placeholder_rejected(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("CURSOR_API_KEY", "...")
    status = inspect_api_key_env()
    assert status.api_key_nonempty
    assert not status.shape_ok
    assert "placeholder_value" in status.shape_notes


def test_whitespace_noted(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("CURSOR_API_KEY", "crsr_abc ")
    status = inspect_api_key_env()
    assert "leading_or_trailing_whitespace" in status.shape_notes
