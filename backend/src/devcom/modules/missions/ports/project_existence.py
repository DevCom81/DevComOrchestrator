from typing import Protocol


class ProjectExistencePort(Protocol):
    def exists(self, project_id: str) -> bool:
        """Return True when the project id is known."""
