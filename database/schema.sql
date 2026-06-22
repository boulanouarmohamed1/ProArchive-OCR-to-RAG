CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(512) NOT NULL,
    file_path VARCHAR(1024) NOT NULL,
    language VARCHAR(16),
    document_type VARCHAR(128),
    upload_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata_json JSONB,
    ocr_text TEXT
);

CREATE INDEX IF NOT EXISTS ix_documents_id ON documents (id);
CREATE INDEX IF NOT EXISTS ix_documents_upload_date ON documents (upload_date DESC);
CREATE INDEX IF NOT EXISTS ix_documents_language ON documents (language);
CREATE INDEX IF NOT EXISTS ix_documents_document_type ON documents (document_type);
