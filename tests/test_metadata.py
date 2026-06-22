from app.schemas import OCRResult
from app.services.metadata_service import MetadataService


def test_extract_contract_metadata() -> None:
    text = "CONTRAT N: CNT-1985-77\nSONATRACH\nAlger le 12/05/1985\nMontant 12 000 DA\nMonsieur Ahmed Benali"
    result = MetadataService().extract(OCRResult(text=text, language="fr", confidence=0.9, blocks=[]))

    assert result.date == "1985-05-12"
    assert result.organization == "SONATRACH"
    assert result.contract_number == "CNT-1985-77"
    assert "12 000 DA" in result.amounts
    assert "Ahmed Benali" in result.people
