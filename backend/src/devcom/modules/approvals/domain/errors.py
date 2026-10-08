from devcom.shared.errors import NotFoundError, ValidationError


class ApprovalValidationError(ValidationError):
    code = "approval_validation"


class ApprovalNotFoundError(NotFoundError):
    code = "approval_not_found"


class ApprovalConflictError(ValidationError):
    code = "approval_conflict"
