from __future__ import annotations

import os
import stat
from pathlib import Path

from devcom.modules.projects.domain.errors import (
    PathEscapeError,
    SourceRootError,
    SpecialFileError,
)


def assert_usable_root(path: Path) -> Path:
    if not path.is_absolute():
        raise SourceRootError("source root must be an absolute path")
    try:
        st = os.lstat(path)
    except OSError as exc:
        raise SourceRootError(f"source root unreadable: {exc}") from exc
    if stat.S_ISLNK(st.st_mode):
        raise SourceRootError("source root must not be a symbolic link")
    if not stat.S_ISDIR(st.st_mode):
        raise SourceRootError("source root must be a directory")
    return path


def split_relative(relative: str) -> tuple[str, ...]:
    normalized = relative.replace("\\", "/").strip("/")
    if not normalized:
        raise PathEscapeError("empty relative path")
    if "\x00" in normalized:
        raise PathEscapeError("null byte in path")
    parts = tuple(part for part in normalized.split("/") if part)
    if any(part in {".", ".."} for part in parts):
        raise PathEscapeError("relative path escapes via . or ..")
    if any(part.startswith("/") or ":" in part for part in parts):
        raise PathEscapeError("absolute segment rejected")
    return parts


def walk_components(root: Path, relative: str) -> Path:
    """Resolve relative path under root without following any symlink."""
    assert_usable_root(root)
    current = root
    parts = split_relative(relative)
    for index, part in enumerate(parts):
        candidate = current / part
        try:
            st = os.lstat(candidate)
        except OSError as exc:
            raise PathEscapeError(f"path component missing: {part}") from exc
        if stat.S_ISLNK(st.st_mode):
            joined = "/".join(parts[: index + 1])
            raise PathEscapeError(f"symlink refused at {joined}")
        is_last = index == len(parts) - 1
        if is_last:
            return candidate
        if not stat.S_ISDIR(st.st_mode):
            joined = "/".join(parts[: index + 1])
            raise PathEscapeError(f"not a directory: {joined}")
        current = candidate
    raise PathEscapeError("empty path")


def open_regular_readonly(root: Path, relative: str) -> tuple[int, Path]:
    target = walk_components(root, relative)
    try:
        st = os.lstat(target)
    except OSError as exc:
        raise SpecialFileError(f"cannot stat {relative}: {exc}") from exc
    if stat.S_ISLNK(st.st_mode):
        raise PathEscapeError(f"symlink refused at {relative}")
    if not stat.S_ISREG(st.st_mode):
        raise SpecialFileError(f"not a regular file: {relative}")
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    if hasattr(os, "O_NONBLOCK"):
        flags |= os.O_NONBLOCK
    try:
        fd = os.open(target, flags)
    except OSError as exc:
        raise SpecialFileError(f"cannot open {relative}: {exc}") from exc
    try:
        opened = os.fstat(fd)
        if not stat.S_ISREG(opened.st_mode):
            os.close(fd)
            raise SpecialFileError(f"not a regular file: {relative}")
    except SpecialFileError:
        raise
    except Exception:
        try:
            os.close(fd)
        except OSError:
            pass
        raise
    return fd, target
