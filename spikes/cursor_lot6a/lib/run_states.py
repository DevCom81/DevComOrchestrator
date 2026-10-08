from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class SpikeRunPhase(StrEnum):
    IDLE = "idle"
    RUNNING = "running"
    FINISHED = "finished"
    CANCELLED = "cancelled"
    ERROR = "error"
    UNCERTAIN = "uncertain"


@dataclass(frozen=True, slots=True)
class SpikeRunRecord:
    agent_id: str | None
    run_id: str | None
    phase: SpikeRunPhase
    note: str


def after_interrupt(
    *,
    known_run_id: str | None,
    reconnect_ok: bool,
) -> SpikeRunRecord:
    """Reconnect ≠ new send. Never auto-send after interrupt."""
    if known_run_id is None:
        return SpikeRunRecord(
            agent_id=None,
            run_id=None,
            phase=SpikeRunPhase.UNCERTAIN,
            note="No run_id; recovery impossible without new human GO + send.",
        )
    if reconnect_ok:
        return SpikeRunRecord(
            agent_id=None,
            run_id=known_run_id,
            phase=SpikeRunPhase.RUNNING,
            note="Reconnected to existing run; no automatic send.",
        )
    return SpikeRunRecord(
        agent_id=None,
        run_id=known_run_id,
        phase=SpikeRunPhase.UNCERTAIN,
        note="Cannot prove local resume; state uncertain until human decision.",
    )


def cancel_is_stop_only(phase: SpikeRunPhase) -> bool:
    return phase == SpikeRunPhase.CANCELLED
