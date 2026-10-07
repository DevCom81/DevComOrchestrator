from pydantic import BaseModel, ConfigDict


class RuntimeDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: str
    app_name: str
    version: str
