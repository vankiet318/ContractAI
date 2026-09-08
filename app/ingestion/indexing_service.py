from app.embedding.base import EmbeddingModel
from app.ingestion.adaptive_chunker import AdaptiveChunker
from app.ingestion.feature_extractor import FeatureExtractor
from app.ingestion.hierarchy_builder import HierarchyBuilder
from app.ingestion.layout_analyzer import LayoutAnalyzer
from app.ingestion.models import ChunkIdentity
from app.ingestion.pdf_parser import PDFParser
from app.ingestion.schema_inference import SchemaInference
from app.ingestion.structure_detector import StructureDetector
from app.retrieval.bm25_index import BM25Index
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
        embedding_model: EmbeddingModel,
        vector_store: QdrantRepository,
        bm25_index: BM25Index,
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
        self.bm25_index = bm25_index

    def index(
        self,
        file_path: str,
        document_id: str,
        session_id: str,
    ) -> int:

        # 1. Parse PDF
        blocks = self.parser.parse(
            file_path
        )

        if not blocks:
            return 0

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
        chunks = self.chunker.chunk(
            roots=tree,
            identity=ChunkIdentity(
                document_id=document_id,
                session_id=session_id,
            ),
        )

        if not chunks:
            return 0

        # 8. Generate embeddings
        texts = [
            chunk.text
            for chunk in chunks
        ]

        vectors = self.embedding_model.embed(
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
        )

        # 11. Build BM25 index
        self.bm25_index.build(
            documents=chunks,
        )

        return len(chunks)