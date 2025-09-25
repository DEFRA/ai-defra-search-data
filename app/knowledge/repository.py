from abc import ABC, abstractmethod

from bson.datetime_ms import DatetimeMS
from bson.objectid import ObjectId
from pymongo.asynchronous.database import AsyncCollection, AsyncDatabase
from pymongo.errors import DuplicateKeyError
from sqlalchemy import select

from app.knowledge.models import (
    KnowledgeGroup,
    KnowledgeGroupAlreadyExistsError,
    KnowledgeResult,
    KnowledgeSearchResults,
    KnowledgeSnapshot,
    KnowledgeSource,
    KnowledgeVector,
)


class AbstractKnowledgeGroupRepository(ABC):
    @abstractmethod
    async def save(self, group: KnowledgeGroup) -> None:
        """Save a knowledge group with all its sources"""

    @abstractmethod
    async def get_by_id(self, group_id: str) -> KnowledgeGroup | None:
        """Get a complete knowledge group with all its sources loaded"""

    @abstractmethod
    async def list_all(self) -> list[KnowledgeGroup]:
        """List all knowledge groups with their sources loaded"""


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


class AbstractKnowledgeVectorRepository(ABC):
    @abstractmethod
    async def add(self, knowledge_vector: KnowledgeVector) -> None:
        """Add a knowledge vector entry"""

    @abstractmethod
    async def query(self, embedding: list[float], top_k: int) -> KnowledgeSearchResults:
        """Query for the top_k most similar knowledge vectors"""


class MongoKnowledgeGroupRepository(AbstractKnowledgeGroupRepository):
    def __init__(self, db: AsyncDatabase):
        self.db: AsyncDatabase = db
        self.knowledge_groups: AsyncCollection = self.db.get_collection("knowledgeGroups")
        self.knowledge_sources: AsyncCollection = self.db.get_collection("knowledgeSources")

    async def save(self, group: KnowledgeGroup) -> None:
        """Save a knowledge group with all its sources"""
        # First, save or update the group document
        entry_data = {
            "groupId": group.group_id,
            "title": group.name,
            "description": group.description,
            "owner": group.owner,
            "createdAt": DatetimeMS(group.created_at),
            "updatedAt": DatetimeMS(group.updated_at)
        }

        try:
            # Use upsert to handle both insert and update
            await self.knowledge_groups.update_one(
                {"groupId": group.group_id},
                {"$set": entry_data},
                upsert=True
            )
        except DuplicateKeyError:
            msg = f"Knowledge entry with group_id '{group.group_id}' already exists"
            raise KnowledgeGroupAlreadyExistsError(msg) from None

        # Get the group document to get the ObjectId
        group_doc = await self.knowledge_groups.find_one({"groupId": group.group_id})

        if not group_doc:
            msg = f"Failed to save knowledge group '{group.group_id}'"
            raise RuntimeError(msg)

        # Insert all sources from the aggregate
        if group.sources:
            source_documents = []
            for source in group.sources:
                print(source)
                source_data = {
                    "_id": ObjectId(),
                    "groupId": group.group_id,
                    "parent_group_id": group_doc["_id"],
                    "name": source.name,
                    "type": source.type,
                    "location": source.location
                }
                source_documents.append(source_data)

            await self.knowledge_sources.insert_many(source_documents)

    async def get_by_id(self, group_id: str) -> KnowledgeGroup | None:
        """Get a complete knowledge group with all its sources loaded"""
        # Get group document
        group_doc = await self.knowledge_groups.find_one({"groupId": group_id})
        if not group_doc:
            return None

        # Create group instance
        group = KnowledgeGroup(
            group_id=group_doc["groupId"],
            name=group_doc["title"],
            description=group_doc["description"],
            owner=group_doc["owner"],
            created_at=group_doc["createdAt"],
            updated_at=group_doc["updatedAt"]
        )

        # Load and add all sources
        cursor = self.knowledge_sources.find({"groupId": group_id})
        async for source_doc in cursor:
            source = KnowledgeSource(
                name=source_doc["name"],
                data_type=source_doc["type"],
                location=source_doc["location"]
            )
            group.add_source(source)

        return group

    async def list_all(self) -> list[KnowledgeGroup]:
        """List all knowledge groups with their sources loaded"""
        cursor = self.knowledge_groups.find()
        groups = []

        async for group_doc in cursor:
            # Create group instance
            group = KnowledgeGroup(
                group_id=group_doc["groupId"],
                name=group_doc["title"],
                description=group_doc["description"],
                owner=group_doc["owner"],
                created_at=group_doc["createdAt"],
                updated_at=group_doc["updatedAt"]
            )

            # Load and add all sources
            source_cursor = self.knowledge_sources.find({"groupId": group.group_id})
            async for source_doc in source_cursor:
                source = KnowledgeSource(
                    name=source_doc["name"],
                    data_type=source_doc["type"],
                    location=source_doc["location"]
                )
                group.add_source(source)

            groups.append(group)

        return groups


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

    async def query(self, embedding: list[float], top_k: int) -> KnowledgeSearchResults:
        """Query for the top_k most similar knowledge vectors using cosine similarity."""
        # Use cosine distance for similarity search (lower distance = higher similarity)
        stmt = (
            select(
                KnowledgeVector.id,
                KnowledgeVector.content,
                KnowledgeVector.embedding,
                KnowledgeVector.created_at,
                KnowledgeVector.embedding.cosine_distance(embedding).label("distance")
            )
            .order_by(KnowledgeVector.embedding.cosine_distance(embedding))
            .limit(top_k)
        )

        result = await self.session.execute(stmt)
        rows = result.fetchall()

        # Convert to domain objects
        vector_results = [
            KnowledgeResult(
                content=row.content,
                similarity_score=1.0 - float(row.distance),  # Convert distance to similarity
                created_at=row.created_at,
                embedding=row.embedding  # Include embedding in results
            )
            for row in rows
        ]

        return KnowledgeSearchResults(
            query_embedding=embedding,
            results=vector_results
        )

