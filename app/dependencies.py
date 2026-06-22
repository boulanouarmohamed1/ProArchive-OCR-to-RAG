from functools import lru_cache

from app.config import get_settings
from app.rag.rag_service import RAGService
from app.services.classification_service import ClassificationService
from app.services.embedding_service import EmbeddingService
from app.services.layout_service import LayoutService
from app.services.metadata_service import MetadataService
from app.services.ocr_service import OCRService
from app.services.pipeline_service import PipelineService
from app.services.qdrant_service import QdrantService


@lru_cache
def get_embedding_service() -> EmbeddingService:
    return EmbeddingService(get_settings())


@lru_cache
def get_qdrant_service() -> QdrantService:
    return QdrantService(get_settings(), get_embedding_service())


@lru_cache
def get_pipeline_service() -> PipelineService:
    settings = get_settings()
    embedding_service = get_embedding_service()
    return PipelineService(
        ocr_service=OCRService(settings),
        layout_service=LayoutService(),
        classification_service=ClassificationService(settings),
        metadata_service=MetadataService(),
        embedding_service=embedding_service,
        qdrant_service=get_qdrant_service(),
        settings=settings,
    )


@lru_cache
def get_rag_service() -> RAGService:
    return RAGService(
        settings=get_settings(),
        embedding_service=get_embedding_service(),
        qdrant_service=get_qdrant_service(),
    )
