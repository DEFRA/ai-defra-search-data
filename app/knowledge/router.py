from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response, status
from pymongo.asynchronous.database import AsyncDatabase

from app.common.bedrock import BedrockEmbeddingService, get_bedrock_client
from app.common.mongo import get_db
from app.common.postgres import get_async_session_factory
from app.config import config
from app.knowledge.models import (
    KnowledgeGroup,
    KnowledgeGroupNotFoundError,
    KnowledgeSource,
)
from app.knowledge.repository import (
    AbstractKnowledgeGroupRepository,
    AbstractKnowledgeVectorRepository,
    MongoKnowledgeGroupRepository,
    PostgresKnowledgeVectorRepository,
)
from app.knowledge.request_schemas import (
    CreateKnowledgeGroupRequest,
    KnowledgeGroupResponse,
)
from app.knowledge.service import KnowledgeService

router = APIRouter(tags=["knowledge"])


def get_knowledge_repository(db: AsyncDatabase = Depends(get_db)) -> MongoKnowledgeGroupRepository:
    """Dependency injection for MongoKnowledgeGroupRepository."""
    return MongoKnowledgeGroupRepository(db)


def get_knowledge_vector_repository(session_factory = Depends(get_async_session_factory)) -> AbstractKnowledgeVectorRepository:
    """Dependency injection for PostgresKnowledgeVectorRepository."""
    session = session_factory()
    return PostgresKnowledgeVectorRepository(session)


async def get_bedrock_embedding_service():
    """Dependency injection for BedrockEmbeddingService."""

    return BedrockEmbeddingService(get_bedrock_client(), config.bedrock_embedding_config)


def get_knowledge_service(group_repo: AbstractKnowledgeGroupRepository = Depends(get_knowledge_repository), vector_repo: AbstractKnowledgeVectorRepository = Depends(get_knowledge_vector_repository), embedding_service: BedrockEmbeddingService = Depends(get_bedrock_embedding_service)) -> KnowledgeService:
    """Dependency injection for KnowledgeService."""
    return KnowledgeService(group_repo, vector_repo, embedding_service)


@router.get("/knowledge/groups", status_code=status.HTTP_200_OK, response_model=list[KnowledgeGroupResponse])
async def list_groups(service: KnowledgeService = Depends(get_knowledge_service)):
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
async def create_group(group: CreateKnowledgeGroupRequest, service: KnowledgeService = Depends(get_knowledge_service)):
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
        knowledge_group.add_source(KnowledgeSource(name=source.name, data_type=source.type, location=source.location))

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
async def get_group(group_id: str, service: KnowledgeService = Depends(get_knowledge_service)):
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
async def ingest_group(group_id: str, background_tasks: BackgroundTasks, service: KnowledgeService = Depends(get_knowledge_service)):
    """
    Initiate the ingestion process for a specific knowledge group.

    Args:
        group_id: The ID of the knowledge group to ingest
        service: Service dependency injection
    Returns:
        Acknowledgment of ingestion initiation
    """

    try:
        group = await service.find_knowledge_group(group_id)

        background_tasks.add_task(service.ingest_knowledge_group, group)
        return {"message": f"Ingestion for knowledge group '{group_id}' has been initiated."}
    except KnowledgeGroupNotFoundError as err:
        raise HTTPException(status_code=404, detail=f"Knowledge group with ID '{group_id}' not found") from err
