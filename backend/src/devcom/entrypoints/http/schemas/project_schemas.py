from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProjectDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    description: str
    created_at: datetime
    updated_at: datetime


class ProjectListDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[ProjectDto]


class CreateProjectBody(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)

    name: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=4000)


class UpdateProjectBody(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)

    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, min_length=1, max_length=4000)
