class KnowledgeVector:
    """Domain model for knowledge vectors."""

    def __init__(self, content: str, embedding: list[float] = None, snapshot_id: str = None, source_id: str = None, metadata: dict = None):
        self.content = content
        self.embedding = embedding
        self.snapshot_id = snapshot_id
        self.source_id = source_id
        self.metadata = metadata
