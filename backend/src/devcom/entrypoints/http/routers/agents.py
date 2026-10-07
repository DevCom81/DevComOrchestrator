from fastapi import APIRouter

from devcom.entrypoints.http.deps import ContainerDep
from devcom.entrypoints.http.schemas.agent_schemas import AgentDto, AgentListDto

router = APIRouter(tags=["agents"])


@router.get("/api/agents", response_model=AgentListDto)
def list_agents(container: ContainerDep) -> AgentListDto:
    agents = container.list_agents.execute()
    return AgentListDto(
        items=[
            AgentDto(
                id=agent.id,
                display_name=agent.display_name,
                specialty_bullets=list(agent.specialty_bullets),
            )
            for agent in agents
        ]
    )
