class KnowledgeVector:
    """Domain model for knowledge vectors."""

    def __init__(self, content: str, embedding: list[float] = None):
        self.content = content
        self.embedding = embedding
