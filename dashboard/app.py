"""DocuMind AI — Main Streamlit Dashboard."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv()

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from dashboard.utils.ui_helpers import (
    apply_premium_theme,
    get_pipeline,
    render_logo,
    render_mode_badge,
    render_page_header,
)

# ─────────────────────────────────────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="DocuMind AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "DocuMind AI — Intelligent Document Q&A powered by RAG & LLMs"},
)

apply_premium_theme()


# ─────────────────────────────────────────────────────────────────────────────
# RAG Explorer (defined before routing)
# ─────────────────────────────────────────────────────────────────────────────

def _render_rag_explorer() -> None:
    render_page_header("🔬", "RAG Explorer", "Inspect every step of the retrieval pipeline")

    pipeline = get_pipeline()

    col_q, col_t = st.columns([3, 1])
    with col_q:
        query = st.text_input(
            "Test query",
            placeholder="e.g. What is the leave policy?",
            label_visibility="collapsed",
        )
    with col_t:
        search_type = st.selectbox("Mode", ["mmr", "similarity"], label_visibility="collapsed")

    run = st.button("&#x1F50D; Run Pipeline", type="primary", use_container_width=False)

    if run and query and pipeline:
        with st.spinner("Running pipeline ..."):
            docs = pipeline.retriever.get_relevant_documents(query)

        tab1, tab2, tab3, tab4 = st.tabs(
            ["&#x1F4C4; Chunks", "&#x1F9E0; Prompt", "&#x1F4AC; Answer", "&#x1F4C8; Embeddings"]
        )

        with tab1:
            st.markdown(f"**Retrieved {len(docs)} chunk(s)**")
            for i, doc in enumerate(docs, 1):
                meta = doc.metadata
                with st.expander(
                    f"Chunk {i} — {meta.get('filename', 'Unknown')} | Page {meta.get('page', 'N/A')}",
                    expanded=(i == 1),
                ):
                    st.markdown(f"`chunk_id: {meta.get('chunk_id', 'N/A')}`")
                    st.text(doc.page_content[:600])

        with tab2:
            context = pipeline.retriever.format_docs_for_context(docs)
            st.code(
                f"Context:\n{context[:1200]}\n\nQuestion: {query}\n\nAnswer:",
                language="text",
            )

        with tab3:
            with st.spinner("Generating answer ..."):
                result = pipeline.query(query)
            st.markdown(f"**{result.get('answer', '')}**")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Confidence",  f"{result.get('confidence_score', 0):.0%}")
            m2.metric("Retrieval",   f"{result.get('retrieval_time_ms', 0):.0f} ms")
            m3.metric("Generation",  f"{result.get('generation_time_ms', 0):.0f} ms")
            m4.metric("Tokens",       str(result.get("tokens_used", 0)))

        with tab4:
            _render_embedding_viz(query, docs, pipeline)

    st.markdown("---")
    st.markdown(
        '<div class="dm-settings-group-ttl">&#x1F9EA; Evaluation Panel</div>',
        unsafe_allow_html=True,
    )
    if st.button("&#x25B6; Run Evaluation Suite", type="secondary"):
        if pipeline is None:
            st.error("Pipeline not initialised.")
        else:
            with st.spinner("Running evaluation ..."):
                from src.evaluation import RAGEvaluator
                evaluator = RAGEvaluator(pipeline, pipeline.config)
                metrics   = evaluator.run_full_evaluation()
            st.success("Evaluation complete!")
            ec1, ec2, ec3 = st.columns(3)
            ec1.metric("Recall@K", f"{metrics['retrieval']['recall_at_k']:.2%}")
            ec2.metric("MRR",      f"{metrics['retrieval']['mrr']:.4f}")
            ec3.metric("ROUGE-L",  f"{metrics['generation']['avg_rouge_l']:.4f}")
            report = evaluator.generate_evaluation_report(metrics)
            st.download_button("Download Report", report, "eval_report.md", "text/markdown")


def _render_embedding_viz(query: str, docs, pipeline) -> None:
    try:
        from sklearn.decomposition import PCA

        texts      = [query] + [d.page_content[:200] for d in docs]
        embeddings = pipeline.embedding_engine.embed_documents(texts)

        if len(embeddings) < 3:
            st.info("Not enough points for PCA.")
            return

        pca     = PCA(n_components=2)
        reduced = pca.fit_transform(np.array(embeddings))
        labels  = ["Query"] + [f"Chunk {i}" for i in range(1, len(docs) + 1)]
        colors  = ["#ef4444"] + ["#6366f1"] * len(docs)
        sizes   = [16] + [9] * len(docs)

        fig = go.Figure()
        for i, (label, color, size) in enumerate(zip(labels, colors, sizes)):
            fig.add_trace(go.Scatter(
                x=[reduced[i, 0]], y=[reduced[i, 1]],
                mode="markers+text",
                marker=dict(color=color, size=size, line=dict(color="rgba(255,255,255,0.3)", width=1)),
                text=[label], textposition="top center",
                textfont=dict(size=11, color="#94a3b8"),
                name=label,
            ))
        fig.update_layout(
            title=dict(text="Embedding Space — PCA 2D", font=dict(size=13, color="#94a3b8")),
            template="plotly_dark",
            paper_bgcolor="#04070f", plot_bgcolor="#080e1c",
            font=dict(color="#94a3b8"),
            height=380, showlegend=False,
            margin=dict(l=10, r=10, t=40, b=10),
            xaxis=dict(gridcolor="rgba(255,255,255,0.04)", zeroline=False),
            yaxis=dict(gridcolor="rgba(255,255,255,0.04)", zeroline=False),
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption(f"PCA explained variance: {pca.explained_variance_ratio_.sum():.1%}")
    except ImportError:
        st.info("Install scikit-learn for embedding viz.")
    except Exception as exc:
        st.warning(f"Visualisation unavailable: {exc}")


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────

render_logo(sidebar=True)
render_mode_badge()

st.sidebar.markdown(
    '<div class="dm-section-lbl" style="padding-left:4px">Navigation</div>',
    unsafe_allow_html=True,
)

NAV = [
    ("&#x1F4AC;", "Chat",        "chat"),
    ("&#x1F4C1;", "Documents",   "documents"),
    ("&#x1F4CA;", "Analytics",   "analytics"),
    ("&#x1F52C;", "RAG Explorer","explorer"),
    ("&#x2699;&#xFE0F;",  "Settings",    "settings"),
]

if "page" not in st.session_state:
    st.session_state.page = "chat"

for icon, label, key in NAV:
    btn_type = "primary" if st.session_state.page == key else "secondary"
    if st.sidebar.button(
        f"{icon}  {label}",
        key=f"nav_{key}",
        use_container_width=True,
        type=btn_type,
    ):
        st.session_state.page = key
        st.rerun()

st.sidebar.markdown("---")

pipeline = get_pipeline()
if pipeline and pipeline._ingested_docs:
    st.sidebar.markdown(
        '<div class="dm-section-lbl" style="padding-left:4px">Indexed Docs</div>',
        unsafe_allow_html=True,
    )
    for doc in pipeline._ingested_docs[:7]:
        st.sidebar.caption(f"&#x1F4C4;  {doc}")
    if len(pipeline._ingested_docs) > 7:
        st.sidebar.caption(f"&#x2026; +{len(pipeline._ingested_docs) - 7} more")
    st.sidebar.markdown("---")

st.sidebar.markdown(
    '<div class="dm-footer">'
    '<b>DocuMind AI</b> v1.0.0<br>'
    'RAG &bull; LangChain &bull; FAISS'
    '</div>',
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────────────────────────────────────────
# Page routing
# ─────────────────────────────────────────────────────────────────────────────

page = st.session_state.page

if page == "chat":
    from dashboard.components.chat_interface import render_chat_interface
    render_chat_interface()

elif page == "documents":
    from dashboard.components.document_uploader import render_document_manager
    render_document_manager()

elif page == "analytics":
    from dashboard.components.analytics_panel import render_analytics
    render_analytics()

elif page == "explorer":
    _render_rag_explorer()

elif page == "settings":
    from dashboard.components.settings_panel import render_settings
    render_settings()
