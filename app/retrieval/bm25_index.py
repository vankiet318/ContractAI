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
                document.session_id
            ].append(document)

        for session_id, chunks in grouped.items():

            all_chunks = (
                self._documents.get(session_id, [])
                + chunks
            )

            tokenized_documents = [
                self._tokenize(chunk.text)
                for chunk in all_chunks
            ]

            self._indexes[session_id] = BM25Okapi(
                tokenized_documents
            )

            self._documents[session_id] = all_chunks

    def delete(self, session_id: str) -> None:
        self._indexes.pop(session_id, None)
        self._documents.pop(session_id, None)

    def delete_document(
        self,
        session_id: str,
        document_id: str,
    ) -> None:

        chunks = self._documents.get(session_id)

        if chunks is None:
            return

        remaining_chunks = [
            chunk
            for chunk in chunks
            if chunk.document_id != document_id
        ]

        if not remaining_chunks:
            self.delete(session_id)
            return

        tokenized_documents = [
            self._tokenize(chunk.text)
            for chunk in remaining_chunks
        ]

        self._indexes[session_id] = BM25Okapi(
            tokenized_documents
        )

        self._documents[session_id] = remaining_chunks

    def search(
        self,
        query: str,
        session_id: str,
        limit: int = 5,
    ) -> list[tuple[DocumentChunk, float]]:

        bm25 = self._indexes.get(session_id)

        if bm25 is None:
            return []

        documents = self._documents[session_id]

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