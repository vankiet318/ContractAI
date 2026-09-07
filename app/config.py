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