import json
from logging import getLogger

from fastapi import BackgroundTasks

from app.common.bedrock import AbstractEmbeddingService
from app.ingestion.models import IngestionVector, NoSourceDataError
from app.ingestion.repository import AbstractIngestionDataRepository
from app.knowledge_management.models import KnowledgeGroup, KnowledgeSource
from app.snapshot.service import SnapshotService

logger = getLogger(__name__)


class IngestionService:
    """Service class for processing individual knowledge sources."""

    def __init__(self,
                 ingestion_repository: AbstractIngestionDataRepository,
                 embedding_service: AbstractEmbeddingService,
                 snapshot_service: SnapshotService,
                 background_tasks: BackgroundTasks
        ):

        self.ingestion_repository = ingestion_repository
        self.embedding_service = embedding_service
        self.snapshot_service = snapshot_service
        self.background_tasks = background_tasks

    async def process_group(self, group: KnowledgeGroup) -> None:
        """
        Initiate background processing for all sources in a knowledge group.

        Args:
            group: The knowledge group containing sources to process
        """
        snapshot = await self.snapshot_service.create_snapshot(group.group_id, group.sources)

        for source in group.sources:
            self.background_tasks.add_task(self._process_source, source, snapshot.snapshot_id)

    async def _process_source(self, source: KnowledgeSource, snapshot_id: str) -> None:
        """
        Process a single source: extract content, generate embeddings, store to S3 for audit,
        and store vector for search. This is the main entry point for individual source processing.
        """
        logger.info("Processing source: %s for group: %s", source.name, snapshot_id)

        vectors = []

        chunk_files = self.ingestion_repository.list(source.source_id)

        if len(chunk_files) == 0:
            msg = f"No pre-chunked data found for source {source.source_id}"
            raise NoSourceDataError(msg)

        for chunk_file in chunk_files:
            file = self.ingestion_repository.get(chunk_file)

            if file is None:
                msg = f"Failed to retrieve file {chunk_file} from repository for source {source.source_id}"
                raise NoSourceDataError(msg)

            file_vectors = await self._process_chunked_data(file, snapshot_id, source.source_id)

            vectors.extend(file_vectors)

        print(f"Storing {len(vectors)} embedded chunks for source {source.source_id}")

        if vectors:
            # Convert IngestionVector to KnowledgeVector for the snapshot domain
            knowledge_vectors = [vector.to_knowledge_vector() for vector in vectors]
            await self.snapshot_service.store_vectors(knowledge_vectors)

        logger.info("Processing completed for source: %s", source.source_id)

    async def _process_chunked_data(self, file: bytes, snapshot_id: str, source_id: str) -> list[IngestionVector]:
        """
        Process pre-chunked data from a file: read content, generate embeddings, and prepare vectors.
        Returns processed vectors ready for search storage.
        """
        logger.info("Processing pre-chunked data from file")

        chunks = [json.loads(line) for line in file.splitlines()]

        logger.info("Generating embeddings for %d chunks", len(chunks))

        vectors = []

        for chunk_no in range(len(chunks)):
            chunk = chunks[chunk_no]
            embedding = self.embedding_service.generate_embeddings(chunk["text"])
            vector = IngestionVector(
                content=chunk["text"],
                embedding=embedding,
                snapshot_id=snapshot_id,
                source_id=source_id,
                metadata=None
            )
            vectors.append(vector)

            if (chunk_no + 1) % 50 == 0:
                logger.info("Generated embeddings for %d chunks", chunk_no + 1)

        return vectors
