from pathlib import Path

from sqlalchemy.orm import Session

from app.config import Settings
from app.models.document import Document
from app.schemas import ProcessResponse
from app.services.classification_service import ClassificationService
from app.services.embedding_service import EmbeddingService
from app.services.layout_service import LayoutService
from app.services.metadata_service import MetadataService
from app.services.ocr_service import OCRService
from app.services.qdrant_service import QdrantService


class PipelineService:
    def __init__(
        self,
        ocr_service: OCRService,
        layout_service: LayoutService,
        classification_service: ClassificationService,
        metadata_service: MetadataService,
        embedding_service: EmbeddingService,
        qdrant_service: QdrantService,
        settings: Settings,
    ) -> None:
        self.ocr_service = ocr_service
        self.layout_service = layout_service
        self.classification_service = classification_service
        self.metadata_service = metadata_service
        self.embedding_service = embedding_service
        self.qdrant_service = qdrant_service
        self.settings = settings

    def process_document(self, db: Session, document: Document) -> ProcessResponse:
        file_path = Path(document.file_path)
        ocr = self.ocr_service.extract(file_path)
        layout = self.layout_service.analyze(ocr)
        classification = self.classification_service.classify(ocr, file_path)
        metadata = self.metadata_service.extract(ocr)

        document.language = ocr.language
        document.document_type = classification.document_type.value
        document.metadata_json = metadata.model_dump()
        document.ocr_text = ocr.text
        db.add(document)
        db.commit()
        db.refresh(document)

        chunk_metadata = {
            "filename": document.filename,
            "language": document.language,
            "document_type": document.document_type,
            **metadata.model_dump(exclude={"raw"}),
        }
        chunks = self.embedding_service.chunk_text(document.id, ocr.text, chunk_metadata)
        indexed = self.qdrant_service.update_document_chunks(document.id, chunks)

        return ProcessResponse(
            document_id=document.id,
            ocr=ocr,
            layout=layout,
            classification=classification,
            metadata=metadata,
            chunks_indexed=indexed,
        )
