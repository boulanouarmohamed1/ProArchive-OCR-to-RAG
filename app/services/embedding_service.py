import logging
from dataclasses import dataclass
from typing import Any

from app.config import Settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TextChunk:
    chunk_id: str
    document_id: int
    text: str
    index: int
    metadata: dict[str, Any]


class EmbeddingService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._model = None
        self._dimension: int | None = None

    @property
    def dimension(self) -> int:
        if self._dimension is None:
            embedding = self.embed_text("dimension probe")
            self._dimension = len(embedding)
        return self._dimension

    def chunk_text(self, document_id: int, text: str, metadata: dict[str, Any]) -> list[TextChunk]:
        chunk_size = self.settings.chunk_size
        overlap = min(self.settings.chunk_overlap, chunk_size - 1)
        chunks: list[TextChunk] = []
        start = 0
        index = 0
        clean_text = text.strip()

        while start < len(clean_text):
            end = min(start + chunk_size, len(clean_text))
            chunk_text = clean_text[start:end].strip()
            if chunk_text:
                chunks.append(
                    TextChunk(
                        chunk_id=f"{document_id}-{index}",
                        document_id=document_id,
                        text=chunk_text,
                        index=index,
                        metadata={**metadata, "chunk_index": index},
                    )
                )
                index += 1
            if end >= len(clean_text):
                break
            start = max(end - overlap, start + 1)
        return chunks

    def embed_text(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        model = self._get_model()
        embeddings = model.encode(
            texts,
            batch_size=self.settings.embedding_batch_size,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return [embedding.astype(float).tolist() for embedding in embeddings]

    def _get_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            logger.info("Loading embedding model %s", self.settings.embedding_model)
            self._model = SentenceTransformer(self.settings.embedding_model, device=self.settings.embedding_device)
        return self._model
