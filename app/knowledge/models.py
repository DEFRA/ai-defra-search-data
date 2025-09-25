from dataclasses import dataclass
from datetime import date, datetime

from app.common.id_utils import generate_random_id


class KnowledgeSource:
    """ Represents the source of a knowledge entry. """

    def __init__(self,
                 name: str,
                 data_type: str,
                 location: str,
                 source_id: str = None):
        self.source_id = source_id or generate_random_id("ks")
        self.name = name
        self.type = data_type
        self.location = location

    def __eq__(self, other):
        if not isinstance(other, KnowledgeSource):
            return False

        return self.source_id == other.source_id

    def __hash__(self):
        return hash(self.source_id)


class KnowledgeGroup:
    """ Represents a knowledge entry with its details and sources. """

    def __init__(self,
                 group_id: str = None,
                 name: str = None,
                 description: str = None,
                 owner: str = None,
                 created_at: date = None,
                 updated_at: date = None):

        if not name.strip():
            msg = "KnowledgeGroup name cannot be empty or whitespace."
            raise ValueError(msg)

        if not description.strip():
            msg = "KnowledgeGroup description cannot be empty or whitespace."
            raise ValueError(msg)

        if not owner.strip():
            msg = "KnowledgeGroup owner cannot be empty or whitespace."
            raise ValueError(msg)

        self.group_id = group_id or generate_random_id("kg")
        self.name = name
        self.description = description
        self.owner = owner
        self.created_at = created_at
        self.updated_at = updated_at

        self._sources = set()

    def __eq__(self, other):
        if not isinstance(other, KnowledgeGroup):
            return False

        return self.group_id == other.group_id

    def __hash__(self):
        return hash(self.group_id)

    def add_source(self, source: KnowledgeSource):
        self._sources.add(source)

    @property
    def sources(self) -> set[KnowledgeSource]:
        return self._sources


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


class KnowledgeVector:
    """Domain model for knowledge vectors."""

    def __init__(self, content: str, embedding: list[float] = None):
        self.content = content
        self.embedding = embedding


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


class KnowledgeGroupAlreadyExistsError(Exception):
    """ Exception raised when a knowledge group (duplicate name) already exists. """


class KnowledgeGroupNotFoundError(Exception):
    """ Exception raised when a knowledge group is not found. """


class KnowledgeSourceAlreadyExistsInGroupError(Exception):
    """ Exception raised when a knowledge source already exists in a knowledge group. """
