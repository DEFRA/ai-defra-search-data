from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, DateTime, Integer, MetaData, Table, Text, func
from sqlalchemy.orm import DeclarativeBase, registry

import app.knowledge.models as model


class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""


metadata = MetaData()
mapper_registry = registry(metadata=metadata)

knowledge_vectors_table = Table(
    "knowledge_vectors",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("content", Text, nullable=False),
    Column("embedding", Vector(1024), nullable=False),
    Column(
        "created_at",
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp()
    ),
)


def start_mappers():
    mapper_registry.map_imperatively(
        model.KnowledgeVector, 
        knowledge_vectors_table,
        properties={
            "id": knowledge_vectors_table.c.id,
            "content": knowledge_vectors_table.c.content,
            "embedding": knowledge_vectors_table.c.embedding,
            "created_at": knowledge_vectors_table.c.created_at,
        }
    )
