from httpx import AsyncClient

from app.common.bedrock import AbstractEmbeddingService


def ingest_url(
        http_client: AsyncClient,  # noqa: ARG001
        embedding_service: AbstractEmbeddingService,
        url: str  # noqa: ARG001
    ):

    content = "Simulated content from the URL."

    return embedding_service.generate_embeddings(content)

