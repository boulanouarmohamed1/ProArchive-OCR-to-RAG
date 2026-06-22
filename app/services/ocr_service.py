import logging
from pathlib import Path
from statistics import mean
from typing import Any

import numpy as np
from langdetect import DetectorFactory, LangDetectException, detect
from pdf2image import convert_from_path
from PIL import Image

from app.config import Settings
from app.schemas import OCRBlock, OCRResult

DetectorFactory.seed = 0
logger = logging.getLogger(__name__)


class OCRService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._engines: dict[str, Any] = {}

    def extract(self, file_path: str | Path) -> OCRResult:
        path = Path(file_path)
        images = self._load_images(path)
        first_pass = self._run_ocr(images, lang="latin")
        language = self._detect_language(first_pass.text)

        if language == "ar":
            result = self._run_ocr(images, lang="arabic")
            return result.model_copy(update={"language": "ar"})

        result = first_pass
        return result.model_copy(update={"language": language})

    def _load_images(self, path: Path) -> list[Image.Image]:
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            return convert_from_path(str(path), dpi=250)
        if suffix in {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp"}:
            return [Image.open(path).convert("RGB")]
        raise ValueError(f"Unsupported file type: {suffix}")

    def _run_ocr(self, images: list[Image.Image], lang: str) -> OCRResult:
        engine = self._get_engine(lang)
        blocks: list[OCRBlock] = []

        for page_number, image in enumerate(images, start=1):
            raw_result = engine.ocr(np.array(image), cls=True)
            page_blocks = self._parse_paddle_result(raw_result, page_number)
            blocks.extend(page_blocks)

        text = "\n".join(block.text for block in blocks).strip()
        confidence = mean([block.confidence for block in blocks]) if blocks else 0.0
        language = self._detect_language(text)
        return OCRResult(text=text, language=language, confidence=confidence, blocks=blocks)

    def _get_engine(self, lang: str) -> Any:
        if lang not in self._engines:
            from paddleocr import PaddleOCR

            paddle_lang = "arabic" if lang == "arabic" else "fr"
            logger.info("Loading PaddleOCR engine for %s", paddle_lang)
            self._engines[lang] = PaddleOCR(use_angle_cls=True, lang=paddle_lang, show_log=False)
        return self._engines[lang]

    @staticmethod
    def _parse_paddle_result(raw_result: Any, page_number: int) -> list[OCRBlock]:
        blocks: list[OCRBlock] = []
        if not raw_result:
            return blocks

        page_items = raw_result[0] if len(raw_result) == 1 and isinstance(raw_result[0], list) else raw_result
        for item in page_items:
            try:
                bbox = [[float(x), float(y)] for x, y in item[0]]
                text = str(item[1][0]).strip()
                confidence = float(item[1][1])
            except (IndexError, TypeError, ValueError):
                continue
            if text:
                blocks.append(OCRBlock(text=text, confidence=confidence, bbox=bbox, page=page_number))
        return blocks

    @staticmethod
    def _detect_language(text: str) -> str:
        if not text.strip():
            return "unknown"
        arabic_chars = sum(1 for char in text if "\u0600" <= char <= "\u06ff")
        if arabic_chars / max(len(text), 1) > 0.15:
            return "ar"
        try:
            lang = detect(text)
        except LangDetectException:
            return "unknown"
        if lang.startswith("fr"):
            return "fr"
        if lang.startswith("ar"):
            return "ar"
        return lang
