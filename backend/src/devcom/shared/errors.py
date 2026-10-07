class DomainError(Exception):
    """Base domain error with a stable machine-readable code."""

    code = "domain_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ValidationError(DomainError):
    code = "validation_error"


class NotFoundError(DomainError):
    code = "not_found"
