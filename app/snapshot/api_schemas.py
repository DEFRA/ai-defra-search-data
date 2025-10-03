from pydantic import BaseModel, Field


class KnowledgeSnapshotResponse(BaseModel):
    """ Response model for a knowledge group. """

    snapshot_id: str = Field(..., description="The unique identifier of the knowledge snapshot", serialization_alias="snapshotId")
    group_id: str = Field(..., description="The unique identifier of the knowledge group", serialization_alias="groupId")
    version: int = Field(..., description="The version number of the snapshot")
    created_at: str = Field(..., description="The creation date of the knowledge snapshot in ISO format", serialization_alias="createdAt")
    sources: list[dict] = Field(..., description="List of knowledge snapshot sources")


class KnowledgeVectorResultResponse(BaseModel):
    """ Response model for a knowledge vector search result. """

    content: str = Field(..., description="The content of the knowledge vector result")
    similarity_score: float = Field(..., description="The similarity score of the result (0.0 to 1.0)", serialization_alias="similarityScore")
    similarity_category: str = Field(..., description="The similarity category of the result (very_high, high, medium, low)", serialization_alias="similarityCategory")
    created_at: str = Field(..., description="The creation date of the knowledge vector result in ISO format", serialization_alias="createdAt")
    source: dict | None = Field(None, description="The source metadata associated with the knowledge vector result")
    metadata: dict | None = Field(None, description="Additional metadata associated with the knowledge vector result")

