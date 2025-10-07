
from app.common.bedrock import BedrockEmbeddingService, get_bedrock_client
from app.common.mongo import get_db, get_mongo_client
from app.common.postgres import get_async_session_factory
from app.config import config
from app.infra.mcp_server import data_mcp_server
from app.knowledge_management.models import KnowledgeGroupNotFoundError
from app.knowledge_management.repository import MongoKnowledgeGroupRepository
from app.knowledge_management.service import KnowledgeManagementService
from app.snapshot.models import KnowledgeVectorResult, NoActiveSnapshotError
from app.snapshot.repository import (
    MongoKnowledgeSnapshotRepository,
    PostgresKnowledgeVectorRepository,
)
from app.snapshot.service import SnapshotService


@data_mcp_server.tool()
async def relevant_sources_by_group(group_id: str, query: str, max_results: int = 5) -> list[KnowledgeVectorResult]:
    """
    A tool to retrieve relevant documents based on a query.
    """

    db = await get_db(await get_mongo_client())
    session_factory = await get_async_session_factory()
    session = session_factory()

    snapshot_repo = MongoKnowledgeSnapshotRepository(db)
    vector_repo = PostgresKnowledgeVectorRepository(session)
    group_repo = MongoKnowledgeGroupRepository(db)

    embedding_service = BedrockEmbeddingService(get_bedrock_client(), config.bedrock_embedding_config)
    snapshot_service = SnapshotService(snapshot_repo, vector_repo, embedding_service)
    knowledge_service = KnowledgeManagementService(group_repo)

    group = await knowledge_service.find_knowledge_group(group_id)

    documents = await snapshot_service.search_similar(group, query, max_results)

    print(documents)

    return documents
