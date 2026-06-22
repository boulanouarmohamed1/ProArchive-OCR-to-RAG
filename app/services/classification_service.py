import base64
import logging
from pathlib import Path

import requests

from app.config import Settings
from app.schemas import ClassificationResult, DocumentType, OCRResult

logger = logging.getLogger(__name__)


class ClassificationService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def classify(self, ocr: OCRResult, file_path: str | Path | None = None) -> ClassificationResult:
        if file_path and self.settings.ollama_vision_model:
            vlm_result = self._classify_with_vision_model(Path(file_path), ocr.text)
            if vlm_result:
                return vlm_result
        return self._classify_with_rules(ocr.text)

    def _classify_with_vision_model(self, file_path: Path, text: str) -> ClassificationResult | None:
        if file_path.suffix.lower() == ".pdf":
            return None
        try:
            encoded = base64.b64encode(file_path.read_bytes()).decode("ascii")
            prompt = (
                "Classify this archive document as one of: Contract, Administrative document, "
                "Letter, Invoice, Report, Historical archive, Unknown. Return only the label."
            )
            response = requests.post(
                f"{self.settings.ollama_base_url}/api/generate",
                json={
                    "model": self.settings.ollama_vision_model,
                    "prompt": f"{prompt}\nOCR text:\n{text[:3000]}",
                    "images": [encoded],
                    "stream": False,
                },
                timeout=60,
            )
            response.raise_for_status()
            label = response.json().get("response", "").strip()
            document_type = self._normalize_label(label)
            return ClassificationResult(document_type=document_type, confidence=0.85)
        except Exception as exc:
            logger.warning("Vision classification failed: %s", exc)
            return None

    def _classify_with_rules(self, text: str) -> ClassificationResult:
        lowered = text.lower()
        rules: list[tuple[DocumentType, list[str]]] = [
            (DocumentType.contract, ["contrat", "contract", "اتفاقية", "عقد", "sonatrach"]),
            (DocumentType.invoice, ["facture", "invoice", "montant", "total ttc", "فاتورة"]),
            (DocumentType.letter, ["monsieur", "madame", "objet", "lettre", "سيدي", "رسالة"]),
            (DocumentType.report, ["rapport", "report", "analyse", "تقرير"]),
            (DocumentType.administrative, ["arrete", "decision", "administratif", "قرار", "اداري"]),
            (DocumentType.historical_archive, ["archive", "historique", "محفوظات", "ارشيف"]),
        ]
        best_type = DocumentType.unknown
        best_hits = 0
        for doc_type, keywords in rules:
            hits = sum(1 for keyword in keywords if keyword in lowered)
            if hits > best_hits:
                best_type = doc_type
                best_hits = hits
        confidence = min(0.55 + best_hits * 0.15, 0.95) if best_hits else 0.35
        return ClassificationResult(document_type=best_type, confidence=confidence)

    @staticmethod
    def _normalize_label(label: str) -> DocumentType:
        lowered = label.lower()
        for document_type in DocumentType:
            if document_type.value.lower() in lowered:
                return document_type
        return DocumentType.unknown
