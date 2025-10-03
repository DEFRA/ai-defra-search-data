from abc import ABC, abstractmethod

from bson.datetime_ms import DatetimeMS
from pymongo.asynchronous.database import AsyncCollection, AsyncDatabase
from sqlalchemy import select

from app.snapshot.models import (
    KnowledgeSnapshot,
    KnowledgeVector,
    KnowledgeVectorResult,
)


class AbstractKnowledgeSnapshotRepository(ABC):
    @abstractmethod
    async def save(self, snapshot) -> None:
        """Save a knowledge snapshot"""

    @abstractmethod
    async def get_by_id(self, snapshot_id: str):
        """Get a knowledge snapshot by its ID"""

    @abstractmethod
    async def list_snapshots_by_group(self, group_id: str) -> list[KnowledgeSnapshot]:
        """List all knowledge snapshots for a specific group"""

    @abstractmethod
    async def get_latest_by_group(self, group_id: str):
        """Get the latest knowledge snapshot for a specific group"""


class MongoKnowledgeSnapshotRepository(AbstractKnowledgeSnapshotRepository):
    def __init__(self, db: AsyncDatabase):
        self.db: AsyncDatabase = db
        self.knowledge_snapshots: AsyncCollection = self.db.get_collection("knowledgeSnapshots")

    async def save(self, snapshot: KnowledgeSnapshot) -> None:
        """Save a knowledge snapshot"""

        snapshot_data = {
            "snapshotId": snapshot.snapshot_id,
            "groupId": snapshot.group_id,
            "version": snapshot.version,
            "createdAt": DatetimeMS(snapshot.created_at),
            "sources": [source.__dict__ for source in snapshot.sources]
        }

        await self.knowledge_snapshots.insert_one(snapshot_data)

    async def get_by_id(self, snapshot_id: str) -> KnowledgeSnapshot | None:
        """Get a knowledge snapshot by its ID"""
        doc = await self.knowledge_snapshots.find_one({"snapshotId": snapshot_id})

        if not doc:
            return None

        return KnowledgeSnapshot(
            group_id=doc["groupId"],
            version=doc["version"],
            created_at=doc["createdAt"],
            sources=doc["sources"]
        )

    async def list_snapshots_by_group(self, group_id: str) -> list[KnowledgeSnapshot]:
        """List all knowledge snapshots for a specific group"""
        cursor = self.knowledge_snapshots.find({"groupId": group_id})
        snapshots = []

        async for doc in cursor:
            snapshot = KnowledgeSnapshot(
                group_id=doc["groupId"],
                version=doc["version"],
                created_at=doc["createdAt"],
                sources=doc["sources"]
            )
            snapshots.append(snapshot)

        return snapshots

    async def get_latest_by_group(self, group_id: str) -> KnowledgeSnapshot | None:
        """Get the latest knowledge snapshot for a specific group"""
        doc = await self.knowledge_snapshots.find_one(
            {"groupId": group_id},
            sort=[("version", -1)]
        )

        if not doc:
            return None

        return KnowledgeSnapshot(
            group_id=doc["groupId"],
            version=doc["version"],
            created_at=doc["createdAt"],
            sources=doc["sources"]
        )


class AbstractKnowledgeVectorRepository(ABC):
    @abstractmethod
    async def add(self, knowledge_vector: KnowledgeVector) -> None:
        """Add a knowledge vector entry"""

    @abstractmethod
    async def query_by_snapshot(self, embedding: list[float], snapshot_id: str, top_k: int) -> list[KnowledgeVectorResult]:
        """Query for the top_k most similar knowledge vectors within a specific snapshot"""


class PostgresKnowledgeVectorRepository(AbstractKnowledgeVectorRepository):
    """PostgreSQL implementation of KnowledgeVectorRepository using pgvector."""

    def __init__(self, session):
        """
        Initialize with SQLAlchemy async session.

        Args:
            session: Async SQLAlchemy session
        """
        self.session = session

    async def add(self, knowledge_vector: KnowledgeVector) -> None:
        """Add a knowledge vector entry to PostgreSQL."""
        self.session.add(knowledge_vector)
        await self.session.commit()

    async def add_batch(self, vectors: list[KnowledgeVector]) -> None:
        """Add multiple knowledge vector entries to PostgreSQL in batch."""
        self.session.add_all(vectors)

        await self.session.commit()

    async def query_by_snapshot(self, embedding: list[float], snapshot_id: str, max_results: int) -> list[KnowledgeVectorResult]:
        """Query for the top_k most similar knowledge vectors within a specific snapshot."""

        query = (
            select(
                KnowledgeVector.id,
                KnowledgeVector.content,
                KnowledgeVector.embedding,
                KnowledgeVector.created_at,
                KnowledgeVector.snapshot_id,
                KnowledgeVector.source_id,
                KnowledgeVector.metadata,
                KnowledgeVector.embedding.cosine_distance(embedding).label("distance")
            )
            .where(KnowledgeVector.snapshot_id == snapshot_id)
            .order_by(KnowledgeVector.embedding.cosine_distance(embedding))
            .limit(max_results)
        )

        result = await self.session.execute(query)
        rows = result.fetchall()

        return [
            KnowledgeVectorResult(
                content=row.content,
                similarity_score=1.0 - float(row.distance),
                created_at=row.created_at,
                snapshot_id=row.snapshot_id,
                source_id=row.source_id,
                metadata=row.metadata
            )
            for row in rows
        ]

