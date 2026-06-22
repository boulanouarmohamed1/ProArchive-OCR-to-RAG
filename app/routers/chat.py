from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_rag_service
from app.rag.rag_service import RAGService
from app.schemas import ChatRequest, ChatResponse

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, rag_service: RAGService = Depends(get_rag_service)) -> ChatResponse:
    try:
        return rag_service.answer(request.question, request.top_k)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
