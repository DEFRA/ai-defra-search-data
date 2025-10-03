from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.ingestion.service import IngestionService
from app.knowledge_management.dependencies import (
    get_ingestion_service,
    get_knowledge_management_service,
)
from app.snapshot.dependencies import get_snapshot_service
from app.snapshot.service import SnapshotService
from app.knowledge_management.models import (
    KnowledgeGroup,
    KnowledgeGroupNotFoundError,
    KnowledgeSource,
)
from app.knowledge_management.api_schemas import (
    CreateKnowledgeGroupRequest,
    KnowledgeGroupResponse,
)
from app.knowledge_management.service import KnowledgeManagementService

router = APIRouter(tags=["knowledge-management"])


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


@router.get("/knowledge/groups/{group_id}/snapshots", response_model=list[dict])
async def list_group_snapshots(
    group_id: str,
    service: SnapshotService = Depends(get_snapshot_service)
):
    """
    List all snapshots for a specific knowledge group.

    Args:
        group_id: The ID of the knowledge group
        service: Service dependency injection

    Returns:
        A list of snapshots for the group
    """
    snapshots = await service._snapshot_repo.list_snapshots_by_group(group_id)

    return [
        {
            "snapshot_id": snapshot.snapshot_id,
            "group_id": snapshot.group_id,
            "version": snapshot.version,
            "created_at": snapshot.created_at.isoformat(),
            "sources": [source.__dict__ for source in snapshot.sources]
        }
        for snapshot in snapshots
    ]


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

