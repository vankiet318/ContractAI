# ContractAI

RAG system for Vietnamese contract PDFs: upload a contract, ask questions, get answers with page/section citations.

## Pipeline

**Ingestion**
1. Parse the PDF into text blocks, detect headings and numbering ("Điều 3", "1.2", "a)"), and build the section hierarchy.
2. Split sections into chunks (~1500 chars, 200 overlap), each prefixed with its section number/title.
3. One BGE-M3 pass per chunk yields a dense vector and a sparse lexical-weight vector, stored in the same Qdrant point.

**Query**
1. One BGE-M3 pass on the question yields both vectors.
2. Dense and sparse search in Qdrant, scoped to the chat session. If the best dense match is below `RETRIEVAL_MIN_DENSE_SCORE` (default 0 = off), stop here: the question is off-topic.
3. Fuse the two lists with Reciprocal Rank Fusion (`k = 60`).
4. Rerank the shortlist with a cross-encoder and drop chunks scoring below `RERANK_MIN_SCORE` (default 0.05). If none remain, the question is off-topic.
5. Gemini answers from the top chunks only. The answer is streamed to the client over Server-Sent Events (`citations` → `delta`… → `done` → `title`).

Off-topic questions get a fixed reply: no LLM call, no citations.

## Models

- Embedding: `BAAI/bge-m3` (dense + sparse)
- Reranker: `BAAI/bge-reranker-v2-m3`
- LLM: Gemini (`gemini-3.6-flash`)

## Run locally

Requires Docker Desktop and a Gemini API key.

1. Create `.env` with `GEMINI_API_KEY` and `JWT_SECRET_KEY`.
2. Start Qdrant, Postgres and the backend (http://localhost:8000):

```
docker compose up -d --build
```

3. Start the frontend (http://localhost:5173):

```
cd frontend
npm install
npm run dev
```

Migrations run automatically on backend start. The first query is slow while models download.

## Retrieval evaluation

```
docker compose exec backend python -m app.eval.retrieval run --pdf data/uploads/<id>.pdf --questions data/eval/questions.json
```

Compares `dense`, `sparse`, `dense+sparse`, and `dense+sparse+rerank` (hit@k, recall@k, MRR, nDCG). See `app/eval/retrieval.py` for the question format.

To pick the off-topic thresholds, score the same on-topic questions against a built-in off-topic list:

```
docker compose exec backend python -m app.eval.retrieval calibrate --pdf data/uploads/<id>.pdf --questions data/eval/questions.json
```

It prints `RETRIEVAL_MIN_DENSE_SCORE` / `RERANK_MIN_SCORE` values that block no on-topic question; put them in `.env`.
