from __future__ import annotations

import fnmatch
from dataclasses import dataclass
from pathlib import PurePosixPath


@dataclass(frozen=True, slots=True)
class ExclusionPolicy:
    hard_name_patterns: tuple[str, ...]
    hard_dir_names: tuple[str, ...]
    hard_extensions: tuple[str, ...]
    project_globs: tuple[str, ...]
    gitignore_patterns: tuple[str, ...]

    def reason_for(self, relative_path: str, *, is_dir: bool = False) -> str | None:
        posix = relative_path.replace("\\", "/")
        parts = PurePosixPath(posix).parts
        name = parts[-1] if parts else posix
        for directory in parts[:-1] if not is_dir else parts:
            if directory in self.hard_dir_names:
                return f"hard dir {directory}"
        if name in self.hard_dir_names:
            return f"hard dir {name}"
        for pattern in self.hard_name_patterns:
            if fnmatch.fnmatch(name, pattern):
                return f"hard name {pattern}"
        lower = name.lower()
        for extension in self.hard_extensions:
            if lower.endswith(extension.lower()):
                return f"hard extension {extension}"
        for pattern in self.project_globs:
            if fnmatch.fnmatch(posix, pattern) or fnmatch.fnmatch(name, pattern):
                return f"project exclusion {pattern}"
        for pattern in self.gitignore_patterns:
            if _gitignore_match(posix, pattern, is_dir=is_dir):
                return f"gitignore {pattern}"
        return None


def _gitignore_match(path: str, pattern: str, *, is_dir: bool) -> bool:
    raw = pattern.strip()
    if not raw or raw.startswith("#") or raw.startswith("!"):
        return False
    directory_only = raw.endswith("/")
    body = raw[:-1] if directory_only else raw
    if directory_only and not is_dir:
        return False
    if body.startswith("/"):
        body = body[1:]
        return fnmatch.fnmatch(path, body) or (is_dir and fnmatch.fnmatch(path + "/", body + "/"))
    if "/" in body:
        return fnmatch.fnmatch(path, body) or fnmatch.fnmatch(path, "*/" + body)
    name = path.rsplit("/", 1)[-1]
    return fnmatch.fnmatch(name, body) or fnmatch.fnmatch(path, "*/" + body)
