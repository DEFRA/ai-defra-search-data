from app.knowledge_management.models import KnowledgeGroupNotFoundError
from app.snapshot.models import KnowledgeSnapshotNotFoundError
from fastapi import APIRouter, Depends, HTTPException, status
from logging import getLogger

from app.snapshot.dependencies import get_snapshot_service
from app.snapshot.service import SnapshotService
from app.knowledge_management.dependencies import get_knowledge_management_service
from app.knowledge_management.service import KnowledgeManagementService

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

