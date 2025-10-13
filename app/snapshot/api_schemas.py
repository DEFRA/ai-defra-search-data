from pydantic import BaseModel, Field


class QuerySnapshotRequest(BaseModel):
    """ Request model for querying a snapshot. """

    group_id: str = Field(..., description="The ID of the knowledge group", validation_alias="groupId")
    query: str = Field(..., description="The search query")
    max_results: int = Field(5, description="Maximum number of results to return", validation_alias="maxResults")


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
    title: str = Field(..., description="The title of the knowledge vector result")
    snapshot_id: str = Field(..., description="Internal ID representing the snapshot used", serialization_alias="snapshotId")
    source_id: str = Field(..., description="Internal ID representing the source document", serialization_alias="sourceId")
