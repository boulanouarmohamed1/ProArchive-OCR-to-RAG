import logging

import requests

from app.config import Settings
from app.schemas import ChatResponse, RetrievedChunk
from app.services.embedding_service import EmbeddingService
from app.services.qdrant_service import QdrantService

logger = logging.getLogger(__name__)


class RAGService:
    SYSTEM_PROMPT = (
        "You are an archive assistant.\n"
        "Answer ONLY using the provided context.\n"
        "If information is missing say:\n"
        "'I could not find this information in the archive.'"
    )

    def __init__(
        self,
        settings: Settings,
        embedding_service: EmbeddingService,
        qdrant_service: QdrantService,
    ) -> None:
        self.settings = settings
        self.embedding_service = embedding_service
        self.qdrant_service = qdrant_service

    def answer(self, question: str, top_k: int | None = None) -> ChatResponse:
        query_embedding = self.embedding_service.embed_text(question)
        retrieved = self.qdrant_service.search(query_embedding, top_k or self.settings.retrieval_top_k)
        context = self._build_context(retrieved)
        answer = self._generate_answer(question, context)
        return ChatResponse(answer=answer, sources=retrieved)

    def _build_context(self, chunks: list[RetrievedChunk]) -> str:
        if not chunks:
            return ""
        parts = []
        for idx, chunk in enumerate(chunks, start=1):
            filename = chunk.metadata.get("filename", "unknown")
            doc_type = chunk.metadata.get("document_type", "unknown")
            parts.append(
                f"[Source {idx}] document_id={chunk.document_id} filename={filename} "
                f"type={doc_type} score={chunk.score:.4f}\n{chunk.text}"
            )
        return "\n\n".join(parts)

    def _generate_answer(self, question: str, context: str) -> str:
        if not context.strip():
            return "I could not find this information in the archive."
        prompt = f"{self.SYSTEM_PROMPT}\n\nContext:\n{context}\n\nQuestion:\n{question}\n\nAnswer:"
        try:
            response = requests.post(
                f"{self.settings.ollama_base_url}/api/generate",
                json={"model": self.settings.ollama_model, "prompt": prompt, "stream": False},
                timeout=120,
            )
            response.raise_for_status()
            answer = response.json().get("response", "").strip()
            return answer or "I could not find this information in the archive."
        except requests.RequestException as exc:
            logger.exception("Ollama generation failed")
            raise RuntimeError(f"Ollama generation failed: {exc}") from exc
