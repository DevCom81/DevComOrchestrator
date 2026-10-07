from enum import StrEnum


class MissionStatus(StrEnum):
    DRAFT = "draft"
    AWAITING_CLARIFICATION = "awaiting_clarification"
    ROUTED = "routed"
    BLOCKED_AUTHORIZATION = "blocked_authorization"


class TaskAssignmentStatus(StrEnum):
    VALIDATED = "validated"
    REJECTED = "rejected"
