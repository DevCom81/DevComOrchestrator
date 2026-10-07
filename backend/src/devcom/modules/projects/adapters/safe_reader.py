from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path

from devcom.modules.projects.adapters.safe_path import open_regular_readonly
from devcom.modules.projects.domain.bounds import FilesystemBounds
from devcom.modules.projects.domain.errors import (
    BoundsExceededError,
    ExclusionError,
    SpecialFileError,
)
from devcom.modules.projects.domain.exclusion_policy import ExclusionPolicy


@dataclass(frozen=True, slots=True)
class ReadFileResult:
    relative_path: str
    sha256: str
    byte_size: int
    content_text: str


def read_text_file(
    *,
    root: Path,
    relative: str,
    policy: ExclusionPolicy,
    bounds: FilesystemBounds,
) -> ReadFileResult:
    reason = policy.reason_for(relative, is_dir=False)
    if reason is not None:
        raise ExclusionError(f"excluded: {relative} ({reason})")
    fd, _ = open_regular_readonly(root, relative)
    try:
        st = os.fstat(fd)
        if st.st_size > bounds.max_bytes_per_file:
            raise BoundsExceededError(
                f"file {relative} exceeds max_bytes_per_file ({st.st_size})"
            )
        raw = os.read(fd, st.st_size + 1)
        if len(raw) > bounds.max_bytes_per_file:
            raise BoundsExceededError(f"file {relative} grew past max_bytes_per_file")
    finally:
        os.close(fd)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SpecialFileError(f"not UTF-8 text: {relative}") from exc
    digest = hashlib.sha256(raw).hexdigest()
    return ReadFileResult(
        relative_path=relative.replace("\\", "/"),
        sha256=digest,
        byte_size=len(raw),
        content_text=text,
    )
