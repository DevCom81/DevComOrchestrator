from __future__ import annotations

import os
import stat
import time
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from devcom.modules.projects.adapters.safe_path import assert_usable_root, split_relative
from devcom.modules.projects.domain.bounds import FilesystemBounds
from devcom.modules.projects.domain.errors import BrowseLimitError, PathEscapeError
from devcom.modules.projects.domain.exclusion_policy import ExclusionPolicy


@dataclass(frozen=True, slots=True)
class TreeEntry:
    relative_path: str
    name: str
    kind: str
    excluded: bool
    exclusion_reason: str | None


@dataclass(frozen=True, slots=True)
class TreePage:
    entries: tuple[TreeEntry, ...]
    cursor: str | None
    truncated: bool
    limit_message: str | None


def browse_tree(
    *,
    root: Path,
    policy: ExclusionPolicy,
    bounds: FilesystemBounds,
    cursor: str | None,
    page_size: int | None = None,
) -> TreePage:
    assert_usable_root(root)
    limit = min(page_size or bounds.max_tree_entries_per_page, bounds.max_tree_entries_per_page)
    started = time.monotonic()
    collected: list[TreeEntry] = []
    skip_until = cursor
    seen = 0
    truncated = False
    limit_message: str | None = None

    def timed_out() -> bool:
        return (time.monotonic() - started) >= bounds.max_browse_seconds

    for relative, name, kind, is_dir in _walk(root, bounds.max_tree_depth):
        if timed_out():
            truncated = True
            limit_message = "browse time limit reached"
            break
        seen += 1
        if seen > bounds.max_tree_entries_total:
            truncated = True
            limit_message = "browse entry total limit reached"
            break
        if skip_until is not None:
            if relative != skip_until:
                continue
            skip_until = None
            continue
        reason = policy.reason_for(relative, is_dir=is_dir)
        collected.append(
            TreeEntry(
                relative_path=relative,
                name=name,
                kind=kind,
                excluded=reason is not None,
                exclusion_reason=reason,
            )
        )
        if len(collected) >= limit:
            truncated = True
            next_cursor = relative
            return TreePage(
                entries=tuple(collected),
                cursor=next_cursor,
                truncated=True,
                limit_message="page full — use cursor for next page",
            )
    return TreePage(
        entries=tuple(collected),
        cursor=None,
        truncated=truncated,
        limit_message=limit_message,
    )


def _walk(root: Path, max_depth: int) -> Iterator[tuple[str, str, str, bool]]:
    stack: list[tuple[Path, str, int]] = [(root, "", 0)]
    while stack:
        current, prefix, depth = stack.pop()
        try:
            names = sorted(os.listdir(current))
        except OSError:
            continue
        for name in reversed(names):
            child = current / name
            relative = name if not prefix else f"{prefix}/{name}"
            try:
                st = os.lstat(child)
            except OSError:
                continue
            if stat.S_ISLNK(st.st_mode):
                yield relative, name, "symlink", False
                continue
            if stat.S_ISDIR(st.st_mode):
                yield relative, name, "directory", True
                if depth + 1 <= max_depth:
                    stack.append((child, relative, depth + 1))
                continue
            if stat.S_ISREG(st.st_mode):
                yield relative, name, "file", False
                continue
            yield relative, name, "special", False


def require_relative_under_listing(relative: str) -> str:
    parts = split_relative(relative)
    return "/".join(parts)


def browse_or_raise_empty_cursor(cursor: str | None) -> None:
    if cursor is None:
        return
    try:
        split_relative(cursor)
    except PathEscapeError as exc:
        raise BrowseLimitError(f"invalid cursor: {exc.message}") from exc
