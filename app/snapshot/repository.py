from abc import ABC, abstractmethod

from bson.datetime_ms import DatetimeMS
from pymongo.asynchronous.database import AsyncCollection, AsyncDatabase

from app.snapshot.models import KnowledgeSnapshot


class AbstractKnowledgeSnapshotRepository(ABC):
    @abstractmethod
    async def save(self, snapshot) -> None:
        """Save a knowledge snapshot"""

    @abstractmethod
    async def get_by_id(self, snapshot_id: str):
        """Get a knowledge snapshot by its ID"""

    @abstractmethod
    async def list_all(self) -> list[KnowledgeSnapshot]:
        """List all knowledge snapshots"""


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
