from qdrant_client import QdrantClient

from app.config import EmbeddingConfig, GeminiConfig, QdrantConfig

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

from app.retrieval.dense_retriever import DenseRetriever
from app.retrieval.bm25_index import BM25Index
from app.retrieval.bm25_retriever import BM25Retriever
from app.retrieval.rrf import RRFFusion
from app.retrieval.hybrid_retriever import HybridRetriever

from app.reranking.cross_encoder import CrossEncoderReranker
from app.reranking.service import RerankingService

from app.generation.context_builder import ContextBuilder
from app.generation.prompt_builder import PromptBuilder
from app.generation.gemini_client import GeminiClient
from app.generation.citation_builder import CitationBuilder

from app.api.query import create_query_router

embedding_config = EmbeddingConfig.from_env()
qdrant_config = QdrantConfig.from_env()
gemini_config = GeminiConfig.from_env()

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

bm25_index = BM25Index()

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
    bm25_index=bm25_index,
)

document_repository = DocumentRepository()

document_service = DocumentService(
    repository=document_repository,
)

dense_retriever = DenseRetriever(
    embedding_model=embedding_model,
    vector_store=vector_store,
)

bm25_retriever = BM25Retriever(
    index=bm25_index,
)


rrf = RRFFusion(k=60)

hybrid_retriever = HybridRetriever(
    dense_retriever=dense_retriever,
    bm25_retriever=bm25_retriever,
    rrf=rrf,
)


reranker_model = CrossEncoderReranker(
    model_name="BAAI/bge-reranker-v2-m3",
    device="cpu",
)

reranking_service = RerankingService(
    reranker=reranker_model,
)

context_builder = ContextBuilder()

prompt_builder = PromptBuilder()

gemini_client = GeminiClient(
    model_name=gemini_config.model_name,
    system_instruction=PromptBuilder.SYSTEM_INSTRUCTION,
    api_key=gemini_config.api_key,
    temperature=gemini_config.temperature,
    max_output_tokens=gemini_config.max_output_tokens,
)

citation_builder = CitationBuilder()

query_router = create_query_router(
    document_repository=document_repository,
    hybrid_retriever=hybrid_retriever,
    reranking_service=reranking_service,
    context_builder=context_builder,
    prompt_builder=prompt_builder,
    llm=gemini_client,
    citation_builder=citation_builder,
)