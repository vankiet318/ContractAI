from qdrant_client import QdrantClient

from app.config import EmbeddingConfig, QdrantConfig

from app.ingestion.pdf_parser import PDFParser
from app.ingestion.layout_analyzer import LayoutAnalyzer
from app.ingestion.feature_extractor import FeatureExtractor
from app.ingestion.schema_inference import SchemaInference
from app.ingestion.structure_detector import StructureDetector
from app.ingestion.hierarchy_builder import HierarchyBuilder
from app.ingestion.adaptive_chunker import AdaptiveChunker
from app.ingestion.indexing_service import DocumentIndexingService

from app.embedding.sentence_transformer import SentenceTransformerEmbedding
from app.vectorstore.qdrant_repository import QdrantRepository

from app.documents.repository import DocumentRepository
from app.documents.service import DocumentService


embedding_config = EmbeddingConfig.from_env()
qdrant_config = QdrantConfig.from_env()

pdf_parser = PDFParser()
layout_analyzer = LayoutAnalyzer()
feature_extractor = FeatureExtractor()
schema_inference = SchemaInference()
structure_detector = StructureDetector()
hierarchy_builder = HierarchyBuilder()

chunker = AdaptiveChunker(
    max_chars=1500,
    overlap_chars=200,
)

embedding_model = SentenceTransformerEmbedding(
    model_name=embedding_config.model_name,
    device=embedding_config.device,
    batch_size=embedding_config.batch_size,
)

qdrant_client = QdrantClient(url=qdrant_config.url)

vector_store = QdrantRepository(
    client=qdrant_client,
    collection_name=qdrant_config.collection_name,
)

indexing_service = DocumentIndexingService(
    parser=pdf_parser,
    layout_analyzer=layout_analyzer,
    feature_extractor=feature_extractor,
    schema_inference=schema_inference,
    structure_detector=structure_detector,
    hierarchy_builder=hierarchy_builder,
    chunker=chunker,
    embedding_model=embedding_model,
    vector_store=vector_store,
)

document_repository = DocumentRepository()

document_service = DocumentService(
    repository=document_repository,
)
