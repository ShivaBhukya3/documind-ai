"""Unit tests for AdvancedRetriever."""

import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

os.environ.setdefault("FREE_MODE", "true")

from src.document_processor import DocumentProcessor, load_config
from src.embedding_engine import EmbeddingEngine
from src.retriever import AdvancedRetriever
from src.vector_store import VectorStoreManager

try:
    from langchain.schema import Document
except ImportError:
    from langchain_core.documents import Document


@pytest.fixture(scope="module")
def config():
    return load_config("config/config.yaml")


@pytest.fixture(scope="module")
def populated_vsm(config, tmp_path_factory):
    tmp = tmp_path_factory.mktemp("vsm_test")
    cfg = {
        **config,
        "vector_store": {**config.get("vector_store", {}), "index_path": str(tmp / "idx"), "top_k": 3},
        "retrieval": {"search_type": "mmr", "fetch_k": 6, "lambda_mult": 0.5, "score_threshold": 0.0},
    }
    engine = EmbeddingEngine(cfg)
    vsm = VectorStoreManager(cfg, engine.embeddings)

    docs = [
        Document(page_content="TechCorp employees receive 18 days annual leave per year.", metadata={"filename": "policy.pdf", "chunk_id": "c1", "chunk_index": 0, "document_hash": "h1"}),
        Document(page_content="Maternity leave is 26 weeks as per the Maternity Benefit Act.", metadata={"filename": "policy.pdf", "chunk_id": "c2", "chunk_index": 1, "document_hash": "h2"}),
        Document(page_content="TechCorp revenue in FY2024 was ₹45 Crore, up 32% YoY.", metadata={"filename": "finance.pdf", "chunk_id": "c3", "chunk_index": 2, "document_hash": "h3"}),
        Document(page_content="Python 3.10 is required for installation.", metadata={"filename": "manual.pdf", "chunk_id": "c4", "chunk_index": 3, "document_hash": "h4"}),
        Document(page_content="The company EBITDA margin improved to 28%.", metadata={"filename": "finance.pdf", "chunk_id": "c5", "chunk_index": 4, "document_hash": "h5"}),
    ]
    vsm.create_vector_store(docs)
    return vsm, cfg


@pytest.fixture(scope="module")
def retriever(populated_vsm):
    vsm, cfg = populated_vsm
    return AdvancedRetriever(vsm, cfg)


class TestSimilaritySearch:
    def test_returns_documents(self, retriever):
        docs = retriever.get_relevant_documents("annual leave policy")
        assert len(docs) >= 1

    def test_returns_relevant_content(self, retriever):
        docs = retriever.get_relevant_documents("revenue and financial results")
        texts = " ".join(d.page_content for d in docs)
        assert "45" in texts or "revenue" in texts.lower() or "crore" in texts.lower()

    def test_mmr_search_diversity(self, populated_vsm):
        vsm, cfg = populated_vsm
        docs = vsm.mmr_search("employee policy", k=3, fetch_k=5)
        assert len(docs) >= 1


class TestScoreThreshold:
    def test_score_threshold_filter(self, populated_vsm):
        vsm, cfg = populated_vsm
        results = vsm.similarity_search_with_score("annual leave")
        assert isinstance(results, list)


class TestFormatDocsForContext:
    def test_format_returns_string(self, retriever):
        docs = retriever.get_relevant_documents("leave policy")
        context = retriever.format_docs_for_context(docs)
        assert isinstance(context, str)
        assert len(context) > 0

    def test_format_includes_source(self, retriever):
        docs = retriever.get_relevant_documents("revenue")
        context = retriever.format_docs_for_context(docs)
        assert "Source" in context

    def test_format_empty_docs(self, retriever):
        result = retriever.format_docs_for_context([])
        assert "No relevant" in result


class TestRetrievalStats:
    def test_stats_returns_dict(self, retriever):
        docs = retriever.get_relevant_documents("leave policy")
        stats = retriever.get_retrieval_stats("leave policy", docs)
        assert "num_retrieved" in stats
        assert "sources_used" in stats
        assert stats["num_retrieved"] == len(docs)
