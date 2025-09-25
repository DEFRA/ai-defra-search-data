from dataclasses import dataclass
from datetime import date

from app.knowledge_management.models import KnowledgeSource


@dataclass(frozen=True)
class KnowledgeSnapshot:
    """ Represents a snapshot of a knowledge group at a specific point in time. """

    group_id: str
    version: int
    created_at: date
    sources: set[KnowledgeSource]

    @property
    def snapshot_id(self) -> str:
        """Generate snapshot ID from group_id and version."""
        return f"{self.group_id}_v{self.version}"

    def add_source(self, source: KnowledgeSource):
        self.sources.add(source)
