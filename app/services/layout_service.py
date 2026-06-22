import re
from statistics import median

from app.schemas import LayoutResult, LayoutSection, OCRResult, TableBlock


class LayoutService:
    def analyze(self, ocr: OCRResult) -> LayoutResult:
        blocks = sorted(ocr.blocks, key=lambda block: (block.page, self._top(block.bbox)))
        sections: list[LayoutSection] = []
        tables: list[TableBlock] = []

        heights = [self._height(block.bbox) for block in blocks if block.bbox]
        typical_height = median(heights) if heights else 0.0

        title = self._detect_title(blocks, typical_height)
        for block in blocks:
            text = block.text.strip()
            if not text:
                continue
            label = self._classify_block(text, block.bbox, typical_height)
            if label == "table":
                tables.append(TableBlock(rows=self._parse_table_rows(text), bbox=self._flatten_bbox(block.bbox), page=block.page))
            else:
                sections.append(
                    LayoutSection(label=label, text=text, bbox=self._flatten_bbox(block.bbox), page=block.page)
                )

        return LayoutResult(
            title=title,
            sections=sections,
            tables=tables,
            has_signature=self._has_signature(ocr.text),
            has_stamp=self._has_stamp(ocr.text),
        )

    def _detect_title(self, blocks: list, typical_height: float) -> str | None:
        candidates = []
        for block in blocks[:10]:
            text = block.text.strip()
            if len(text) < 4:
                continue
            height = self._height(block.bbox)
            if height >= typical_height or text.isupper():
                candidates.append(text)
        return candidates[0] if candidates else (blocks[0].text.strip() if blocks else None)

    def _classify_block(self, text: str, bbox: list[list[float]], typical_height: float) -> str:
        lowered = text.lower()
        if self._is_table_like(text):
            return "table"
        if any(token in lowered for token in ["signature", "signe", "signataire", "امضاء", "توقيع"]):
            return "signature"
        if any(token in lowered for token in ["cachet", "stamp", "ختم"]):
            return "stamp"
        top = self._top(bbox)
        if top < 120:
            return "header"
        if top > 3000:
            return "footer"
        if self._height(bbox) > typical_height * 1.25 and len(text) < 160:
            return "title"
        return "paragraph"

    @staticmethod
    def _is_table_like(text: str) -> bool:
        lines = [line for line in text.splitlines() if line.strip()]
        separators = text.count("|") + text.count("\t") + len(re.findall(r"\s{3,}", text))
        numeric_cells = len(re.findall(r"\b\d+(?:[.,]\d+)?\b", text))
        return separators >= 2 or (len(lines) >= 2 and numeric_cells >= 4)

    @staticmethod
    def _parse_table_rows(text: str) -> list[list[str]]:
        rows: list[list[str]] = []
        for line in text.splitlines():
            cells = [cell.strip() for cell in re.split(r"\s{2,}|\t|\|", line) if cell.strip()]
            if cells:
                rows.append(cells)
        return rows

    @staticmethod
    def _has_signature(text: str) -> bool:
        return bool(re.search(r"\b(signature|signe|signataire)\b|امضاء|توقيع", text, re.IGNORECASE))

    @staticmethod
    def _has_stamp(text: str) -> bool:
        return bool(re.search(r"\b(cachet|stamp|seal)\b|ختم", text, re.IGNORECASE))

    @staticmethod
    def _top(bbox: list[list[float]]) -> float:
        return min((point[1] for point in bbox), default=0.0)

    @staticmethod
    def _height(bbox: list[list[float]]) -> float:
        ys = [point[1] for point in bbox]
        return max(ys) - min(ys) if ys else 0.0

    @staticmethod
    def _flatten_bbox(bbox: list[list[float]]) -> list[float] | None:
        if not bbox:
            return None
        xs = [point[0] for point in bbox]
        ys = [point[1] for point in bbox]
        return [min(xs), min(ys), max(xs), max(ys)]
