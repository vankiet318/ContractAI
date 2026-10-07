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


# HS256 needs a key of at least 256 bits to resist brute force.
MIN_JWT_SECRET_LENGTH = 32


@dataclass
class AuthConfig:

    secret_key: str

    algorithm: str = "HS256"

    access_token_expire_minutes: int = 60

    max_failed_logins: int = 5

    lockout_minutes: int = 15

    @classmethod
    def from_env(cls) -> "AuthConfig":
        return cls(
            secret_key=read_jwt_secret(),
            algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
            access_token_expire_minutes=int(
                os.getenv("JWT_EXPIRE_MINUTES", "60")
            ),
            max_failed_logins=int(
                os.getenv("AUTH_MAX_FAILED_LOGINS", "5")
            ),
            lockout_minutes=int(
                os.getenv("AUTH_LOCKOUT_MINUTES", "15")
            ),
        )


def read_jwt_secret() -> str:
    # No fallback: a guessable default would let anyone forge tokens.
    secret = os.getenv("JWT_SECRET_KEY", "")

    if len(secret) < MIN_JWT_SECRET_LENGTH:
        raise RuntimeError(
            f"JWT_SECRET_KEY must be set to at least "
            f"{MIN_JWT_SECRET_LENGTH} characters"
        )

    return secret


@dataclass
class RateLimitConfig:

    login_per_minute: int = 10

    register_per_hour: int = 5

    query_per_minute: int = 20

    @classmethod
    def from_env(cls) -> "RateLimitConfig":
        return cls(
            login_per_minute=int(
                os.getenv("RATE_LIMIT_LOGIN_PER_MINUTE", "10")
            ),
            register_per_hour=int(
                os.getenv("RATE_LIMIT_REGISTER_PER_HOUR", "5")
            ),
            query_per_minute=int(
                os.getenv("RATE_LIMIT_QUERY_PER_MINUTE", "20")
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

    # Chunks scoring below this (sigmoid, 0-1) are treated as unrelated to
    # the question. Not yet calibrated on labeled data.
    min_score: float = 0.05

    @classmethod
    def from_env(cls) -> "RerankingConfig":
        return cls(
            model_name=os.getenv(
                "RERANKER_MODEL_NAME",
                "BAAI/bge-reranker-v2-m3",
            ),
            device=os.getenv("RERANKER_DEVICE", "cpu"),
            min_score=float(
                os.getenv("RERANK_MIN_SCORE", "0.05")
            ),
        )


@dataclass
class RetrievalConfig:

    candidate_limit: int = 20

    limit: int = 20

    rrf_k: int = 60

    # Cosine pre-filter applied before reranking; 0 disables it until it
    # is calibrated with `python -m app.eval.retrieval calibrate`.
    min_dense_score: float = 0.0

    # Off-topic gate on the question alone (see AnchorTopicGate); -1
    # disables it.
    topic_min_margin: float = -0.02

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
            min_dense_score=float(
                os.getenv("RETRIEVAL_MIN_DENSE_SCORE", "0")
            ),
            topic_min_margin=float(
                os.getenv("RETRIEVAL_TOPIC_MIN_MARGIN", "-0.02")
            ),
        )


@dataclass
class StorageConfig:

    upload_dir: str = "data/uploads"

    max_upload_mb: int = 20

    @classmethod
    def from_env(cls) -> "StorageConfig":
        return cls(
            upload_dir=os.getenv(
                "UPLOAD_DIR",
                "data/uploads",
            ),
            max_upload_mb=int(
                os.getenv("UPLOAD_MAX_MB", "20")
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