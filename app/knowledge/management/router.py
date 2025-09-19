from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pymongo.asynchronous.database import AsyncDatabase

from app.common.mongo import get_db
from app.knowledge.management import service as knowledge_service
from app.knowledge.management.models import (
    KnowledgeGroup,
    KnowledgeGroupNotFoundError,
    KnowledgeSource,
    KnowledgeSourceAlreadyExistsInGroupError,
)
from app.knowledge.management.repository import (
    AbstractKnowledgeGroupRepository,
    MongoKnowledgeGroupRepository,
)
from app.knowledge.management.request_schemas import (
    CreateKnowledgeGroupRequest,
    KnowledgeGroupResponse,
)

router = APIRouter(tags=["knowledge"])


def get_knowledge_repository(db: AsyncDatabase = Depends(get_db)) -> MongoKnowledgeGroupRepository:
    """Dependency injection for MongoKnowledgeGroupRepository."""
    return MongoKnowledgeGroupRepository(db)


@router.get("/knowledge/management/groups", status_code=status.HTTP_200_OK, response_model=list[KnowledgeGroupResponse])
async def list_groups(repository: AbstractKnowledgeGroupRepository = Depends(get_knowledge_repository)):
    """
    List all knowledge groups.

    Args:
        repository: Repository dependency injection

    Returns:
        A list of knowledge group responses
    """
    groups = await knowledge_service.list_knowledge_groups(repository)

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


@router.post("/knowledge/management/groups", status_code=status.HTTP_201_CREATED, response_model=KnowledgeGroupResponse)
async def create_group(entry: CreateKnowledgeGroupRequest, repository: AbstractKnowledgeGroupRepository = Depends(get_knowledge_repository)):
    """
    Create a new knowledge group.

    Args:
        entry: The knowledge group request data
        repository: Repository dependency injection

    Returns:
        Success message with the created group name
    """
    knowledge_entry = KnowledgeGroup(
        name=entry.name,
        description=entry.description,
        owner=entry.owner,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        sources={KnowledgeSource(name=source.name, type=source.type, location=source.location) for source in entry.sources}
    )

    await knowledge_service.create_knowledge_group(repository, knowledge_entry)

    return KnowledgeGroupResponse(
        group_id=knowledge_entry.group_id,
        title=knowledge_entry.name,
        description=knowledge_entry.description,
        owner=knowledge_entry.owner,
        created_at=knowledge_entry.created_at.isoformat(),
        updated_at=knowledge_entry.updated_at.isoformat()
    )


@router.patch("/knowledge/management/groups/{group_id}/sources", status_code=status.HTTP_200_OK)
async def add_source_to_group(group_id: str, source: KnowledgeSource, repository: AbstractKnowledgeGroupRepository = Depends(get_knowledge_repository)):
    """
    Add a knowledge source to an existing knowledge group.

    Args:
        group_id: The ID of the knowledge group to add the source to
        source: The knowledge source data
        repository: Repository dependency injection

    Returns:
        Success message with the added source name
    """
    try:
        await repository.add_knowledge_source(group_id, source)
    except KnowledgeGroupNotFoundError:
        raise HTTPException(status_code=404, detail=f"Knowledge group with ID '{group_id}' not found") from None
    except KnowledgeSourceAlreadyExistsInGroupError:
        raise HTTPException(status_code=409, detail=f"Knowledge source with name '{source.name}' already exists in group '{group_id}'") from None

    return {"message": f"Knowledge source '{source.name}' added to group '{group_id}' successfully"}


@router.get("/knowledge/management/groups/{group_id}", response_model=KnowledgeGroupResponse)
async def get_group(group_id: str, repository: AbstractKnowledgeGroupRepository = Depends(get_knowledge_repository)):
    """
    Retrieve a knowledge group by its group ID.

    Args:
        group_id: The ID of the knowledge group to retrieve
        repository: Repository dependency injection

    Returns:
        The knowledge group response data or None if not found
    """
    try:
        group = await knowledge_service.find_knowledge_group(repository, group_id)

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

