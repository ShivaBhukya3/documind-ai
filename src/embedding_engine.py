"""Embedding engine — wraps OpenAI and HuggingFace embedding providers."""

import os
import time
from functools import lru_cache
from typing import Optional

import numpy as np
from loguru import logger


class EmbeddingEngine:
    """Manages embedding model initialisation and text vectorisation.

    Supports OpenAI text-embedding-ada-002 and HuggingFace sentence-transformers.
    Automatically falls back to HuggingFace when no OpenAI key is available or
    when FREE_MODE=true is set in the environment.
    """

    def __init__(self, config: dict) -> None:
        """Initialise embedding engine from config.

        Args:
            config: Full application config dict (from config.yaml).
        """
        self.config = config
        emb_cfg = config.get("embeddings", {})
        self.provider: str = emb_cfg.get("provider", "openai")
        self.model_name: str = emb_cfg.get("model_name", "text-embedding-ada-002")
        self.fallback_model: str = emb_cfg.get(
            "fallback", "sentence-transformers/all-MiniLM-L6-v2"
        )
        self.dimension: int = emb_cfg.get("dimension", 1536)
        self.batch_size: int = emb_cfg.get("batch_size", 100)

        self._total_embedded: int = 0
        self._cache_hits: int = 0
        self._embeddings_obj = None  # lazy-loaded

        # Honour FREE_MODE env var
        free_mode = os.getenv("FREE_MODE", "false").lower() == "true"
        if free_mode:
            logger.info("FREE_MODE enabled — switching to HuggingFace embeddings.")
            self.provider = "huggingface"
            free_cfg = config.get("free_mode", {})
            self.model_name = free_cfg.get(
                "embedding_model", "sentence-transformers/all-MiniLM-L6-v2"
            )
            self.dimension = free_cfg.get("embedding_dimension", 384)

        # Auto-fallback if no OpenAI key
        if self.provider == "openai" and not os.getenv("OPENAI_API_KEY"):
            logger.warning("OPENAI_API_KEY not set — falling back to fastembed.")
            self.provider = "fastembed"
            self.model_name = "BAAI/bge-small-en-v1.5"
            self.dimension = 384

        logger.info(
            f"EmbeddingEngine initialised | provider={self.provider} | model={self.model_name}"
        )

    # ─────────────────────────────────────────────────────────────────────────
    # LangChain Embeddings Object
    # ─────────────────────────────────────────────────────────────────────────

    def get_embeddings(self, provider: Optional[str] = None):
        """Return a LangChain-compatible Embeddings object."""
        provider = provider or self.provider

        if provider == "openai":
            return self._get_openai_embeddings()
        if provider == "huggingface":
            return self._get_huggingface_embeddings()
        return self._get_fastembed_embeddings()

    def _get_openai_embeddings(self):
        try:
            from langchain_openai import OpenAIEmbeddings
        except ImportError:
            from langchain.embeddings import OpenAIEmbeddings  # type: ignore

        logger.debug("Loading OpenAI embeddings model.")
        return OpenAIEmbeddings(
            model=self.model_name,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
        )

    def _get_fastembed_embeddings(self):
        from langchain_community.embeddings import FastEmbedEmbeddings
        logger.debug(f"Loading FastEmbed model: {self.model_name}")
        return FastEmbedEmbeddings(model_name=self.model_name)

    def _get_huggingface_embeddings(self):
        try:
            from langchain_community.embeddings import HuggingFaceEmbeddings
        except ImportError:
            from langchain.embeddings import HuggingFaceEmbeddings  # type: ignore

        logger.debug(f"Loading HuggingFace embeddings model: {self.model_name}")
        return HuggingFaceEmbeddings(
            model_name=self.model_name,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )

    @property
    def embeddings(self):
        """Lazy-load and cache the embeddings object."""
        if self._embeddings_obj is None:
            self._embeddings_obj = self.get_embeddings()
        return self._embeddings_obj

    # ─────────────────────────────────────────────────────────────────────────
    # Core embedding methods
    # ─────────────────────────────────────────────────────────────────────────

    def embed_query(self, query: str) -> list[float]:
        """Embed a single query string.

        Args:
            query: The query text to embed.

        Returns:
            Embedding vector as a list of floats.
        """
        start = time.time()
        vector = self.embeddings.embed_query(query)
        self._total_embedded += 1
        logger.debug(f"Query embedded in {(time.time()-start)*1000:.1f} ms.")
        return vector

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Batch embed multiple texts with progress logging.

        Args:
            texts: List of text strings to embed.

        Returns:
            List of embedding vectors.
        """
        if not texts:
            return []

        logger.info(f"Embedding {len(texts)} texts in batches of {self.batch_size}.")
        all_vectors: list[list[float]] = []
        start = time.time()

        for i in range(0, len(texts), self.batch_size):
            batch = texts[i: i + self.batch_size]
            vectors = _embed_with_backoff(self.embeddings, batch)
            all_vectors.extend(vectors)
            logger.debug(f"  Embedded batch {i // self.batch_size + 1} ({len(batch)} texts).")

        self._total_embedded += len(texts)
        elapsed = time.time() - start
        logger.info(f"Embedded {len(texts)} texts in {elapsed:.2f}s ({len(texts)/elapsed:.1f} texts/s).")
        return all_vectors

    def compute_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """Compute cosine similarity between two embedding vectors.

        Args:
            vec1: First embedding vector.
            vec2: Second embedding vector.

        Returns:
            Cosine similarity score in [-1, 1].
        """
        a = np.array(vec1, dtype=np.float32)
        b = np.array(vec2, dtype=np.float32)
        denom = np.linalg.norm(a) * np.linalg.norm(b)
        if denom == 0:
            return 0.0
        return float(np.dot(a, b) / denom)

    # ─────────────────────────────────────────────────────────────────────────
    # Stats & validation
    # ─────────────────────────────────────────────────────────────────────────

    def get_embedding_stats(self) -> dict:
        """Return runtime statistics for the embedding engine."""
        return {
            "provider": self.provider,
            "model_name": self.model_name,
            "dimension": self.dimension,
            "total_embedded": self._total_embedded,
            "cache_hits": self._cache_hits,
        }

    def test_embeddings(self) -> bool:
        """Run a quick smoke test to verify embeddings are working.

        Returns:
            True if test passes, False otherwise.
        """
        try:
            vec = self.embed_query("test query for DocuMind AI")
            assert len(vec) > 0, "Empty embedding returned."
            logger.info(f"Embedding test passed. Vector dimension: {len(vec)}")
            self.dimension = len(vec)
            return True
        except Exception as exc:
            logger.error(f"Embedding test failed: {exc}")
            return False


# ─────────────────────────────────────────────────────────────────────────────
# Private helpers
# ─────────────────────────────────────────────────────────────────────────────

def _get_device() -> str:
    try:
        import torch
        return "cuda" if torch.cuda.is_available() else "cpu"
    except ImportError:
        return "cpu"


def _embed_with_backoff(embeddings_obj, texts: list[str], max_retries: int = 3) -> list[list[float]]:
    """Call embeddings.embed_documents with exponential backoff on rate limit."""
    for attempt in range(max_retries):
        try:
            return embeddings_obj.embed_documents(texts)
        except Exception as exc:
            if attempt == max_retries - 1:
                raise
            wait = 2 ** attempt
            logger.warning(f"Embedding attempt {attempt + 1} failed ({exc}). Retrying in {wait}s.")
            time.sleep(wait)
    return []
