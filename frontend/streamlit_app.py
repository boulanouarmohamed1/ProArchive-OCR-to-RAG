from __future__ import annotations

import os
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import requests
from requests import RequestException
import streamlit as st

APP_NAME = "Archive Digitization RAG"
DEFAULT_API_BASE_URL = "http://localhost:8000"
API_BASE_URL = os.getenv("API_BASE_URL", DEFAULT_API_BASE_URL).rstrip("/")
LOCAL_API_BASE_URL = os.getenv("LOCAL_API_BASE_URL", "").rstrip("/")

_ACTIVE_API_BASE_URL = API_BASE_URL

SUGGESTED_QUESTIONS = [
    "Show me CVs that mention ProArchive",
    "Find contracts signed in 1985",
    "Which documents mention Sonatrach?",
]

st.set_page_config(page_title=APP_NAME, layout="wide", initial_sidebar_state="expanded")


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
          --bg: #0b0f14;
          --panel: #151a22;
          --panel-2: #1c2230;
          --panel-3: #232838;
          --text: #f4f6fa;
          --muted: #aab2c5;
          --accent: #ff5b57;
          --accent-2: #ffb84d;
          --border: rgba(255, 255, 255, 0.08);
        }

        .stApp {
          background:
            radial-gradient(circle at top right, rgba(255, 184, 77, 0.08), transparent 24%),
            radial-gradient(circle at bottom left, rgba(255, 91, 87, 0.08), transparent 28%),
            linear-gradient(180deg, #0b0f14 0%, #090c10 100%);
          color: var(--text);
        }

        section.main > div {
          padding-top: 1rem;
          padding-bottom: 2rem;
        }

        [data-testid="stSidebar"] {
          background: linear-gradient(180deg, rgba(21, 26, 34, 0.98), rgba(16, 19, 26, 0.98));
          border-right: 1px solid var(--border);
        }

        [data-testid="stSidebar"] * {
          color: var(--text);
        }

        .hero {
          margin-bottom: 1.5rem;
          padding: 1.2rem 0 0.4rem;
        }

        .eyebrow {
          display: inline-flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.35rem 0.7rem;
          border-radius: 999px;
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid var(--border);
          color: var(--muted);
          font-size: 0.85rem;
          letter-spacing: 0.04em;
          text-transform: uppercase;
          margin-bottom: 0.8rem;
        }

        .hero h1 {
          margin: 0;
          font-size: clamp(2.3rem, 4vw, 4.2rem);
          line-height: 0.98;
          letter-spacing: -0.04em;
        }

        .hero p {
          margin: 0.8rem 0 0;
          max-width: 58rem;
          color: var(--muted);
          font-size: 1.02rem;
          line-height: 1.6;
        }

        .panel {
          background: rgba(21, 26, 34, 0.88);
          border: 1px solid var(--border);
          border-radius: 22px;
          box-shadow: 0 18px 40px rgba(0, 0, 0, 0.22);
          padding: 1.1rem 1.2rem;
        }

        .panel.secondary {
          background: rgba(28, 34, 48, 0.82);
        }

        .panel h3, .panel h4 {
          margin-top: 0;
          margin-bottom: 0.5rem;
        }

        .small-muted {
          color: var(--muted);
          font-size: 0.95rem;
          line-height: 1.55;
        }

        .kpi-row {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
          gap: 0.8rem;
          margin: 1rem 0 1.4rem;
        }

        .kpi {
          background: rgba(255, 255, 255, 0.04);
          border: 1px solid var(--border);
          border-radius: 18px;
          padding: 0.9rem 1rem;
        }

        .kpi .label {
          color: var(--muted);
          font-size: 0.82rem;
          text-transform: uppercase;
          letter-spacing: 0.06em;
          margin-bottom: 0.4rem;
        }

        .kpi .value {
          font-size: 1.5rem;
          font-weight: 700;
          letter-spacing: -0.03em;
        }

        .doc-card {
          background: rgba(255, 255, 255, 0.035);
          border: 1px solid var(--border);
          border-radius: 18px;
          padding: 1rem 1rem 0.8rem;
          margin-bottom: 0.9rem;
        }

        .doc-title {
          font-size: 1.02rem;
          font-weight: 700;
          margin-bottom: 0.3rem;
        }

        .doc-meta {
          color: var(--muted);
          font-size: 0.9rem;
          line-height: 1.5;
        }

        .source-card {
          border-left: 3px solid var(--accent);
          background: rgba(255, 255, 255, 0.04);
          border-radius: 14px;
          padding: 0.85rem 0.9rem;
          margin: 0.55rem 0;
        }

        .source-title {
          font-weight: 600;
          margin-bottom: 0.2rem;
        }

        .source-snippet {
          color: var(--muted);
          font-size: 0.92rem;
          line-height: 1.5;
        }

        .pill-row {
          display: flex;
          flex-wrap: wrap;
          gap: 0.5rem;
          margin: 0.8rem 0 0.2rem;
        }

        .pill {
          display: inline-flex;
          align-items: center;
          padding: 0.45rem 0.7rem;
          border-radius: 999px;
          border: 1px solid var(--border);
          background: rgba(255, 255, 255, 0.04);
          color: var(--text);
          font-size: 0.85rem;
        }

        .streamlit-expanderHeader {
          font-weight: 600;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _candidate_base_urls() -> list[str]:
    candidates = [API_BASE_URL]
    if LOCAL_API_BASE_URL and LOCAL_API_BASE_URL not in candidates:
        candidates.append(LOCAL_API_BASE_URL)
    return candidates


def _api_request(method: str, path: str, **kwargs: Any) -> requests.Response:
    global _ACTIVE_API_BASE_URL

    last_error: Exception | None = None
    for base_url in _candidate_base_urls():
        try:
            response = requests.request(method, f"{base_url}{path}", **kwargs)
            response.raise_for_status()
            _ACTIVE_API_BASE_URL = base_url
            return response
        except RequestException as exc:
            last_error = exc

    assert last_error is not None
    raise last_error


def api_post(path: str, **kwargs: Any) -> requests.Response:
    return _api_request("post", path, timeout=180, **kwargs)


def api_get(path: str) -> requests.Response:
    return _api_request("get", path, timeout=30)


@st.cache_data(ttl=10, show_spinner=False)
def load_documents() -> list[dict[str, Any]]:
    return api_get("/documents").json()


def clear_document_cache() -> None:
    load_documents.clear()


def format_bytes(value: int | None) -> str:
    if value is None:
        return "Unknown size"
    units = ["B", "KB", "MB", "GB"]
    size = float(value)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} {unit}"
        size /= 1024
    return f"{size:.1f} GB"


def humanize_datetime(value: Any) -> str:
    if not value:
        return "Unknown"
    if isinstance(value, datetime):
        dt = value
    else:
        text = str(value).replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(text)
        except ValueError:
            return str(value)
    return dt.strftime("%b %d, %Y %H:%M")


def shorten_text(value: str | None, width: int = 220) -> str:
    text = (value or "").strip().replace("\n", " ")
    return text if len(text) <= width else f"{text[: width - 1].rstrip()}…"


def metric_card(label: str, value: str) -> str:
    return f"<div class='kpi'><div class='label'>{label}</div><div class='value'>{value}</div></div>"


def archive_stats(documents: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(documents)
    processed = sum(1 for doc in documents if (doc.get("ocr_text") or "").strip())
    types = Counter((doc.get("document_type") or "Unknown") for doc in documents if doc.get("document_type"))
    languages = Counter((doc.get("language") or "unknown") for doc in documents if doc.get("language"))
    latest = None
    for doc in documents:
        ts = doc.get("upload_date")
        if not ts:
            continue
        latest = max(latest, str(ts)) if latest else str(ts)
    return {
        "total": total,
        "processed": processed,
        "types": types,
        "languages": languages,
        "latest": latest,
    }


def render_sidebar(documents: list[dict[str, Any]] | None) -> None:
    stats = archive_stats(documents or []) if documents is not None else None
    st.sidebar.markdown(
        f"""
        <div class="panel secondary">
          <div class="eyebrow">Archive workspace</div>
          <h3 style="margin: 0 0 0.35rem;">{APP_NAME}</h3>
          <div class="small-muted">Upload scanned files, inspect OCR and metadata, then ask grounded questions against the archive.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.sidebar.markdown(
        f"""
        <div class="panel secondary" style="margin-top: 0.9rem;">
          <div class="small-muted">Connected API</div>
          <div style="font-weight: 700; margin-top: 0.25rem;">{_ACTIVE_API_BASE_URL}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if stats is not None:
        st.sidebar.markdown(
            f"""
            <div class="panel secondary" style="margin-top: 0.9rem;">
              <div class="small-muted">Archive status</div>
              <div style="margin-top: 0.65rem;">{metric_card("Documents", str(stats["total"]))}</div>
              <div style="margin-top: 0.55rem;">{metric_card("Processed", str(stats["processed"]))}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.sidebar.markdown(
        """
        <div class="panel secondary" style="margin-top: 0.9rem;">
          <div class="small-muted">Tips</div>
          <div style="margin-top: 0.45rem; line-height: 1.6;">
            Ask for names, dates, contract numbers, or organizations. If the answer model is slow, you will still get the closest archive passages.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_header(title: str, subtitle: str, eyebrow: str) -> None:
    st.markdown(
        f"""
        <div class="hero">
          <div class="eyebrow">{eyebrow}</div>
          <h1>{title}</h1>
          <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_upload_page(documents: list[dict[str, Any]]) -> None:
    render_header(
        "Archive Upload",
        "Bring in scanned JPG, PNG, TIFF, or PDF files. The pipeline extracts text, builds metadata, and indexes the result for search and chat.",
        "Step 1",
    )

    left, right = st.columns([1.05, 0.95], gap="large")
    with left:
        st.markdown(
            """
            <div class="panel">
              <h3>What happens next</h3>
              <div class="small-muted">
                1. The file is uploaded to the backend.<br/>
                2. OCR extracts readable text and metadata clues.<br/>
                3. The text is chunked and indexed for retrieval.<br/>
                4. You can inspect the document or ask questions about it.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
            <div class="kpi-row">
              {metric_card("Indexed docs", str(archive_stats(documents)["processed"]))}
              {metric_card("Total docs", str(len(documents)))}
              {metric_card("API", "Ready")}
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        uploaded = st.file_uploader(
            "Choose a document",
            type=["jpg", "jpeg", "png", "tif", "tiff", "pdf"],
            help="Keep files under 200 MB. PDFs and images are supported.",
        )

        if uploaded is not None:
            st.markdown(
                f"""
                <div class="panel secondary" style="margin-bottom: 0.9rem;">
                  <div style="font-weight: 700;">{uploaded.name}</div>
                  <div class="small-muted">{format_bytes(getattr(uploaded, "size", None))} • {uploaded.type or "application/octet-stream"}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        process_clicked = st.button("Upload and process", type="primary", use_container_width=True, disabled=uploaded is None)

        if process_clicked and uploaded is not None:
            try:
                with st.status("Processing document", expanded=True) as status:
                    st.write("Uploading file to the archive API...")
                    files = {"file": (uploaded.name, uploaded.getvalue(), uploaded.type or "application/octet-stream")}
                    upload_response = api_post("/upload", files=files).json()
                    document_id = upload_response["document_id"]
                    st.write("Running OCR, metadata extraction, and layout analysis...")
                    process_response = api_post("/process", json={"document_id": document_id}).json()
                    st.write("Indexing text for search and chat...")
                    status.update(label=f"Document #{document_id} processed", state="complete")

                st.session_state["last_document"] = process_response
                clear_document_cache()
                st.success(f"Processed document #{document_id}")
                st.markdown(
                    f"""
                    <div class="panel" style="margin-top: 1rem;">
                      <div style="font-weight: 700; margin-bottom: 0.3rem;">Processing summary</div>
                      <div class="small-muted">Type: {process_response["classification"]["document_type"]} • Language: {process_response["ocr"]["language"]} • Chunks indexed: {process_response["chunks_indexed"]}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            except requests.RequestException as exc:
                st.error(f"Processing failed: {exc}")

    document = st.session_state.get("last_document")
    if document:
        st.markdown('<div style="margin-top: 1.2rem;"></div>', unsafe_allow_html=True)
        detail_left, detail_right = st.columns([1.15, 0.85], gap="large")
        with detail_left:
            st.markdown(
                """
                <div class="panel">
                  <h3>Latest result</h3>
                  <div class="small-muted">A quick snapshot of the most recent processed file.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.text_area("OCR text", document["ocr"]["text"], height=360, label_visibility="collapsed")
        with detail_right:
            st.markdown(
                f"""
                <div class="panel">
                  <h4>Metadata</h4>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.json(document["metadata"])
            st.markdown(
                f"""
                <div class="panel" style="margin-top: 0.9rem;">
                  <h4>Classification</h4>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.json(document["classification"])
            st.markdown(
                f"""
                <div class="panel" style="margin-top: 0.9rem;">
                  <h4>Layout</h4>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.json(document["layout"])


def render_documents_page(documents: list[dict[str, Any]]) -> None:
    render_header(
        "Documents",
        "Review the archive at a glance. Filter by filename or metadata, then open a document to inspect OCR and extracted fields.",
        "Step 2",
    )

    stats = archive_stats(documents)
    st.markdown(
        f"""
        <div class="kpi-row">
          {metric_card("Documents", str(stats["total"]))}
          {metric_card("Processed", str(stats["processed"]))}
          {metric_card("Languages", str(len(stats["languages"])))}
          {metric_card("Document types", str(len(stats["types"])))}
        </div>
        """,
        unsafe_allow_html=True,
    )

    query = st.text_input("Filter archive", placeholder="Search filename, language, document type, or OCR text")
    filtered = []
    query_text = query.strip().lower()
    for document in documents:
        haystack = " ".join(
            [
                str(document.get("filename") or ""),
                str(document.get("language") or ""),
                str(document.get("document_type") or ""),
                str(document.get("ocr_text") or ""),
                str(document.get("metadata_json") or {}),
            ]
        ).lower()
        if not query_text or query_text in haystack:
            filtered.append(document)

    if not filtered:
        st.info("No documents match that filter.")
        return

    for document in filtered:
        upload_label = humanize_datetime(document.get("upload_date"))
        title = document.get("filename", "Untitled document")
        language = document.get("language") or "unknown"
        doc_type = document.get("document_type") or "unknown"
        excerpt = shorten_text(document.get("ocr_text"), 320)

        st.markdown(
            f"""
            <div class="doc-card">
              <div class="doc-title">#{document['id']} • {title}</div>
              <div class="doc-meta">
                Uploaded {upload_label} • Language: {language} • Type: {doc_type}
              </div>
              <div class="doc-meta" style="margin-top: 0.6rem;">{excerpt or "No OCR text available yet."}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.expander("Open details"):
            detail_left, detail_right = st.columns([1.15, 0.85], gap="large")
            with detail_left:
                st.text_area("OCR text", document.get("ocr_text") or "", height=240, key=f"ocr-{document['id']}")
            with detail_right:
                st.json(document.get("metadata_json") or {})


def render_source_list(sources: list[dict[str, Any]]) -> None:
    if not sources:
        st.caption("No source passages were returned.")
        return

    st.markdown("<div class='pill-row'><span class='pill'>Grounded sources</span></div>", unsafe_allow_html=True)
    for source in sources:
        filename = source.get("metadata", {}).get("filename", "unknown")
        doc_type = source.get("metadata", {}).get("document_type", "unknown")
        score = source.get("score", 0.0)
        snippet = shorten_text(source.get("text"), 260)
        st.markdown(
            f"""
            <div class="source-card">
              <div class="source-title">Document #{source.get('document_id')} • {filename}</div>
              <div class="source-snippet">Type: {doc_type} • Score: {score:.3f}<br/>{snippet}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def ask_archive(question: str, top_k: int) -> dict[str, Any]:
    response = api_post("/chat", json={"question": question, "top_k": top_k})
    return response.json()


def render_chat_page(documents: list[dict[str, Any]]) -> None:
    render_header(
        "Archive Chat",
        "Ask questions in plain language. The assistant will search the archive first and, if generation is slow, it will still return the most relevant passages instead of failing.",
        "Step 3",
    )

    docs_ready = sum(1 for doc in documents if (doc.get("ocr_text") or "").strip())
    st.markdown(
        f"""
        <div class="kpi-row">
          {metric_card("Indexed docs", str(docs_ready))}
          {metric_card("Active sources", str(len(documents)))}
          {metric_card("Response mode", "Grounded")}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="panel">
          <h3>Try a prompt</h3>
          <div class="small-muted">Use one of the examples below or ask your own question.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    top_k = st.slider("How many sources to search", min_value=1, max_value=10, value=5)

    prompt_cols = st.columns(len(SUGGESTED_QUESTIONS))
    for idx, (col, prompt) in enumerate(zip(prompt_cols, SUGGESTED_QUESTIONS, strict=True)):
        with col:
            if st.button(prompt, key=f"prompt-{idx}", use_container_width=True):
                st.session_state["pending_chat_prompt"] = prompt
                st.rerun()

    chat_messages = st.session_state.setdefault("chat_messages", [])
    for message in chat_messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if message["role"] == "assistant" and message.get("sources"):
                with st.expander("Sources"):
                    render_source_list(message["sources"])

    pending_prompt = st.session_state.pop("pending_chat_prompt", None)
    question = pending_prompt or st.chat_input("Ask about names, dates, contracts, or organizations")

    if question:
        chat_messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.write(question)

        with st.chat_message("assistant"):
            with st.spinner("Searching the archive and drafting a grounded answer..."):
                try:
                    result = ask_archive(question, top_k=top_k)
                    answer = result.get("answer", "I could not find this information in the archive.")
                    sources = result.get("sources", [])
                except requests.RequestException as exc:
                    answer = f"Chat failed: {exc}"
                    sources = []

            st.write(answer)
            if sources:
                with st.expander("Sources"):
                    render_source_list(sources)

        chat_messages.append({"role": "assistant", "content": answer, "sources": sources})


def main() -> None:
    inject_styles()
    Path("storage/uploads").mkdir(parents=True, exist_ok=True)

    try:
        documents = load_documents()
    except requests.RequestException as exc:
        documents = []
        st.error(f"Could not connect to the API: {exc}")

    render_sidebar(documents)
    page = st.sidebar.radio("Navigation", ["Upload", "Documents", "Chat"])

    if page == "Upload":
        render_upload_page(documents)
    elif page == "Documents":
        render_documents_page(documents)
    else:
        render_chat_page(documents)


if __name__ == "__main__":
    main()
