from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast


class PromptBundle:
    def __init__(self, root: Path) -> None:
        self._root = root

    def system(self, name: str, **replacements: str) -> str:
        text = (self._root / "system" / name).read_text(encoding="utf-8")
        for key, value in replacements.items():
            text = text.replace("{{" + key + "}}", value)
        return text

    def schema(self, name: str) -> dict[str, Any]:
        raw = (self._root / "schemas" / name).read_text(encoding="utf-8")
        return cast(dict[str, Any], json.loads(raw))
