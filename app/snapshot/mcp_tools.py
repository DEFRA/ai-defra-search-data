from app.infra.mcp_server import data_mcp_server
from app.common.mongo import get_db, get_mongo_client
from app.common.postgres import get_async_session_factory
from app.common.bedrock import BedrockEmbeddingService, get_bedrock_client
from app.snapshot.repository import MongoKnowledgeSnapshotRepository, PostgresKnowledgeVectorRepository
from app.snapshot.service import SnapshotService
from app.config import config

@data_mcp_server.tool()
async def retrieve_relevant_sources(snapshot_id: str, query: str, top_k: int = 5) -> list[str]:
    """
    A tool to retrieve relevant documents based on a query.
    """

    # Initialize dependencies directly
    db = await get_db(await get_mongo_client())
    session_factory = await get_async_session_factory()
    session = session_factory()
    
    snapshot_repo = MongoKnowledgeSnapshotRepository(db)
    vector_repo = PostgresKnowledgeVectorRepository(session)
    embedding_service = BedrockEmbeddingService(get_bedrock_client(), config.bedrock_embedding_config)
    
    snapshot_service = SnapshotService(snapshot_repo, vector_repo, embedding_service)

    vectors = await snapshot_service.search_similar(snapshot_id, query, top_k)

    return [vector.content for vector in vectors]
