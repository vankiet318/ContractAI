from dataclasses import dataclass

from app.retrieval.models import RetrievalResult


SNIPPET_LENGTH = 200


@dataclass
class Citation:
    source_id: str
    chunk_id: str
    document_id: str
    page_start: int
    page_end: int
    section_number: str | None
    section_title: str | None
    text_snippet: str


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
                    document_id=result.document_id,
                    page_start=result.page_start,
                    page_end=result.page_end,
                    section_number=result.section_number,
                    section_title=result.section_title,
                    text_snippet=self._content_snippet(result.text),
                )
            )

        return citations

    @staticmethod
    def _content_snippet(text: str) -> str:
        # AdaptiveChunker prepends "<structural context>\n\n<content>" to
        # every chunk, always separated by exactly one blank line. Snippet
        # must come from the real content, not the repeated section header,
        # or preview highlighting matches the wrong occurrence on the page.
        _, separator, content = text.partition("\n\n")
        body = content if separator else text
        return body[:SNIPPET_LENGTH]