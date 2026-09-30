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

    @classmethod
    def from_payload(
        cls,
        payload: dict[str, Any],
        score: float,
    ) -> "RetrievalResult":

        return cls(
            chunk_id=payload["chunk_id"],
            document_id=payload["document_id"],
            text=payload["text"],
            score=score,
            page_start=payload["page_start"],
            page_end=payload["page_end"],
            section_number=payload.get(
                "section_number"
            ),
            section_title=payload.get(
                "section_title"
            ),
            metadata=payload.get(
                "metadata",
                {},
            ),
        )
