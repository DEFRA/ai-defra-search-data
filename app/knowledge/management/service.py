from logging import getLogger

from app.knowledge.management.models import KnowledgeGroup, KnowledgeGroupNotFoundError
from app.knowledge.management.repository import AbstractKnowledgeGroupRepository

logger = getLogger(__name__)

async def create_knowledge_group(
        repository: AbstractKnowledgeGroupRepository,
        group: KnowledgeGroup
    ) -> None:
    """
    Create a new knowledge entry in the database.

    Args:
        repository: The repository instance
        entry: The knowledge entry domain model to create
    """
    logger.info("Creating knowledge entry: %s", group.name)

    await repository.add_knowledge_group(group)

    if group._sources:
        await repository.add_knowledge_sources(group.group_id, group._sources)

    logger.info("Knowledge entry created successfully: %s", group.name)


async def list_knowledge_groups(
        repository: AbstractKnowledgeGroupRepository
    ) -> list[KnowledgeGroup]:
    """
    List all knowledge entries in the database.

    Args:
        repository: The repository instance

    Returns:
        A list of knowledge entries
    """
    return await repository.list_knowledge_groups()


async def find_knowledge_group(
        repository: AbstractKnowledgeGroupRepository,
        group_id: str
    ) -> KnowledgeGroup:
    """
    Find a knowledge entry by its group ID.

    Args:
        repository: The repository instance
        group_id: The group ID of the knowledge entry to find

    Returns:
        The found knowledge entry

    Raises:
        KnowledgeGroupNotFoundError: If no entry is found with the given group ID
    """
    entry = await repository.get_knowledge_group_by_id(group_id)

    if entry:
        return entry

    msg = f"Knowledge entry with group ID '{group_id}' not found"
    raise KnowledgeGroupNotFoundError(msg)

