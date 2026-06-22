from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies import get_pipeline_service
from app.models.document import Document
from app.schemas import ProcessRequest, ProcessResponse
from app.services.pipeline_service import PipelineService

router = APIRouter(tags=["processing"])


@router.post("/process", response_model=ProcessResponse)
def process_document(
    request: ProcessRequest,
    db: Session = Depends(get_db),
    pipeline: PipelineService = Depends(get_pipeline_service),
) -> ProcessResponse:
    document = db.get(Document, request.document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return pipeline.process_document(db, document)
