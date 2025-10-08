from logging import getLogger

from fastapi import APIRouter, Depends, HTTPException, status

from app.knowledge_management.dependencies import get_knowledge_management_service
from app.knowledge_management.models import KnowledgeGroupNotFoundError
from app.knowledge_management.service import KnowledgeManagementService
from app.snapshot.api_schemas import KnowledgeVectorResultResponse, QuerySnapshotRequest
from app.snapshot.dependencies import get_snapshot_service
from app.snapshot.models import KnowledgeSnapshotNotFoundError, NoActiveSnapshotError
from app.snapshot.service import SnapshotService

logger = getLogger(__name__)
router = APIRouter(tags=["snapshots"])


@router.get("/snapshots/{snapshot_id}", response_model=dict)
async def get_snapshot(
    snapshot_id: str,
    service: SnapshotService = Depends(get_snapshot_service)
):
    """
    Retrieve a snapshot by its ID.

    Args:
        snapshot_id: The ID of the snapshot to retrieve
        service: Service dependency injection

    Returns:
        The snapshot data

    Raises:
        HTTPException: If snapshot is not found
    """
    try:
        snapshot = await service.get_by_id(snapshot_id)
    except KnowledgeSnapshotNotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Snapshot with ID '{snapshot_id}' not found"
        ) from err

    return {
        "snapshot_id": snapshot.snapshot_id,
        "group_id": snapshot.group_id,
        "version": snapshot.version,
        "created_at": snapshot.created_at.isoformat(),
        "sources": [source.__dict__ for source in snapshot.sources]
    }


@router.post("/snapshots/query", response_model=list[KnowledgeVectorResultResponse])
async def query_snapshot(
    request: QuerySnapshotRequest,
    knowledge_service: KnowledgeManagementService = Depends(get_knowledge_management_service),
    snp_service: SnapshotService = Depends(get_snapshot_service)
):
    """
    Query a snapshot for relevant documents based on a search query.

    Args:
        request: The query request containing group_id, query, and max_results
        knowledge_service: Knowledge management service dependency injection
        snp_service: Snapshot service dependency injection
    Returns:
        A list of relevant documents
    """

    try:
        group = await knowledge_service.find_knowledge_group(request.group_id)

        if not group.active_snapshot:
            msg = f"Knowledge group with ID '{request.group_id}' has no active snapshot"
            raise NoActiveSnapshotError(msg)

        documents = await snp_service.search_similar(group, request.query, request.max_results)
    except KnowledgeGroupNotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge group with ID '{request.group_id}' not found"
        ) from err
    except NoActiveSnapshotError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Knowledge group with ID '{request.group_id}' has no active snapshot"
        ) from err

    # Convert domain models to response models
    return [
        KnowledgeVectorResultResponse(
            content=doc.content,
            similarity_score=doc.similarity_score,
            similarity_category=doc.similarity_category,
            created_at=doc.created_at.isoformat(),
            metadata=doc.metadata
        )
        for doc in documents
    ]


@router.patch("/snapshots/{snapshot_id}/activate", status_code=status.HTTP_200_OK)
async def activate_snapshot(
    snapshot_id: str,
    snapshot_service: SnapshotService = Depends(get_snapshot_service),
    knowledge_service: KnowledgeManagementService = Depends(get_knowledge_management_service)
):
    """
    Activate a snapshot by setting it as the active snapshot for its knowledge group.

    Args:
        snapshot_id: The ID of the snapshot to activate
        snapshot_service: Snapshot service dependency injection
        knowledge_service: Knowledge management service dependency injection

    Returns:
        Success message

    Raises:
        HTTPException: If snapshot is not found
    """
    try:
        snapshot = await snapshot_service.get_by_id(snapshot_id)

        await knowledge_service.set_active_snapshot(
            group_id=snapshot.group_id,
            snapshot_id=snapshot_id
        )

        logger.info("Successfully activated snapshot %s for group %s", snapshot_id, snapshot.group_id)

        return {"message": f"Snapshot '{snapshot_id}' activated successfully for group '{snapshot.group_id}'"}
    except KnowledgeSnapshotNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Snapshot with ID '{snapshot_id}' not found"
        ) from e
    except KnowledgeGroupNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Knowledge group with ID '{snapshot.group_id}' does not exist"
        ) from e

