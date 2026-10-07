from __future__ import annotations

import json
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from devcom.modules.missions.tech.adapters.sqlalchemy_models import TechPipelineStepRow


class SqlAlchemyStepStore:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._sessions = session_factory

    def replace_plan(self, review_id: str, steps: list[dict[str, Any]]) -> None:
        with self._sessions() as session:
            existing = session.scalars(
                select(TechPipelineStepRow).where(TechPipelineStepRow.review_id == review_id)
            ).all()
            for row in existing:
                session.delete(row)
            for step in steps:
                session.add(
                    TechPipelineStepRow(
                        id=str(uuid4()),
                        review_id=review_id,
                        step_key=step["step_key"],
                        phase=step["phase"],
                        agent_id=step["agent_id"],
                        status="pending",
                        optional=1 if step.get("optional") else 0,
                        result_json=None,
                        error_message=None,
                        cost_status=None,
                    )
                )
            session.commit()

    def list_steps(self, review_id: str) -> list[dict[str, Any]]:
        with self._sessions() as session:
            rows = session.scalars(
                select(TechPipelineStepRow)
                .where(TechPipelineStepRow.review_id == review_id)
                .order_by(TechPipelineStepRow.phase, TechPipelineStepRow.agent_id)
            ).all()
            return [
                {
                    "step_key": row.step_key,
                    "phase": row.phase,
                    "agent_id": row.agent_id,
                    "status": row.status,
                    "optional": bool(row.optional),
                    "result": json.loads(row.result_json) if row.result_json else None,
                    "error_message": row.error_message,
                    "cost_status": row.cost_status,
                }
                for row in rows
            ]

    def mark(
        self,
        review_id: str,
        step_key: str,
        *,
        status: str,
        result: dict[str, Any] | None = None,
        error_message: str | None = None,
        cost_status: str | None = None,
    ) -> bool:
        """Return False if step was already terminal (double-exec guard)."""
        with self._sessions() as session:
            row = session.scalars(
                select(TechPipelineStepRow).where(
                    TechPipelineStepRow.review_id == review_id,
                    TechPipelineStepRow.step_key == step_key,
                )
            ).first()
            if row is None:
                return False
            if row.status in {"completed", "skipped", "failed", "uncertain"}:
                return False
            if status == "in_flight" and row.status != "pending":
                return False
            row.status = status
            if result is not None:
                row.result_json = json.dumps(result, ensure_ascii=False)
            if error_message is not None:
                row.error_message = error_message
            if cost_status is not None:
                row.cost_status = cost_status
            session.commit()
            return True

    def mark_in_flight_uncertain(self, review_id: str | None = None) -> int:
        with self._sessions() as session:
            query = select(TechPipelineStepRow).where(
                TechPipelineStepRow.status == "in_flight"
            )
            if review_id is not None:
                query = query.where(TechPipelineStepRow.review_id == review_id)
            rows = session.scalars(query).all()
            for row in rows:
                row.status = "uncertain"
                row.cost_status = "uncertain"
                row.error_message = "interrupted before confirmed persistence"
            session.commit()
            return len(rows)

    def list_uncertain_keys(self) -> list[tuple[str, str]]:
        with self._sessions() as session:
            rows = session.scalars(
                select(TechPipelineStepRow).where(TechPipelineStepRow.status == "uncertain")
            ).all()
            return [(row.review_id, row.step_key) for row in rows]
