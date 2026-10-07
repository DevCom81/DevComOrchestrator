from __future__ import annotations

import os
from pathlib import Path
from typing import IO

from devcom.modules.projects.adapters.safe_path import open_regular_readonly


def load_gitignore_patterns(root: Path) -> tuple[str, ...]:
    """Parse root .gitignore text only — does not execute repo config."""
    try:
        fd, _ = open_regular_readonly(root, ".gitignore")
    except Exception:
        return ()
    try:
        with os_fdopen(fd) as handle:
            raw = handle.read()
    except OSError:
        return ()
    patterns: list[str] = []
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        patterns.append(stripped)
    return tuple(patterns)


def os_fdopen(fd: int) -> IO[str]:
    return os.fdopen(fd, "r", encoding="utf-8", errors="strict")
