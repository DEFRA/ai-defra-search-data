from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class KnowledgeResult:
    """Represents a knowledge search result with similarity scoring."""

    content: str
    similarity_score: float  # 0.0 to 1.0, higher is more similar
    created_at: datetime

    embedding: list[float] | None = None

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
class KnowledgeSearchResults:
    """Container for knowledge search results with metadata."""

    query_embedding: list[float]
    results: list[KnowledgeResult]

    @property
    def best_match(self) -> KnowledgeResult | None:
        """Get the highest scoring result."""
        return self.results[0] if self.results else None
