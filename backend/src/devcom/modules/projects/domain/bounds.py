from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class FilesystemBounds:
    max_files_per_snapshot: int
    max_bytes_per_file: int
    max_bytes_per_snapshot: int
    max_estimated_tokens_per_snapshot: int
    max_tree_depth: int
    max_tree_entries_per_page: int
    max_tree_entries_total: int
    max_browse_seconds: int
    preview_ttl_seconds: int
    token_blocking_method: str
    token_indicative_method: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FilesystemBounds:
        return cls(
            max_files_per_snapshot=int(data["max_files_per_snapshot"]),
            max_bytes_per_file=int(data["max_bytes_per_file"]),
            max_bytes_per_snapshot=int(data["max_bytes_per_snapshot"]),
            max_estimated_tokens_per_snapshot=int(data["max_estimated_tokens_per_snapshot"]),
            max_tree_depth=int(data["max_tree_depth"]),
            max_tree_entries_per_page=int(data["max_tree_entries_per_page"]),
            max_tree_entries_total=int(data["max_tree_entries_total"]),
            max_browse_seconds=int(data["max_browse_seconds"]),
            preview_ttl_seconds=int(data["preview_ttl_seconds"]),
            token_blocking_method=str(data["token_blocking_method"]),
            token_indicative_method=str(data["token_indicative_method"]),
        )
