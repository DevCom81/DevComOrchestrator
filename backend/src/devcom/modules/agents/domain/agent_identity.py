from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AgentIdentity:
    """Catalogue identity only — no operational runtime state in lot 0."""

    id: str
    display_name: str
    specialty_bullets: tuple[str, str, str]
