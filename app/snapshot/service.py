import datetime
from logging import getLogger

from app.common.bedrock import AbstractEmbeddingService
from app.ingestion.models import KnowledgeVector
from app.snapshot.models import KnowledgeSnapshot
from app.snapshot.repository import (
    AbstractKnowledgeVectorRepository,
    MongoKnowledgeSnapshotRepository,
)

logger = getLogger(__name__)


class SnapshotService:
    """Service for managing knowledge vector snapshots and search operations."""

    def __init__(
            self,
            snapshot_repo: MongoKnowledgeSnapshotRepository,
            vector_repo: AbstractKnowledgeVectorRepository,
            embedding_service: AbstractEmbeddingService
        ):
        self.snapshot_repo = snapshot_repo
        self.vector_repo = vector_repo
        self.embedding_service = embedding_service

    async def create_snapshot(self, group_id: str, version: str, sources: list[dict]):
        """Create a new knowledge snapshot."""
        snapshot = KnowledgeSnapshot(
            group_id=group_id,
            version=version,
            created_at=datetime.utcnow(),
            sources=sources
        )
        await self.snapshot_repo.save(snapshot)

    async def get_by_id(self, snapshot_id: str):
        """Get a knowledge snapshot by its ID"""
        return await self.snapshot_repo.get_by_id(snapshot_id)

    async def store_vectors(self, vectors: list[KnowledgeVector]) -> None:
        """Store processed vectors for search operations."""
        if not vectors:
            logger.warning("No vectors provided for storage")
            return

        logger.info("Storing %d vectors for search operations", len(vectors))
        await self.vector_repo.add_batch(vectors)
        logger.info("Successfully stored vectors for search")

    async def search_similar(self, query: str, top_k: int):
        """Search for similar vectors."""
        logger.info("Searching for top %d similar vectors", top_k)
        embedding = self.embedding_service.generate_embeddings(query)
        return await self.vector_repo.query(embedding, top_k)
