from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    FilterSelector,
    MatchValue,
    PayloadSchemaType,
    PointStruct,
    ScoredPoint,
    SparseVector,
    SparseVectorParams,
    VectorParams,
)

from app.embedding.base import SparseEmbedding
from app.ingestion.models import DocumentChunk

DENSE_VECTOR = "dense"
SPARSE_VECTOR = "sparse"


class QdrantRepository:

    def __init__(
        self,
        client: QdrantClient,
        collection_name: str,
    ):
        self.client = client
        self.collection_name = collection_name

    def create_collection(
        self,
        vector_size: int,
    ) -> None:

        if self.client.collection_exists(self.collection_name):
            self._ensure_hybrid_schema()
            return

        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config={
                DENSE_VECTOR: VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE,
                ),
            },
            sparse_vectors_config={
                SPARSE_VECTOR: SparseVectorParams(),
            },
        )

        self.client.create_payload_index(
            collection_name=self.collection_name,
            field_name="session_id",
            field_schema=PayloadSchemaType.KEYWORD,
        )

    def delete_collection(self) -> None:
        if self.client.collection_exists(self.collection_name):
            self.client.delete_collection(self.collection_name)

    def upsert(
        self,
        chunks: list[DocumentChunk],
        vectors: list[list[float]],
        sparse_vectors: list[SparseEmbedding],
    ) -> None:

        if not (len(chunks) == len(vectors) == len(sparse_vectors)):
            raise ValueError(
                "Number of chunks and vectors must match"
            )

        points = []

        for chunk, vector, sparse_vector in zip(
            chunks,
            vectors,
            sparse_vectors,
        ):

            payload = {
                "chunk_id": chunk.chunk_id,
                "document_id": chunk.document_id,
                "session_id": chunk.session_id,
                "text": chunk.text,

                "page_start": chunk.page_start,
                "page_end": chunk.page_end,

                "section_number": (
                    chunk.section_number
                ),
                "section_title": (
                    chunk.section_title
                ),

                "parent_number": (
                    chunk.parent_number
                ),
                "parent_title": (
                    chunk.parent_title
                ),

                "structure_path": (
                    chunk.structure_path
                ),

                "chunk_index": (
                    chunk.chunk_index
                ),

                "metadata": chunk.metadata,
            }

            points.append(
                PointStruct(
                    id=chunk.chunk_id,
                    vector={
                        DENSE_VECTOR: vector,
                        SPARSE_VECTOR: SparseVector(
                            indices=sparse_vector.indices,
                            values=sparse_vector.values,
                        ),
                    },
                    payload=payload,
                )
            )

        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
        )

    def search_dense(
        self,
        vector: list[float],
        limit: int = 5,
        document_id: str | None = None,
        session_id: str | None = None,
    ) -> list[ScoredPoint]:

        return self._search(
            query=vector,
            using=DENSE_VECTOR,
            limit=limit,
            document_id=document_id,
            session_id=session_id,
        )

    def search_sparse(
        self,
        vector: SparseEmbedding,
        limit: int = 5,
        document_id: str | None = None,
        session_id: str | None = None,
    ) -> list[ScoredPoint]:

        if not vector.indices:
            return []

        return self._search(
            query=SparseVector(
                indices=vector.indices,
                values=vector.values,
            ),
            using=SPARSE_VECTOR,
            limit=limit,
            document_id=document_id,
            session_id=session_id,
        )

    def _search(
        self,
        query: list[float] | SparseVector,
        using: str,
        limit: int,
        document_id: str | None,
        session_id: str | None,
    ) -> list[ScoredPoint]:

        query_filter = self._build_filter(
            document_id=document_id,
            session_id=session_id,
        )

        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query,
            using=using,
            query_filter=query_filter,
            limit=limit,
            with_payload=True,
        )
        return results.points

    def _ensure_hybrid_schema(self) -> None:

        params = self.client.get_collection(
            self.collection_name
        ).config.params

        vectors = params.vectors
        sparse_vectors = params.sparse_vectors or {}

        if (
            isinstance(vectors, dict)
            and DENSE_VECTOR in vectors
            and SPARSE_VECTOR in sparse_vectors
        ):
            return

        raise RuntimeError(
            f"Qdrant collection '{self.collection_name}' uses the old "
            "dense-only schema. Rebuild it with: "
            "python -m app.scripts.reindex"
        )

    def delete_by_session(self, session_id: str) -> None:
        self._delete_by_field("session_id", session_id)

    def delete_by_document(self, document_id: str) -> None:
        self._delete_by_field("document_id", document_id)

    def _delete_by_field(self, field_name: str, value: str) -> None:
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=FilterSelector(
                filter=Filter(
                    must=[
                        FieldCondition(
                            key=field_name,
                            match=MatchValue(value=value),
                        )
                    ]
                )
            ),
        )

    @staticmethod
    def _build_filter(
        document_id: str | None = None,
        session_id: str | None = None,
    ) -> Filter | None:

        conditions = []

        if document_id is not None:
            conditions.append(
                FieldCondition(
                    key="document_id",
                    match=MatchValue(
                        value=document_id
                    ),
                )
            )

        if session_id is not None:
            conditions.append(
                FieldCondition(
                    key="session_id",
                    match=MatchValue(
                        value=session_id
                    ),
                )
            )

        if not conditions:
            return None

        return Filter(
            must=conditions
        )