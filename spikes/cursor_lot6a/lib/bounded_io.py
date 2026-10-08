from __future__ import annotations

import hashlib
from pathlib import Path

DEFAULT_MAX_FILE_BYTES = 200 * 1024
DEFAULT_MAX_TOTAL_BYTES = 1 * 1024 * 1024


class BoundExceededError(ValueError):
    pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_bounded(path: Path, *, max_bytes: int) -> bytes:
    data = path.read_bytes()
    if len(data) > max_bytes:
        raise BoundExceededError(f"{path}: {len(data)} > {max_bytes}")
    return data


def write_bounded(path: Path, data: bytes, *, max_bytes: int) -> str:
    if len(data) > max_bytes:
        raise BoundExceededError(f"write {path}: {len(data)} > {max_bytes}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return sha256_bytes(data)
