from dataclasses import dataclass
from datetime import date, datetime

from app.knowledge_management.models import KnowledgeSource


@dataclass(frozen=True)
class KnowledgeVectorResult:
    """Represents a knowledge search result with similarity scoring."""

    content: str
    similarity_score: float  # 0.0 to 1.0, higher is more similar
    created_at: datetime

    embedding: list[float] | None = None
    snapshot_id: str | None = None
    source_id: str | None = None
    metadata: dict | None = None

    @property
    def similarity_category(self) -> str:
        """Categorize similarity level."""
        if self.similarity_score >= 0.9:
            return "very_high"
        if self.similarity_score >= 0.8:
            return "high"
        if self.similarity_score >= 0.6:
            return "medium"
        return "low"


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
