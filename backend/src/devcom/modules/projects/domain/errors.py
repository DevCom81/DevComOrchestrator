from devcom.shared.errors import DomainError, NotFoundError, ValidationError


class ProjectValidationError(ValidationError):
    code = "validation_error"


class ProjectNotFoundError(NotFoundError):
    code = "project_not_found"


class SourceRootError(ValidationError):
    code = "source_root_error"


class PathEscapeError(ValidationError):
    code = "path_escape"


class SpecialFileError(ValidationError):
    code = "special_file"


class ExclusionError(ValidationError):
    code = "exclusion"


class BoundsExceededError(ValidationError):
    code = "bounds_exceeded"


class PreviewExpiredError(ValidationError):
    code = "preview_expired"


class PreviewIntegrityError(ValidationError):
    code = "preview_integrity"


class SnapshotNotFoundError(NotFoundError):
    code = "snapshot_not_found"


class SnapshotIntegrityError(DomainError):
    code = "snapshot_integrity"


class BrowseLimitError(ValidationError):
    code = "browse_limit"
