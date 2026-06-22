from app.config import Settings
from app.services.embedding_service import EmbeddingService


def test_chunk_text_uses_overlap() -> None:
    settings = Settings(chunk_size=10, chunk_overlap=3)
    service = EmbeddingService(settings)
    chunks = service.chunk_text(1, "abcdefghijklmnopqrstuvwxyz", {"filename": "x.pdf"})

    assert [chunk.text for chunk in chunks] == ["abcdefghij", "hijklmnopq", "opqrstuvwx", "vwxyz"]
    assert chunks[1].metadata["chunk_index"] == 1
