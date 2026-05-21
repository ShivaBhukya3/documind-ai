"""Document management page — upload, index, and manage documents."""

import os
import tempfile
from pathlib import Path

import streamlit as st

from dashboard.utils.ui_helpers import get_pipeline, render_stat_card, render_doc_item

ALLOWED_TYPES = ["pdf", "docx", "txt", "csv", "pptx", "md"]

_EXT_ICONS = {
    ".pdf":  "&#x1F4D5;",
    ".docx": "&#x1F4D8;",
    ".txt":  "&#x1F4C4;",
    ".csv":  "&#x1F4CA;",
    ".pptx": "&#x1F4D9;",
    ".md":   "&#x1F5D2;",
}


def render_document_manager() -> None:
    pipeline = get_pipeline()

    # ── Page header ──────────────────────────────────────────────────────────
    st.markdown(
        '<div style="display:flex;align-items:center;gap:13px;margin-bottom:1.4rem;'
        'padding-bottom:1.1rem;border-bottom:1px solid rgba(255,255,255,0.055)">'
        '  <div style="width:42px;height:42px;border-radius:11px;background:'
        '    linear-gradient(135deg,rgba(99,102,241,0.18),rgba(168,85,247,0.18));'
        '    border:1px solid rgba(99,102,241,0.22);display:flex;align-items:center;'
        '    justify-content:center;font-size:1.15rem">&#x1F4C1;</div>'
        '  <div>'
        '    <div style="font-size:1.32rem;font-weight:750;color:#f1f5f9;letter-spacing:-0.025em">'
        '      Document Manager</div>'
        '    <div style="font-size:0.78rem;color:#475569;margin-top:2px">'
        '      Upload and index files — then chat with their content</div>'
        '  </div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── Stats row ────────────────────────────────────────────────────────────
    stats = {}
    if pipeline:
        stats = pipeline.vector_store_manager.get_index_stats()

    doc_count  = len(pipeline._ingested_docs) if pipeline else 0
    chunk_count = stats.get("total_vectors", 0)
    index_mb   = stats.get("index_size_mb", 0.0)
    updated    = stats.get("last_updated") or "Never"
    if updated != "Never":
        updated = str(updated)[:10]

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_stat_card(str(doc_count),          "Documents",   "&#x1F4C4;")
    with c2:
        render_stat_card(str(chunk_count),         "Chunks",      "&#x1F9E9;")
    with c3:
        render_stat_card(f"{index_mb:.2f} MB",    "Index Size",  "&#x1F4BE;")
    with c4:
        render_stat_card(updated,                  "Last Updated","&#x1F552;")

    st.markdown('<div style="height:18px"></div>', unsafe_allow_html=True)

    # ── Upload zone ──────────────────────────────────────────────────────────
    st.markdown(
        '<div style="font-size:0.8rem;font-weight:700;color:#94a3b8;'
        'text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px">'
        '&#x2B06; Upload Documents</div>',
        unsafe_allow_html=True,
    )

    max_mb = os.getenv("MAX_UPLOAD_SIZE_MB", 50)
    uploaded_files = st.file_uploader(
        "Drop files here or click to browse",
        type=ALLOWED_TYPES,
        accept_multiple_files=True,
        help=f"Supported: {', '.join(f'.{t}' for t in ALLOWED_TYPES)}  |  Max {max_mb} MB per file",
    )

    if uploaded_files:
        # Preview selected files
        st.markdown(
            f'<div style="background:rgba(99,102,241,0.04);border:1px solid rgba(99,102,241,0.14);'
            f'border-radius:10px;padding:10px 14px;margin:10px 0;font-size:0.82rem;color:#94a3b8">'
            f'  &#x1F4CE; <b style="color:#818cf8">{len(uploaded_files)}</b> file(s) selected</div>',
            unsafe_allow_html=True,
        )

        if pipeline and st.button(
            "&#x26A1; Index Documents", type="primary", use_container_width=False
        ):
            _process_uploads(uploaded_files, pipeline)

    st.markdown('<div style="height:16px"></div>', unsafe_allow_html=True)

    # ── Indexed documents list ───────────────────────────────────────────────
    st.markdown(
        '<div style="font-size:0.8rem;font-weight:700;color:#94a3b8;'
        'text-transform:uppercase;letter-spacing:0.08em;margin-bottom:10px">'
        '&#x1F4DA; Indexed Documents</div>',
        unsafe_allow_html=True,
    )

    if pipeline and pipeline._ingested_docs:
        for i, doc in enumerate(pipeline._ingested_docs):
            col_doc, col_del = st.columns([8, 1])
            with col_doc:
                render_doc_item(doc)
            with col_del:
                st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)
                if st.button(
                    "&#x1F5D1;", key=f"del_{i}",
                    help=f"Remove {doc}", type="secondary"
                ):
                    pipeline.vector_store_manager.delete_documents([doc])
                    pipeline._ingested_docs.remove(doc)
                    st.success(f"Removed: {doc}")
                    st.rerun()
    else:
        st.markdown(
            '<div class="dm-empty">'
            '  <div class="dm-empty-ico">&#x1F4C2;</div>'
            '  <div class="dm-empty-ttl">No documents indexed yet</div>'
            '  <div class="dm-empty-sub">Upload files above to get started</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    # ── URL ingestion ─────────────────────────────────────────────────────────
    st.markdown('<div style="height:10px"></div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="font-size:0.8rem;font-weight:700;color:#94a3b8;'
        'text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px">'
        '&#x1F310; Index from URL</div>',
        unsafe_allow_html=True,
    )

    with st.container():
        url_col, btn_col = st.columns([5, 1])
        with url_col:
            url_input = st.text_input(
                "url",
                placeholder="https://example.com/document.pdf",
                label_visibility="collapsed",
            )
        with btn_col:
            url_go = st.button(
                "Fetch &#x27A4;", use_container_width=True, type="secondary"
            )

        if url_go and url_input and pipeline:
            with st.spinner("Fetching and indexing URL ..."):
                report = pipeline.ingest_documents(url_input)
            if report.get("errors"):
                st.error(f"Error: {report['errors']}")
            else:
                st.success(
                    f"Indexed {report['chunks_created']} chunks from URL."
                )
            st.rerun()


def _process_uploads(uploaded_files, pipeline) -> None:
    progress = st.progress(0, text="Preparing ...")
    results  = []

    for i, uf in enumerate(uploaded_files):
        progress.progress(
            int((i / len(uploaded_files)) * 90),
            text=f"Processing {uf.name} ...",
        )
        suffix = Path(uf.name).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uf.read())
            tmp_path = tmp.name

        try:
            report = pipeline.ingest_documents(tmp_path)
            if pipeline._ingested_docs:
                pipeline._ingested_docs[-1] = uf.name
            results.append({
                "name": uf.name,
                "chunks": report.get("chunks_created", 0),
                "ok": True,
                "error": "",
            })
        except Exception as exc:
            results.append({
                "name": uf.name, "chunks": 0, "ok": False, "error": str(exc)
            })
        finally:
            os.unlink(tmp_path)

    progress.progress(100, text="Done!")

    ok_count  = sum(1 for r in results if r["ok"])
    err_count = len(results) - ok_count

    if ok_count:
        st.success(
            f"&#x2705; Indexed {ok_count} file(s) successfully — "
            f"{sum(r['chunks'] for r in results if r['ok'])} total chunks created."
        )
    if err_count:
        for r in results:
            if not r["ok"]:
                st.error(f"&#x274C; **{r['name']}** — {r['error']}")

    st.rerun()
