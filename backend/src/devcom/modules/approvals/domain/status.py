from enum import StrEnum

GO_TTL_HOURS = 24
LOCAL_AUTHOR = "local-demo-user"


class ApprovalStatus(StrEnum):
    PENDING = "pending"
    GRANTED = "granted"
    REFUSED = "refused"
    EXPIRED = "expired"
    INVALIDATED = "invalidated"
    CONSUMED = "consumed"


ACTION_CURSOR_EXPORT = "cursor.plan.export"
