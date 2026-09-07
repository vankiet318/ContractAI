from dataclasses import dataclass

from app.retrieval.models import RetrievalResult


@dataclass
class ContextItem:
    source_id: str
    text: str
    page_start: int
    page_end: int
    section_number: str | None
    section_title: str | None


class ContextBuilder:

    def build(
        self,
        results: list[RetrievalResult],
    ) -> list[ContextItem]:
        context_items = []

        for index, result in enumerate(results, start=1):
            context_items.append(
                ContextItem(
                    source_id=f"Source {index}",
                    text=result.text,
                    page_start=result.page_start,
                    page_end=result.page_end,
                    section_number=result.section_number,
                    section_title=result.section_title,
                )
            )

        return context_items

    def format(self, items: list[ContextItem]) -> str:
        parts = []

        for item in items:
            section = ""

            if item.section_number:
                section = item.section_number

                if item.section_title:
                    section += f". {item.section_title}"

            page = str(item.page_start)

            if item.page_end != item.page_start:
                page = f"{item.page_start}-{item.page_end}"

            parts.append(
                f"[{item.source_id}]\n"
                f"Page: {page}\n"
                f"Section: {section}\n\n"
                f"{item.text}"
            )

        return "\n\n---\n\n".join(parts)