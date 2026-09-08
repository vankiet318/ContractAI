import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class EmbeddingConfig:

    model_name: str

    device: str = "cpu"

    batch_size: int = 32

    @classmethod
    def from_env(cls) -> "EmbeddingConfig":
        return cls(
            model_name=os.getenv(
                "EMBEDDING_MODEL_NAME",
                "BAAI/bge-m3",
            ),
            device=os.getenv("EMBEDDING_DEVICE", "cpu"),
            batch_size=int(
                os.getenv("EMBEDDING_BATCH_SIZE", "16")
            ),
        )


@dataclass
class QdrantConfig:

    url: str

    collection_name: str

    @classmethod
    def from_env(cls) -> "QdrantConfig":
        return cls(
            url=os.getenv(
                "QDRANT_URL",
                "http://localhost:6333",
            ),
            collection_name=os.getenv(
                "QDRANT_COLLECTION_NAME",
                "contracts",
            ),
        )


@dataclass
class PostgresConfig:

    database_url: str

    @classmethod
    def from_env(cls) -> "PostgresConfig":
        return cls(
            database_url=os.getenv(
                "DATABASE_URL",
                "postgresql+psycopg2://contractai:contractai@localhost:5432/contractai",
            ),
        )


@dataclass
class AuthConfig:

    secret_key: str

    algorithm: str = "HS256"

    access_token_expire_minutes: int = 60

    @classmethod
    def from_env(cls) -> "AuthConfig":
        return cls(
            secret_key=os.getenv(
                "JWT_SECRET_KEY",
                "insecure-dev-secret-change-me",
            ),
            algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
            access_token_expire_minutes=int(
                os.getenv("JWT_EXPIRE_MINUTES", "60")
            ),
        )


@dataclass
class ChunkingConfig:

    max_chars: int = 1500

    overlap_chars: int = 200

    @classmethod
    def from_env(cls) -> "ChunkingConfig":
        return cls(
            max_chars=int(
                os.getenv("CHUNKING_MAX_CHARS", "1500")
            ),
            overlap_chars=int(
                os.getenv("CHUNKING_OVERLAP_CHARS", "200")
            ),
        )


@dataclass
class RerankingConfig:

    model_name: str = "BAAI/bge-reranker-v2-m3"

    device: str = "cpu"

    @classmethod
    def from_env(cls) -> "RerankingConfig":
        return cls(
            model_name=os.getenv(
                "RERANKER_MODEL_NAME",
                "BAAI/bge-reranker-v2-m3",
            ),
            device=os.getenv("RERANKER_DEVICE", "cpu"),
        )


@dataclass
class RetrievalConfig:

    candidate_limit: int = 20

    limit: int = 20

    rrf_k: int = 60

    @classmethod
    def from_env(cls) -> "RetrievalConfig":
        return cls(
            candidate_limit=int(
                os.getenv("RETRIEVAL_CANDIDATE_LIMIT", "20")
            ),
            limit=int(
                os.getenv("RETRIEVAL_LIMIT", "20")
            ),
            rrf_k=int(
                os.getenv("RETRIEVAL_RRF_K", "60")
            ),
        )


@dataclass
class StorageConfig:

    upload_dir: str = "data/uploads"

    @classmethod
    def from_env(cls) -> "StorageConfig":
        return cls(
            upload_dir=os.getenv(
                "UPLOAD_DIR",
                "data/uploads",
            ),
        )


@dataclass
class GeminiConfig:

    api_key: str | None

    model_name: str = "gemini-3.6-flash"

    temperature: float = 0.2

    max_output_tokens: int = 4096

    @classmethod
    def from_env(cls) -> "GeminiConfig":
        return cls(
            api_key=os.getenv("GEMINI_API_KEY"),
            model_name=os.getenv(
                "GEMINI_MODEL_NAME",
                "gemini-3.6-flash",
            ),
            temperature=float(
                os.getenv("GEMINI_TEMPERATURE", "0.2")
            ),
            max_output_tokens=int(
                os.getenv("GEMINI_MAX_OUTPUT_TOKENS", "4096")
            ),
        )