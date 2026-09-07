import os
from dataclasses import dataclass


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