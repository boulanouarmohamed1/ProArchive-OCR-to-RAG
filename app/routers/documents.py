from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies import get_qdrant_service
from app.models.document import Document
from app.schemas import DocumentRead
from app.services.qdrant_service import QdrantService

router = APIRouter(tags=["documents"])


@router.get("/documents", response_model=list[DocumentRead])
def list_documents(db: Session = Depends(get_db)) -> list[DocumentRead]:
    documents = db.scalars(select(Document).order_by(Document.upload_date.desc())).all()
    return [DocumentRead.model_validate(document) for document in documents]


@router.get("/documents/{document_id}", response_model=DocumentRead)
def get_document(document_id: int, db: Session = Depends(get_db)) -> DocumentRead:
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentRead.model_validate(document)


@router.delete("/documents/{document_id}", status_code=204)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    qdrant_service: QdrantService = Depends(get_qdrant_service),
) -> None:
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    qdrant_service.delete_document(document_id)
    db.delete(document)
    db.commit()
