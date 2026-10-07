from devcom.shared.errors import NotFoundError, ValidationError


class MissionValidationError(ValidationError):
    code = "validation_error"


class MissionNotFoundError(NotFoundError):
    code = "mission_not_found"


class ProjectMissingError(ValidationError):
    code = "project_not_found"


class StaleClarificationError(ValidationError):
    code = "stale_clarification"


class OutOfScopeAssignmentError(ValidationError):
    code = "out_of_scope_assignment"


class UnknownActionError(ValidationError):
    code = "unknown_action"


class PermissionDeniedError(ValidationError):
    code = "permission_denied"
