from __future__ import annotations

from lib.run_states import SpikeRunPhase, after_interrupt, cancel_is_stop_only


def test_interrupt_without_run_id_is_uncertain() -> None:
    rec = after_interrupt(known_run_id=None, reconnect_ok=False)
    assert rec.phase == SpikeRunPhase.UNCERTAIN
    assert "No run_id" in rec.note


def test_reconnect_does_not_imply_send() -> None:
    rec = after_interrupt(known_run_id="run-1", reconnect_ok=True)
    assert rec.phase == SpikeRunPhase.RUNNING
    assert "no automatic send" in rec.note.lower()


def test_failed_resume_is_uncertain() -> None:
    rec = after_interrupt(known_run_id="run-1", reconnect_ok=False)
    assert rec.phase == SpikeRunPhase.UNCERTAIN


def test_cancel_is_stop_only() -> None:
    assert cancel_is_stop_only(SpikeRunPhase.CANCELLED)
    assert not cancel_is_stop_only(SpikeRunPhase.FINISHED)
