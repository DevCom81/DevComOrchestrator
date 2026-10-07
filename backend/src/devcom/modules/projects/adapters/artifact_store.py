from __future__ import annotations

import hashlib
import json
import os
import tempfile
from collections.abc import Mapping
from pathlib import Path

from devcom.modules.projects.domain.code_artifacts import FileBlob
from devcom.modules.projects.domain.errors import PreviewIntegrityError, SnapshotIntegrityError


class ArtifactStore:
    """Private copies under data_dir with restrictive permissions and atomic replace."""

    def __init__(self, data_dir: Path) -> None:
        self._root = data_dir / "code_artifacts"
        self._root.mkdir(parents=True, exist_ok=True)
        os.chmod(self._root, 0o700)

    def preview_dir(self, preview_id: str) -> Path:
        path = self._root / "previews" / preview_id
        path.mkdir(parents=True, exist_ok=True)
        os.chmod(path, 0o700)
        return path

    def snapshot_dir(self, snapshot_id: str) -> Path:
        path = self._root / "snapshots" / snapshot_id
        return path

    def write_files_atomic(self, directory: Path, files: tuple[FileBlob, ...]) -> str:
        directory.mkdir(parents=True, exist_ok=True)
        os.chmod(directory, 0o700)
        manifest_files: list[dict[str, object]] = []
        for blob in files:
            self._write_blob(directory, blob)
            manifest_files.append(
                {
                    "relative_path": blob.relative_path,
                    "sha256": blob.sha256,
                    "byte_size": blob.byte_size,
                }
            )
        fingerprint = _fingerprint(manifest_files)
        payload: dict[str, object] = {
            "fingerprint": fingerprint,
            "files": manifest_files,
        }
        self._atomic_write_json(directory / "manifest.json", payload)
        return fingerprint

    def read_files(self, directory: Path) -> tuple[FileBlob, ...]:
        manifest_path = directory / "manifest.json"
        if not manifest_path.is_file():
            raise SnapshotIntegrityError("manifest missing")
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        blobs: list[FileBlob] = []
        for item in payload["files"]:
            rel = str(item["relative_path"])
            expected = str(item["sha256"])
            path = directory / "files" / rel
            if not path.is_file():
                raise SnapshotIntegrityError(f"missing copy {rel}")
            raw = path.read_bytes()
            digest = hashlib.sha256(raw).hexdigest()
            if digest != expected:
                raise SnapshotIntegrityError(f"hash mismatch {rel}")
            blobs.append(
                FileBlob(
                    relative_path=rel,
                    sha256=digest,
                    byte_size=len(raw),
                    content_text=raw.decode("utf-8"),
                )
            )
        return tuple(blobs)

    def verify_fingerprint(self, directory: Path, expected: str) -> None:
        manifest_path = directory / "manifest.json"
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        if payload.get("fingerprint") != expected:
            raise PreviewIntegrityError("preview fingerprint mismatch")
        files = self.read_files(directory)
        actual = _fingerprint(
            [
                {
                    "relative_path": item.relative_path,
                    "sha256": item.sha256,
                    "byte_size": item.byte_size,
                }
                for item in files
            ]
        )
        if actual != expected:
            raise PreviewIntegrityError("preview copies altered")

    def promote_preview_to_snapshot(self, preview_id: str, snapshot_id: str) -> Path:
        source = self.preview_dir(preview_id)
        target = self.snapshot_dir(snapshot_id)
        if target.exists():
            raise SnapshotIntegrityError("snapshot directory already exists")
        staging = target.with_suffix(".partial")
        if staging.exists():
            _rm_tree(staging)
        staging.mkdir(parents=True)
        os.chmod(staging, 0o700)
        files = self.read_files(source)
        self.write_files_atomic(staging, files)
        os.rename(staging, target)
        os.chmod(target, 0o700)
        return target

    def _write_blob(self, directory: Path, blob: FileBlob) -> None:
        dest = directory / "files" / blob.relative_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        raw = blob.content_text.encode("utf-8")
        if hashlib.sha256(raw).hexdigest() != blob.sha256:
            raise PreviewIntegrityError(f"blob hash mismatch before write {blob.relative_path}")
        tmp = dest.with_suffix(dest.suffix + ".tmp")
        tmp.write_bytes(raw)
        os.chmod(tmp, 0o600)
        os.replace(tmp, dest)

    def _atomic_write_json(self, path: Path, payload: Mapping[str, object]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", delete=False, dir=path.parent
        ) as handle:
            json.dump(payload, handle, ensure_ascii=False)
            handle.flush()
            os.fsync(handle.fileno())
            tmp_name = handle.name
        os.chmod(tmp_name, 0o600)
        os.replace(tmp_name, path)


def _fingerprint(files: list[dict[str, object]]) -> str:
    canonical = json.dumps(files, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _rm_tree(path: Path) -> None:
    for child in sorted(path.rglob("*"), reverse=True):
        if child.is_file():
            child.unlink(missing_ok=True)
        elif child.is_dir():
            child.rmdir()
    path.rmdir()
