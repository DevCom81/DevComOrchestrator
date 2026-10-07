from pydantic import BaseModel, ConfigDict, Field


class AgentDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    display_name: str
    specialty_bullets: list[str] = Field(min_length=3, max_length=3)


class AgentListDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[AgentDto]
