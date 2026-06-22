import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database.session import get_db
from app.models.document import Document
from app.schemas import UploadResponse

router = APIRouter(tags=["upload"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf", ".tif", ".tiff", ".bmp"}


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> UploadResponse:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {suffix}")

    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    if size > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="Uploaded file exceeds size limit")

    safe_name = f"{uuid4().hex}{suffix}"
    destination = settings.upload_dir / safe_name
    with destination.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    document = Document(filename=file.filename or safe_name, file_path=str(destination))
    db.add(document)
    db.commit()
    db.refresh(document)

    return UploadResponse(document_id=document.id, filename=document.filename, status="uploaded")
