from app.infra.mcp_server import data_mcp_server


@data_mcp_server.tool()
def retrieve_relevant_sources(query: str, top_k: int = 5) -> list[str]:
    """
    A tool to retrieve relevant documents based on a query.
    This is a mock implementation and should be replaced with actual retrieval logic.
    """
    # Mock implementation: return dummy documents
    return [f"Document {i+1} relevant to '{query}'" for i in range(top_k)]

