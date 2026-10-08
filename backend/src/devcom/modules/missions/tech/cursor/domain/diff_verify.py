from __future__ import annotations

from dataclasses import dataclass

from devcom.modules.missions.tech.cursor.domain.status import VerificationStatus
from devcom.modules.projects.domain.code_artifacts import CodeSnapshot


@dataclass(frozen=True, slots=True)
class VerifyResult:
    status: VerificationStatus
    notes: str


@dataclass(frozen=True, slots=True)
class _Hunk:
    path: str
    lines: list[str]


def verify_unified_diff(
    diff_text: str,
    *,
    snapshot: CodeSnapshot | None,
    declared_commit: str | None,
    snapshot_git_commit: str | None,
) -> VerifyResult:
    if snapshot is None:
        return VerifyResult(
            VerificationStatus.UNKNOWN_BASE,
            "Base source inconnue — aucun snapshot lié au plan.",
        )
    files = {item.relative_path: item.content_text.splitlines() for item in snapshot.files}
    paths: list[str] = []
    checked = 0
    mismatches = 0
    for hunk in _parse_hunks(diff_text):
        if not _safe_rel(hunk.path):
            return VerifyResult(
                VerificationStatus.REJECTED_FORMAT,
                f"Chemin de diff refusé : `{hunk.path}`.",
            )
        paths.append(hunk.path)
        if hunk.path not in files:
            continue
        checked += 1
        if not _context_matches(files[hunk.path], hunk.lines):
            mismatches += 1
    if declared_commit and snapshot_git_commit and declared_commit != snapshot_git_commit:
        note = (
            f"declared_commit `{declared_commit}` ≠ snapshot git `{snapshot_git_commit}` "
            "(signal, pas une preuve de cohérence du diff)."
        )
    else:
        note = ""
    if not paths:
        return VerifyResult(
            VerificationStatus.REJECTED_FORMAT,
            "Diff unifié vide ou non reconnu.",
        )
    if checked == 0:
        return VerifyResult(
            VerificationStatus.PARTIAL,
            "Aucun fichier du diff présent dans le snapshot — vérification partielle. " + note,
        )
    if mismatches:
        return VerifyResult(
            VerificationStatus.BASE_MISMATCH,
            f"{mismatches} hunk(s) ne correspondent pas au snapshot. " + note,
        )
    return VerifyResult(
        VerificationStatus.CONSISTENT_WITH_REF,
        "Contextes/suppressions du diff cohérents avec le snapshot pour les fichiers présents. "
        "Ce n'est pas une preuve que des tests ont réussi ni que le patch a été appliqué. "
        + note,
    )


def _safe_rel(path: str) -> bool:
    if not path or path.startswith("/") or path.startswith("\\"):
        return False
    parts = path.replace("\\", "/").split("/")
    return ".." not in parts and all(parts)


def _parse_hunks(diff_text: str) -> list[_Hunk]:
    hunks: list[_Hunk] = []
    current_path: str | None = None
    current_lines: list[str] = []
    for line in diff_text.splitlines():
        if line.startswith("+++ "):
            raw = line[4:].strip()
            if raw.startswith("b/"):
                raw = raw[2:]
            current_path = raw
            continue
        if line.startswith("@@"):
            if current_path is not None and current_lines:
                hunks.append(_Hunk(path=current_path, lines=list(current_lines)))
            current_lines = []
            continue
        if current_path is None:
            continue
        if line.startswith((" ", "-", "+")):
            current_lines.append(line)
    if current_path is not None and current_lines:
        hunks.append(_Hunk(path=current_path, lines=list(current_lines)))
    return hunks


def _context_matches(file_lines: list[str], hunk_lines: list[str]) -> bool:
    expected: list[str] = []
    for line in hunk_lines:
        if line.startswith(" "):
            expected.append(line[1:])
        elif line.startswith("-"):
            expected.append(line[1:])
    if not expected:
        return True
    n = len(expected)
    limit = len(file_lines) - n + 1
    for index in range(max(0, limit)):
        if file_lines[index : index + n] == expected:
            return True
    return False
