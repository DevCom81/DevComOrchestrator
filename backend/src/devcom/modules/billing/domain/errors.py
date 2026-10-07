from devcom.shared.errors import ValidationError


class BudgetExceededError(ValidationError):
    code = "budget_exceeded"


class BudgetConflictError(ValidationError):
    code = "budget_conflict"


class PricingError(ValidationError):
    code = "pricing_error"


class RealModeUnavailableError(ValidationError):
    code = "real_mode_unavailable"


class PipelineLockError(ValidationError):
    code = "pipeline_lock"
