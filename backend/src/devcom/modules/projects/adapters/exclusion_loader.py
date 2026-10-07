from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from devcom.modules.projects.adapters.gitignore_loader import load_gitignore_patterns
from devcom.modules.projects.domain.exclusion_policy import ExclusionPolicy


def load_hard_exclusions(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def build_policy(
    *,
    contract: dict[str, Any],
    project_globs: tuple[str, ...],
    root: Path | None,
    apply_gitignore: bool,
) -> ExclusionPolicy:
    gitignore: tuple[str, ...] = ()
    if apply_gitignore and root is not None and bool(contract.get("apply_gitignore", True)):
        gitignore = load_gitignore_patterns(root)
    return ExclusionPolicy(
        hard_name_patterns=_string_tuple(contract["hard_name_patterns"]),
        hard_dir_names=_string_tuple(contract["hard_dir_names"]),
        hard_extensions=_string_tuple(contract["hard_extensions"]),
        project_globs=project_globs,
        gitignore_patterns=gitignore,
    )


def _string_tuple(raw: object) -> tuple[str, ...]:
    if not isinstance(raw, list):
        raise TypeError("exclusion contract list expected")
    return tuple(str(item) for item in raw)
