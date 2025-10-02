from dataclasses import dataclass


@dataclass
class KnowledgeVector:
    """Domain model for knowledge vectors."""

    content: str
    embedding: list[float]
    snapshot_id: str
    source_id: str
    metadata: dict | None = None


@dataclass(frozen=True)
class ChunkData:
    source: str
    chunk_id: int
    text: str


class NoSourceDataError(Exception):
    """Raised when no source data is found for a given source."""
