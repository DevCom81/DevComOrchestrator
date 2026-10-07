from devcom.shared.errors import NotFoundError, ValidationError


class TechValidationError(ValidationError):
    code = "validation_error"


class TechNotFoundError(NotFoundError):
    code = "tech_review_not_found"


class TechConflictError(ValidationError):
    code = "conflict"


class TechIdempotencyConflictError(ValidationError):
    code = "idempotency_conflict"


class ScenarioContractError(ValidationError):
    code = "invalid_scenario_contract"


class ProposalBlockedError(ValidationError):
    code = "proposal_blocked"


class StaleProposalVersionError(ValidationError):
    code = "stale_proposal_version"
