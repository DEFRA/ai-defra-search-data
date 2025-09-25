import asyncio
from logging import getLogger

from app.common.bedrock import AbstractEmbeddingService
from app.knowledge.models import (
    KnowledgeGroup,
    KnowledgeGroupNotFoundError,
    KnowledgeSource,
    KnowledgeVector,
)
from app.knowledge.repository import AbstractKnowledgeGroupRepository, AbstractKnowledgeVectorRepository

logger = getLogger(__name__)


class KnowledgeService:
    """Service class for handling knowledge group operations."""

    def __init__(self, group_repo: AbstractKnowledgeGroupRepository, vector_repo: AbstractKnowledgeVectorRepository, embedding_service: AbstractEmbeddingService):
        self.group_repo = group_repo
        self.vector_repo = vector_repo
        self.embedding_service = embedding_service

    async def create_knowledge_group(self, group: KnowledgeGroup) -> None:
        """
        Create a new knowledge group in the database.

        Args:
            group: The knowledge group domain model to create
        """
        logger.info("Creating knowledge group: %s", group.name)

        await self.group_repo.save(group)

        logger.info("Knowledge group created successfully: %s", group.name)

    async def list_knowledge_groups(self) -> list[KnowledgeGroup]:
        """
        List all knowledge entries in the database.

        Returns:
            A list of knowledge entries
        """
        return await self.group_repo.list_all()

    async def find_knowledge_group(self, group_id: str) -> KnowledgeGroup:
        """
        Find a knowledge entry by its group ID.

        Args:
            group_id: The group ID of the knowledge entry to find

        Returns:
            The found knowledge entry

        Raises:
            KnowledgeGroupNotFoundError: If no entry is found with the given group ID
        """
        entry = await self.group_repo.get_by_id(group_id)

        if entry:
            return entry

        msg = f"Knowledge entry with group ID '{group_id}' not found"
        raise KnowledgeGroupNotFoundError(msg)

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

