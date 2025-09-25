from abc import ABC, abstractmethod

from sqlalchemy import select

from app.ingestion.models import KnowledgeVector
from app.search.models import KnowledgeResult, KnowledgeSearchResults


class AbstractKnowledgeVectorRepository(ABC):
    @abstractmethod
    async def add(self, knowledge_vector: KnowledgeVector) -> None:
        """Add a knowledge vector entry"""

    @abstractmethod
    async def query(self, embedding: list[float], top_k: int) -> KnowledgeSearchResults:
        """Query for the top_k most similar knowledge vectors"""


class PostgresKnowledgeVectorRepository(AbstractKnowledgeVectorRepository):
    """PostgreSQL implementation of KnowledgeVectorRepository using pgvector."""

    def __init__(self, session):
        """
        Initialize with SQLAlchemy async session.

        Args:
            session: Async SQLAlchemy session
        """
        self.session = session

    async def add(self, knowledge_vector: KnowledgeVector) -> None:
        """Add a knowledge vector entry to PostgreSQL."""
        self.session.add(knowledge_vector)
        await self.session.commit()

    async def add_batch(self, vectors: list[KnowledgeVector]) -> None:
        """Add multiple knowledge vector entries to PostgreSQL in batch."""
        self.session.add_all(vectors)

        await self.session.commit()

    async def query(self, embedding: list[float], top_k: int) -> KnowledgeSearchResults:
        """Query for the top_k most similar knowledge vectors using cosine similarity."""
        # Use cosine distance for similarity search (lower distance = higher similarity)
        stmt = (
            select(
                KnowledgeVector.id,
                KnowledgeVector.content,
                KnowledgeVector.embedding,
                KnowledgeVector.created_at,
                KnowledgeVector.embedding.cosine_distance(embedding).label("distance")
            )
            .order_by(KnowledgeVector.embedding.cosine_distance(embedding))
            .limit(top_k)
        )

        result = await self.session.execute(stmt)
        rows = result.fetchall()

        # Convert to domain objects
        vector_results = [
            KnowledgeResult(
                content=row.content,
                similarity_score=1.0 - float(row.distance),  # Convert distance to similarity
                created_at=row.created_at,
                embedding=row.embedding  # Include embedding in results
            )
            for row in rows
        ]

        return KnowledgeSearchResults(
            query_embedding=embedding,
            results=vector_results
        )
