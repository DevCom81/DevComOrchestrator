from fastapi import APIRouter

from devcom.entrypoints.http.deps import ContainerDep
from devcom.entrypoints.http.schemas.runtime_schemas import RuntimeDto
from devcom.entrypoints.http.schemas.tech_schemas import BudgetSummaryDto
from devcom.modules.billing.domain.period import budget_month_id
from devcom.shared.time import SystemClock

router = APIRouter(tags=["runtime"])


@router.get("/api/runtime", response_model=RuntimeDto)
def runtime(container: ContainerDep) -> RuntimeDto:
    settings = container.settings
    month_id = budget_month_id(SystemClock().now())
    raw = container.budget_ledger.summary(month_id)
    return RuntimeDto(
        mode=settings.mode,
        app_name=settings.app_name,
        version=settings.version,
        openai_key_configured=container.openai_key_configured,
        real_mode_enabled=settings.real_mode_enabled,
        budget=BudgetSummaryDto(
            month_id=str(raw["month_id"]),
            cap_eur_micros=int(raw["cap_eur_micros"]),
            confirmed_eur_micros=int(raw["confirmed_eur_micros"]),
            reserved_eur_micros=int(raw["reserved_eur_micros"]),
            uncertain_eur_micros=int(raw["uncertain_eur_micros"]),
        ),
    )
