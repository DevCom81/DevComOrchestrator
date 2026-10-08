from __future__ import annotations

import hashlib
import json
from typing import Any

from devcom.modules.missions.tech.cursor.domain.errors import CursorValidationError
from devcom.modules.missions.tech.cursor.domain.status import (
    CANON_VERSION,
    SECTION_MAX,
    SECTION_MIN,
)

SECTION_KEYS = (
    "objectif",
    "perimetre",
    "exclusions",
    "contraintes_architecture",
    "criteres_acceptation",
    "validations_attendues",
)


def normalize_markdown(text: str) -> bytes:
    if "\x00" in text:
        raise CursorValidationError("markdown must not contain NUL")
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    try:
        return normalized.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise CursorValidationError("markdown must be UTF-8 encodable") from exc


def build_markdown(sections: dict[str, str]) -> str:
    parts = ["# Plan Cursor", ""]
    titles = {
        "objectif": "Objectif",
        "perimetre": "Périmètre",
        "exclusions": "Exclusions",
        "contraintes_architecture": "Contraintes d'architecture",
        "criteres_acceptation": "Critères d'acceptation",
        "validations_attendues": "Validations attendues",
    }
    for key in SECTION_KEYS:
        value = _bounded(sections[key], key)
        parts.extend([f"## {titles[key]}", value, ""])
    return "\n".join(parts).rstrip() + "\n"


def metadata_without_hash(meta: dict[str, Any]) -> dict[str, Any]:
    clean = {key: meta[key] for key in sorted(meta) if key != "content_hash"}
    return clean


def canonical_metadata_bytes(meta: dict[str, Any]) -> bytes:
    payload = metadata_without_hash(meta)
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return encoded.encode("utf-8")


def compute_content_hash(markdown_utf8: bytes, meta: dict[str, Any]) -> str:
    digest = hashlib.sha256()
    digest.update(markdown_utf8)
    digest.update(b"\n---\n")
    digest.update(canonical_metadata_bytes(meta))
    return digest.hexdigest()


def build_manifest(meta: dict[str, Any], content_hash: str) -> dict[str, Any]:
    """Preview/export manifest includes hash AFTER computation (not in hash input)."""
    body = metadata_without_hash(meta)
    body["content_hash"] = content_hash
    body["canon_version"] = CANON_VERSION
    return body


def manifest_json(manifest: dict[str, Any]) -> str:
    return json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def preview_document(markdown_utf8: bytes, manifest: dict[str, Any]) -> str:
    return (
        markdown_utf8.decode("utf-8")
        + "\n---\n\n## Manifeste approuvé\n\n```json\n"
        + json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n```\n"
    )


def _bounded(raw: str, label: str) -> str:
    text = raw.strip()
    if not (SECTION_MIN <= len(text) <= SECTION_MAX):
        raise CursorValidationError(
            f"{label} must be {SECTION_MIN}–{SECTION_MAX} characters after trim"
        )
    return text
