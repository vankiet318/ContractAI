from dataclasses import dataclass
from typing import Any


@dataclass
class RetrievalResult:
    chunk_id: str
    document_id: str

    text: str
    score: float

    page_start: int
    page_end: int

    section_number: str | None
    section_title: str | None

    metadata: dict[str, Any]