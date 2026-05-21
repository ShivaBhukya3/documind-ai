"""Chat interface — premium streaming Q&A with source citations."""

import time
import uuid

import streamlit as st

from dashboard.utils.ui_helpers import (
    render_ai_message,
    render_user_message,
    render_context_bar,
    get_pipeline,
)


def render_chat_interface() -> None:
    pipeline = get_pipeline()

    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())[:8]
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "total_tokens" not in st.session_state:
        st.session_state.total_tokens = 0

    # ── Header row ──────────────────────────────────────────────────────────
    col_title, col_tokens, col_clear = st.columns([4, 2, 1])
    with col_title:
        st.markdown(
            '<div style="display:flex;align-items:center;gap:11px;padding-bottom:2px">'
            '  <div style="width:40px;height:40px;border-radius:11px;background:'
            '    linear-gradient(135deg,rgba(99,102,241,0.18),rgba(168,85,247,0.18));'
            '    border:1px solid rgba(99,102,241,0.22);display:flex;align-items:center;'
            '    justify-content:center;font-size:1.1rem;flex-shrink:0">&#x1F4AC;</div>'
            '  <div>'
            '    <div style="font-size:1.28rem;font-weight:750;color:#f1f5f9;'
            '      letter-spacing:-0.025em">Chat with your Documents</div>'
            '    <div style="font-size:0.75rem;color:#475569;margin-top:1px">'
            '      Ask anything — answers grounded in your uploaded files</div>'
            '  </div>'
            '</div>',
            unsafe_allow_html=True,
        )

    with col_tokens:
        st.markdown(
            f'<div class="dm-tokens" style="padding-top:10px">'
            f'  &#x1FA99; <b>{st.session_state.total_tokens:,}</b> tokens used'
            f'  &nbsp;&bull;&nbsp; session <b>{st.session_state.session_id}</b>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with col_clear:
        if st.button("&#x1F5D1; Clear", use_container_width=True, type="secondary"):
            st.session_state.messages = []
            if pipeline:
                pipeline.reset_conversation(st.session_state.session_id)
            st.rerun()

    st.markdown("---")

    # ── Context indicator ────────────────────────────────────────────────────
    if pipeline and pipeline._ingested_docs:
        render_context_bar(pipeline._ingested_docs)
    else:
        st.markdown(
            '<div style="background:rgba(245,158,11,0.06);border:1px solid rgba(245,158,11,0.18);'
            'border-radius:12px;padding:14px 18px;display:flex;align-items:center;gap:10px;'
            'margin-bottom:16px;font-size:0.875rem">'
            '  <span style="font-size:1.2rem">&#x26A0;&#xFE0F;</span>'
            '  <span style="color:#94a3b8">No documents indexed yet. Go to '
            '    <b style="color:#fbbf24">Documents</b> to upload files.</span>'
            '</div>',
            unsafe_allow_html=True,
        )

    # ── Message history ──────────────────────────────────────────────────────
    msg_container = st.container()
    with msg_container:
        if not st.session_state.messages:
            st.markdown(
                '<div class="dm-empty" style="padding:2.5rem 0">'
                '  <div class="dm-empty-ico">&#x1F4AC;</div>'
                '  <div class="dm-empty-ttl">Start a conversation</div>'
                '  <div class="dm-empty-sub">Ask a question about your documents below</div>'
                '</div>',
                unsafe_allow_html=True,
            )
        else:
            for msg in st.session_state.messages:
                if msg["role"] == "user":
                    render_user_message(msg["content"])
                else:
                    render_ai_message(
                        msg["content"],
                        msg.get("sources", []),
                        msg.get("confidence", 0.5),
                    )
                    sources = msg.get("sources", [])
                    if sources:
                        with st.expander(
                            f"&#x1F4CE; {len(sources)} source chunk(s) — click to expand",
                            expanded=False,
                        ):
                            for i, src in enumerate(sources, 1):
                                cols = st.columns([3, 1, 1])
                                cols[0].markdown(
                                    f"**{i}. {src.get('filename', 'Unknown')}**"
                                )
                                cols[1].caption(f"Page {src.get('page', 'N/A')}")
                                if src.get("preview"):
                                    st.caption(f"> {src['preview'][:200]}")
                                if i < len(sources):
                                    st.markdown(
                                        '<hr style="margin:6px 0;border-color:rgba(255,255,255,0.05)">',
                                        unsafe_allow_html=True,
                                    )

    # ── Input form ───────────────────────────────────────────────────────────
    st.markdown('<div style="height:12px"></div>', unsafe_allow_html=True)
    with st.form("chat_form", clear_on_submit=True):
        col_inp, col_btn = st.columns([6, 1])
        with col_inp:
            question = st.text_input(
                "question",
                placeholder="Ask about your documents …  e.g. What is the refund policy?",
                label_visibility="collapsed",
            )
        with col_btn:
            submitted = st.form_submit_button(
                "→", use_container_width=True, type="primary"
            )

    # ── Suggested prompts (only when no messages yet) ────────────────────────
    if not st.session_state.messages:
        st.markdown(
            '<div style="display:flex;flex-wrap:wrap;gap:7px;margin-top:10px">',
            unsafe_allow_html=True,
        )
        suggestions = [
            "Summarise all documents",
            "What are the key takeaways?",
            "List all dates mentioned",
            "What actions are required?",
        ]
        cols = st.columns(len(suggestions))
        for col, s in zip(cols, suggestions):
            if col.button(s, key=f"sug_{s}", type="secondary", use_container_width=True):
                question = s
                submitted = True
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Handle submission ────────────────────────────────────────────────────
    if submitted and question and question.strip():
        if pipeline is None:
            st.error("Pipeline not initialised. Check configuration.")
            return

        st.session_state.messages.append({"role": "user", "content": question})

        with st.spinner("&#x1F50D; Searching and generating answer …"):
            start  = time.time()
            result = pipeline.query(question, st.session_state.session_id)
            elapsed = round((time.time() - start) * 1000)

        answer     = result.get("answer", "No answer generated.")
        sources    = result.get("sources", [])
        confidence = result.get("confidence_score", 0.5)
        tokens     = result.get("tokens_used", 0)

        st.session_state.messages.append({
            "role":            "assistant",
            "content":         answer,
            "sources":         sources,
            "confidence":      confidence,
            "response_time_ms": elapsed,
        })
        st.session_state.total_tokens += tokens
        st.rerun()
