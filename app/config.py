from functools import lru_cache
from pathlib import Path

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Archive Digitization RAG"
    app_env: str = "development"
    log_level: str = "INFO"

    database_url: str = "postgresql+psycopg2://archive:archive@localhost:5432/archive"
    qdrant_url: AnyHttpUrl = "http://localhost:6333"
    qdrant_collection: str = "archive_documents"

    ollama_base_url: AnyHttpUrl = "http://localhost:11434"
    ollama_model: str = "qwen2.5:3b"
    ollama_vision_model: str | None = None

    embedding_model: str = "BAAI/bge-m3"
    embedding_device: str = "cpu"
    embedding_batch_size: int = 8

    upload_dir: Path = Path("storage/uploads")
    max_upload_mb: int = 100
    chunk_size: int = Field(default=1000, ge=200)
    chunk_overlap: int = Field(default=200, ge=0)
    retrieval_top_k: int = Field(default=5, ge=1, le=20)

    api_base_url: AnyHttpUrl = "http://localhost:8000"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    return settings
