from __future__ import annotations

import threading
from collections.abc import Callable

from devcom.modules.billing.domain.errors import PipelineLockError


class SupervisedRealRunner:
    """In-process supervised runner — one live real review at a time."""

    def __init__(self, run_review: Callable[[str], None]) -> None:
        self._run_review = run_review
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._active_review_id: str | None = None

    @property
    def active_review_id(self) -> str | None:
        return self._active_review_id

    def start(self, review_id: str) -> None:
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                if self._active_review_id == review_id:
                    return
                raise PipelineLockError("supervised runner already busy")
            self._active_review_id = review_id
            self._thread = threading.Thread(
                target=self._safe_run,
                args=(review_id,),
                name=f"real-tech-{review_id[:8]}",
                daemon=False,
            )
            self._thread.start()

    def _safe_run(self, review_id: str) -> None:
        try:
            self._run_review(review_id)
        finally:
            with self._lock:
                if self._active_review_id == review_id:
                    self._active_review_id = None
