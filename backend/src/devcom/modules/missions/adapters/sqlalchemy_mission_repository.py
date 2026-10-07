from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, sessionmaker

from devcom.modules.missions.adapters.mission_mappers import (
    mission_to_row,
    row_to_mission,
    task_to_row,
)
from devcom.modules.missions.adapters.sqlalchemy_models import MissionRow, MissionTaskRow
from devcom.modules.missions.domain.mission import Mission


class SqlAlchemyMissionRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def save_atomic(self, mission: Mission) -> None:
        with self._session_factory() as session:
            existing = session.get(MissionRow, mission.id)
            fresh = mission_to_row(mission)
            if existing is None:
                session.add(fresh)
            else:
                _copy_mission_row(fresh, existing)
            session.execute(
                delete(MissionTaskRow).where(MissionTaskRow.mission_id == mission.id)
            )
            for task in mission.tasks:
                session.add(task_to_row(task, mission.id))
            session.commit()

    def get_by_id(self, mission_id: str) -> Mission | None:
        with self._session_factory() as session:
            row = session.get(MissionRow, mission_id)
            if row is None:
                return None
            tasks = session.scalars(
                select(MissionTaskRow).where(MissionTaskRow.mission_id == mission_id)
            ).all()
            return row_to_mission(row, list(tasks))

    def list_for_project(self, project_id: str | None) -> list[Mission]:
        with self._session_factory() as session:
            statement = select(MissionRow).order_by(MissionRow.updated_at.desc())
            if project_id is not None:
                statement = statement.where(MissionRow.project_id == project_id)
            rows = list(session.scalars(statement).all())
            return [self._hydrate(session, row) for row in rows]

    def _hydrate(self, session: Session, row: MissionRow) -> Mission:
        tasks = session.scalars(
            select(MissionTaskRow).where(MissionTaskRow.mission_id == row.id)
        ).all()
        return row_to_mission(row, list(tasks))


def _copy_mission_row(source: MissionRow, target: MissionRow) -> None:
    target.project_id = source.project_id
    target.request_text = source.request_text
    target.status = source.status
    target.created_at = source.created_at
    target.updated_at = source.updated_at
    target.routing_mode = source.routing_mode
    target.routing_disclaimer = source.routing_disclaimer
    target.routing_rule_ids = source.routing_rule_ids
    target.routing_rationale = source.routing_rationale
    target.capability_registry_version = source.capability_registry_version
    target.permission_policy_version = source.permission_policy_version
    target.dispatch_rules_version = source.dispatch_rules_version
    target.clarification_token = source.clarification_token
    target.clarification_questions_json = source.clarification_questions_json
    target.auth_block_action_id = source.auth_block_action_id
    target.auth_block_message = source.auth_block_message
    target.auth_block_rationale = source.auth_block_rationale
