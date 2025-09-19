from fastapi import APIRouter, Depends, status

from app.common.bedrock import (
    AbstractEmbeddingService,
    BedrockEmbeddingService,
    get_bedrock_client,
)
from app.config import config
from app.knowledge.ingestion import service as ingestion_service

router = APIRouter(tags=["knowledge-ingestion"])


def get_embedding_service() -> AbstractEmbeddingService:
    client = get_bedrock_client()
    model_id = config.bedrock_embedding_model_id

    return BedrockEmbeddingService(client, model_id)


@router.post("/knowledge/ingest", status_code=status.HTTP_202_ACCEPTED)
async def ingest_knowledge(
    embedding_service: AbstractEmbeddingService = Depends(get_embedding_service)
):
    """
    Ingest knowledge from a given URL.

    Args:
        url: The URL to ingest knowledge from
        embedding_service: The embedding service to use

    Returns:
        Acknowledgment of ingestion initiation
    """

    embeddings = ingestion_service.ingest_url(None, embedding_service, "what is the capital of france?")

    return {"message": "Ingestion initiated", "embeddings": embeddings}

