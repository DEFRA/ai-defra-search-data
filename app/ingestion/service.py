from logging import getLogger

from app.common.bedrock import AbstractEmbeddingService
from app.ingestion.models import KnowledgeVector
from app.knowledge_management.models import KnowledgeSource
from app.snapshot.service import SnapshotService

logger = getLogger(__name__)


class IngestionService:
    """Service class for processing individual knowledge sources."""

    def __init__(self, embedding_service: AbstractEmbeddingService, snapshot_service: SnapshotService):
        self.embedding_service = embedding_service
        self.snapshot_service = snapshot_service

    async def process_source(self, source: KnowledgeSource, snapshot_id: str) -> None:
        """
        Process a single source: extract content, generate embeddings, store to S3 for audit,
        and store vector for search. This is the main entry point for individual source processing.
        """
        logger.info("Processing source: %s for group: %s", source.name, snapshot_id)

        # Step 1: Process the source and create vector
        vectors = await self._process_source_data(source, snapshot_id)

        # Step 2: Store vectors for search operations
        if vectors:
            await self.snapshot_service.store_vectors(vectors)

        logger.info("Processing completed for source: %s", source.name)

    async def _process_source_data(self, source: KnowledgeSource) -> list[KnowledgeVector]:
        """
        Process a single source: extract content, generate embeddings, store to S3 for audit.
        Returns processed vectors ready for search storage.
        """
        logger.info("Processing source data: %s", source.name)

        # TODO: Extract actual content from source based on source.data_type and source.location
        content = "Sample content extracted from source"

        # Generate embedding
        embedding = self.embedding_service.generate_embeddings(content)

        # TODO: Store to S3 for audit purposes
        # audit_path = await self.s3_repo.store_audit_record(source, content, embedding, group_id)

        vector = KnowledgeVector(content=content, embedding=embedding)

        logger.info("Processing completed for source data: %s", source.name)
        return [vector]
