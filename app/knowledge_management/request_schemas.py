from pydantic import BaseModel, Field


class KnowledgeSource(BaseModel):
    """ Model for a knowledge source. """

    name: str = Field(..., description="The name of the knowledge source", min_length=1, max_length=255)
    type: str = Field(..., description="The type of the knowledge source", min_length=1, max_length=100)
    location: str = Field(..., description="The URL of the knowledge source", min_length=1, max_length=2048)


class CreateKnowledgeGroupRequest(BaseModel):
    """ Request model for creating a knowledge group. """

    name: str = Field(..., description="The name of the knowledge group", min_length=1, max_length=255)
    description: str = Field(..., description="A description of the knowledge group", min_length=1)
    owner: str = Field(..., description="The owner of the knowledge group", min_length=1, max_length=255)
    sources: list[KnowledgeSource] | None = Field(..., description="List of knowledge group sources", min_items=1)


class KnowledgeGroupResponse(BaseModel):
    """ Response model for a knowledge group. """

    group_id: str = Field(..., description="The unique identifier of the knowledge group", serialization_alias="groupId")
    title: str = Field(..., description="The title of the knowledge group")
    description: str = Field(..., description="A description of the knowledge group")
    owner: str = Field(..., description="The owner of the knowledge group")
    created_at: str = Field(..., description="The creation date of the knowledge group in ISO format", serialization_alias="createdAt")
    updated_at: str = Field(..., description="The last update date of the knowledge group in ISO format", serialization_alias="updatedAt")
