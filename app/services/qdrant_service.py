import logging
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from app.config import Settings
from app.schemas import RetrievedChunk
from app.services.embedding_service import EmbeddingService, TextChunk

logger = logging.getLogger(__name__)


class QdrantService:
    def __init__(self, settings: Settings, embedding_service: EmbeddingService) -> None:
        self.settings = settings
        self.embedding_service = embedding_service
        self.client = QdrantClient(url=str(settings.qdrant_url))

    def ensure_collection(self) -> None:
        if self._collection_exists():
            return
        self.client.create_collection(
            collection_name=self.settings.qdrant_collection,
            vectors_config=qmodels.VectorParams(
                size=self.embedding_service.dimension,
                distance=qmodels.Distance.COSINE,
            ),
        )
        logger.info("Created Qdrant collection %s", self.settings.qdrant_collection)

    def insert_chunks(self, chunks: list[TextChunk]) -> int:
        if not chunks:
            return 0
        self.ensure_collection()
        vectors = self.embedding_service.embed_texts([chunk.text for chunk in chunks])
        points = [
            qmodels.PointStruct(
                id=str(uuid5(NAMESPACE_URL, f"archive-document-chunk:{chunk.chunk_id}")),
                vector=vector,
                payload={
                    "chunk_id": chunk.chunk_id,
                    "document_id": chunk.document_id,
                    "text": chunk.text,
                    "metadata": chunk.metadata,
                },
            )
            for chunk, vector in zip(chunks, vectors, strict=True)
        ]
        self.client.upsert(collection_name=self.settings.qdrant_collection, points=points)
        return len(points)

    def update_document_chunks(self, document_id: int, chunks: list[TextChunk]) -> int:
        self.delete_document(document_id)
        return self.insert_chunks(chunks)

    def delete_document(self, document_id: int) -> None:
        if not self._collection_exists():
            return
        self.client.delete(
            collection_name=self.settings.qdrant_collection,
            points_selector=qmodels.FilterSelector(
                filter=qmodels.Filter(
                    must=[
                        qmodels.FieldCondition(
                            key="document_id",
                            match=qmodels.MatchValue(value=document_id),
                        )
                    ]
                )
            ),
        )

    def search(self, query_embedding: list[float], top_k: int = 5) -> list[RetrievedChunk]:
        if not self._collection_exists():
            return []
        results = self.client.search(
            collection_name=self.settings.qdrant_collection,
            query_vector=query_embedding,
            limit=top_k,
            with_payload=True,
        )
        chunks: list[RetrievedChunk] = []
        for result in results:
            payload: dict[str, Any] = result.payload or {}
            chunks.append(
                RetrievedChunk(
                    document_id=int(payload.get("document_id", 0)),
                    chunk_id=str(payload.get("chunk_id", result.id)),
                    text=str(payload.get("text", "")),
                    score=float(result.score),
                    metadata=dict(payload.get("metadata", {})),
                )
            )
        return chunks

    def _collection_exists(self) -> bool:
        collections = self.client.get_collections().collections
        return any(collection.name == self.settings.qdrant_collection for collection in collections)
