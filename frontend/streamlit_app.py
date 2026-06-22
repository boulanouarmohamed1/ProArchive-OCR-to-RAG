import os
from pathlib import Path
from typing import Any

import requests
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")

st.set_page_config(page_title="Archive Digitization RAG", layout="wide")


def api_post(path: str, **kwargs: Any) -> requests.Response:
    response = requests.post(f"{API_BASE_URL}{path}", timeout=300, **kwargs)
    response.raise_for_status()
    return response


def api_get(path: str) -> requests.Response:
    response = requests.get(f"{API_BASE_URL}{path}", timeout=60)
    response.raise_for_status()
    return response


def render_upload_page() -> None:
    st.title("Archive Upload")
    uploaded = st.file_uploader("Upload JPG, PNG, TIFF, or PDF", type=["jpg", "jpeg", "png", "tif", "tiff", "pdf"])

    if uploaded and st.button("Upload and process", type="primary"):
        try:
            files = {"file": (uploaded.name, uploaded.getvalue(), uploaded.type or "application/octet-stream")}
            upload_response = api_post("/upload", files=files).json()
            document_id = upload_response["document_id"]
            with st.spinner("Running OCR, layout analysis, metadata extraction, embeddings, and indexing..."):
                process_response = api_post("/process", json={"document_id": document_id}).json()
            st.session_state["last_document"] = process_response
            st.success(f"Processed document #{document_id}")
        except requests.RequestException as exc:
            st.error(f"Processing failed: {exc}")

    document = st.session_state.get("last_document")
    if document:
        col_left, col_right = st.columns([1, 1])
        with col_left:
            st.subheader("OCR Text")
            st.text_area("Extracted text", document["ocr"]["text"], height=420)
        with col_right:
            st.subheader("Metadata")
            st.json(document["metadata"])
            st.subheader("Classification")
            st.json(document["classification"])
            st.subheader("Layout")
            st.json(document["layout"])


def render_documents_page() -> None:
    st.title("Documents")
    try:
        documents = api_get("/documents").json()
    except requests.RequestException as exc:
        st.error(f"Could not load documents: {exc}")
        return

    if not documents:
        st.info("No documents indexed yet.")
        return

    for document in documents:
        with st.expander(f"#{document['id']} - {document['filename']}"):
            st.write(f"Language: {document.get('language') or 'unknown'}")
            st.write(f"Type: {document.get('document_type') or 'unknown'}")
            st.json(document.get("metadata_json") or {})
            st.text_area("OCR text", document.get("ocr_text") or "", height=180, key=f"ocr-{document['id']}")


def render_chat_page() -> None:
    st.title("Archive Chat")
    question = st.text_input("Ask a question about the archive", placeholder="Show me all contracts signed in 1985 mentioning Sonatrach")
    top_k = st.slider("Sources", min_value=1, max_value=10, value=5)

    if st.button("Ask", type="primary") and question.strip():
        try:
            with st.spinner("Searching archive and generating grounded answer..."):
                result = api_post("/chat", json={"question": question, "top_k": top_k}).json()
            st.subheader("Answer")
            st.write(result["answer"])
            st.subheader("Sources")
            for source in result.get("sources", []):
                label = f"Document #{source['document_id']} - score {source['score']:.3f}"
                with st.expander(label):
                    st.write(source["text"])
                    st.json(source.get("metadata") or {})
        except requests.RequestException as exc:
            st.error(f"Chat failed: {exc}")


def main() -> None:
    Path("storage/uploads").mkdir(parents=True, exist_ok=True)
    page = st.sidebar.radio("Navigation", ["Upload", "Documents", "Chat"])
    st.sidebar.caption(f"API: {API_BASE_URL}")

    if page == "Upload":
        render_upload_page()
    elif page == "Documents":
        render_documents_page()
    else:
        render_chat_page()


if __name__ == "__main__":
    main()
