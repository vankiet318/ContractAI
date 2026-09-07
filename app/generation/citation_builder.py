from dataclasses import dataclass

from app.retrieval.models import RetrievalResult


@dataclass
class Citation:
    source_id: str
    chunk_id: str
    page_start: int
    page_end: int
    section_number: str | None
    section_title: str | None


class CitationBuilder:

    def build(
        self,
        results: list[RetrievalResult],
    ) -> list[Citation]:

        citations = []

        for index, result in enumerate(results, start=1):
            citations.append(
                Citation(
                    source_id=f"Source {index}",
                    chunk_id=result.chunk_id,
                    page_start=result.page_start,
                    page_end=result.page_end,
                    section_number=result.section_number,
                    section_title=result.section_title,
                )
            )

        return citations