Production-ready pipeline for Arabic and French archive digitization.

## Stack

- FastAPI backend
- PaddleOCR for Arabic/French OCR
- Heuristic layout analysis with optional Qwen2.5-VL classification through Ollama
- BAAI/bge-m3 embeddings
- Qdrant vector database
- PostgreSQL document registry
- Qwen2.5:3B through Ollama for grounded RAG answers
- Streamlit frontend
- Docker Compose orchestration

## Quick Start

```bash
cp .env.example .env
docker compose up --build
```

Services:

- API: http://localhost:8000
- API docs: http://localhost:8000/docs
- Streamlit: http://localhost:8501
- Qdrant: http://localhost:6333
- Ollama: http://localhost:11434

The `ollama-init` service pulls `qwen2.5:3b` automatically.

## API

Upload a file:

```bash
curl -F "file=@sample.pdf" http://localhost:8000/upload
```

Process it:

```bash
curl -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -d '{"document_id":1}'
```

Ask the archive:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"Show me all contracts signed in 1985 mentioning Sonatrach","top_k":5}'
```

## Project Structure

```text
project/
├── app/
│   ├── database/
│   ├── models/
│   ├── rag/
│   ├── routers/
│   └── services/
├── frontend/
├── tests/
├── scripts/
├── docker/
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## Environment Variables

See `.env.example`.

Important values:

- `DATABASE_URL`
- `QDRANT_URL`
- `QDRANT_COLLECTION`
- `OLLAMA_BASE_URL`
- `OLLAMA_MODEL`
- `EMBEDDING_MODEL`
- `UPLOAD_DIR`
- `CHUNK_SIZE`
- `CHUNK_OVERLAP`

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
uvicorn app.main:app --reload
streamlit run frontend/streamlit_app.py
```

For local development outside Docker, run PostgreSQL, Qdrant, and Ollama locally or update `.env`.
