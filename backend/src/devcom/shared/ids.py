from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class ProjectId:
    value: str

    @classmethod
    def new(cls) -> ProjectId:
        return cls(str(uuid4()))

    @classmethod
    def parse(cls, raw: str) -> ProjectId:
        try:
            return cls(str(UUID(raw)))
        except ValueError as exc:
            raise ValueError("project id must be a UUID") from exc

    def __str__(self) -> str:
        return self.value
