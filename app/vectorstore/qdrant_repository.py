from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    ScoredPoint,
    VectorParams,
)

from app.ingestion.models import DocumentChunk


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

        collections = (
            self.client.get_collections()
        )

        existing = {
            collection.name
            for collection in collections.collections
        }

        if self.collection_name in existing:
            return

        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE,
            ),
        )

    def upsert(
        self,
        chunks: list[DocumentChunk],
        vectors: list[list[float]],
    ) -> None:

        if len(chunks) != len(vectors):
            raise ValueError(
                "Number of chunks and vectors must match"
            )

        points = []

        for chunk, vector in zip(
            chunks,
            vectors,
        ):

            payload = {
                "chunk_id": chunk.chunk_id,
                "document_id": chunk.document_id,
                "workspace_id": chunk.workspace_id,
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
                    vector=vector,
                    payload=payload,
                )
            )

        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
        )

    def search(
        self,
        vector: list[float],
        limit: int = 5,
        document_id: str | None = None,
        workspace_id: str | None = None,
    ) -> list[ScoredPoint]:

        query_filter = self._build_filter(
            document_id=document_id,
            workspace_id=workspace_id,
        )

        results = self.client.query_points(
            collection_name=self.collection_name,
            query=vector,
            query_filter=query_filter,
            limit=limit,
            with_payload=True,
        )
        return results.points

    @staticmethod
    def _build_filter(
        document_id: str | None = None,
        workspace_id: str | None = None,
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

        if workspace_id is not None:
            conditions.append(
                FieldCondition(
                    key="workspace_id",
                    match=MatchValue(
                        value=workspace_id
                    ),
                )
            )

        if not conditions:
            return None

        return Filter(
            must=conditions
        )