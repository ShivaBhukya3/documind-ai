"""LLM chain manager — builds and manages LangChain RAG and utility chains."""

import os
import time
from typing import Generator, Optional

import yaml
from loguru import logger


class LLMChainManager:
    """Manage LLM instantiation and LangChain chain construction.

    Handles OpenAI, HuggingFace Hub, and Ollama providers with
    automatic fallback and streaming support.
    """

    def __init__(self, config: dict) -> None:
        """Initialise from config dict.

        Args:
            config: Full application config dict.
        """
        self.config = config
        llm_cfg = config.get("llm", {})
        self.provider: str = llm_cfg.get("provider", "openai")
        self.model_name: str = llm_cfg.get("model_name", "gpt-3.5-turbo")
        self.temperature: float = llm_cfg.get("temperature", 0.1)
        self.max_tokens: int = llm_cfg.get("max_tokens", 1000)
        self.streaming: bool = llm_cfg.get("streaming", True)
        self.request_timeout: int = llm_cfg.get("request_timeout", 60)
        self.max_retries: int = llm_cfg.get("max_retries", 3)

        self._total_calls: int = 0
        self._total_tokens: int = 0
        self._total_time: float = 0.0
        self._llm = None  # lazy-loaded
        self._prompts: dict = self._load_prompts()

        # FREE_MODE override
        if os.getenv("FREE_MODE", "false").lower() == "true":
            self.provider = "huggingface"
            free_cfg = config.get("free_mode", {})
            self.model_name = free_cfg.get("llm_model", "google/flan-t5-base")
            logger.info("FREE_MODE: using HuggingFace LLM.")

        # Groq takes priority when key is present and provider is groq
        if self.provider == "groq" and not os.getenv("GROQ_API_KEY"):
            logger.warning("GROQ_API_KEY missing — falling back to HuggingFace Hub.")
            self.provider = "huggingface"
            self.model_name = config.get("free_mode", {}).get("llm_model", "google/flan-t5-base")

        # Auto-fallback when no OpenAI key
        if self.provider == "openai" and not os.getenv("OPENAI_API_KEY"):
            logger.warning("OPENAI_API_KEY missing — falling back to HuggingFace Hub.")
            self.provider = "huggingface"
            self.model_name = config.get("free_mode", {}).get("llm_model", "google/flan-t5-base")

        logger.info(f"LLMChainManager initialised | provider={self.provider} | model={self.model_name}")

    # ─────────────────────────────────────────────────────────────────────────
    # LLM factory
    # ─────────────────────────────────────────────────────────────────────────

    def get_llm(self, provider: Optional[str] = None, streaming: Optional[bool] = None):
        """Return an initialised LangChain LLM object.

        Args:
            provider: Override provider ('openai', 'huggingface', 'ollama').
            streaming: Override streaming flag.

        Returns:
            A LangChain BaseLLM or BaseChatModel instance.
        """
        provider = provider or self.provider
        streaming = streaming if streaming is not None else self.streaming

        if provider == "groq":
            return self._build_groq_llm(streaming)
        if provider == "openai":
            return self._build_openai_llm(streaming)
        if provider == "ollama":
            return self._build_ollama_llm()
        return self._build_huggingface_llm()

    @property
    def llm(self):
        """Lazy-load and cache the default LLM."""
        if self._llm is None:
            self._llm = self.get_llm()
        return self._llm

    def _build_groq_llm(self, streaming: bool):
        from langchain_groq import ChatGroq

        return ChatGroq(
            model=self.model_name,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            streaming=streaming,
            groq_api_key=os.getenv("GROQ_API_KEY"),
        )

    def _build_openai_llm(self, streaming: bool):
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            from langchain.chat_models import ChatOpenAI  # type: ignore

        return ChatOpenAI(
            model=self.model_name,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            streaming=streaming,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            request_timeout=self.request_timeout,
            max_retries=self.max_retries,
        )

    def _build_huggingface_llm(self):
        hf_token = os.getenv("HUGGINGFACEHUB_API_TOKEN", "")
        try:
            from langchain_community.llms import HuggingFaceHub
        except ImportError:
            from langchain.llms import HuggingFaceHub  # type: ignore

        return HuggingFaceHub(
            repo_id=self.model_name,
            huggingfacehub_api_token=hf_token,
            task="text2text-generation",
            model_kwargs={
                "temperature": max(self.temperature, 0.01),
                "max_new_tokens": self.max_tokens,
            },
        )

    def _build_ollama_llm(self):
        try:
            from langchain_community.llms import Ollama
        except ImportError:
            from langchain.llms import Ollama  # type: ignore

        return Ollama(
            model=self.model_name or "llama2",
            temperature=self.temperature,
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Chain builders
    # ─────────────────────────────────────────────────────────────────────────

    def build_qa_chain(self, retriever, memory):
        """Build a ConversationalRetrievalChain with streaming support.

        Args:
            retriever: LangChain VectorStoreRetriever.
            memory: LangChain ConversationMemory object.

        Returns:
            ConversationalRetrievalChain ready for .invoke() calls.
        """
        from langchain_classic.chains import ConversationalRetrievalChain
        from langchain_core.prompts import PromptTemplate

        qa_template = self._prompts.get("qa_prompt_template", _DEFAULT_QA_TEMPLATE)
        condense_template = self._prompts.get("condense_question_prompt", _DEFAULT_CONDENSE_TEMPLATE)

        qa_prompt = PromptTemplate(
            template=qa_template,
            input_variables=["context", "chat_history", "question"],
        )
        condense_prompt = PromptTemplate(
            template=condense_template,
            input_variables=["chat_history", "question"],
        )

        chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=retriever,
            memory=memory,
            return_source_documents=True,
            combine_docs_chain_kwargs={"prompt": qa_prompt},
            condense_question_prompt=condense_prompt,
            verbose=False,
        )
        logger.debug("ConversationalRetrievalChain built.")
        return chain

    def build_summary_chain(self):
        """Build a chain for summarising a single document.

        Returns:
            LLMChain for document summarisation.
        """
        from langchain_classic.chains import LLMChain
        from langchain_core.prompts import PromptTemplate

        template = self._prompts.get("document_summary_prompt", _DEFAULT_SUMMARY_TEMPLATE)
        prompt = PromptTemplate(
            template=template, input_variables=["document_text"]
        )
        return LLMChain(llm=self.llm, prompt=prompt, verbose=False)

    def build_query_expansion_chain(self):
        """Build a chain that generates multiple query variants.

        Returns:
            LLMChain for multi-query generation.
        """
        from langchain_classic.chains import LLMChain
        from langchain_core.prompts import PromptTemplate

        template = self._prompts.get("multi_query_prompt", _DEFAULT_MULTI_QUERY_TEMPLATE)
        prompt = PromptTemplate(template=template, input_variables=["question"])
        return LLMChain(llm=self.llm, prompt=prompt, verbose=False)

    # ─────────────────────────────────────────────────────────────────────────
    # Streaming
    # ─────────────────────────────────────────────────────────────────────────

    def stream_response(self, chain, query: str, chat_history: list) -> Generator[str, None, None]:
        """Stream LLM response tokens via a generator.

        Args:
            chain: A ConversationalRetrievalChain.
            query: User question.
            chat_history: Formatted chat history list.

        Yields:
            Individual response tokens as strings.
        """
        try:
            streaming_llm = self.get_llm(streaming=True)
            from langchain_classic.chains import ConversationalRetrievalChain
            stream_chain = ConversationalRetrievalChain.from_llm(
                llm=streaming_llm,
                retriever=chain.retriever,
                return_source_documents=True,
                verbose=False,
            )
            result = stream_chain.invoke(
                {"question": query, "chat_history": chat_history}
            )
            answer = result.get("answer", "")
            # Simulate token-level streaming from the full answer
            words = answer.split()
            for i, word in enumerate(words):
                yield word + (" " if i < len(words) - 1 else "")
        except Exception as exc:
            logger.error(f"Streaming failed: {exc}")
            yield f"Error generating response: {exc}"

    # ─────────────────────────────────────────────────────────────────────────
    # Stats
    # ─────────────────────────────────────────────────────────────────────────

    def get_llm_stats(self) -> dict:
        """Return runtime statistics for the LLM manager."""
        avg_response = (
            self._total_time / self._total_calls if self._total_calls else 0.0
        )
        return {
            "provider": self.provider,
            "model_name": self.model_name,
            "temperature": self.temperature,
            "total_calls": self._total_calls,
            "total_tokens": self._total_tokens,
            "avg_response_time_s": round(avg_response, 3),
        }

    # ─────────────────────────────────────────────────────────────────────────
    # Private helpers
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _load_prompts(prompts_path: str = "config/prompts.yaml") -> dict:
        try:
            with open(prompts_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            logger.warning(f"Prompts file not found at {prompts_path}. Using defaults.")
            return {}


# ─────────────────────────────────────────────────────────────────────────────
# Default prompt fallbacks
# ─────────────────────────────────────────────────────────────────────────────

_DEFAULT_QA_TEMPLATE = """Context from documents:
{context}

Conversation history:
{chat_history}

Question: {question}

Answer based strictly on the context above. Cite your source document when possible.
If the information is not in the documents, say so clearly.

Answer:"""

_DEFAULT_CONDENSE_TEMPLATE = """Given the conversation history and follow-up question,
rephrase the follow-up as a standalone question.

History: {chat_history}
Follow-up: {question}
Standalone question:"""

_DEFAULT_SUMMARY_TEMPLATE = """Summarise the following document in 3-5 bullet points,
focusing on main topics, key facts, and important figures:

{document_text}

Summary:"""

_DEFAULT_MULTI_QUERY_TEMPLATE = """Generate 3 different versions of this question
to retrieve relevant documents. Separate by newlines.
Original: {question}
Alternatives:"""
