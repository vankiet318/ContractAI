# ContractAI

RAG system for Vietnamese contract PDFs: upload a contract, ask questions, get answers with page/section citations.

## Pipeline

**Ingestion**
1. Parse the PDF into text blocks, detect headings and numbering ("Điều 3", "1.2", "a)"), and build the section hierarchy.
2. Split sections into chunks (~1500 chars, 200 overlap), each prefixed with its section number/title.
3. One BGE-M3 pass per chunk yields a dense vector and a sparse lexical-weight vector, stored in the same Qdrant point.

**Query**
1. One BGE-M3 pass on the question yields both vectors.
2. Dense and sparse search in Qdrant, scoped to the chat session.
3. Fuse the two lists with Reciprocal Rank Fusion (`k = 60`).
4. Rerank the shortlist with a cross-encoder.
5. Gemini answers from the top chunks only; citations are returned alongside.

## Models

- Embedding: `BAAI/bge-m3` (dense + sparse)
- Reranker: `BAAI/bge-reranker-v2-m3`
- LLM: Gemini (`gemini-3.6-flash`)

## Run locally

Requires Docker Desktop and a Gemini API key.

1. Create `.env` with `GEMINI_API_KEY` and `JWT_SECRET_KEY`.
2. Start everything:

```
docker compose up -d --build
```

- Frontend: http://localhost:8080
- Backend: http://localhost:8000

Migrations run automatically on backend start. The first query is slow while models download.

Frontend with hot reload: `cd frontend && npm install && npm run dev` (http://localhost:5173).

## Retrieval evaluation

```
docker compose exec backend python -m app.eval.retrieval run --pdf data/uploads/<id>.pdf --questions data/eval/questions.json
```

Compares `dense`, `sparse`, `dense+sparse`, and `dense+sparse+rerank` (hit@k, recall@k, MRR, nDCG). See `app/eval/retrieval.py` for the question format.
