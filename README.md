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

## Running the frontend (local)

Requirements: Node.js.

```
cd frontend
npm install
npm run dev
```

Runs on `http://localhost:5173` by default and calls the backend at the URL set in `frontend/.env` (`VITE_API_BASE_URL`, default `http://localhost:8000`).

The backend's CORS configuration (`app/main.py`) currently allows only `http://localhost:5173`; update it if the frontend runs on a different origin.

## Known limitations

- Document metadata (`app/documents/repository.py`) is stored in memory and is lost on backend restart. Vector data in Qdrant persists independently.
- The BM25 index is also in-memory and rebuilt only when a document is (re-)indexed.
- No authentication or per-user data isolation yet; any client that can reach the API can read/query any document.
