# ContractAI

RAG system for querying Vietnamese contract PDFs. Upload a contract, ask questions in natural language, get answers grounded in the document with page/section citations.

## How it works

### Ingestion (when a PDF is uploaded)

1. Extract raw text blocks from the PDF, keeping font size/style and position for each block.
2. Detect headers/footers and general layout so they don't pollute the content.
3. For each block, compute structural features: does it look like a heading (font size, bold, numbering, short line, etc.), and if it has numbering (e.g. "Dieu 3", "1.2", "a)"), what numbering level does that imply.
4. Infer the document's own numbering/heading conventions from those features (e.g. this document uses "Dieu N" for top-level sections).
5. Walk the blocks in order and turn them into a flat list of nodes: a heading starts a new node, non-heading text is appended as the body of the current node.
6. Build a hierarchy out of that flat list using the numbering level of each node (a level-2 node becomes a child of the nearest preceding level-1 node, and so on).
7. Walk the hierarchy and split it into retrieval-sized chunks: each chunk keeps its section number/title as context, long sections are split by paragraph, then sentence, then raw character count as a fallback, with some character overlap between adjacent chunks so context isn't cut off mid-thought.
8. Embed every chunk and upsert it into the vector database; also index the same chunks into an in-memory keyword (BM25) index.

### Answering a question

1. Embed the question and run a dense (semantic) similarity search against the vector database, scoped to the target document.
2. Run a keyword (BM25) search against the same document's chunks.
3. Fuse both ranked lists into one using Reciprocal Rank Fusion (a chunk's fused score is the sum of `1 / (k + rank)` across the lists it appears in, so it rewards chunks that rank well in either method).
4. Rerank the fused candidates with a cross-encoder that scores the query against each candidate chunk directly (more accurate, but too slow to run over the whole document, hence only applied to the fused shortlist).
5. Take the top-ranked chunks and build a prompt: the chunks as context, the question, and instructions to answer only from that context and say so when the context is insufficient.
6. Send the prompt to the LLM and return its answer to the client, together with citation metadata (page range, section) for each chunk that was used as context.

Document upload and question-answering both happen synchronously within a single HTTP request: the client waits for the full pipeline to finish before getting a response.

## Models

- Embedding: `BAAI/bge-m3` (multilingual dense embeddings, good Vietnamese support).
- Reranker: `BAAI/bge-reranker-v2-m3` (cross-encoder).
- LLM: Gemini (`gemini-3.6-flash` by default), via the free-tier API.

Both embedding and reranker models run on CPU by default and are cached under `~/.cache/huggingface` (mounted as a Docker volume in `docker-compose.yml` so they are not re-downloaded on every rebuild).

## Running the backend (Docker)

Requirements: Docker Desktop, a Gemini API key from [Google AI Studio](https://aistudio.google.com).

1. Copy `.env` and fill in `GEMINI_API_KEY`.
2. Build and start Qdrant and the backend:

```
docker compose up -d --build
```

The backend listens on `http://localhost:8000`. The first request that needs the embedding/reranker models will take longer while they load (or download, on a clean cache volume).

Environment variables (`.env`, at the project root):

| Variable | Default | Description |
|---|---|---|
| `QDRANT_URL` | `http://localhost:6333` | Qdrant endpoint. Overridden to `http://qdrant:6333` inside Docker Compose. |
| `QDRANT_COLLECTION_NAME` | `contracts` | Qdrant collection name. |
| `EMBEDDING_MODEL_NAME` | `BAAI/bge-m3` | Sentence-transformers embedding model. |
| `EMBEDDING_DEVICE` | `cpu` | Device for the embedding model. |
| `EMBEDDING_BATCH_SIZE` | `16` | Batch size for embedding. |
| `GEMINI_API_KEY` | - | Required. Gemini API key. |
| `GEMINI_MODEL_NAME` | `gemini-3.6-flash` | Gemini model used for answer generation. |
| `GEMINI_MAX_OUTPUT_TOKENS` | `4096` | Max output tokens per generation call. |
| `DATABASE_URL` | - | Postgres connection string. Overridden inside Docker Compose. |
| `JWT_SECRET_KEY` | - | Required. Secret used to sign session JWTs. |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm. |
| `JWT_EXPIRE_MINUTES` | `60` | JWT expiry, in minutes. |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:5173` | Comma-separated list of origins allowed to call the API. |

## Running the frontend (local)

Requirements: Node.js.

```
cd frontend
npm install
npm run dev
```

Runs on `http://localhost:5173` by default and calls the backend at the URL set in `frontend/.env` (`VITE_API_BASE_URL`, default `http://localhost:8000`).

The backend's CORS configuration (`app/main.py`) reads allowed origins from `CORS_ALLOWED_ORIGINS` (comma-separated, defaults to `http://localhost:5173`); set it to match wherever the frontend is served.

## Deploying to a Linux server

Requirements on the server: Docker + the Docker Compose plugin, and a domain name pointed at the server's IP (for HTTPS).

1. Clone the repo onto the server and `cd` into it.
2. Copy `.env` (see the variable table above) and fill in `GEMINI_API_KEY`, `JWT_SECRET_KEY`, and set `CORS_ALLOWED_ORIGINS` to the frontend's public origin (e.g. `https://contractai.yourdomain.com`).
3. Export the two build-time variables used by `docker-compose.yml` before building, so the frontend bakes in the right API URL:

```
export CORS_ALLOWED_ORIGINS=https://contractai.yourdomain.com
export VITE_API_BASE_URL=https://api.yourdomain.com
docker compose up -d --build
```

   (Also add both as persistent `KEY=value` lines in a `.env` file at the repo root — Compose reads `.env` automatically, so you don't need to `export` them on every login.)

4. `docker compose up` runs the backend's `entrypoint.sh`, which applies Alembic migrations (`alembic upgrade head`) automatically before starting Uvicorn — no manual migration step needed.
5. All 4 containers (`qdrant`, `postgres`, `backend`, `frontend`) bind only to `127.0.0.1` on the host — they are not reachable from the internet directly. Put a reverse proxy in front to terminate HTTPS and route public traffic:
   - `api.yourdomain.com` → `127.0.0.1:8000` (backend)
   - `contractai.yourdomain.com` → `127.0.0.1:8080` (frontend)

   Install Nginx + Certbot on the host (outside Docker) for this — it's the simplest way to keep certificate renewal working:

   ```
   sudo apt install nginx certbot python3-certbot-nginx
   # add two server blocks (api.yourdomain.com -> :8000, contractai.yourdomain.com -> :8080)
   sudo certbot --nginx -d api.yourdomain.com -d contractai.yourdomain.com
   ```

6. To redeploy after new commits: `git pull && docker compose up -d --build`.

### CI/CD (GitHub Actions)

`.github/workflows/deploy.yml` runs the test suite on every push/PR to `main`, and on a successful push to `main` SSHes into the server and re-deploys (`git pull && docker compose up -d --build`). It expects the server to already have the repo cloned with a working `.env` in place (steps 1–3 above, done once manually).

Add these repository secrets (Settings → Secrets and variables → Actions):

| Secret | Description |
|---|---|
| `DEPLOY_HOST` | Server IP or hostname. |
| `DEPLOY_USER` | SSH user with Docker permissions on the server. |
| `DEPLOY_SSH_KEY` | Private key for that user (add the matching public key to the server's `~/.ssh/authorized_keys`). |
| `DEPLOY_PORT` | SSH port, optional (defaults to `22`). |
| `DEPLOY_PATH` | Absolute path to the cloned repo on the server, e.g. `/home/deploy/ContractAI`. |

## Known limitations

- Document metadata (`app/documents/repository.py`) is stored in memory and is lost on backend restart. Vector data in Qdrant persists independently.
- The BM25 index is also in-memory and rebuilt only when a document is (re-)indexed.
