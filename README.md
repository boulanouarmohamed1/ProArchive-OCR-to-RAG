#                                                 ProArchive: OCR to RAG

ProArchive: OCR to RAG is a document digitization platform designed for historical and administrative archives. It transforms scanned Arabic and French documents into a searchable knowledge base using OCR, semantic embeddings, and Retrieval-Augmented Generation (RAG).

The project automates the complete workflow from document upload and text extraction to intelligent question answering—allowing users to search large collections of archives using natural language instead of manually browsing documents.

---

## Features

- OCR for Arabic and French scanned documents
- Automatic document layout analysis
- Semantic document chunking and indexing
- Vector search powered by Qdrant
- AI-assisted question answering using Retrieval-Augmented Generation (RAG)
- FastAPI REST API
- Streamlit web interface
- PostgreSQL document registry
- Docker-based deployment
  
---

## Tech Stack

### Backend

- FastAPI
- PostgreSQL
- Qdrant
- Docker

### AI Models

- PaddleOCR
- BAAI/bge-m3
- Qwen2.5
- Ollama

### Frontend

- Streamlit


---

## Architecture

```
                Upload Document
                       │
                       ▼
                OCR (PaddleOCR)
                       │
                       ▼
              Layout Analysis
                       │
                       ▼
             Text Chunking Pipeline
                       │
                       ▼
        BGE-M3 Embedding Generation
                       │
                       ▼
              Qdrant Vector Store
                       │
         ┌─────────────┴─────────────┐
         │                           │
         ▼                           ▼
 PostgreSQL Metadata          Semantic Search
                                      │
                                      ▼
                       Qwen2.5 (RAG Answering)
                                      │
                                      ▼
                               User Response
```



## Getting Started

Clone the repository

```bash
git clone https://github.com/your-username/ProArchive-OCR-to-RAG.git
cd ProArchive-OCR-to-RAG
```

Create the environment file

```bash
cp .env.example .env
```

Start all services

```bash
docker compose up --build
```

---

## Available Services

| Service | URL |
|----------|-----|
| FastAPI | http://localhost:8000 |
| API Documentation | http://localhost:8000/docs |
| Streamlit | http://localhost:8501 |
| Qdrant Dashboard | http://localhost:6333 |
| Ollama | http://localhost:11434 |

The Docker setup automatically downloads the required Qwen model during initialization.

---

## API Examples

### Upload a document

```bash
curl -F "file=@sample.pdf" http://localhost:8000/upload
```

### Process the document

```bash
curl -X POST http://localhost:8000/process \
-H "Content-Type: application/json" \
-d '{"document_id":1}'
```

### Query the archive

```bash
curl -X POST http://localhost:8000/chat \
-H "Content-Type: application/json" \
-d '{
      "question":"Show me all contracts signed in 1985 mentioning Sonatrach",
      "top_k":5
    }'
```

---

## Project Structure

```
project/
│
├── app/
│   ├── database/
│   ├── models/
│   ├── rag/
│   ├── routers/
│   └── services/
│
├── frontend/
├── tests/
├── docker/
├── scripts/
│
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## Environment Variables

The application configuration is defined in `.env`.

Some important variables include:

```
DATABASE_URL
QDRANT_URL
QDRANT_COLLECTION
OLLAMA_BASE_URL
OLLAMA_MODEL
EMBEDDING_MODEL
UPLOAD_DIR
CHUNK_SIZE
CHUNK_OVERLAP
```

Refer to `.env.example` for the complete configuration.

---

## Local Development

Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

Run the backend

```bash
uvicorn app.main:app --reload
```

Run the frontend

```bash
streamlit run frontend/streamlit_app.py
```

Run the test suite

```bash
pytest
```

When running outside Docker, make sure PostgreSQL, Qdrant, and Ollama are running locally or update the corresponding values in the `.env` file.

For the Streamlit frontend, `API_BASE_URL` should usually be `http://localhost:8000` when you run the backend on your host machine. The Docker Compose frontend service overrides this to `http://api:8000` inside the container network.

---

## Use Cases

- Historical archive digitization
- Government document management
- Enterprise knowledge retrieval
- Legal and administrative record search
- Research document indexing
- Multilingual document exploration

---

## Future Improvements

- PDF annotation support
- Multi-user authentication
- Hybrid keyword and semantic search
- OCR quality evaluation dashboard
- Batch processing pipeline
- Cloud deployment support

---

## License

This project is intended for educational, research, and production use. 
