from enum import StrEnum


class TechReviewStatus(StrEnum):
    SELECTING_SCENARIO = "selecting_scenario"
    READY_TO_RUN = "ready_to_run"
    RUNNING = "running"
    AWAITING_DECISION = "awaiting_decision"
    FAILED_PARTIAL = "failed_partial"
    INTERRUPTED = "interrupted"
    BLOCKED_UNCERTAIN = "blocked_uncertain"
    PAUSED_BUDGET = "paused_budget"
    DECIDED = "decided"


IDEM_ACK_UNCERTAIN = "tech.ack_uncertain"


class ExecutionMode(StrEnum):
    DEMO = "demo"
    REAL = "real"


class EffortBand(StrEnum):
    S = "S"
    M = "M"
    L = "L"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    CRITICAL = "critical"


DEMO_DECISION_AUTHOR = "local-demo-user"
REQUEST_MIN = 1
REQUEST_MAX = 2000
RATIONALE_MIN = 1
RATIONALE_MAX = 2000
UNMATCHED_SCENARIO_NOTE = (
    "Résultats du scénario de démonstration choisi — "
    "votre demande n'a pas été analysée librement."
)
IDEM_CREATE = "tech.create"
IDEM_RUN = "tech.run"
IDEM_DECIDE = "tech.decide"
