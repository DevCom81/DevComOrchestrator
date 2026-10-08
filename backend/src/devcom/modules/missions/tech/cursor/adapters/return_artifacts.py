from __future__ import annotations

import hashlib
import os
from pathlib import Path
from uuid import uuid4


class CursorReturnArtifactStore:
    """Private UTF-8 blobs under data_dir — server-generated ids only."""

    def __init__(self, data_dir: Path) -> None:
        self._root = data_dir / "cursor_returns"
        self._root.mkdir(parents=True, exist_ok=True)
        os.chmod(self._root, 0o700)

    def write_pair(self, *, report: bytes, diff: bytes) -> tuple[str, str, str, str]:
        """Return (return_id, artifact_dir, report_sha256, diff_sha256)."""
        return_id = str(uuid4())
        directory = self._root / return_id
        directory.mkdir(parents=True, exist_ok=True)
        os.chmod(directory, 0o700)
        _atomic_write(directory / "report.txt", report)
        _atomic_write(directory / "diff.patch", diff)
        return (
            return_id,
            str(directory),
            hashlib.sha256(report).hexdigest(),
            hashlib.sha256(diff).hexdigest(),
        )

    def read_text(self, artifact_dir: str, name: str) -> str:
        path = Path(artifact_dir) / name
        return path.read_bytes().decode("utf-8")


def _atomic_write(path: Path, data: bytes) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(data)
    os.chmod(tmp, 0o600)
    tmp.replace(path)
