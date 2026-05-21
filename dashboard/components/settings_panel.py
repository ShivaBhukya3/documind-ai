"""Settings panel — configure LLM, retrieval, and system parameters."""

import json
import os

import streamlit as st
import yaml

from dashboard.utils.ui_helpers import get_pipeline


def render_settings() -> None:
    # ── Page header ──────────────────────────────────────────────────────────
    st.markdown(
        '<div style="display:flex;align-items:center;gap:13px;margin-bottom:1.4rem;'
        'padding-bottom:1.1rem;border-bottom:1px solid rgba(255,255,255,0.055)">'
        '  <div style="width:42px;height:42px;border-radius:11px;background:'
        '    linear-gradient(135deg,rgba(99,102,241,0.18),rgba(168,85,247,0.18));'
        '    border:1px solid rgba(99,102,241,0.22);display:flex;align-items:center;'
        '    justify-content:center;font-size:1.15rem">&#x2699;&#xFE0F;</div>'
        '  <div>'
        '    <div style="font-size:1.32rem;font-weight:750;color:#f1f5f9;letter-spacing:-0.025em">'
        '      Settings</div>'
        '    <div style="font-size:0.78rem;color:#475569;margin-top:2px">'
        '      Configure LLM, retrieval, and system behaviour</div>'
        '  </div>'
        '</div>',
        unsafe_allow_html=True,
    )

    config_path = "config/config.yaml"
    try:
        with open(config_path) as f:
            config = yaml.safe_load(f) or {}
    except Exception:
        config = {}

    tab_llm, tab_ret, tab_sys = st.tabs(
        ["&#x1F916; LLM", "&#x1F50D; Retrieval", "&#x1F6E0; System"]
    )

    # ════════════════════════════════════════════════════════════════
    # LLM TAB
    # ════════════════════════════════════════════════════════════════
    with tab_llm:
        llm_cfg = config.get("llm", {})

        _group_header("&#x1F916;", "Language Model")
        providers = ["groq", "openai", "huggingface", "ollama"]
        cur_provider = llm_cfg.get("provider", "groq")
        if cur_provider not in providers:
            cur_provider = "groq"
        provider = st.selectbox(
            "LLM Provider",
            providers,
            index=providers.index(cur_provider),
        )
        model_map = {
            "groq":         ["llama-3.1-8b-instant", "llama-3.3-70b-versatile", "llama-3.1-70b-versatile", "gemma2-9b-it"],
            "openai":       ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "gpt-4o", "gpt-4o-mini"],
            "huggingface":  ["google/flan-t5-base", "google/flan-t5-large",
                             "mistralai/Mistral-7B-Instruct-v0.1"],
            "ollama":       ["llama2", "mistral", "codellama", "gemma"],
        }
        model = st.selectbox("Model", model_map.get(provider, ["gpt-3.5-turbo"]))

        col_a, col_b = st.columns(2)
        with col_a:
            temperature = st.slider(
                "Temperature", 0.0, 1.0,
                float(llm_cfg.get("temperature", 0.1)), 0.05
            )
        with col_b:
            max_tokens = st.slider(
                "Max Tokens", 256, 4096,
                int(llm_cfg.get("max_tokens", 1000)), 128
            )
        streaming = st.toggle(
            "Enable Streaming", value=bool(llm_cfg.get("streaming", True))
        )

        st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)
        _group_header("&#x1F511;", "API Keys")

        col_k1, col_k2, col_k3 = st.columns(3)
        with col_k1:
            groq_key = st.text_input(
                "Groq API Key", value="", type="password",
                placeholder="gsk_..."
            )
        with col_k2:
            api_key = st.text_input(
                "OpenAI API Key", value="", type="password",
                placeholder="sk-..."
            )
        with col_k3:
            hf_token = st.text_input(
                "HuggingFace Token", value="", type="password",
                placeholder="hf_..."
            )

        st.markdown('<div style="height:4px"></div>', unsafe_allow_html=True)
        if st.button("&#x1F4BE; Save LLM Settings", type="primary"):
            config.setdefault("llm", {}).update({
                "provider":   provider,
                "model_name": model,
                "temperature": temperature,
                "max_tokens":  max_tokens,
                "streaming":   streaming,
            })
            _save_config(config, config_path)
            if groq_key:
                os.environ["GROQ_API_KEY"] = groq_key
            if api_key:
                os.environ["OPENAI_API_KEY"] = api_key
            if hf_token:
                os.environ["HUGGINGFACEHUB_API_TOKEN"] = hf_token
            st.success("&#x2705; LLM settings saved. Restart the app to apply.")

    # ════════════════════════════════════════════════════════════════
    # RETRIEVAL TAB
    # ════════════════════════════════════════════════════════════════
    with tab_ret:
        retrieval_cfg = config.get("retrieval", {})
        vs_cfg        = config.get("vector_store", {})
        chunk_cfg     = config.get("chunking", {})

        _group_header("&#x1F50D;", "Search Configuration")
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            top_k = st.slider(
                "Top-K Results", 1, 20, int(vs_cfg.get("top_k", 5))
            )
            score_threshold = st.slider(
                "Score Threshold", 0.0, 1.0,
                float(retrieval_cfg.get("score_threshold", 0.3)), 0.05
            )
        with col_r2:
            search_type = st.selectbox(
                "Search Type",
                ["mmr", "similarity", "hybrid"],
                index=["mmr", "similarity", "hybrid"].index(
                    retrieval_cfg.get("search_type", "mmr")
                ),
            )
            fetch_k = st.slider(
                "MMR Fetch-K", 5, 50, int(retrieval_cfg.get("fetch_k", 20))
            )

        st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)
        _group_header("&#x2702;&#xFE0F;", "Chunking")
        chunk_size = st.select_slider(
            "Chunk Size (tokens)",
            options=[256, 512, 750, 1000, 1500, 2000],
            value=int(chunk_cfg.get("chunk_size", 1000)),
        )
        chunk_overlap = st.slider(
            "Chunk Overlap", 0, 400,
            int(chunk_cfg.get("chunk_overlap", 200)), 25
        )

        st.markdown('<div style="height:4px"></div>', unsafe_allow_html=True)
        if st.button("&#x1F4BE; Save Retrieval Settings", type="primary"):
            config.setdefault("retrieval", {}).update({
                "search_type":      search_type,
                "score_threshold":  score_threshold,
                "fetch_k":          fetch_k,
            })
            config.setdefault("vector_store", {})["top_k"] = top_k
            config.setdefault("chunking", {}).update({
                "chunk_size":    chunk_size,
                "chunk_overlap": chunk_overlap,
            })
            _save_config(config, config_path)
            st.success("&#x2705; Retrieval settings saved. Re-ingest documents to apply chunk changes.")

    # ════════════════════════════════════════════════════════════════
    # SYSTEM TAB
    # ════════════════════════════════════════════════════════════════
    with tab_sys:
        _group_header("&#x1F527;", "Runtime Flags")

        free_mode = st.toggle(
            "FREE MODE  (local models — no API keys needed)",
            value=os.getenv("FREE_MODE", "false").lower() == "true",
            help="Uses HuggingFace sentence-transformers + flan-t5-base",
        )
        use_redis = st.toggle(
            "Enable Redis cache",
            value=os.getenv("USE_REDIS", "false").lower() == "true",
        )

        col_s1, col_s2 = st.columns(2)
        with col_s1:
            log_level = st.selectbox(
                "Log Level",
                ["DEBUG", "INFO", "WARNING", "ERROR"],
                index=["DEBUG", "INFO", "WARNING", "ERROR"].index(
                    os.getenv("LOG_LEVEL", "INFO")
                ),
            )
        with col_s2:
            rate_limit = st.number_input(
                "Rate Limit (req/min)", min_value=1, max_value=1000,
                value=int(os.getenv("RATE_LIMIT_PER_MINUTE", 10))
            )

        if st.button("&#x1F4BE; Apply Runtime Settings", type="primary"):
            os.environ["FREE_MODE"]              = str(free_mode).lower()
            os.environ["USE_REDIS"]              = str(use_redis).lower()
            os.environ["LOG_LEVEL"]              = log_level
            os.environ["RATE_LIMIT_PER_MINUTE"]  = str(rate_limit)
            st.success("&#x2705; Applied for this session. Edit .env to persist across restarts.")

        st.markdown('<div style="height:12px"></div>', unsafe_allow_html=True)

        # ── Danger zone ──────────────────────────────────────────────────────
        st.markdown(
            '<div class="dm-danger">'
            '  <div class="dm-danger-ttl">&#x26A0;&#xFE0F; Danger Zone</div>',
            unsafe_allow_html=True,
        )
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            if st.button(
                "&#x1F5D1; Clear All Data",
                type="secondary", use_container_width=True
            ):
                pipeline = get_pipeline()
                if pipeline:
                    pipeline.vector_store_manager.clear_index()
                    pipeline._ingested_docs = []
                    st.session_state.messages = []
                    st.success("All data cleared.")
                    st.rerun()
        with col_d2:
            if st.button(
                "&#x1F504; Reset to Defaults",
                type="secondary", use_container_width=True
            ):
                st.info("Delete config/config.yaml and restart to reset to defaults.")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div style="height:12px"></div>', unsafe_allow_html=True)

        # ── Export / Import ───────────────────────────────────────────────────
        _group_header("&#x1F4E4;", "Export / Import")
        col_e1, col_e2 = st.columns(2)
        with col_e1:
            settings_json = json.dumps(config, indent=2)
            st.download_button(
                "&#x2B07; Download settings.json",
                data=settings_json,
                file_name="documind_settings.json",
                mime="application/json",
                use_container_width=True,
            )
        with col_e2:
            uploaded = st.file_uploader(
                "Import settings.json", type=["json"],
                label_visibility="collapsed"
            )
            if uploaded:
                try:
                    imported = json.load(uploaded)
                    config.update(imported)
                    _save_config(config, config_path)
                    st.success("Settings imported.")
                except Exception as exc:
                    st.error(f"Failed to import: {exc}")


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _group_header(icon: str, title: str) -> None:
    st.markdown(
        f'<div class="dm-settings-group-ttl">{icon} {title}</div>',
        unsafe_allow_html=True,
    )


def _save_config(config: dict, path: str) -> None:
    with open(path, "w") as f:
        yaml.dump(config, f, default_flow_style=False)
