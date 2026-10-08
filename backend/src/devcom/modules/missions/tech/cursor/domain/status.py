from enum import StrEnum

CANON_VERSION = "cursor_package_canon_v1"
REPORT_MAX_BYTES = 204_800
DIFF_MAX_BYTES = 1_048_576
SECTION_MIN = 1
SECTION_MAX = 4000


class CursorPlanStatus(StrEnum):
    DRAFT = "draft"
    AWAITING_GO = "awaiting_go"
    GO_GRANTED = "go_granted"
    EXPORTED = "exported"
    RETURN_IMPORTED = "return_imported"


class VerificationStatus(StrEnum):
    UNVERIFIED = "unverified"
    CONSISTENT_WITH_REF = "consistent_with_ref"
    PARTIAL = "partial"
    BASE_MISMATCH = "base_mismatch"
    UNKNOWN_BASE = "unknown_base"
    REJECTED_BOUNDS = "rejected_bounds"
    REJECTED_FORMAT = "rejected_format"
