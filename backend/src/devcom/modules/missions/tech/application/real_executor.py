from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session, sessionmaker

from devcom.modules.billing.adapters.rate_tables import FxTable, OpenAiRateTable
from devcom.modules.billing.adapters.sqlalchemy_ledger import SqlAlchemyBudgetLedger
from devcom.modules.missions.domain.assignment_guard import assign_agent
from devcom.modules.missions.domain.capability import CapabilityRegistry
from devcom.modules.missions.domain.permission import PermissionPolicy
from devcom.modules.missions.tech.adapters.sqlalchemy_events import SqlAlchemyEventStore
from devcom.modules.missions.tech.adapters.sqlalchemy_steps import SqlAlchemyStepStore
from devcom.modules.missions.tech.application.complete_real_step import complete_real_step
from devcom.modules.missions.tech.application.persist_step_outcome import mark_step_started
from devcom.modules.missions.tech.application.prompt_loader import PromptBundle
from devcom.modules.missions.tech.application.real_finalize import finalize_real_review
from devcom.modules.missions.tech.application.real_ingest import needs_reply
from devcom.modules.missions.tech.application.real_request_builder import build_llm_request
from devcom.modules.missions.tech.application.real_settle import fail_review, settle_if_safe
from devcom.modules.missions.tech.application.real_step_accept import accept_input_bound
from devcom.modules.missions.tech.domain.artifacts import (
    Challenge,
    Finding,
    SpecialistAnalysis,
)
from devcom.modules.missions.tech.domain.blocking import BlockingPolicy
from devcom.modules.missions.tech.domain.review import TechReview
from devcom.modules.missions.tech.domain.status import TechReviewStatus
from devcom.modules.missions.tech.ports.code_snapshot_port import CodeSnapshotPort
from devcom.modules.missions.tech.ports.llm_completion import LlmCompletionPort
from devcom.modules.missions.tech.ports.tech_review_repository import TechReviewRepository
from devcom.modules.projects.domain.code_artifacts import CodeSnapshot
from devcom.shared.time import Clock


class RealPipelineExecutor:
    def __init__(
        self,
        *,
        repository: TechReviewRepository,
        steps: SqlAlchemyStepStore,
        ledger: SqlAlchemyBudgetLedger,
        events: SqlAlchemyEventStore,
        sessions: sessionmaker[Session],
        llm: LlmCompletionPort,
        prompts: PromptBundle,
        registry: CapabilityRegistry,
        policy: PermissionPolicy,
        blocking: BlockingPolicy,
        rates: OpenAiRateTable,
        fx: FxTable,
        clock: Clock,
        apply_regional: bool,
        code_snapshots: CodeSnapshotPort | None = None,
    ) -> None:
        self._repository = repository
        self._steps = steps
        self._ledger = ledger
        self._events = events
        self._sessions = sessions
        self._llm = llm
        self._prompts = prompts
        self._registry = registry
        self._policy = policy
        self._blocking = blocking
        self._rates = rates
        self._fx = fx
        self._clock = clock
        self._regional = rates.regional_uplift_ratio if apply_regional else "0"
        self._code_snapshots = code_snapshots

    def run(self, review_id: str) -> None:
        review = self._repository.get_by_id(review_id)
        if review is None or review.plan_json is None or review.snapshot is None:
            return
        plan = json.loads(review.plan_json)
        code = self._load_code(review)
        analyses: dict[str, SpecialistAnalysis] = {}
        findings: dict[str, Finding] = {}
        challenges: list[Challenge] = []
        try:
            for step in plan:
                if not self._execute_step(review, step, analyses, findings, challenges, code):
                    return
            self._finalize(review, analyses, challenges, findings)
        finally:
            self._ledger.release_global_lock(review_id)
            settle_if_safe(
                steps=self._steps,
                ledger=self._ledger,
                events=self._events,
                review_id=review_id,
                now=self._clock.now(),
            )

    def _load_code(self, review: TechReview) -> CodeSnapshot | None:
        if review.code_snapshot_id is None or self._code_snapshots is None:
            return None
        return self._code_snapshots.get(review.project_id, review.code_snapshot_id)

    def _execute_step(
        self,
        review: TechReview,
        step: dict[str, Any],
        analyses: dict[str, SpecialistAnalysis],
        findings: dict[str, Finding],
        challenges: list[Challenge],
        code: CodeSnapshot | None,
    ) -> bool:
        skip = self._preflight(review, step, analyses, findings, challenges)
        if skip is not None:
            return skip
        assign_agent(self._registry, step["capability_id"], step["agent_id"], "real-pipeline")
        request = build_llm_request(
            review=review,
            step=step,
            prompts=self._prompts,
            analyses=analyses,
            findings=findings,
            challenges=challenges,
            code_snapshot=code,
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
        now = self._clock.now()
        if not mark_step_started(
            sessions=self._sessions,
            events=self._events,
            review_id=review.id,
            step_key=step["step_key"],
            now=now,
        ):
            return True
        result = self._llm.complete(request)
        ok, fail_status, message = complete_real_step(
            sessions=self._sessions,
            events=self._events,
            rates=self._rates,
            fx=self._fx,
            regional=self._regional,
            review=review,
            step=step,
            result=result,
            analyses=analyses,
            findings=findings,
            challenges=challenges,
            code_snapshot=code,
            now=self._clock.now(),
        )
        if ok:
            return True
        assert fail_status is not None and message is not None
        self._fail(review, message, fail_status)
        return False

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
        settle_if_safe(
            steps=self._steps,
            ledger=self._ledger,
            events=self._events,
            review_id=review.id,
            now=self._clock.now(),
        )
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
        self._events.append(
            review_id=review.id,
            event_type="review.terminal",
            dedupe_key="review.terminal:awaiting_decision",
            payload={"status": TechReviewStatus.AWAITING_DECISION.value},
            occurred_at=self._clock.now(),
        )

    def _fail(self, review: TechReview, message: str, status: TechReviewStatus) -> None:
        fail_review(
            repository=self._repository,
            steps=self._steps,
            ledger=self._ledger,
            events=self._events,
            review=review,
            message=message,
            status=status,
            now=self._clock.now(),
        )
