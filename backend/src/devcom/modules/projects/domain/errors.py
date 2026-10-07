from devcom.shared.errors import NotFoundError, ValidationError


class ProjectValidationError(ValidationError):
    code = "validation_error"


class ProjectNotFoundError(NotFoundError):
    code = "project_not_found"
