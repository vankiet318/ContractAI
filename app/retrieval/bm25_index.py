from collections import defaultdict

from rank_bm25 import BM25Okapi
import re
from app.ingestion.models import DocumentChunk


class BM25Index:

    def __init__(self):
        self._indexes: dict[
            str,
            BM25Okapi,
        ] = {}

        self._documents: dict[
            str,
            list[DocumentChunk],
        ] = {}

    def build(
        self,
        documents: list[DocumentChunk],
    ) -> None:

        if not documents:
            return

        grouped: dict[
            str,
            list[DocumentChunk],
        ] = defaultdict(list)

        for document in documents:
            grouped[
                document.document_id
            ].append(document)

        for document_id, chunks in grouped.items():

            tokenized_documents = [
                self._tokenize(chunk.text)
                for chunk in chunks
            ]

            self._indexes[document_id] = BM25Okapi(
                tokenized_documents
            )

            self._documents[document_id] = chunks

    def search(
        self,
        query: str,
        document_id: str,
        limit: int = 5,
    ) -> list[tuple[DocumentChunk, float]]:

        bm25 = self._indexes.get(document_id)

        if bm25 is None:
            return []

        documents = self._documents[document_id]

        query_tokens = self._tokenize(query)

        scores = bm25.get_scores(query_tokens)

        ranked_indices = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True,
        )[:limit]

        return [
            (
                documents[index],
                float(scores[index]),
            )
            for index in ranked_indices
        ]

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return re.findall(
            r"\w+",
            text.lower(),
            flags=re.UNICODE,
        )