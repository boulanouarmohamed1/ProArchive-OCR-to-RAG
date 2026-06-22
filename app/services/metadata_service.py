import re
from collections import Counter

from dateutil import parser

from app.schemas import MetadataResult, OCRResult


class MetadataService:
    DATE_PATTERNS = [
        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
        r"\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b",
        r"\b\d{1,2}\s+(?:janvier|fevrier|mars|avril|mai|juin|juillet|aout|septembre|octobre|novembre|decembre)\s+\d{4}\b",
    ]
    MONEY_PATTERN = r"\b\d{1,3}(?:[ .]\d{3})*(?:[,.]\d{2})?\s?(?:DZD|DA|EUR|USD|FRF|dinars?)\b"
    ARCHIVE_PATTERN = r"(?:archive|archives?|ref(?:erence)?|numero|n[°o]|رقم)\s*[:\-]?\s*([A-Z0-9][A-Z0-9/\-_.]{2,})"
    CONTRACT_PATTERN = r"(?:contrat|contract|عقد)\s*(?:n[°o]|numero|رقم)?\s*[:\-]?\s*([A-Z0-9][A-Z0-9/\-_.]{2,})"

    ORG_SUFFIXES = ("SARL", "SPA", "EPE", "EPIC", "SONATRACH", "SONELGAZ", "MINISTERE")
    KNOWN_LOCATIONS = {
        "alger",
        "oran",
        "constantine",
        "annaba",
        "blida",
        "setif",
        "tlemcen",
        "paris",
        "marseille",
        "الجزائر",
        "وهران",
        "قسنطينة",
        "عنابة",
    }

    def extract(self, ocr: OCRResult) -> MetadataResult:
        text = ocr.text
        return MetadataResult(
            date=self._extract_date(text),
            organization=self._extract_organization(text),
            archive_number=self._first_group(self.ARCHIVE_PATTERN, text),
            contract_number=self._first_group(self.CONTRACT_PATTERN, text),
            amounts=self._unique(re.findall(self.MONEY_PATTERN, text, flags=re.IGNORECASE)),
            people=self._extract_people(text),
            locations=self._extract_locations(text),
            raw={"language": ocr.language, "ocr_confidence": ocr.confidence},
        )

    def _extract_date(self, text: str) -> str | None:
        for pattern in self.DATE_PATTERNS:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                value = match.group(0)
                try:
                    return parser.parse(value, dayfirst=True, fuzzy=True).date().isoformat()
                except (ValueError, OverflowError):
                    return value
        year_match = re.search(r"\b(18|19|20)\d{2}\b", text)
        return year_match.group(0) if year_match else None

    def _extract_organization(self, text: str) -> str | None:
        uppercase_candidates = re.findall(r"\b[A-Z][A-Z&.'\- ]{2,}\b", text)
        scored: Counter[str] = Counter()
        for candidate in uppercase_candidates:
            normalized = " ".join(candidate.split())
            if any(suffix in normalized for suffix in self.ORG_SUFFIXES):
                scored[normalized] += 3
            elif len(normalized.split()) <= 5:
                scored[normalized] += 1
        if scored:
            return scored.most_common(1)[0][0]
        match = re.search(r"(?:organisation|organisme|societe|company)\s*[:\-]\s*(.+)", text, re.IGNORECASE)
        return match.group(1).strip()[:200] if match else None

    def _extract_people(self, text: str) -> list[str]:
        french_names = re.findall(r"\b(?:M\.|Mme|Monsieur|Madame)\s+([A-Z][A-Za-z'\-]+(?:\s+[A-Z][A-Za-z'\-]+){0,3})", text)
        arabic_names = re.findall(r"(?:السيد|السيدة)\s+([\u0600-\u06ff ]{3,40})", text)
        return self._unique([*french_names, *[name.strip() for name in arabic_names]])

    def _extract_locations(self, text: str) -> list[str]:
        lowered = text.lower()
        found = [location for location in self.KNOWN_LOCATIONS if location.lower() in lowered]
        city_matches = re.findall(r"\b(?:a|ville de|wilaya de)\s+([A-Z][A-Za-z'\-]+)\b", text)
        return self._unique([*found, *city_matches])

    @staticmethod
    def _first_group(pattern: str, text: str) -> str | None:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        return match.group(1).strip() if match else None

    @staticmethod
    def _unique(values: list[str]) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()
        for value in values:
            normalized = " ".join(value.split()).strip(" .,:;-")
            key = normalized.lower()
            if normalized and key not in seen:
                seen.add(key)
                result.append(normalized)
        return result
