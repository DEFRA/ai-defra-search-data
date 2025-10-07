from logging import getLogger

from app.knowledge_management.models import (
    KnowledgeGroup,
    KnowledgeGroupNotFoundError,
)
from app.knowledge_management.repository import AbstractKnowledgeGroupRepository

logger = getLogger(__name__)


class KnowledgeManagementService:
    """Service class for handling knowledge group operations."""

    def __init__(self, group_repo: AbstractKnowledgeGroupRepository):
        self.group_repo = group_repo

    async def create_knowledge_group(self, group: KnowledgeGroup) -> None:
        """
        Create a new knowledge group in the database.

        Args:
            group: The knowledge group domain model to create
        """
        logger.info("Creating knowledge group: %s", group.name)

        await self.group_repo.save(group)

        logger.info("Knowledge group created successfully: %s", group.name)

    async def list_knowledge_groups(self) -> list[KnowledgeGroup]:
        """
        List all knowledge entries in the database.

        Returns:
            A list of knowledge entries
        """
        return await self.group_repo.list_all()

    async def find_knowledge_group(self, group_id: str) -> KnowledgeGroup:
        """
        Find a knowledge entry by its group ID.

        Args:
            group_id: The group ID of the knowledge entry to find

        Returns:
            The found knowledge entry

        Raises:
            KnowledgeGroupNotFoundError: If no entry is found with the given group ID
        """
        entry = await self.group_repo.get_by_id(group_id)

        if entry:
            return entry

        msg = f"Knowledge entry with group ID '{group_id}' not found"
        raise KnowledgeGroupNotFoundError(msg)

    async def set_active_snapshot(self, group_id: str, snapshot_id: str) -> None:
        """
        Set the active snapshot for a knowledge group.

        Args:
            group_id: The group ID of the knowledge entry to update
            snapshot_id: The snapshot ID to set as active
        """
        group = await self.find_knowledge_group(group_id)

        group.active_snapshot = snapshot_id

        await self.group_repo.save(group)

        logger.info("Set active snapshot for group %s to %s", group_id, group.active_snapshot)
