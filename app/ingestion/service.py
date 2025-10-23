import json
import logging

import fastapi

from app.common import bedrock
from app.ingestion import models, repository
from app.knowledge_management import models as km_models
from app.snapshot import service as snapshot_service

logger = logging.getLogger(__name__)


class IngestionService:
    """Service class for processing knowledge sources."""

    def __init__(self,
                 ingestion_repository: repository.AbstractIngestionDataRepository,
                 embedding_service: bedrock.AbstractEmbeddingService,
                 snapshot_service: snapshot_service.SnapshotService,
                 background_tasks: fastapi.BackgroundTasks
        ):

        self.ingestion_repository = ingestion_repository
        self.embedding_service = embedding_service
        self.snapshot_service = snapshot_service
        self.background_tasks = background_tasks

    async def process_group(self, group: km_models.KnowledgeGroup) -> None:
        """
        Initiate background processing for all sources in a knowledge group.

        Args:
            group: The knowledge group containing sources to process
        """
        snapshot = await self.snapshot_service.create_snapshot(group.group_id, group.sources.values())

        for source in group.sources.values():
            self.background_tasks.add_task(self._process_source, source, snapshot.snapshot_id)

    async def _process_source(self, source: km_models.KnowledgeSource, snapshot_id: str) -> None:
        """
        Process a single source: process data, generate embeddings, and store vector for search.

        Args:
            source: The knowledge source to process
            snapshot_id: The associated snapshot ID
        """
        logger.info("Processing source: %s for group: %s", source.name, snapshot_id)

        vectors: models.IngestionVector = None

        match source.source_type:
            case "PRECHUNKED_BLOB":
                vectors = await self._process_prechunked_source(source, snapshot_id)
            case _:
                msg = f"Source type {source.source_type} ingestion not implemented"
                raise NotImplementedError(msg)

        if vectors:
            knowledge_vectors = [vector.to_knowledge_vector() for vector in vectors]
            await self.snapshot_service.store_vectors(knowledge_vectors)
        else:
            logger.warning("No vectors generated for source: %s", source.source_id)

        logger.info("Processing completed for source: %s", source.source_id)

    async def _process_prechunked_source(self, source: km_models.KnowledgeSource, snapshot_id: str) -> list[models.IngestionVector]:
        """
        Process a source that has pre-chunked data available.
        This method retrieves the chunked data, generates embeddings, and stores the vectors.
        """
        logger.info("Processing pre-chunked source: %s", source.source_id)

        chunk_files = self.ingestion_repository.list(source.source_id)

        if len(chunk_files) == 0:
            msg = f"No pre-chunked data found for source {source.source_id}"
            raise models.NoSourceDataError(msg)

        vectors = []

        for chunk_file in chunk_files:
            file = self.ingestion_repository.get(chunk_file)

            if file is None:
                msg = f"Failed to retrieve file {chunk_file} from repository for source {source.source_id}"
                raise models.NoSourceDataError(msg)

            file_vectors = await self._process_chunked_data(file, snapshot_id, source.source_id)

            vectors.extend(file_vectors)

        return vectors

    async def _process_chunked_data(self, file: bytes, snapshot_id: str, source_id: str) -> list[models.IngestionVector]:
        """
        Process pre-chunked data from a file: read content, generate embeddings, and prepare vectors.
        Returns processed vectors ready for search storage.
        """
        logger.info("Processing pre-chunked data from file")

        chunks = [
            models.ChunkData(**json.loads(line))
            for line in file.splitlines()
        ]

        logger.info("Generating embeddings for %d chunks", len(chunks))

        vectors = []

        for chunk_no in range(len(chunks)):
            chunk = chunks[chunk_no]
            embedding = self.embedding_service.generate_embeddings(chunk.text)
            vector = models.IngestionVector(
                content=chunk.text,
                embedding=embedding,
                snapshot_id=snapshot_id,
                source_id=source_id,
                metadata=None
            )

            vectors.append(vector)

            if (chunk_no + 1) % 50 == 0:
                logger.info("Generated embeddings for %d chunks", chunk_no + 1)

        return vectors
