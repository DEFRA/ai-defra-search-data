"""Dependency injection factories for knowledge management module."""

from fastapi import BackgroundTasks, Depends
from pymongo.asynchronous.database import AsyncDatabase

from app.common.bedrock import (
    AbstractEmbeddingService,
    BedrockEmbeddingService,
    get_bedrock_client,
)
from app.common.mongo import get_db
from app.common.postgres import get_async_session_factory
from app.common.s3 import get_s3_client
from app.config import config
from app.ingestion.repository import (
    AbstractIngestionDataRepository,
    S3IngestionDataRepository,
)
from app.ingestion.service import IngestionService
from app.knowledge_management.repository import (
    AbstractKnowledgeGroupRepository,
    MongoKnowledgeGroupRepository,
)
from app.knowledge_management.service import KnowledgeManagementService
from app.snapshot.repository import (
    AbstractKnowledgeSnapshotRepository,
    AbstractKnowledgeVectorRepository,
    MongoKnowledgeSnapshotRepository,
    PostgresKnowledgeVectorRepository,
)
from app.snapshot.service import SnapshotService


def get_snapshot_repository(db: AsyncDatabase = Depends(get_db)) -> AbstractKnowledgeSnapshotRepository:
    """Dependency injection for MongoKnowledgeSnapshotRepository."""
    return MongoKnowledgeSnapshotRepository(db)


def get_knowledge_repository(db: AsyncDatabase = Depends(get_db)) -> AbstractKnowledgeGroupRepository:
    """Dependency injection for MongoKnowledgeGroupRepository."""
    return MongoKnowledgeGroupRepository(db)


def get_knowledge_vector_repository(session_factory = Depends(get_async_session_factory)) -> AbstractKnowledgeVectorRepository:
    """Dependency injection for PostgresKnowledgeVectorRepository."""
    session = session_factory()
    return PostgresKnowledgeVectorRepository(session)

def get_ingestion_data_repository() -> AbstractIngestionDataRepository:
    return S3IngestionDataRepository(
        s3_client=get_s3_client(),
        bucket_name=config.ingestion_data_bucket
    )

def get_bedrock_embedding_service() -> AbstractEmbeddingService:
    """Dependency injection for BedrockEmbeddingService."""
    return BedrockEmbeddingService(get_bedrock_client(), config.bedrock_embedding_config)


def get_snapshot_service(
        snapshot_repo: AbstractKnowledgeSnapshotRepository = Depends(get_snapshot_repository),
        vector_repo: AbstractKnowledgeVectorRepository = Depends(get_knowledge_vector_repository),
        embedding_service: AbstractEmbeddingService = Depends(get_bedrock_embedding_service)
    ) -> SnapshotService:
    """Dependency injection for SnapshotService."""
    return SnapshotService(snapshot_repo, vector_repo, embedding_service)


def get_knowledge_management_service(group_repo: AbstractKnowledgeGroupRepository = Depends(get_knowledge_repository)) -> KnowledgeManagementService:
    """Dependency injection for KnowledgeManagementService."""
    return KnowledgeManagementService(group_repo)


def get_ingestion_service(
    ingestion_repository: AbstractIngestionDataRepository = Depends(get_ingestion_data_repository),
    embedding_service: BedrockEmbeddingService = Depends(get_bedrock_embedding_service),
    snapshot_service: SnapshotService = Depends(get_snapshot_service),
    background_tasks: BackgroundTasks = None
) -> IngestionService:
    """Dependency injection for IngestionService."""
    return IngestionService(ingestion_repository, embedding_service, snapshot_service, background_tasks)
