from app.embedding.base import HybridEmbeddingModel
from app.ingestion.adaptive_chunker import AdaptiveChunker
from app.ingestion.feature_extractor import FeatureExtractor
from app.ingestion.hierarchy_builder import HierarchyBuilder
from app.ingestion.layout_analyzer import LayoutAnalyzer
from app.ingestion.models import ChunkIdentity, DocumentChunk
from app.ingestion.pdf_parser import PDFParser
from app.ingestion.schema_inference import SchemaInference
from app.ingestion.structure_detector import StructureDetector
from app.vectorstore.qdrant_repository import QdrantRepository


class DocumentIndexingService:

    def __init__(
        self,
        parser: PDFParser,
        layout_analyzer: LayoutAnalyzer,
        feature_extractor: FeatureExtractor,
        schema_inference: SchemaInference,
        structure_detector: StructureDetector,
        hierarchy_builder: HierarchyBuilder,
        chunker: AdaptiveChunker,
        embedding_model: HybridEmbeddingModel,
        vector_store: QdrantRepository,
    ):
        self.parser = parser
        self.layout_analyzer = layout_analyzer
        self.feature_extractor = feature_extractor
        self.schema_inference = schema_inference
        self.structure_detector = structure_detector
        self.hierarchy_builder = hierarchy_builder
        self.chunker = chunker
        self.embedding_model = embedding_model
        self.vector_store = vector_store

    def index(
        self,
        file_path: str,
        document_id: str,
        session_id: str,
    ) -> int:

        chunks = self.build_chunks(
            file_path=file_path,
            document_id=document_id,
            session_id=session_id,
        )

        self.store_chunks(chunks)

        return len(chunks)

    def build_chunks(
        self,
        file_path: str,
        document_id: str,
        session_id: str,
    ) -> list[DocumentChunk]:

        # 1. Parse PDF
        blocks = self.parser.parse(
            file_path
        )

        if not blocks:
            return []

        # 2. Analyze layout
        blocks = self.layout_analyzer.analyze(
            blocks
        )

        # 3. Extract structural features
        features = self.feature_extractor.extract(
            blocks
        )

        # 4. Infer document schema
        schema = self.schema_inference.infer(
            features
        )

        # 5. Detect structural nodes
        nodes = self.structure_detector.detect(
            features=features,
            schema=schema,
        )

        # 6. Build hierarchy
        tree = self.hierarchy_builder.build(
            nodes
        )

        # 7. Create retrieval chunks
        return self.chunker.chunk(
            roots=tree,
            identity=ChunkIdentity(
                document_id=document_id,
                session_id=session_id,
            ),
        )

    def store_chunks(
        self,
        chunks: list[DocumentChunk],
    ) -> None:

        if not chunks:
            return

        # 8. Generate dense + sparse embeddings (one model pass)
        texts = [
            chunk.text
            for chunk in chunks
        ]

        vectors, sparse_vectors = self.embedding_model.embed_hybrid(
            texts
        )

        # 9. Create Qdrant collection
        vector_size = len(vectors[0])

        self.vector_store.create_collection(
            vector_size=vector_size
        )

        # 10. Store vectors + metadata
        self.vector_store.upsert(
            chunks=chunks,
            vectors=vectors,
            sparse_vectors=sparse_vectors,
        )