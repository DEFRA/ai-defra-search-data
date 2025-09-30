from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response, status
from pymongo.asynchronous.database import AsyncDatabase

from app.common.bedrock import AbstractEmbeddingService, BedrockEmbeddingService, get_bedrock_client
from app.common.mongo import get_db
from app.common.postgres import get_async_session_factory
from app.config import config
from app.ingestion.service import IngestionService
from app.knowledge_management.models import (
    KnowledgeGroup,
    KnowledgeGroupNotFoundError,
    KnowledgeSource,
)
from app.knowledge_management.repository import (
    AbstractKnowledgeGroupRepository,
    MongoKnowledgeGroupRepository,
)
from app.knowledge_management.request_schemas import (
    CreateKnowledgeGroupRequest,
    KnowledgeGroupResponse,
)
from app.knowledge_management.service import KnowledgeManagementService
from app.snapshot.repository import (
    AbstractKnowledgeSnapshotRepository,
    AbstractKnowledgeVectorRepository,
    MongoKnowledgeSnapshotRepository,
    PostgresKnowledgeVectorRepository,
)
from app.snapshot.service import SnapshotService

router = APIRouter(tags=["knowledge-management"])


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
    embedding_service: BedrockEmbeddingService = Depends(get_bedrock_embedding_service),
    snapshot_service: SnapshotService = Depends(get_snapshot_service),
    background_tasks: BackgroundTasks = None
) -> IngestionService:
    """Dependency injection for IngestionService."""
    return IngestionService(embedding_service, snapshot_service, background_tasks)


@router.get("/knowledge/groups", status_code=status.HTTP_200_OK, response_model=list[KnowledgeGroupResponse])
async def list_groups(service: KnowledgeManagementService = Depends(get_knowledge_management_service)):
    """
    List all knowledge groups.

    Args:
        service: Service dependency injection

    Returns:
        A list of knowledge group responses
    """
    groups = await service.list_knowledge_groups()

    if len(groups) == 0:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return [
        KnowledgeGroupResponse(
            group_id=group.group_id,
            title=group.name,
            description=group.description,
            owner=group.owner,
            created_at=group.created_at.isoformat(),
            updated_at=group.updated_at.isoformat()
        ) for group in groups
    ]


@router.post("/knowledge/groups", status_code=status.HTTP_201_CREATED, response_model=KnowledgeGroupResponse)
async def create_group(group: CreateKnowledgeGroupRequest, service: KnowledgeManagementService = Depends(get_knowledge_management_service)):
    """
    Create a new knowledge group.

    Args:
        group: The knowledge group request data
        service: Service dependency injection

    Returns:
        Success message with the created group name
    """
    knowledge_group = KnowledgeGroup(
        name=group.name,
        description=group.description,
        owner=group.owner,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    for source in group.sources:
        knowledge_group.add_source(KnowledgeSource(name=source.name, source_type=source.type, location=source.location))

    await service.create_knowledge_group(knowledge_group)

    return KnowledgeGroupResponse(
        group_id=knowledge_group.group_id,
        title=knowledge_group.name,
        description=knowledge_group.description,
        owner=knowledge_group.owner,
        created_at=knowledge_group.created_at.isoformat(),
        updated_at=knowledge_group.updated_at.isoformat()
    )


@router.get("/knowledge/groups/{group_id}", response_model=KnowledgeGroupResponse)
async def get_group(group_id: str, service: KnowledgeManagementService = Depends(get_knowledge_management_service)):
    """
    Retrieve a knowledge group by its group ID.

    Args:
        group_id: The ID of the knowledge group to retrieve
        service: Service dependency injection

    Returns:
        The knowledge group response data or None if not found
    """
    try:
        group = await service.find_knowledge_group(group_id)

        return KnowledgeGroupResponse(
            group_id=group.group_id,
            title=group.name,
            description=group.description,
            owner=group.owner,
            created_at=group.created_at.isoformat(),
            updated_at=group.updated_at.isoformat(),
            sources=group.sources
        )
    except KnowledgeGroupNotFoundError as err:
        raise HTTPException(status_code=404, detail=f"Knowledge group with ID '{group_id}' not found") from err


@router.post("/knowledge/groups/{group_id}/ingest", status_code=status.HTTP_202_ACCEPTED)
async def ingest_group(
        group_id: str,
        km_service: KnowledgeManagementService = Depends(get_knowledge_management_service),
        ingestion_service: IngestionService = Depends(get_ingestion_service)
    ):
    """
    Initiate the ingestion process for a specific knowledge group.
    Each source will be processed individually.

    Args:
        group_id: The ID of the knowledge group to ingest
        km_service: Knowledge management service dependency injection
        ingestion_service: Ingestion service dependency injection
    Returns:
        Acknowledgment of ingestion initiation
    """

    try:
        group = await km_service.find_knowledge_group(group_id)

        if not group.sources:
            return {"message": f"No sources found for knowledge group '{group_id}'."}

        await ingestion_service.process_group(group)

        return {"message": f"Ingestion for knowledge group '{group_id}' has been initiated. Processing {len(group.sources)} sources individually."}
    except KnowledgeGroupNotFoundError as err:
        raise HTTPException(status_code=404, detail=f"Knowledge group with ID '{group_id}' not found") from err

