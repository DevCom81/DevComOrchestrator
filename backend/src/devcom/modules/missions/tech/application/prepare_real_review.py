from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from devcom.modules.billing.adapters.rate_tables import (
    load_call_bounds,
    load_fx_table,
    load_openai_rates,
)
from devcom.modules.billing.application.envelope import compute_max_envelope
from devcom.modules.billing.domain.errors import PricingError, RealModeUnavailableError
from devcom.modules.missions.tech.application.real_plan import build_real_plan, plan_as_dicts
from devcom.modules.missions.tech.domain.errors import TechValidationError
from devcom.modules.missions.tech.domain.review import TechReview
from devcom.modules.missions.tech.domain.status import ExecutionMode
from devcom.modules.missions.tech.ports.project_snapshot import ProjectSnapshotPort
from devcom.shared.time import Clock

REAL_DISCLAIMER = (
    "Revue TECH réelle — appels OpenAI facturés selon l'enveloppe réservée. "
    "Aucune décision n'autorise une implémentation, modification de dépôt "
    "ni action externe."
)


class PrepareRealReview:
    def __init__(
        self,
        *,
        snapshots: ProjectSnapshotPort,
        bounds_path: Path,
        rates_path: Path,
        fx_path: Path,
        review_cap_eur_micros: int,
        real_mode_enabled: bool,
        clock: Clock,
    ) -> None:
        self._snapshots = snapshots
        self._bounds_path = bounds_path
        self._rates_path = rates_path
        self._fx_path = fx_path
        self._review_cap = review_cap_eur_micros
        self._real_enabled = real_mode_enabled
        self._clock = clock

    def apply(self, review: TechReview) -> TechReview:
        if not self._real_enabled:
            raise RealModeUnavailableError(
                "real mode is disabled — set DEVCOM_MODE=real to enable paid reviews"
            )
        if review.execution_mode != ExecutionMode.REAL:
            raise TechValidationError("prepare requires execution_mode=real")
        bounds = load_call_bounds(self._bounds_path)
        rates = load_openai_rates(self._rates_path)
        fx = load_fx_table(self._fx_path)
        envelope = compute_max_envelope(bounds, rates, fx)
        if envelope.eur_micros > self._review_cap:
            raise PricingError(
                "reserved envelope exceeds 1 EUR review cap — refusing launch; "
                f"envelope={envelope.eur_micros} µ€, cap={self._review_cap} µ€"
            )
        if envelope.max_calls != int(bounds["max_calls"]):
            raise PricingError("call graph size mismatch with bounds contract")
        now = self._clock.now()
        review.disclaimer = REAL_DISCLAIMER
        review.snapshot = self._snapshots.capture(review.project_id, now.isoformat())
        steps = build_real_plan(bounds, envelope)
        review.plan_json = json.dumps(plan_as_dicts(steps), ensure_ascii=False)
        review.envelope_usd_micros = envelope.usd_micros
        review.envelope_eur_micros = envelope.eur_micros
        review.frozen_models_json = _freeze_json(bounds, envelope)
        review.updated_at = now
        return review


def _freeze_json(bounds: dict[str, Any], envelope: object) -> str:
    from devcom.modules.billing.application.envelope import ReviewEnvelope

    assert isinstance(envelope, ReviewEnvelope)
    return json.dumps(
        {
            "models": bounds["models"],
            "max_calls": envelope.max_calls,
            "fx_rate": envelope.fx_rate,
            "fx_rate_date": envelope.fx_rate_date,
            "fx_margin_ratio": envelope.fx_margin_ratio,
            "rates_verified_at": envelope.rates_verified_at,
            "regional_uplift_ratio": envelope.regional_uplift_ratio,
            "lines": [asdict(line) for line in envelope.lines],
        },
        ensure_ascii=False,
    )
