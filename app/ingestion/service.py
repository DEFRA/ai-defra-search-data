import asyncio
from logging import getLogger

from app.common.bedrock import AbstractEmbeddingService
from app.ingestion.models import KnowledgeVector
from app.ingestion.repository import AbstractKnowledgeVectorRepository
from app.knowledge_management.models import KnowledgeGroup, KnowledgeSource

logger = getLogger(__name__)


class IngestionService:
    """Service class for handling knowledge ingestion operations."""

    def __init__(self, vector_repo: AbstractKnowledgeVectorRepository, embedding_service: AbstractEmbeddingService):
        self.vector_repo = vector_repo
        self.embedding_service = embedding_service

    async def ingest_knowledge_group(self, group: KnowledgeGroup) -> None:
        if not group.sources:
            logger.warning("No sources found for knowledge group: %s", group.group_id)
            return

        logger.info("Starting ingestion of %d sources for knowledge group: %s", len(group.sources), group.group_id)

        ingestion_tasks = []

        for source in group.sources:
            task = asyncio.create_task(self._ingest_source(source))
            ingestion_tasks.append(task)

        await asyncio.gather(*ingestion_tasks)

        logger.info("Ingestion completed for knowledge group: %s", group.group_id)

    async def _ingest_source(self, source: KnowledgeSource) -> None:
        logger.info("Ingesting source: %s", source.name)

        embedding = self.embedding_service.generate_embeddings("Sample text for embedding generation.")

        await self.vector_repo.add(KnowledgeVector(content="Sample content", embedding=embedding))

        logger.info("Ingestion completed for source: %s", source.name)
