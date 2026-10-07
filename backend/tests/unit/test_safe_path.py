from __future__ import annotations

import os
from pathlib import Path

import pytest

from devcom.modules.projects.adapters.safe_path import (
    assert_usable_root,
    open_regular_readonly,
    walk_components,
)
from devcom.modules.projects.domain.errors import (
    PathEscapeError,
    SourceRootError,
    SpecialFileError,
)


def test_rejects_symlink_root(tmp_path: Path) -> None:
    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "link"
    link.symlink_to(real)
    with pytest.raises(SourceRootError):
        assert_usable_root(link)


def test_rejects_symlink_component(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    target = tmp_path / "outside"
    target.mkdir()
    (target / "secret.txt").write_text("nope", encoding="utf-8")
    (root / "via").symlink_to(target)
    with pytest.raises(PathEscapeError):
        walk_components(root, "via/secret.txt")


def test_rejects_dotdot(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    with pytest.raises(PathEscapeError):
        walk_components(root, "../escape")


def test_rejects_fifo(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    fifo = root / "pipe"
    try:
        os.mkfifo(fifo)
    except OSError:
        pytest.skip("mkfifo unavailable")
    with pytest.raises(SpecialFileError):
        open_regular_readonly(root, "pipe")


def test_reads_regular_file(tmp_path: Path) -> None:
    root = tmp_path / "root"
    nested = root / "a"
    nested.mkdir(parents=True)
    (nested / "ok.txt").write_text("hello", encoding="utf-8")
    fd, path = open_regular_readonly(root, "a/ok.txt")
    try:
        assert path.name == "ok.txt"
        assert os.read(fd, 1024) == b"hello"
    finally:
        os.close(fd)
