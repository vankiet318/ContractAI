# ContractAI

RAG system for Vietnamese contract PDFs: upload a contract, ask questions, get answers with page/section citations.

## How it works

- **Ingestion:** parse PDF → detect sections ("Điều 3", "1.2", "a)") → chunk (~1500 chars) → embed with BGE-M3 → store in Qdrant.
- **Query:** hybrid dense + sparse search → RRF fusion → cross-encoder rerank → Gemini answers from top chunks, streamed over SSE.
- Off-topic questions get a fixed reply with no LLM call. Most are caught right after embedding the question (`RETRIEVAL_TOPIC_MIN_MARGIN`, no search or reranking); the rest by `RETRIEVAL_MIN_DENSE_SCORE` / `RERANK_MIN_SCORE`.

## Run locally

Requires Docker Desktop and a Gemini API key.

```
cp .env.example .env                    # set GEMINI_API_KEY and JWT_SECRET_KEY
docker compose up -d --build            # app → http://localhost:8080, API → http://localhost:8000
```

For frontend hot reload, run the Vite dev server instead (it calls the backend on port 8000):

```
cd frontend
cp .env.example .env
npm install && npm run dev              # → http://localhost:5173
```

Migrations run on backend start. The first query is slow while models download.

## Deploy (production)

Requires a server with Docker, ports 80/443 open, and a domain pointing at it. Plan for ~6 GB RAM for the embedding and reranker models.

```
cp .env.example .env                    # also set DOMAIN and POSTGRES_PASSWORD
docker compose -f docker-compose.prod.yml up -d --build   # → https://<DOMAIN>
```

Caddy serves the built frontend, proxies `/api/*` to the backend, and obtains the HTTPS certificate. Qdrant, Postgres and the backend are not exposed outside the Docker network.

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
