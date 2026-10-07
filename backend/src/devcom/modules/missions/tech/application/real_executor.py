from __future__ import annotations

import json
from typing import Any

from devcom.modules.billing.adapters.rate_tables import FxTable, OpenAiRateTable
from devcom.modules.billing.adapters.sqlalchemy_ledger import SqlAlchemyBudgetLedger
from devcom.modules.missions.domain.assignment_guard import assign_agent
from devcom.modules.missions.domain.capability import CapabilityRegistry
from devcom.modules.missions.domain.permission import PermissionPolicy
from devcom.modules.missions.tech.adapters.sqlalchemy_steps import SqlAlchemyStepStore
from devcom.modules.missions.tech.application.prompt_loader import PromptBundle
from devcom.modules.missions.tech.application.real_cost import record_step_cost
from devcom.modules.missions.tech.application.real_finalize import finalize_real_review
from devcom.modules.missions.tech.application.real_ingest import needs_reply
from devcom.modules.missions.tech.application.real_request_builder import build_llm_request
from devcom.modules.missions.tech.application.real_step_accept import (
    accept_input_bound,
    accept_result,
)
from devcom.modules.missions.tech.domain.artifacts import (
    Challenge,
    Finding,
    SpecialistAnalysis,
)
from devcom.modules.missions.tech.domain.blocking import BlockingPolicy
from devcom.modules.missions.tech.domain.review import TechReview
from devcom.modules.missions.tech.domain.status import TechReviewStatus
from devcom.modules.missions.tech.ports.llm_completion import LlmCompletionPort
from devcom.modules.missions.tech.ports.tech_review_repository import TechReviewRepository
from devcom.shared.time import Clock


class RealPipelineExecutor:
    def __init__(
        self,
        *,
        repository: TechReviewRepository,
        steps: SqlAlchemyStepStore,
        ledger: SqlAlchemyBudgetLedger,
        llm: LlmCompletionPort,
        prompts: PromptBundle,
        registry: CapabilityRegistry,
        policy: PermissionPolicy,
        blocking: BlockingPolicy,
        rates: OpenAiRateTable,
        fx: FxTable,
        clock: Clock,
        apply_regional: bool,
    ) -> None:
        self._repository = repository
        self._steps = steps
        self._ledger = ledger
        self._llm = llm
        self._prompts = prompts
        self._registry = registry
        self._policy = policy
        self._blocking = blocking
        self._rates = rates
        self._fx = fx
        self._clock = clock
        self._regional = rates.regional_uplift_ratio if apply_regional else "0"

    def run(self, review_id: str) -> None:
        review = self._repository.get_by_id(review_id)
        if review is None or review.plan_json is None or review.snapshot is None:
            return
        plan = json.loads(review.plan_json)
        analyses: dict[str, SpecialistAnalysis] = {}
        findings: dict[str, Finding] = {}
        challenges: list[Challenge] = []
        try:
            for step in plan:
                if not self._execute_step(review, step, analyses, findings, challenges):
                    return
            self._finalize(review, analyses, challenges, findings)
        finally:
            self._ledger.release_global_lock(review_id)
            self._ledger.release_unused_envelope(review_id)

    def _execute_step(
        self,
        review: TechReview,
        step: dict[str, Any],
        analyses: dict[str, SpecialistAnalysis],
        findings: dict[str, Finding],
        challenges: list[Challenge],
    ) -> bool:
        skip = self._preflight(review, step, analyses, findings, challenges)
        if skip is not None:
            return skip
        if not self._steps.mark(review.id, step["step_key"], status="in_flight"):
            return True
        assign_agent(self._registry, step["capability_id"], step["agent_id"], "real-pipeline")
        request = build_llm_request(
            review=review,
            step=step,
            prompts=self._prompts,
            analyses=analyses,
            findings=findings,
            challenges=challenges,
        )
        if not accept_input_bound(
            llm=self._llm,
            steps=self._steps,
            review=review,
            step_key=step["step_key"],
            request=request,
            fail=self._fail,
        ):
            return False
        result = self._llm.complete(request)
        record_step_cost(
            ledger=self._ledger,
            rates=self._rates,
            fx=self._fx,
            regional=self._regional,
            review_id=review.id,
            step=step,
            result=result,
            now=self._clock.now(),
        )
        return accept_result(
            steps=self._steps,
            review=review,
            step=step,
            result=result,
            analyses=analyses,
            findings=findings,
            challenges=challenges,
            fail=self._fail,
        )

    def _preflight(
        self,
        review: TechReview,
        step: dict[str, Any],
        analyses: dict[str, SpecialistAnalysis],
        findings: dict[str, Finding],
        challenges: list[Challenge],
    ) -> bool | None:
        if step["phase"] == "reply" and not needs_reply(
            step["agent_id"], challenges, analyses, findings
        ):
            self._steps.mark(review.id, step["step_key"], status="skipped")
            return True
        if self._blocked_by_uncertain(review.id, step.get("depends_on", [])):
            self._fail(
                review,
                "blocked by uncertain dependency",
                TechReviewStatus.BLOCKED_UNCERTAIN,
            )
            return False
        if self._ledger.is_overrun(review.id):
            self._fail(review, "budget overrun — new calls blocked", TechReviewStatus.PAUSED_BUDGET)
            return False
        return None

    def _blocked_by_uncertain(self, review_id: str, depends_on: list[str]) -> bool:
        if not depends_on:
            return False
        return any(
            item["status"] == "uncertain"
            for item in self._steps.list_steps(review_id)
            if item["step_key"] in depends_on
        )

    def _finalize(
        self,
        review: TechReview,
        analyses: dict[str, SpecialistAnalysis],
        challenges: list[Challenge],
        findings: dict[str, Finding],
    ) -> None:
        steps = {item["step_key"]: item for item in self._steps.list_steps(review.id)}
        synth_row = steps.get("synthesize")
        if synth_row is None or synth_row["status"] != "completed" or not synth_row["result"]:
            self._fail(review, "synthesis missing", TechReviewStatus.FAILED_PARTIAL)
            return
        # Settle before terminal status so polls never see held + done.
        self._ledger.release_unused_envelope(review.id)
        finalize_real_review(
            review=review,
            repository=self._repository,
            blocking=self._blocking,
            analyses=analyses,
            challenges=challenges,
            findings=findings,
            synth_result=synth_row["result"],
            registry_version=self._registry.version,
            policy_version=self._policy.version,
            now=self._clock.now(),
        )

    def _fail(self, review: TechReview, message: str, status: TechReviewStatus) -> None:
        self._ledger.release_unused_envelope(review.id)
        review.status = status
        review.failure_message = message
        review.updated_at = self._clock.now()
        self._repository.save_atomic(review)
