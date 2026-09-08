from pathlib import Path

from qdrant_client import QdrantClient

from app.config import (
    ChunkingConfig,
    EmbeddingConfig,
    GeminiConfig,
    QdrantConfig,
    RerankingConfig,
    RetrievalConfig,
    StorageConfig,
)

from app.auth.dependencies import create_get_current_user
from app.auth.repository import UserRepository
from app.auth.service import AuthService

from app.sessions.dependencies import create_get_owned_session
from app.sessions.repository import SessionRepository
from app.sessions.service import SessionService
from app.sessions.deletion_service import SessionDeletionService
from app.sessions.title_generator import SessionTitleGenerator
from app.sessions.title_service import SessionTitleService

from app.messages.repository import ChatMessageRepository
from app.messages.service import ChatMessageService

from app.query.use_case import QuerySessionUseCase

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

from app.documents.deletion_service import DocumentDeletionService
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
from app.api.auth import create_auth_router
from app.api.sessions import create_sessions_router
from app.api.documents import create_documents_router

embedding_config = EmbeddingConfig.from_env()
qdrant_config = QdrantConfig.from_env()
gemini_config = GeminiConfig.from_env()
chunking_config = ChunkingConfig.from_env()
reranking_config = RerankingConfig.from_env()
retrieval_config = RetrievalConfig.from_env()
storage_config = StorageConfig.from_env()

upload_dir = Path(storage_config.upload_dir)
upload_dir.mkdir(parents=True, exist_ok=True)

pdf_parser = PDFParser()
layout_analyzer = LayoutAnalyzer()
feature_extractor = FeatureExtractor()
schema_inference = SchemaInference()
structure_detector = StructureDetector()
hierarchy_builder = HierarchyBuilder()

chunker = AdaptiveChunker(
    max_chars=chunking_config.max_chars,
    overlap_chars=chunking_config.overlap_chars,
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

user_repository = UserRepository()

auth_service = AuthService(
    repository=user_repository,
)

session_repository = SessionRepository()

session_service = SessionService(
    repository=session_repository,
)

document_repository = DocumentRepository()

document_service = DocumentService(
    repository=document_repository,
)

session_deletion_service = SessionDeletionService(
    session_service=session_service,
    document_service=document_service,
    vector_store=vector_store,
    bm25_index=bm25_index,
)

document_deletion_service = DocumentDeletionService(
    document_service=document_service,
    vector_store=vector_store,
    bm25_index=bm25_index,
)

message_repository = ChatMessageRepository()

message_service = ChatMessageService(
    repository=message_repository,
)

get_current_user = create_get_current_user(user_repository)

get_owned_session = create_get_owned_session(
    session_service=session_service,
    get_current_user=get_current_user,
)

dense_retriever = DenseRetriever(
    embedding_model=embedding_model,
    vector_store=vector_store,
)

bm25_retriever = BM25Retriever(
    index=bm25_index,
)


rrf = RRFFusion(k=retrieval_config.rrf_k)

hybrid_retriever = HybridRetriever(
    dense_retriever=dense_retriever,
    bm25_retriever=bm25_retriever,
    rrf=rrf,
)


reranker_model = CrossEncoderReranker(
    model_name=reranking_config.model_name,
    device=reranking_config.device,
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

session_title_generator = SessionTitleGenerator(llm=gemini_client)

session_title_service = SessionTitleService(
    session_service=session_service,
    title_generator=session_title_generator,
)

query_use_case = QuerySessionUseCase(
    document_service=document_service,
    message_service=message_service,
    hybrid_retriever=hybrid_retriever,
    reranking_service=reranking_service,
    context_builder=context_builder,
    prompt_builder=prompt_builder,
    llm=gemini_client,
    citation_builder=citation_builder,
    candidate_limit=retrieval_config.candidate_limit,
    limit=retrieval_config.limit,
)

auth_router = create_auth_router(
    auth_service=auth_service,
)

sessions_router = create_sessions_router(
    session_service=session_service,
    deletion_service=session_deletion_service,
    get_current_user=get_current_user,
)

documents_router = create_documents_router(
    document_service=document_service,
    indexing_service=indexing_service,
    deletion_service=document_deletion_service,
    get_owned_session=get_owned_session,
    upload_dir=upload_dir,
)

query_router = create_query_router(
    query_use_case=query_use_case,
    message_service=message_service,
    title_service=session_title_service,
    get_owned_session=get_owned_session,
)