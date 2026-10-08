from devcom.shared.errors import NotFoundError, ValidationError


class CursorValidationError(ValidationError):
    code = "cursor_validation"


class CursorNotFoundError(NotFoundError):
    code = "cursor_not_found"


class CursorConflictError(ValidationError):
    code = "cursor_conflict"
