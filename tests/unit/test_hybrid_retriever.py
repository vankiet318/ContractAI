from types import SimpleNamespace

from app.embedding.base import SparseEmbedding
from app.retrieval.hybrid_retriever import HybridRetriever
from app.retrieval.models import RetrievalResult
from app.retrieval.rrf import RRFFusion


def make_result(chunk_id: str, score: float) -> RetrievalResult:
    return RetrievalResult(
        chunk_id=chunk_id,
        document_id="doc",
        text=chunk_id,
        score=score,
        page_start=1,
        page_end=1,
        section_number=None,
        section_title=None,
        metadata={},
    )


class FakeEmbedding:

    def __init__(self):
        self.calls = 0

    def embed_hybrid(self, texts):
        self.calls += 1
        return [[1.0]], [SparseEmbedding(indices=[1], values=[1.0])]


class FakeSparseRetriever:

    def __init__(self, results):
        self.results = results
        self.calls = 0

    def search(self, **kwargs):
        self.calls += 1
        return self.results


def build(dense_score: float, min_dense_score: float):
    embedding = FakeEmbedding()
    sparse = FakeSparseRetriever([make_result("s1", 3.0)])

    retriever = HybridRetriever(
        embedding_model=embedding,
        dense_retriever=SimpleNamespace(
            search=lambda **kwargs: [make_result("d1", dense_score)],
        ),
        sparse_retriever=sparse,
        rrf=RRFFusion(),
        min_dense_score=min_dense_score,
    )

    return retriever, embedding, sparse


def test_query_is_embedded_once():
    retriever, embedding, _ = build(dense_score=0.8, min_dense_score=0.0)

    results = retriever.retrieve(query="Điều 12", session_id="s")

    assert embedding.calls == 1
    assert {result.chunk_id for result in results} == {"d1", "s1"}


def test_weak_dense_match_returns_nothing_and_skips_sparse():
    retriever, _, sparse = build(dense_score=0.2, min_dense_score=0.35)

    assert retriever.retrieve(query="Thời tiết hôm nay?", session_id="s") == []
    assert sparse.calls == 0


def test_blank_query_does_not_embed():
    retriever, embedding, _ = build(dense_score=0.8, min_dense_score=0.0)

    assert retriever.retrieve(query="   ", session_id="s") == []
    assert embedding.calls == 0
