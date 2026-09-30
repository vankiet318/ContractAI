from pathlib import Path

import torch
from huggingface_hub import hf_hub_download
from sentence_transformers import SentenceTransformer

from .base import EmbeddingModel, SparseEmbedding, SparseEmbeddingModel

SPARSE_HEAD_FILENAME = "sparse_linear.pt"


class BGEM3Embedding(EmbeddingModel, SparseEmbeddingModel):
    """
    Dense + sparse embeddings from a single BGE-M3 forward pass.

    Dense: the model's sentence embedding (CLS pooling), normalized.

    Sparse: relu(sparse_linear(hidden state)) for every token, keeping
    the max weight per token id and dropping special tokens. This is the
    same "lexical weights" output as FlagEmbedding's BGEM3FlagModel; the
    sparse_linear head ships in the BAAI/bge-m3 repo.
    """

    def __init__(
        self,
        model_name: str,
        device: str = "cpu",
        batch_size: int = 32,
    ):
        self.model = SentenceTransformer(
            model_name,
            device=device,
        )

        self.batch_size = batch_size

        self.sparse_head = self._load_sparse_head(model_name)

        self.special_token_ids = set(
            self.model.tokenizer.all_special_ids
        )

    def embed(
        self,
        texts: list[str],
    ) -> list[list[float]]:

        dense, _ = self.embed_hybrid(texts)

        return dense

    def embed_sparse(
        self,
        texts: list[str],
    ) -> list[SparseEmbedding]:

        _, sparse = self.embed_hybrid(texts)

        return sparse

    def embed_hybrid(
        self,
        texts: list[str],
    ) -> tuple[list[list[float]], list[SparseEmbedding]]:

        dense: list[list[float]] = []
        sparse: list[SparseEmbedding] = []

        for start in range(0, len(texts), self.batch_size):

            batch_dense, batch_sparse = self._encode_batch(
                texts[start:start + self.batch_size]
            )

            dense.extend(batch_dense)
            sparse.extend(batch_sparse)

        return dense, sparse

    def _encode_batch(
        self,
        texts: list[str],
    ) -> tuple[list[list[float]], list[SparseEmbedding]]:

        features = {
            name: value.to(self.model.device)
            for name, value in self.model.tokenize(texts).items()
        }

        with torch.inference_mode():
            output = self.model(features)

            dense = torch.nn.functional.normalize(
                output["sentence_embedding"],
                dim=-1,
            )

            token_weights = torch.relu(
                self.sparse_head(output["token_embeddings"])
            ).squeeze(-1)

        sparse = [
            self._to_sparse(token_ids, weights, mask)
            for token_ids, weights, mask in zip(
                features["input_ids"].tolist(),
                token_weights.tolist(),
                features["attention_mask"].tolist(),
            )
        ]

        return dense.cpu().tolist(), sparse

    def _to_sparse(
        self,
        token_ids: list[int],
        weights: list[float],
        mask: list[int],
    ) -> SparseEmbedding:

        best: dict[int, float] = {}

        for token_id, weight, keep in zip(token_ids, weights, mask):

            if not keep or token_id in self.special_token_ids:
                continue

            if weight > best.get(token_id, 0.0):
                best[token_id] = weight

        return SparseEmbedding(
            indices=list(best.keys()),
            values=list(best.values()),
        )

    def _load_sparse_head(
        self,
        model_name: str,
    ) -> torch.nn.Linear:

        local_path = Path(model_name) / SPARSE_HEAD_FILENAME

        path = (
            local_path
            if local_path.is_file()
            else hf_hub_download(
                repo_id=model_name,
                filename=SPARSE_HEAD_FILENAME,
            )
        )

        hidden_size = self.model[0].auto_model.config.hidden_size

        head = torch.nn.Linear(hidden_size, 1)

        head.load_state_dict(
            torch.load(
                path,
                map_location="cpu",
                weights_only=True,
            )
        )

        return head.to(self.model.device).eval()
