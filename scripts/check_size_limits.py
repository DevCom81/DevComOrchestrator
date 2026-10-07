#!/usr/bin/env python3
"""Check AGENTS.md readability limits for Python sources."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_ROOTS = [
    REPO_ROOT / "backend" / "src",
    REPO_ROOT / "backend" / "tests",
    REPO_ROOT / "backend" / "migrations",
    REPO_ROOT / "scripts",
]
FILE_MAX = 250
FUNC_MAX = 40
TEST_FILE_MAX = 300
SCRIPT_MAX = 100
EXEMPT_FILES: dict[str, str] = {}


class FunctionVisitor(ast.NodeVisitor):
    def __init__(self, path: Path) -> None:
        self.path = path
        self.violations: list[str] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._check(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._check(node)
        self.generic_visit(node)

    def _check(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        if node.end_lineno is None:
            return
        lines = node.end_lineno - node.lineno + 1
        if lines > FUNC_MAX:
            self.violations.append(
                f"{self.path}:{node.lineno} function `{node.name}` "
                f"has {lines} lines (max {FUNC_MAX})"
            )


def check_python_file(path: Path) -> list[str]:
    relative = str(path.relative_to(REPO_ROOT))
    if relative in EXEMPT_FILES:
        return []
    violations: list[str] = []
    line_count = len(path.read_text(encoding="utf-8").splitlines())
    is_test = "/tests/" in relative.replace("\\", "/")
    is_script = relative.startswith("scripts/")
    limit = SCRIPT_MAX if is_script else TEST_FILE_MAX if is_test else FILE_MAX
    if line_count > limit:
        violations.append(f"{relative}: file has {line_count} lines (max {limit})")
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    visitor = FunctionVisitor(path)
    visitor.visit(tree)
    violations.extend(visitor.violations)
    return violations


def main() -> int:
    violations: list[str] = []
    for root in PYTHON_ROOTS:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.py")):
            violations.extend(check_python_file(path))
    if violations:
        print("Python size limit violations:")
        for item in violations:
            print(f"  - {item}")
        return 1
    print(f"Python size limits OK (file max {FILE_MAX}, function max {FUNC_MAX}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
