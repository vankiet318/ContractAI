# ContractAI

RAG system for Vietnamese contract PDFs: upload a contract, ask questions, get answers with page/section citations.

## How it works

- **Ingestion:** parse PDF → detect sections ("Điều 3", "1.2", "a)") → chunk (~1500 chars) → embed with BGE-M3 → store in Qdrant.
- **Query:** hybrid dense + sparse search → RRF fusion → cross-encoder rerank → Gemini answers from top chunks, streamed over SSE.
- Off-topic questions (below `RETRIEVAL_MIN_DENSE_SCORE` / `RERANK_MIN_SCORE`) get a fixed reply with no LLM call.

## Run locally

Requires Docker Desktop and a Gemini API key.

```
cp .env.example .env                    # set GEMINI_API_KEY and JWT_SECRET_KEY
docker compose up -d --build            # Qdrant, Postgres, backend → http://localhost:8000

cd frontend
cp .env.example .env
npm install && npm run dev              # → http://localhost:5173
```

Migrations run on backend start. The first query is slow while models download.

## Tests

```
pytest
```

## Retrieval evaluation

```
docker compose exec backend python -m app.eval.retrieval run --pdf data/uploads/<id>.pdf --questions data/eval/questions.json
docker compose exec backend python -m app.eval.retrieval calibrate --pdf data/uploads/<id>.pdf --questions data/eval/questions.json
```

`run` compares retrieval modes (hit@k, recall@k, MRR, nDCG). `calibrate` suggests off-topic thresholds to put in `.env`. Question format: `app/eval/retrieval.py`.
