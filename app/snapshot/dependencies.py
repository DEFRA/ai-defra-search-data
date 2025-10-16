"""Dependency injection factories for snapshot module."""

from fastapi import Depends
from pymongo.asynchronous.database import AsyncDatabase

from app.common.bedrock import (
    AbstractEmbeddingService,
    BedrockEmbeddingService,
    get_bedrock_client,
)
from app.common.mongo import get_db
from app.common.postgres import get_async_session_factory
from app.config import config
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


def get_knowledge_vector_repository(session_factory = Depends(get_async_session_factory)) -> AbstractKnowledgeVectorRepository:
    """Dependency injection for PostgresKnowledgeVectorRepository."""
    return PostgresKnowledgeVectorRepository(session_factory)


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
