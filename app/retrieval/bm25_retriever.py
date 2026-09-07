from app.retrieval.bm25_index import BM25Index
from app.retrieval.models import RetrievalResult


class BM25Retriever:

    def __init__(
        self,
        index: BM25Index,
    ):
        self.index = index

    def retrieve(
        self,
        query: str,
        document_id: str,
        limit: int = 5,
    ) -> list[RetrievalResult]:

        results = self.index.search(
            query=query,
            document_id=document_id,
            limit=limit,
        )

        return [
            RetrievalResult(
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                text=chunk.text,
                score=score,
                page_start=chunk.page_start,
                page_end=chunk.page_end,
                section_number=chunk.section_number,
                section_title=chunk.section_title,
                metadata=chunk.metadata,
            )
            for chunk, score in results
        ]