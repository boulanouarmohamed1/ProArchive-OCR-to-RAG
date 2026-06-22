from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class OCRBlock(BaseModel):
    text: str
    confidence: float = Field(ge=0.0, le=1.0)
    bbox: list[list[float]] = Field(default_factory=list)
    page: int = Field(default=1, ge=1)


class OCRResult(BaseModel):
    text: str
    language: str
    confidence: float = Field(ge=0.0, le=1.0)
    blocks: list[OCRBlock] = Field(default_factory=list)


class LayoutSection(BaseModel):
    label: str
    text: str
    bbox: list[float] | None = None
    page: int = Field(default=1, ge=1)


class TableBlock(BaseModel):
    rows: list[list[str]] = Field(default_factory=list)
    bbox: list[float] | None = None
    page: int = Field(default=1, ge=1)


class LayoutResult(BaseModel):
    title: str | None = None
    sections: list[LayoutSection] = Field(default_factory=list)
    tables: list[TableBlock] = Field(default_factory=list)
    has_signature: bool = False
    has_stamp: bool = False


class DocumentType(str, Enum):
    contract = "Contract"
    administrative = "Administrative document"
    letter = "Letter"
    invoice = "Invoice"
    report = "Report"
    historical_archive = "Historical archive"
    unknown = "Unknown"


class ClassificationResult(BaseModel):
    document_type: DocumentType
    confidence: float = Field(ge=0.0, le=1.0)


class MetadataResult(BaseModel):
    date: str | None = None
    organization: str | None = None
    archive_number: str | None = None
    contract_number: str | None = None
    amounts: list[str] = Field(default_factory=list)
    people: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)


class DocumentRead(BaseModel):
    id: int
    filename: str
    language: str | None
    document_type: str | None
    upload_date: datetime
    metadata_json: dict[str, Any] | None
    ocr_text: str | None

    model_config = {"from_attributes": True}


class UploadResponse(BaseModel):
    document_id: int
    filename: str
    status: str


class ProcessRequest(BaseModel):
    document_id: int


class ProcessResponse(BaseModel):
    document_id: int
    ocr: OCRResult
    layout: LayoutResult
    classification: ClassificationResult
    metadata: MetadataResult
    chunks_indexed: int


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    top_k: int = Field(default=5, ge=1, le=20)


class RetrievedChunk(BaseModel):
    document_id: int
    chunk_id: str
    text: str
    score: float
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    answer: str
    sources: list[RetrievedChunk] = Field(default_factory=list)
