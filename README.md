# ContractAI

RAG system for Vietnamese contract PDFs: upload a contract, ask questions, get answers with page/section citations.

## How it works

- **Ingestion:** in the background after upload, parse the PDF, detect its section structure, chunk it, embed the chunks and store them in a vector database.
- **Query:** hybrid search, rerank, then an LLM answers from the most relevant chunks, streamed to the browser. Off-topic questions are filtered out before the LLM is called.

Models, providers, thresholds and other settings are configured through environment variables; `.env.example` lists them all with their defaults and explanations.

## Run locally

Requires Docker Desktop and an API key for at least one supported LLM provider (see `.env.example`).

```
cp .env.example .env                    # fill in the values marked REQUIRED
docker compose up -d --build            # backend services; API → http://localhost:8000
```

The frontend runs separately with the Vite dev server (it calls the backend on port 8000):

```
cd frontend
cp .env.example .env
npm install && npm run dev              # → http://localhost:5173
```

Migrations run on backend start. The first query is slow while models download.

## Deploy (production)

Requires a server with Docker, ports 80/443 open, and a domain pointing at it. The embedding and reranker models run on the server, so plan for several GB of RAM.

```
cp .env.example .env                    # also fill in the production section
docker compose -f docker-compose.prod.yml up -d --build   # → https://<DOMAIN>
```

Caddy serves the built frontend, proxies `/api/*` to the backend, and obtains the HTTPS certificate. Only Caddy is exposed outside the Docker network.

## Admin dashboard

Admins see an extra **Quản trị** button in the sidebar: usage per day (questions asked, documents uploaded), feedback, and every user's activity. The first admin is made from the command line; after that, admins can grant or remove the role from the dashboard.

```
docker compose exec backend python -m app.scripts.set_role <email> admin
```

Days are counted in `USAGE_TIMEZONE` (default `Asia/Ho_Chi_Minh`). The **Log hệ thống** tab shows the latest `LOG_BUFFER_SIZE` server log lines, kept in memory since the last restart; `docker compose logs backend` has the full log.

## Tests

```
pytest
```

## Evaluation

Evaluation scripts live in `app/eval/`. Each one documents its usage and input format:

```
docker compose exec backend python -m app.eval.<script> --help
```
