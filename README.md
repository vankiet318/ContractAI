# ContractAI

RAG system for querying Vietnamese contract PDFs. Upload a contract, ask questions in natural language, get answers grounded in the document with page/section citations.

## Architecture

The system follows a pipeline of independent, single-responsibility stages, wired together in `app/dependencies.py` (composition root).

### Ingestion pipeline (`app/ingestion/`)

1. `pdf_parser.py` - extracts text blocks from PDF via PyMuPDF, preserving font/position metadata.
2. `layout_analyzer.py` - detects headers/footers and layout structure.
3. `feature_extractor.py` - extracts structural features per block (numbering, heading likelihood, font style).
4. `schema_inference.py` - infers the document's numbering/heading schema.
5. `structure_detector.py` - converts features into structural nodes (headings + body text).
6. `hierarchy_builder.py` - builds a hierarchical tree from flat structural nodes.
7. `adaptive_chunker.py` - splits the tree into retrieval-sized chunks, preserving structural context (section number/title) in each chunk.

Chunks are embedded (`app/embedding/`) and stored in Qdrant (`app/vectorstore/`), with a parallel BM25 index (`app/retrieval/bm25_index.py`) built in memory.

### Retrieval and generation (`app/retrieval/`, `app/reranking/`, `app/generation/`)

1. `dense_retriever.py` - semantic search against Qdrant using the query embedding.
2. `bm25_retriever.py` - keyword search against the in-memory BM25 index.
3. `rrf.py` - fuses dense and BM25 results via Reciprocal Rank Fusion (`hybrid_retriever.py`).
4. `reranking/cross_encoder.py` - reranks fused candidates with a cross-encoder model.
5. `generation/context_builder.py` + `prompt_builder.py` - build the LLM prompt from top-ranked chunks.
6. `generation/gemini_client.py` - calls Gemini to generate the answer.
7. `generation/citation_builder.py` - maps the ranked chunks used as context to citation metadata (page range, section) returned to the client.

### API (`app/api/`)

- `documents.py` - upload a PDF (`POST /documents`, runs the full ingestion pipeline synchronously and returns the final status), list documents (`GET /documents`), get one document (`GET /documents/{id}`).
- `query.py` - ask a question about a ready document (`POST /documents/{id}/query`), returns the answer plus citations.

### Frontend (`frontend/`)

React + TypeScript + Vite + Tailwind. Document list with upload, and a per-document chat panel with streaming-style markdown rendering and citation display.

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
