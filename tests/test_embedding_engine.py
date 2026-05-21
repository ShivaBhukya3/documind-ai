"""Unit tests for EmbeddingEngine."""

import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.document_processor import load_config
from src.embedding_engine import EmbeddingEngine


@pytest.fixture
def config():
    return load_config("config/config.yaml")


@pytest.fixture
def engine(config):
    # Always use HuggingFace in tests to avoid requiring API keys
    cfg = {**config, "embeddings": {"provider": "huggingface", "fallback": "sentence-transformers/all-MiniLM-L6-v2", "batch_size": 10}}
    os.environ.setdefault("FREE_MODE", "true")
    return EmbeddingEngine(cfg)


class TestEmbedQuery:
    def test_embed_single_query_returns_vector(self, engine):
        vec = engine.embed_query("What is the leave policy?")
        assert isinstance(vec, list)
        assert len(vec) > 0
        assert all(isinstance(v, float) for v in vec)

    def test_embed_query_consistent_dimension(self, engine):
        v1 = engine.embed_query("query one")
        v2 = engine.embed_query("query two")
        assert len(v1) == len(v2)

    def test_embed_empty_string(self, engine):
        vec = engine.embed_query("")
        assert isinstance(vec, list)


class TestEmbedDocuments:
    def test_embed_multiple_texts(self, engine):
        texts = ["Text about annual leave.", "Revenue grew by 32%.", "Python installation guide."]
        vectors = engine.embed_documents(texts)
        assert len(vectors) == 3
        assert all(len(v) > 0 for v in vectors)

    def test_embed_empty_list(self, engine):
        result = engine.embed_documents([])
        assert result == []

    def test_embed_single_text(self, engine):
        result = engine.embed_documents(["Single text."])
        assert len(result) == 1


class TestComputeSimilarity:
    def test_identical_texts_high_similarity(self, engine):
        text = "The employee is entitled to 18 days of annual leave."
        v1 = engine.embed_query(text)
        v2 = engine.embed_query(text)
        sim = engine.compute_similarity(v1, v2)
        assert sim > 0.98

    def test_paraphrase_high_similarity(self, engine):
        v1 = engine.embed_query("18 days annual leave per year")
        v2 = engine.embed_query("employees get 18 vacation days annually")
        sim = engine.compute_similarity(v1, v2)
        assert sim > 0.75

    def test_unrelated_texts_lower_similarity(self, engine):
        v1 = engine.embed_query("annual leave policy")
        v2 = engine.embed_query("database schema and SQL queries")
        sim = engine.compute_similarity(v1, v2)
        assert sim < 0.95

    def test_similarity_range(self, engine):
        v1 = engine.embed_query("hello world")
        v2 = engine.embed_query("goodbye universe")
        sim = engine.compute_similarity(v1, v2)
        assert -1.0 <= sim <= 1.0


class TestFallback:
    def test_fallback_to_huggingface_when_no_key(self, config):
        original_key = os.environ.pop("OPENAI_API_KEY", None)
        try:
            cfg = {**config, "embeddings": {"provider": "openai", "model_name": "text-embedding-ada-002", "fallback": "sentence-transformers/all-MiniLM-L6-v2", "batch_size": 10}}
            # Make sure FREE_MODE is false so it triggers auto-fallback logic
            os.environ["FREE_MODE"] = "false"
            engine = EmbeddingEngine(cfg)
            assert engine.provider == "huggingface"
        finally:
            if original_key:
                os.environ["OPENAI_API_KEY"] = original_key
            os.environ["FREE_MODE"] = "true"


class TestStats:
    def test_get_embedding_stats(self, engine):
        engine.embed_query("test")
        stats = engine.get_embedding_stats()
        assert "provider" in stats
        assert "model_name" in stats
        assert "total_embedded" in stats
        assert stats["total_embedded"] >= 1

    def test_test_embeddings(self, engine):
        result = engine.test_embeddings()
        assert result is True
